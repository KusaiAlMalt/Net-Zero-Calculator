from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException, 
    StaleElementReferenceException
)
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
import os

def setup_driver(headless=False):
    """Configure and return a Chrome webdriver with appropriate options."""
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

def load_target_companies(csv_file):
    """Load the list of target companies from CSV file."""
    try:
        if not os.path.exists(csv_file):
            print(f"Error: Target companies file {csv_file} not found.")
            return []
            
        df = pd.read_csv(csv_file)
        # Get company names and their delivery tonnage
        companies = []
        for _, row in df.iterrows():
            companies.append({
                'name': row['Name'],
                'tons': row['Tons Delivered'] if 'Tons Delivered' in df.columns else None,
                'method': row['Method'] if 'Method' in df.columns else None
            })
        print(f"Successfully loaded {len(companies)} target companies from {csv_file}")
        return companies
    except Exception as e:
        print(f"Error loading target companies: {e}")
        return []

def find_element_safely(driver, by, selector, max_attempts=3, wait_time=10):
    """Find a single element with retry mechanism for stale elements."""
    attempts = 0
    while attempts < max_attempts:
        try:
            # Try with explicit wait first
            element = WebDriverWait(driver, wait_time).until(
                EC.presence_of_element_located((by, selector))
            )
            return element
        except StaleElementReferenceException:
            print(f"Stale element when finding {selector}, retrying...")
            time.sleep(1)
            attempts += 1
        except TimeoutException:
            print(f"Timeout waiting for {selector}")
            return None
        except Exception as e:
            print(f"Error finding element {selector}: {e}")
            return None
    
    # If we reach here, we've exceeded max attempts
    print(f"Failed to find element {selector} after {max_attempts} attempts")
    return None

def click_element_safely(driver, element, max_attempts=3):
    """Try to safely click an element with retries."""
    attempts = 0
    while attempts < max_attempts:
        try:
            element.click()
            return True
        except StaleElementReferenceException:
            print("Encountered stale element, retrying...")
            time.sleep(1)
            attempts += 1
        except Exception as e:
            print(f"Error clicking element: {e}")
            # Try JavaScript click as a fallback
            try:
                driver.execute_script("arguments[0].click();", element)
                return True
            except:
                attempts += 1
    
    return False

def setup_map_interface(driver):
    """Initialize the map interface after page load."""
    print("Setting up map interface...")
    
    # Step 1: Wait for cookie consent (manual step, give time for user to accept)
    print("Please accept any cookie consent popups if they appear...")
    time.sleep(7)  # Time for manual interaction
    
    # Step 2: Click "Show list" button
    try:
        show_list_button = driver.find_element(By.XPATH, "//button[contains(.,'Show list')]")
        click_element_safely(driver, show_list_button)
        print("Clicked 'Show list' button")
        time.sleep(2)  # Wait for list to appear
    except Exception as e:
        print(f"Error clicking 'Show list' button: {e}")
        print("Will try to continue without clicking it...")
    
    print("Map interface setup completed.")
    return True

def get_geo_address(driver):
    """Extract the Geo Address Text from the list items."""
    try:
        # First, look for list items that contain "Geo Address Text"
        # Using XPath to find the precise element structure you provided
        geo_address_xpath = "//li[contains(@class, 'MuiListItem-root')][contains(@class, 'MuiListItem-divider')]//div[contains(text(), 'Geo Address Text')]/following-sibling::div"
        
        # Alternative approaches if needed
        geo_address_selectors = [
            # XPath approach (most precise)
            (By.XPATH, "//li[contains(@class, 'MuiListItem-root')][contains(@class, 'MuiListItem-divider')]//div[contains(text(), 'Geo Address Text')]/following-sibling::div"),
            
            # CSS selector approach (alternative)
            (By.CSS_SELECTOR, "li.MuiListItem-divider div.MuiTypography-colorTextPrimary"),
            
            # More general approach to find any address-like text
            (By.CSS_SELECTOR, "div.MuiTypography-colorTextPrimary")
        ]
        
        for by, selector in geo_address_selectors:
            try:
                elements = driver.find_elements(by, selector)
                
                for element in elements:
                    # For XPath, check directly
                    if by == By.XPATH:
                        text = element.text.strip()
                        if text:
                            return text
                    # For CSS selectors, check if it's below 'Geo Address Text'
                    else:
                        # Check the element or its siblings for 'Geo Address Text'
                        parent = element.find_element(By.XPATH, "./ancestor::li")
                        if "Geo Address Text" in parent.text:
                            return element.text.strip()
                        # Otherwise, check if text looks like an address
                        text = element.text.strip()
                        if text and "," in text and any(c.isdigit() for c in text) and len(text) > 10:
                            return text
            except Exception as e:
                print(f"Error with selector {selector}: {e}")
                continue
                
        print("⚠️ Could not find Geo Address Text")
        return "Address not found"
        
    except Exception as e:
        print(f"Error extracting Geo Address: {e}")
        return "Error extracting address"

