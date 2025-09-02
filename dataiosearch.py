from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time


def search_part_number_in_dataio(original_part_number):
    """Search with variations - try up to 4 times by removing characters from the end"""
    part_variations = [original_part_number]
    
    # Generate variations by removing one character at a time
    current_part = original_part_number
    for i in range(3):  # Try 3 more times (total 4 attempts)
        if len(current_part) > 1:  # Make sure we don't end up with empty string
            current_part = current_part[:-1]  # Remove last character
            part_variations.append(current_part)
    
    print(f"Will try these part number variations: {part_variations}")
    
    for i, part_number in enumerate(part_variations):
        print(f"\n--- Attempt {i+1}: Trying part number '{part_number}' ---")
        
        result = _search_single_part_dataio(part_number)
        if result:
            print(f"SUCCESS! Found result for part number '{part_number}': {result}")
            return result
        else:
            print(f"No results found for part number '{part_number}'")
    
    # If we get here, no results were found for any variation
    print(f"No results found for any variation of part number '{original_part_number}' after trying {len(part_variations)} variations")
    return None

def _search_single_part_dataio(part_number):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=1000)
        page = browser.new_page()
        
        page.set_default_timeout(60000)
        page.set_default_navigation_timeout(60000)
        
        try:
            print(f"Searching for part number: {part_number}")


            print("Navigating to website...")
            page.goto("https://dataio.com/Support/Device-Search", wait_until="domcontentloaded")
            print("Page loaded successfully")
            
            
            try:

                print("Waiting for search input...")
                search_input = page.wait_for_selector('input[placeholder="Part #, Adapter or Manfacturer"]', timeout=30000)
                print("Search input found!")
                print("Filling search input...")
                search_input.fill(part_number)
                print("Search input filled!")
                time.sleep(2)
            except Exception as e:
                print(f"Error waiting for search input: {e}")

            try:
                print("Waiting for search button...")
                search_button = page.wait_for_selector('input[type="button"][value="SEARCH"]', timeout=30000)
                print("Search button found!")
                print("Clicking search button...")
                search_button.click()

                time.sleep(2)

                # First check if there are result links
                print("Checking for result links...")
                first_link = page.locator('a[id*="dnn_ctr6237_View_lvDeviceSearchResults_ctrl"][id*="lnkDeviceSearchResultDevice"]')
                
                if first_link.count() > 0:
                    print("Results found! Clicking first result:", first_link.first.inner_text())
                    first_link.first.click()
                else:
                    # Only check for "no results" message if no links are found
                    print("No result links found, checking for 'no results' message...")
                    try:
                        message = page.locator("div#dnn_ctr6237_View_pnlSearchResults h3")
                        if message.count() > 0:
                            message_text = message.inner_text()
                            print("Message is:", message_text)
                            if "No search results found." in message_text:
                                print("No results, stopping.")
                                return None
                    except Exception as e:
                        print(f"Error checking for no results message: {e}")
                    
                    print("No result links found and no clear 'no results' message")
                    return None

                                
                # Wait for navigation to results page
                print("Waiting for navigation to results page...")
                try:
                    # Wait for the page to navigate to a new URL
                    page.wait_for_url("**", timeout=15000)
                    print(f"Navigated to: {page.url}")
                    
                    # Wait for the new page to load
                    page.wait_for_load_state("domcontentloaded", timeout=15000)
                    print("Results page loaded successfully")
                    
                    # Give extra time for results to fully load
                    time.sleep(3)
                    
                    print("Waiting for results table...")
                    page.wait_for_selector('div[class="row"]', timeout=15000)
                    print("Results table found!")

                    time.sleep(1)

                    print("Extracting results...")
                    # Wait for the results element to appear first
                    selector = ('div[id="dnn_ctr6237_View_lvDeviceDetailEngineContent_'
                               'lvDeviceDetailProductContent_1_lvDeviceDetailProductAlgorithms_0_'
                               'lvDeviceDetailAlgorithmAdapters_0_lvDeviceDetailAlgorithmAdaptersRow_0"] '
                               'div[class="col-sm-5"][id="dataPartNumber"]')
                    page.wait_for_selector(selector, timeout=30000)
                    results = page.locator(selector).text_content()
                    print("Results extracted!")

                    if results:
                        print(f"Found result for part number '{part_number}': {results}")
                        return results
                    else:
                        print(f"No results found for part number '{part_number}'")
                        return None

                    
                except Exception as e:
                    print(f"Error during navigation: {e}")
                    return None
                
            except Exception as e:
                print(f"Error waiting for search button: {e}")
                return None

        except Exception as e:
            print(f"Error searching for part number '{part_number}': {e}")
        finally:
            print("Closing browser...")
            browser.close()
        
        


