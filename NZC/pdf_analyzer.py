"""
pdf_analyzer.py

This module provides functions for extracting text and tables from PDFs, creating vector stores,
and analyzing the extracted text using GPT to extract specific data.
"""

import pdfplumber
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
import os
from dotenv import load_dotenv
import openai
import json

# Load environment variables
load_dotenv()

# Initialize OpenAI client and embeddings
#client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
#embeddings = OpenAIEmbeddings()

def extract_text_from_pdf(pdf_file):
    """
    Extract text and tables from a PDF file.

    Args:
        pdf_file (str or file-like object): The path to the PDF file or a file-like object.

    Returns:
        str: A string containing the extracted text and tables, cleaned and concatenated.
    """
    full_text = []
    tables_text = []
    
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text(x_tolerance=1.5, y_tolerance=1.5)
            if text:
                full_text.append(text)
            tables = page.extract_tables()
            if not tables:
                tables = page.find_tables()
            for table in tables:
                table_text = "\n".join([" | ".join([str(cell) for cell in row if cell]) for row in table if any(row)])
                tables_text.append(table_text)
    
    all_text = "\n\n".join(full_text + tables_text)
    all_text = "\n".join([line for line in all_text.splitlines() if len(line.strip()) > 10])
    return all_text

def create_vector_store(text):
    """
    Create a FAISS vector store from the given text.

    Args:
        text (str): The text to be split into chunks and embedded.

    Returns:
        FAISS: A FAISS vector store containing the text chunks and their embeddings.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=400,
        separators=[
            "\n\n", "\n", ".", "Scope", "MSEK", "Utsläpp", "Resultat", "|"
        ]
    )
    chunks = splitter.split_text(text)
    return FAISS.from_texts(chunks, embeddings)

def analyze_with_gpt(context):
    """
    Analyze extracted text using GPT and return structured data in JSON format.

    Args:
        context (str): The text to be analyzed by GPT.

    Returns:
        dict or None: A dictionary containing extracted values (e.g., Scope 1, Scope 2, Scope 3 emissions, and profit),
                      or None if the analysis fails.
    """
    prompt = f"""
Analysera text från en årsredovisning på svenska eller engelska och extrahera:

- Scope 1 (direkta utsläpp, i ton CO2e)
- Scope 2 (indirekta utsläpp, i ton CO2e, prioritera market-based)
- Scope 3 (övriga indirekta utsläpp, i ton CO2e)
- Resultat före skatt (profit before tax, i MSEK)

**Instruktioner:**
- Leta Scope-värden i tabeller.
- Leta resultat före skatt både i tabeller och löpande text.
- Extrahera endast siffror som heltal utan enheter eller parenteser.
- Välj alltid senaste årets värde.
- Om värde saknas, skriv null.

**Format på svaret:**

{{
  "scope_1": heltal eller null,
  "scope_1_year": heltal eller null,
  "scope_2": heltal eller null,
  "scope_2_year": heltal eller null,
  "scope_3": heltal eller null,
  "scope_3_year": heltal eller null,
  "profit_before_tax": heltal eller null,
  "profit_year": heltal eller null
}}

Svara endast med en korrekt JSON-struktur, inget annat.

Text att analysera:
{context}
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo-2024-04-09",  # SNABBARE och BILLIGARE modell
            temperature=0.2,
            timeout=60,
            messages=[
                {"role": "system", "content": "Du är en expert på hållbarhetsrapporter. Följ instruktionerna exakt och svara endast med JSON."},
                {"role": "user", "content": prompt}
            ]
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"GPT Error: {str(e)}")
        return None

def extract_info_from_pdf(pdf_file):
    """
    Main function to extract and analyze information from a PDF file.

    Args:
        pdf_file (str or file-like object): The path to the PDF file or a file-like object.

    Returns:
        dict: A dictionary containing:
            - 'extracted_values': Extracted Scope 1, Scope 2, Scope 3 emissions, and profit.
            - 'text_sample': A sample of the extracted text.
            - 'relevant_contexts': Relevant contexts used for analysis.
    """
    text = extract_text_from_pdf(pdf_file)
    vectordb = create_vector_store(text)
    
    queries = [
        "scope 1 utsläpp greenhouse gas emissions GHG",
        "scope 2 indirekta utsläpp market-based electricity emissions",
        "scope 3 värdekedja supply chain emissions",
        "vinst före skatt resultat före skatt profit before tax"
    ]
    
    all_contexts = []
    for query in queries:
        docs = vectordb.similarity_search(query, k=3)
        contexts = [doc.page_content for doc in docs]
        all_contexts.extend(contexts)

    unique_contexts = []
    for context in all_contexts:
        if context not in unique_contexts:
            unique_contexts.append(context)

    # Begränsa textmängden
    max_tokens = 12000
    current_length = 0
    selected_contexts = []

    for context in unique_contexts:
        context_length = len(context.split())
        if current_length + context_length <= max_tokens:
            selected_contexts.append(context)
            current_length += context_length
        else:
            break

    combined_context = "\n\n---\n\n".join(selected_contexts)

    extracted_values = analyze_with_gpt(combined_context)
    # Sätt till '-' om värdet är None
    if extracted_values is None:
        extracted_values = {}
    for key in ["scope_1", "scope_2", "scope_3", "profit_before_tax"]:
        if extracted_values.get(key) is None:
            extracted_values[key] = "-"
    return {
        'extracted_values': {
            'scope1': extracted_values.get('scope_1', '-'),
            'scope2': extracted_values.get('scope_2', '-'),
            'scope3': extracted_values.get('scope_3', '-'),
            'profit': extracted_values.get('profit_before_tax', '-')
        },
        'text_sample': text[:1000],
        'relevant_contexts': unique_contexts
    }
