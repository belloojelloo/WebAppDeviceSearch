from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time



def search_part_number_in_bpmicro(original_part_number):
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
        
        result = _search_single_part_bpmicro(part_number)
        if result:
            print(f"SUCCESS! Found result for part number '{part_number}': {result}")
            return result
        else:
            print(f"No results found for part number '{part_number}'")
    
    # If we get here, no results were found for any variation
    print(f"No results found for any variation of part number '{original_part_number}' after trying {len(part_variations)} variations")
    return None

def _search_single_part_bpmicro(part_number):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=1000)
        page = browser.new_page()
        
        page.set_default_timeout(60000)
        page.set_default_navigation_timeout(60000)
        
        try:
            print(f"Searching for part number: {part_number}")
            
            # Navigate to the device search page
            print("Navigating to website...")
            page.goto("https://www.bpmmicro.com/device-search/", wait_until="domcontentloaded")
            print("Page loaded successfully")
            
            # Wait for iframe to load (using the specific class from the HTML)
            print("Waiting for iframe to load...")
            iframe = page.wait_for_selector('iframe#myIframe', timeout=30000)
            print("Iframe found!")
            
            # Switch to iframe context
            print("Switching to iframe...")
            # Get the frame object directly
            frame = page.frame_locator('iframe#myIframe').first
            print("Switched to iframe context")

            # Wait for the search section inside iframe
            print("Waiting for search section in iframe...")
            frame.locator('input[placeholder="Type to search for a device..."]').wait_for(timeout=30000)
            print("Search section found in iframe!")
            
            # Fill the part number input field in iframe
            print("Filling part number...")
            search_input = frame.locator('input[placeholder="Type to search for a device..."]')
            search_input.fill(part_number)
            
            # Wait for search results to appear automatically
            print("Waiting for search results to appear...")
            time.sleep(3)
            
            # Wait for search results to load
            try:
                # Wait for either search results or "No results found" message
                frame.locator('div[id="search-results"]').wait_for(state="visible", timeout=15000)
                
                # Check if "No results found" message appears or qty shows 0 or over 50000
                try:
                    # Check for "No results found" text
                    results_text = frame.locator('div[id="search-results"]').text_content()
                    if "No results found" in results_text:
                        print(f"No results found for part number '{part_number}'")
                        return None
                    
                    # Check qty_found for "0 found" or over 50000 results
                    try:
                        qty_text = frame.locator('div[id="qty_found"]').text_content()
                        if "0 found" in qty_text:
                            print(f"No results found (0 found) for part number '{part_number}'")
                            return None
                        
                        # Extract number from qty_text (e.g., "1234 found")
                        import re
                        qty_match = re.search(r'(\d+)\s+found', qty_text)
                        if qty_match:
                            qty_number = int(qty_match.group(1))
                            if qty_number > 50000:
                                print(f"Too many results found ({qty_number}), search failed - restart needed")
                                return "RESTART_SEARCH"
                    except:
                        pass
                        
                except:
                    pass
                
                # Wait for the first search result item to appear
                frame.locator('div[id="search-results"] ul li').first.wait_for(state="visible", timeout=5000)
                print("Search results found!")
            except:
                print("No search results appeared within timeout")
                return None
            
            # Click on the first search result
            print("Clicking on first search result...")
            try:
                first_result = frame.locator('div[id="search-results"] ul li').first
                first_result.click()
                print("Successfully clicked on first search result!")
                
                # Wait for the page to load after clicking
                time.sleep(3)
                
                # Extract the socket number from the table that appears after clicking
                try:
                    # Wait for the table to load after clicking
                    print("Waiting for socket adapter table to load...")
                    time.sleep(3)
                    
                    # Look for the table with socket adapter information within the iframe
                    table_selector = 'table.data-table'
                    frame.locator(table_selector).wait_for(state="visible", timeout=15000)
                    print("Socket adapter table found!")
                    
                    # Extract the socket number from the first row of the table
                    # The socket number is in the first column as a link text
                    socket_link = frame.locator('table.data-table tbody tr td:first-child a').first
                    socket_number = socket_link.text_content().strip()
                    print(f"Extracted socket number from table: {socket_number}")
                    return socket_number
                            
                except Exception as extract_error:
                    print(f"Error extracting socket number from table: {extract_error}")
                    # Fallback: try to get any link text that looks like a socket number
                    try:
                        print("Trying fallback socket number extraction...")
                        import re
                        # Look for links with socket number patterns (like FVE4ASMR48QFPE)
                        all_links = frame.locator('a').all()
                        for link in all_links:
                            try:
                                link_text = link.text_content().strip()
                                # Socket numbers are typically 10+ alphanumeric characters
                                if re.match(r'^[A-Z0-9]{10,}$', link_text):
                                    print(f"Found socket number pattern: {link_text}")
                                    return link_text
                            except:
                                continue
                        return "Socket number not found in page"
                    except:
                        return "Could not extract socket number"
                    
            except Exception as click_error:
                print(f"Error clicking on search result: {click_error}")
                return None



        except Exception as e:
            print(f"Error searching for part number '{part_number}': {e}")
        finally:
            print("Closing browser...")
            browser.close()