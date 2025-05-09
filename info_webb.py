from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Setup for Selenium WebDriver
driver = webdriver.Chrome()

# Open the webpage
url = "https://tradingeconomics.com/commodity/carbon"
driver.get(url)

# Wait for the page to load
try:
    # Wait for the element with the specified CSS selector to become visible
    price_element = WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "#item_definition > div.table-responsive > table > tbody > tr > td:nth-child(2)"))
    )
    # Retrieve and print the current price
    price = price_element.text
    print(f"Nuvarande pris: {price}")
    with open("emmisssonrights_price.txt", "w") as f:
            f.write(str(price))
except Exception as e:
    print(f"Fel vid hämtning av pris: {e}")
finally:
    # Close the browser
    driver.quit()




