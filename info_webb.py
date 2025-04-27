from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Setup för Selenium WebDriver
driver = webdriver.Chrome()

# Öppna sidan
url = "https://tradingeconomics.com/commodity/carbon"
driver.get(url)

# Vänta på att sidan ska ladda
try:
    # Vänta på att elementet med den angivna CSS-selektorn ska bli synligt
    price_element = WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "#item_definition > div.table-responsive > table > tbody > tr > td:nth-child(2)"))
    )
    # Hämta och skriv ut det aktuella priset
    price = price_element.text
    print(f"Nuvarande pris: {price}")
    with open("emmisssonrights_price.txt", "w") as f:
            f.write(str(price))
except Exception as e:
    print(f"Fel vid hämtning av pris: {e}")
finally:
    # Stäng webbläsaren
    driver.quit()