def search_company_and_get_address(driver, company_name):
    """Search for company and extract Geo Address Text."""
    try:
        # Find the search input field
        search_input = find_element_safely(driver, By.CSS_SELECTOR, "input[placeholder='Search by name or location...']", wait_time=5)
        
        if not search_input:
            print(f"⚠️ Could not find search input field for company: {company_name}")
            return None
        
        # Clear any existing search text
        search_input.clear()
        time.sleep(0.5)
        
        # Type the company name in the search box
        search_input.send_keys(company_name)
        print(f"Searching for: {company_name}")
        time.sleep(1)  # Wait for search results
        
        # Press Enter to submit the search
        search_input.send_keys(Keys.RETURN)
        time.sleep(2)  # Wait for search results to load
        
        # First check if we need to click a search result
        result_buttons = driver.find_elements(By.CSS_SELECTOR, "button.MuiCardActionArea-root")
        if result_buttons:
            # Click the first search result
            click_element_safely(driver, result_buttons[0])
            print("Clicked on search result")
            time.sleep(1)  # Wait for details to load
        
        # Extract Geo Address Text
        geo_address = get_geo_address(driver)
        
        if geo_address != "Address not found" and geo_address != "Error extracting address":
            print(f"💡 GEO ADDRESS FOUND: {geo_address}")
        
        # Clear the search for the next company
        try:
            # Press Escape to close details if open
            webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            time.sleep(0.5)
            
            # Clear search field
            search_input = find_element_safely(driver, By.CSS_SELECTOR, "input[placeholder='Search by name or location...']", wait_time=3)
            if search_input:
                search_input.clear()
        except:
            pass
        
        return geo_address
        
    except Exception as e:
        print(f"Error during search for {company_name}: {e}")
        # Try to reset the state
        try:
            webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        except:
            pass
        return "Error occurred"

def scrape_company_locations(map_url, target_companies, headless=False):
    """Main function to scrape company locations."""
    driver = setup_driver(headless=headless)
    results = []
    
    try:
        # Navigate to the map URL
        print(f"Opening map URL: {map_url}")
        driver.get(map_url)
        driver.maximize_window()  # Maximize window to ensure elements are visible
        
        # Check if the map is inside an iframe
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        if iframes:
            print(f"Found {len(iframes)} iframes on the page")
            
            # Try to switch to the iframe that contains the map
            iframe_found = False
            for i, iframe in enumerate(iframes):
                try:
                    print(f"Switching to iframe {i}")
                    driver.switch_to.frame(iframe)
                    
                    # Check if this iframe contains map elements
                    search_elements = driver.find_elements(By.CSS_SELECTOR, "input[placeholder='Search by name or location...']")
                    if search_elements:
                        print(f"Found search input in iframe {i}")
                        iframe_found = True
                        break
                    else:
                        # Switch back to main content to try the next iframe
                        driver.switch_to.default_content()
                except Exception as e:
                    print(f"Error switching to iframe {i}: {e}")
                    driver.switch_to.default_content()
                    
            if not iframe_found:
                print("No iframe with search input found, remaining in main document")
        
        # Setup the map interface
        setup_map_interface(driver)
        
        # Process each target company
        total_companies = len(target_companies)
        for i, target in enumerate(target_companies):
            company_name = target['name']
            
            # Print progress information
            print(f"\n[PROGRESS] Processing company {i+1}/{total_companies} ({(i+1)/total_companies*100:.1f}%): {company_name}")
            
            # Search for the company and get its Geo Address
            geo_address = search_company_and_get_address(driver, company_name)
            
            # Save the result
            result = {
                'name': company_name,
                'geo_address': geo_address,
                'tons_delivered': target['tons'],
                'method': target['method']
            }
            results.append(result)
            
            # Print stats
            addresses_found = sum(1 for r in results if r['geo_address'] != "Address not found" and r['geo_address'] != "Error occurred" and r['geo_address'] != "Error extracting address")
            print(f"Current stats: {addresses_found}/{i+1} addresses found ({addresses_found/(i+1)*100:.1f}% success rate)")
            
            # Add a small delay between searches
            time.sleep(1.5)
        
        # Save results to CSV
        if results:
            pd.DataFrame(results).to_csv('company_locations.csv', index=False)
            print(f"Saved location data for {len(results)} companies to 'company_locations.csv'")
        
        return results
        
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()

def main():
    # URL
    direct_map_url = "https://app.nocodemapapp.com/app/XfChjmld8U5pw7ohNesh"
    
    # Load target companies from CSV
    csv_file = 'cdr_suppliers_full.csv'
    target_companies = load_target_companies(csv_file)
    
    if not target_companies:
        print(f"No target companies loaded. Make sure {csv_file} exists and is properly formatted.")
        return
    
    print(f"Loaded {len(target_companies)} target companies from CSV")
    
    # Ask if user wants to test with a small subset first
    test_mode = input("Run in test mode with just 5 companies? (y/n): ").lower() == 'y'
    
    if test_mode:
        target_companies = target_companies[:5]
        print(f"Test mode enabled. Will only process {len(target_companies)} companies.")
    
    # Run scraper
    headless = False  # Set to True to run without UI
    results = scrape_company_locations(
        direct_map_url, 
        target_companies, 
        headless=headless
    )
    
    # Report results
    if results:
        addresses_found = sum(1 for r in results if r['geo_address'] != "Address not found" and r['geo_address'] != "Error occurred" and r['geo_address'] != "Error extracting address")
        print("\nResults summary:")
        print(f"Total companies processed: {len(target_companies)}")
        print(f"Companies with geo address data: {addresses_found}")
        print(f"Success rate: {addresses_found/len(target_companies)*100:.1f}%")
    else:
        print("No results were returned.")

if __name__ == "__main__":
    main()