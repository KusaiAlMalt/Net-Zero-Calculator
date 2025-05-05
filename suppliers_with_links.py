from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
from bs4 import BeautifulSoup

# Setup Chrome in headless mode
options = Options()
options.add_argument("--headless")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# Läs in CSV-filen som redan har CDR_Link
df = pd.read_csv("cdr_suppliers_with_links.csv")

# Skapa en lista för att lagra nya data
company_links = []

# Funktion för att hämta Company Link från en CDR-Link
def fetch_company_link(cdr_link):
    driver.get(cdr_link)
    time.sleep(2)  # Vänta för att sidan ska ladda ordentligt

    soup = BeautifulSoup(driver.page_source, "html.parser")
    
    # Hämta företagslänken baserat på den specifika klassen (eller andra attribut)
    try:
        company_link_tag = soup.find("a", class_="text-muted-foreground")
        company_link = company_link_tag.get("href") if company_link_tag else "N/A"
        print(f"Found company link: {company_link}")
    except AttributeError:
        company_link = "N/A"
        print('Company link not found.')
    
    return company_link

# Loopa genom alla CDR_link och hämta Company_Link
for index, row in df.iterrows():
    cdr_link = row['CDR_Link']
    if cdr_link:
        print(f"Scraping Company Link for index {index} and link: {cdr_link}")
        company_link = fetch_company_link(cdr_link)
    else:
        company_link = "N/A"
    company_links.append(company_link)

# Lägg till Company_Link som en ny kolumn i DataFrame
df['Company_Link'] = company_links

# Stäng webbläsaren
driver.quit()

# Spara den uppdaterade DataFrame till en ny CSV-fil
df.to_csv("cdr_suppliers_with_links_and_company.csv", index=False)
print("✅ All data scraped and saved to 'cdr_suppliers_with_links_and_company.csv'")
