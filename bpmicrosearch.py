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
            return (result, part_number)
        else:
            print(f"No results found for part number '{part_number}'")
    
    # If we get here, no results were found for any variation
    print(f"No results found for any variation of part number '{original_part_number}' after trying {len(part_variations)} variations")
    return None

def _search_single_part_bpmicro(part_number):
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
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

            time.sleep(1)

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
                
                # Extract socket modules from the table that appears after clicking
                try:
                    # Wait for the table to load after clicking
                    print("Waiting for device information table to load...")
                    time.sleep(3)
                    
                    # Look for any table that contains device information
                    print("Looking for device information table...")
                    tables = frame.locator('table')
                    
                    if tables.count() > 0:
                        print(f"Found {tables.count()} tables, searching for Socket Modules row...")
                        
                        # Search through all tables for Socket Modules information
                        for i in range(tables.count()):
                            table = tables.nth(i)
                            table_text = table.text_content()
                            
                            # Look for "Socket Modules" row in the table
                            if "Socket Modules" in table_text or "Socket Module" in table_text:
                                print(f"Found Socket Modules information in table {i+1}")
                                print(f"Table content: {table_text[:500]}...")  # Print first 500 chars for debugging
                                
                                # Look for table rows
                                rows = table.locator('tr')
                                for j in range(rows.count()):
                                    row = rows.nth(j)
                                    row_text = row.text_content()
                                    
                                    # Check if this row contains Socket Modules information
                                    if "Socket Modules" in row_text or "Socket Module" in row_text:
                                        print(f"Found Socket Modules row: {row_text}")
                                        
                                        # Look for the cell containing the socket module list
                                        cells = row.locator('td')
                                        for k in range(cells.count()):
                                            cell = cells.nth(k)
                                            cell_text = cell.text_content().strip()
                                            
                                            # Skip the "Socket Modules" label cell, look for the cell with actual socket names
                                            if cell_text and "Socket Modules" not in cell_text and len(cell_text) > 5:
                                                # This should contain the socket modules like "SM48D, SM48DH, ASM48D300, ASM48D600, SM48DB (disc.)"
                                                print(f"Found socket modules: {cell_text}")
                                                return cell_text
                                
                                # If we found the table but couldn't extract from rows, try extracting from full table text
                                import re
                                # Look for pattern after "Socket Modules" or "Socket Module"
                                socket_pattern = re.search(r'Socket Modules?\s*:?\s*([A-Z0-9, ().-]+)', table_text, re.IGNORECASE)
                                if socket_pattern:
                                    socket_modules = socket_pattern.group(1).strip()
                                    print(f"Extracted socket modules from pattern: {socket_modules}")
                                    return socket_modules
                        
                        print("Socket Modules information not found in any table")
                        return "Socket modules information not found"
                    else:
                        print("No tables found on the page")
                        return "No device information table found"
                            
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