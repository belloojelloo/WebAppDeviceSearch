from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time

def search_part_number_in_system_general_limited(part_number):
    with sync_playwright() as p:
        # Launch browser with longer timeout and visible for debugging
        browser = p.chromium.launch(headless=False, slow_mo=1000)
        page = browser.new_page()
        
        # Set longer timeouts
        page.set_default_timeout(60000)  # 60 seconds
        page.set_default_navigation_timeout(60000)
        
        try:
            print(f"Searching for part number: {part_number}")
            
            # Navigate to the device search page
            print("Navigating to website...")
            page.goto("https://www.systemgenerallimited.com/device-search", wait_until="domcontentloaded")
            print("Page loaded successfully")
            
            # Wait for iframe to load (using the specific class from the HTML)
            print("Waiting for iframe to load...")
            iframe = page.wait_for_selector('iframe.Z8YsjS', timeout=30000)
            print("Iframe found!")
            
            # Switch to iframe context
            print("Switching to iframe...")
            # Get the frame object directly
            frame = page.frame_locator('iframe.Z8YsjS').first
            print("Switched to iframe context")
            
            # Wait for the search section inside iframe
            print("Waiting for search section in iframe...")
            frame.locator('section[data-cb-name="cbTable"]').wait_for(timeout=30000)
            print("Search section found in iframe!")
            
            # Debug: Check if elements exist in iframe
            print("Debug: Checking if elements exist in iframe...")
            try:
                input_element = frame.locator('input[name="Value2_1"]')
                if input_element.count() > 0:
                    print("Debug: Found Value2_1 input in iframe")
                else:
                    print("Debug: Value2_1 input NOT found in iframe")
            except Exception as e:
                print(f"Debug: Error checking input: {e}")
                
            try:
                button_element = frame.locator('input[name="searchID"]')
                if button_element.count() > 0:
                    print("Debug: Found searchID button in iframe")
                else:
                    print("Debug: searchID button NOT found in iframe")
            except Exception as e:
                print(f"Debug: Error checking button: {e}")
            
            # Fill the part number input field in iframe
            print("Filling part number...")
            frame.locator('input[name="Value2_1"]').fill(part_number)
            
            # Click the search button in iframe (use first one to avoid strict mode violation)
            print("Clicking search button...")
            frame.locator('input[name="searchID"]').first.click()
            
            # Wait for either results table or "No records found" message
            print("Waiting for results...")
            try:
                # First try to wait for results table
                frame.locator('table.cbResultSetTable').wait_for(timeout=10000)
                print("Results table found!")
                has_results = True
            except:
                # If no table, check for "No records found" message
                print("No results table found, checking for 'No records found' message...")
                try:
                    frame.locator('p.cbResultSetRecordMessage').wait_for(timeout=5000)
                    no_records_text = frame.locator('p.cbResultSetRecordMessage').text_content()
                    if "No records found" in no_records_text:
                        print("'No records found' message detected")
                        has_results = False
                    else:
                        print(f"Found message: {no_records_text}")
                        has_results = True
                except:
                    print("Neither results table nor 'No records found' message found")
                    has_results = False
            
            # Give extra time for results to load if we have results
            if has_results:
                time.sleep(3)
            
            # Print the page title
            print(f"Page title: {page.title()}")
            
            # If no results found, return None immediately
            if not has_results:
                print("No results found for this part number")
                return None
            
            # Get the iframe content for parsing
            print("Getting iframe content...")
            # Get the actual frame object for content
            frame_element = page.locator('iframe.Z8YsjS').element_handle()
            frame_obj = frame_element.content_frame()
            page_content = frame_obj.content()
            
            # Parse the page content with BeautifulSoup
            soup = BeautifulSoup(page_content, "html.parser")
            
            # Find the first table row in the tbody (excluding the header)
            table = soup.find("table", {"class": "cbResultSetTable"})
            skb_name = None
            
            if table:
                print("Found results table")
                tbody = table.find("tbody")
                if tbody:
                    rows = tbody.find_all("tr")
                    print(f"Found {len(rows)} result rows")
                    if rows:
                        first_row = rows[0]
                        # The SKB Name is the 5th <td> (index 4)
                        tds = first_row.find_all("td")
                        print(f"Found {len(tds)} columns in first row")
                        if len(tds) >= 5:
                            skb_name = tds[4].get_text(strip=True)
            else:
                print("No results table found in parsed content")
            
            if skb_name:
                print(f"SKB Name of first result: {skb_name}")
                return skb_name
            else:
                print("SKB Name not found in the first result.")
                return None
                
        except Exception as e:
            print(f"Error occurred: {e}")
            print(f"Error type: {type(e).__name__}")
            return None
        finally:
            print("Closing browser...")
            browser.close()
