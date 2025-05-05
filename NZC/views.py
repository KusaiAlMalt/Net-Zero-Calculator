from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Result
from calculator1 import *
from .pdf_analyzer import extract_info_from_pdf
import math
import os
import pandas as pd
from django.conf import settings

openai_enabled = os.getenv("OPENAI_API_KEY") is not None

# Create your views here.
def index(request):
    return render(request, 'index.html', {'openai_enabled': openai_enabled})

def about(request):
    return render(request, 'about.html', {'openai_enabled': openai_enabled})

def pdf(request):
    return render(request, 'pdf.html', {'openai_enabled': openai_enabled})

def manual(request):
    return render(request, 'manual.html', {"scopes" : [1,2,3], 'openai_enabled': openai_enabled})

def results(request):
    context = {}  # Initialize context as empty dictionary
    
    # Exempel på kostnadsintervall (du kan lägga till fler eller ändra)
    removal_methods = {
        'Direct Air Capture': (100, 345),      # Cost in U.S. dollars per ton of CO₂
        'Biochar': (10, 345),
        'Reforestation': (5, 240),
        'Enhanced Weathering': (50, 200),
        'BECCS': (15, 400),
        'Soil carbon sequestration': (45, 100)
    }
    
    if request.method == 'POST':
        if request.FILES.get('file'):
            pdf_file = request.FILES.get('file')

            if not pdf_file.name.endswith('.pdf'):
                messages.error(request, 'File is not PDF type')
                return redirect('index')

            try:
                # Use the PDF analyzer to get initial data
                analysis_results = extract_info_from_pdf(pdf_file)
                extracted_values = analysis_results['extracted_values']
                
                # Sätt defaultvärden till '-' om de saknas
                data = {
                    'scope1': extracted_values.get('scope1', '-'),
                    'scope2': extracted_values.get('scope2', '-'),
                    'scope3': extracted_values.get('scope3', '-'),
                    'profit': extracted_values.get('profit', '-')
                }

                # Om alla scope-värden är siffror, kör beräkning och visa tabell
                if all(isinstance(data[k], int) or (isinstance(data[k], str) and data[k].isdigit()) for k in ['scope1', 'scope2', 'scope3']):
                    # Konvertera strängar till int om det behövs
                    for k in ['scope1', 'scope2', 'scope3']:
                        if isinstance(data[k], str):
                            data[k] = int(data[k])
                    # profit kan vara '-' så vi hanterar den separat
                    if isinstance(data['profit'], str) and data['profit'].isdigit():
                        data['profit'] = int(data['profit'])
                    results = get_results(data)

                    # Beräkna kostnader per metod
                    costs_per_method = {}
                    price_per_ton = {}
                    for method, (low, high) in removal_methods.items():
                        total_low = math.ceil((data['scope1'] + data['scope2'] + data['scope3']) * low * 10 / 1_000)
                        total_high = math.ceil((data['scope1'] + data['scope2'] + data['scope3']) * high * 10 / 1_000)
                        profit_tsek = data['profit'] * 1000 if isinstance(data['profit'], (int, float)) and data['profit'] != 0 else None
                        if profit_tsek:
                            percent_low = round((total_low / profit_tsek) * 100, 1) if total_low else "-"
                            percent_high = round((total_high / profit_tsek) * 100, 1) if total_high else "-"
                        else:
                            percent_low = percent_high = "-"
                        costs_per_method[method] = {
                            'scope1': (math.ceil(data['scope1'] * low * 10 / 1_000), math.ceil(data['scope1'] * high * 10 / 1_000)),
                            'scope2': (math.ceil(data['scope2'] * low * 10 / 1_000), math.ceil(data['scope2'] * high * 10 / 1_000)),
                            'scope3': (math.ceil(data['scope3'] * low * 10 / 1_000), math.ceil(data['scope3'] * high * 10 / 1_000)),
                            'total': (total_low, total_high),
                            'profit_total_percent': (percent_low, percent_high)
                        }
                        price_per_ton[method] = (low * 10, high * 10)  # SEK per ton
                    context = {
                        'results': results,
                        'text_sample': analysis_results['text_sample'],
                        'relevant_contexts': analysis_results['relevant_contexts'],
                        'costs_per_method': costs_per_method,
                        'price_per_ton': price_per_ton
                    }
                else:
                    results = (
                        f"Scope 1: {data['scope1']}\n"
                        f"Scope 2: {data['scope2']}\n"
                        f"Scope 3: {data['scope3']}\n"
                        f"Vinst (MSEK): {data['profit']}"
                    )
                    context = {
                        'results': results,
                        'text_sample': analysis_results['text_sample'],
                        'relevant_contexts': analysis_results['relevant_contexts']
                    }
            except Exception as e:
                messages.error(request, f'Error analyzing PDF: {str(e)}')
                return redirect('index')

        elif request.POST.get('scope1') and request.POST.get('scope2') and request.POST.get('scope3') and request.POST.get('profit'):
            data = {
                'scope1': int(request.POST.get('scope1')), 
                'scope2': int(request.POST.get('scope2')), 
                'scope3': int(request.POST.get('scope3')),
                'profit': int(request.POST.get('profit'))
            }
            results = get_results(data)
            context = {
                'results': results
            }

            # Beräkna kostnader per metod
            costs_per_method = {}
            price_per_ton = {}
            for method, (low, high) in removal_methods.items():
                total_low = math.ceil((data['scope1'] + data['scope2'] + data['scope3']) * low * 10 / 1_000)
                total_high = math.ceil((data['scope1'] + data['scope2'] + data['scope3']) * high * 10 / 1_000)
                profit_tsek = data['profit'] * 1000 if isinstance(data['profit'], (int, float)) and data['profit'] != 0 else None
                if profit_tsek:
                    percent_low = round((total_low / profit_tsek) * 100, 1) if total_low else "-"
                    percent_high = round((total_high / profit_tsek) * 100, 1) if total_high else "-"
                else:
                    percent_low = percent_high = "-"
                costs_per_method[method] = {
                    'scope1': (math.ceil(data['scope1'] * low * 10 / 1_000), math.ceil(data['scope1'] * high * 10 / 1_000)),
                    'scope2': (math.ceil(data['scope2'] * low * 10 / 1_000), math.ceil(data['scope2'] * high * 10 / 1_000)),
                    'scope3': (math.ceil(data['scope3'] * low * 10 / 1_000), math.ceil(data['scope3'] * high * 10 / 1_000)),
                    'total': (total_low, total_high),
                    'profit_total_percent': (percent_low, percent_high)
                }
                price_per_ton[method] = (low * 10, high * 10)  # SEK per ton
            context['costs_per_method'] = costs_per_method
            context['price_per_ton'] = price_per_ton
        else:
            messages.error(request, 'Missing required data')
            return redirect('index')
    else:
        messages.error(request, 'Please submit data first')
        return redirect('index')
        
    context['openai_enabled'] = openai_enabled

    # save results to database
    result = Result(
        scope1=data['scope1'],
        scope2=data['scope2'],
        scope3=data['scope3'],
        profit=data['profit'],
        pdfname=pdf_file.name if request.FILES.get('file') else None,
        email=None
    )
    result.save()
    context["result_id"] =  result.id
    return render(request, 'results.html', context)

def ccs_methods(request):
    csv_path = os.path.join(settings.BASE_DIR, 'cdr_suppliers_with_links_and_company.csv')
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip()  # Tar bort eventuella mellanslag

    methods = [
        "Biochar Carbon Removal (BCR)",
        "Enhanced Weathering",
        "Ex-situ Mineralization",
        "Direct Air Carbon Capture and Storage (DACCS)",
        "Bioenergy with Carbon Capture and Storage (BECCS)"
    ]

    method_tables = {}
    for method in methods:
        suppliers = df[df['Method'] == method][['Name', 'Tons Delivered', 'Tons Sold', 'Company_Link']].to_dict(orient='records')
        method_tables[method] = suppliers

    columns = ['Name', 'Tons Delivered', 'Tons Sold', 'Company_Link']

    context = {
        'method_tables': method_tables,
        'columns': columns,
    }
    return render(request, 'ccs_methods.html', context)
