from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import time

# Set up Chrome in headless mode
options = webdriver.ChromeOptions()
options.add_argument("--headless")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

url = "https://www.cdr.fyi/leaderboards"
driver.get(url)
wait = WebDriverWait(driver, 15)

# Wait for the table to load initially
wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))

all_dfs = []

for page in range(1, 20):  # Pages 1 through 19
    print(f"📄 Scraping page {page}...")

    # Wait for the page number button and click it
    try:
        button_xpath = f"//nav//ul//li/button[normalize-space(text())='{page}']"
        page_button = wait.until(EC.element_to_be_clickable((By.XPATH, button_xpath)))
        page_button.click()
    except TimeoutException:
        print(f"❌ Page {page} button not found.")
        break

    # Wait a bit for table to update
    time.sleep(2)

    # Grab the updated table
    soup = BeautifulSoup(driver.page_source, "html.parser")
    table_html = str(soup.find("table"))
    df = pd.read_html(table_html)[0]
    all_dfs.append(df)

# Done
driver.quit()

# Save result
final_df = pd.concat(all_dfs, ignore_index=True)
final_df.to_csv("cdr_suppliers_full.csv", index=False)
print("✅ All 19 pages scraped and saved to 'cdr_suppliers_full.csv'")
