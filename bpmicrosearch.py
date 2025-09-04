from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time
import re
import os


def _filter_socket_text(socket_text, original_part_number):
    """Remove original part number from socket text and clean up the result"""
    if not socket_text or not original_part_number:
        return socket_text
    
    # Split socket text by common separators
    parts = re.split(r'[,;\s]+', socket_text)
    filtered_parts = []
    
    for part in parts:
        part = part.strip()
        if part and part.upper() != original_part_number.upper():
            # Only keep parts that don't match the original part number
            filtered_parts.append(part)
    
    # Join back with commas and clean up
    result = ', '.join(filtered_parts)
    return result if result else socket_text  # Return original if nothing left after filtering



def _is_banner_text(text: str) -> bool:
    if not text:
        return False
    t = text.lower()
    banned = [
        'server started',
        'database loaded',
        'best-efforts',
        'prices, and, specifications',
        'you, may, search, for, an, adapter',
        'bpm, microsystems, device, search',
        'adapter:asm',
        'adapter:fx4asm',
    ]
    return any(b in t for b in banned)


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
        
        result = _search_single_part_bpmicro(part_number, original_part_number)
        if result == "RESTART_SEARCH":
            print(f"Too many results for '{part_number}', automatically restarting search...")
            # Wait a moment and try again
            import time
            time.sleep(2)
            result = _search_single_part_bpmicro(part_number, original_part_number)
            if result == "RESTART_SEARCH":
                print(f"Still too many results after restart, skipping '{part_number}'")
                continue
        
        if result:
            print(f"SUCCESS! Found result for part number '{part_number}': {result}")
            return (result, part_number)
        else:
            print(f"No results found for part number '{part_number}'")
    
    # If we get here, no results were found for any variation
    print(f"No results found for any variation of part number '{original_part_number}' after trying {len(part_variations)} variations")
    return None

def _search_single_part_bpmicro(part_number, original_part_number=None):
    with sync_playwright() as p:
        env_headless = os.environ.get("BPM_HEADLESS", "true").lower() in ("1", "true", "yes")
        browser = p.chromium.launch(channel="msedge", headless=env_headless, args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-dev-shm-usage",
        ])
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0"
            ),
            locale="en-US",
            timezone_id="UTC",
            viewport={"width": 1366, "height": 900},
        )
        try:
            context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")
            context.add_init_script("window.chrome = { runtime: {} };")
            context.add_init_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US','en']});")
            context.add_init_script("Object.defineProperty(navigator, 'platform', {get: () => 'Win32'});")
        except Exception:
            pass
        page = context.new_page()
        
        page.set_default_timeout(60000)
        page.set_default_navigation_timeout(60000)
        
        try:
            print(f"Searching for part number: {part_number}")
            
            # Navigate to the device search page
            print("Navigating to website...")
            page.goto("https://www.bpmmicro.com/device-search/", wait_until="domcontentloaded")
            try:
                page.wait_for_load_state("networkidle", timeout=20000)
            except Exception:
                pass
            print("Page loaded successfully")
            
            # Wait for iframe to load (using the specific class from the HTML)
            print("Waiting for iframe to load...")
            iframe = page.wait_for_selector('iframe#myIframe', timeout=30000)
            print("Iframe found!")
            
            # Switch to iframe context
            print("Switching to iframe...")
            # Get the frame object directly
            frame = page.frame_locator('iframe#myIframe')
            print("Switched to iframe context")

            time.sleep(1)

            # Wait for the search section inside iframe
            print("Waiting for search section in iframe...")
            frame.locator('input[placeholder="Type to search for a device..."]').wait_for(timeout=30000)
            print("Search section found in iframe!")
            
            # Fill the part number input field in iframe and fire events
            print("Filling part number...")
            search_input = frame.locator('input[placeholder="Type to search for a device..."]')
            search_input.fill("")
            search_input.fill(part_number)
            try:
                search_input.press("Enter")
            except Exception:
                pass
            try:
                frame.locator('input[placeholder="Type to search for a device..."]').evaluate(
                    "(el)=>{ el.dispatchEvent(new Event('input',{bubbles:true})); el.dispatchEvent(new Event('change',{bubbles:true})); }"
                )
            except Exception:
                pass
            
            print("Waiting for search results to appear...")
            time.sleep(1)
            
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
                
                # Wait for the first search result item to appear (retry once)
                try:
                    frame.locator('div[id="search-results"] ul li').first.wait_for(state="visible", timeout=5000)
                except Exception:
                    print("Retrying to trigger search...")
                    try:
                        search_input.fill("")
                        search_input.fill(part_number)
                        search_input.press("Enter")
                    except Exception:
                        pass
                    frame.locator('div[id="search-results"] ul li').first.wait_for(state="visible", timeout=7000)
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
                time.sleep(2)
                
                # Check if we navigated to a main BPM Micro product page
                print("=== Checking current page context ===")
                try:
                    current_url = page.url
                    print(f"Current page URL: {current_url}")
                    
                    # Check if we navigated to a main BPM Micro product page
                    if "bpmmicro.com" in current_url and "device-search" not in current_url:
                        print("Navigated to main BPMicro product page - extracting from main page")
                        
                        # Wait for the main page to load completely
                        try:
                            page.wait_for_load_state("networkidle", timeout=15000)
                        except Exception:
                            time.sleep(1)
                        
                        # Restrict main-page extraction to exact table rows only to avoid banner text
                        main_page_text = page.locator('body').inner_text()
                        if _is_banner_text(main_page_text):
                            print("Detected banner text on main page; skipping.")
                            return "No socket information found on product page"
                        socket_rows = page.locator('tr:has-text("Socket Modules")')
                        if socket_rows.count() > 0:
                            print("✓ Found 'Socket Modules' on main page")
                            cells = socket_rows.first.locator('td')
                            if cells.count() >= 2:
                                socket_text = cells.nth(1).inner_text().strip()
                                if _is_banner_text(socket_text):
                                    print("Banner-like content detected in Socket Modules cell; skipping.")
                                    return "No Socket information found"
                                clean_socket = ' '.join(socket_text.replace('\n', ' ').replace('\t', ' ').split())
                                filtered_socket = _filter_socket_text(clean_socket, original_part_number)
                                return filtered_socket
                        adapter_rows = page.locator('tr:has-text("Socket Adapter")')
                        if adapter_rows.count() > 0:
                            print("✓ Found 'Socket Adapter' on main page")
                            cells = adapter_rows.first.locator('td')
                            if cells.count() >= 2:
                                socket_text = cells.nth(1).inner_text().strip()
                                if _is_banner_text(socket_text):
                                    print("Banner-like content detected in Socket Adapter cell; skipping.")
                                    return "No Socket information found"
                                clean_socket = ' '.join(socket_text.replace('\n', ' ').replace('\t', ' ').split())
                                filtered_socket = _filter_socket_text(clean_socket, original_part_number)
                                return filtered_socket
                        print("No exact socket rows on main page; skipping to iframe extraction")
                        return "No socket information found on product page"
                    else:
                        print("Still in iframe context - continuing with iframe extraction")
                        
                except Exception as url_error:
                    print(f"Error checking URL: {url_error}")
                
                # Extract socket modules from the device information table at bottom of page
                try:
                    # Wait for the page to fully load after clicking
                    print("Waiting for device information table to load...")
                    time.sleep(2)

                    # Try to scroll the iframe content so the table/row becomes visible
                    try:
                        print("Attempting to scroll 'Socket Modules' row into view...")
                        frame.locator('tr:has-text("Socket Modules")').first.scroll_into_view_if_needed(timeout=2000)
                        time.sleep(0.5)
                    except:
                        try:
                            print("Socket row not immediately found; scrolling through iframe...")
                            for _ in range(4):
                                frame.evaluate("() => window.scrollBy(0, Math.floor(window.innerHeight*0.9))")
                                time.sleep(0.4)
                        except Exception:
                            pass
                    
                    # Debug: Print all page content to understand structure
                    print("=== DEBUG: Getting page content ===")
                    try:
                        page_text = frame.locator('body').inner_text()
                        print(f"Page content length: {len(page_text)}")
                        
                        # Check if "Socket Modules" appears anywhere in the page
                        if "Socket Modules" in page_text:
                            print("✓ 'Socket Modules' text found in page content")
                        else:
                            print("✗ 'Socket Modules' text NOT found in page content")
                            
                        # Print a sample of the page content around tables
                        lines = page_text.split('\n')
                        for i, line in enumerate(lines):
                            if 'socket' in line.lower() or 'module' in line.lower():
                                print(f"Line {i}: {line.strip()}")
                                
                    except Exception as debug_error:
                        print(f"Debug error: {debug_error}")
                    
                    print("=== Looking for tables ===")
                    # Check all tables on the page
                    tables = frame.locator('table')
                    table_count = tables.count()
                    print(f"Found {table_count} tables on page")
                    
                    for i in range(table_count):
                        try:
                            table = tables.nth(i)
                            table_text = table.inner_text()
                            print(f"Table {i+1} content preview: {table_text[:200]}...")
                            
                            if "Socket Modules" in table_text:
                                print(f"✓ Found 'Socket Modules' in table {i+1}")
                        except:
                            print(f"Could not read table {i+1}")
                    
                    # Try multiple approaches to find socket modules
                    print("=== Trying different selectors ===")

                    # Method 0: Exact parse of device parameters table using BeautifulSoup
                    try:
                        device_tables = frame.locator('table.device-parameters-table')
                        dt_count = device_tables.count()
                        print(f"Method 0 - device-parameters-table count: {dt_count}")
                        for di in range(dt_count):
                            try:
                                table_html = device_tables.nth(di).inner_html()
                                soup = BeautifulSoup(table_html, 'html.parser')
                                rows = soup.find_all('tr')
                                for row in rows:
                                    cells = row.find_all('td')
                                    if len(cells) >= 2:
                                        key_text = cells[0].get_text(strip=True)
                                        if key_text.lower() == 'socket modules':
                                            value_text = cells[1].get_text(" ", strip=True)
                                            if value_text:
                                                print(f"Method 0 - Found Socket Modules: {value_text}")
                                                clean_socket = ' '.join(value_text.replace('\n', ' ').replace('\t', ' ').split())
                                                filtered_socket = _filter_socket_text(clean_socket, original_part_number)
                                                return filtered_socket
                            except Exception as m0err:
                                print(f"Method 0 - error parsing device table {di}: {m0err}")
                    except Exception as m0outer:
                        print(f"Method 0 - outer error: {m0outer}")
                    
                    # Method 1: Look for "Socket Adapter" (from memory)
                    socket_adapter_rows = frame.locator('tr:has-text("Socket Adapter")')
                    print(f"Method 1 - Socket Adapter: {socket_adapter_rows.count()} rows")
                    
                    # Method 2: Look for "Socket Modules"
                    socket_modules_rows = frame.locator('tr:has-text("Socket Modules")')
                    print(f"Method 2 - Socket Modules: {socket_modules_rows.count()} rows")
                    
                    # Method 3: Look for any text containing socket patterns
                    import re
                    socket_pattern_elements = frame.locator('text=/SM\d+|ASM\d+|FVE\d+/i')
                    print(f"Method 3 - Socket patterns: {socket_pattern_elements.count()} elements")
                    
                    # Method 4: Look for h1.entry-title (from memory)
                    entry_title = frame.locator('h1.entry-title')
                    print(f"Method 4 - h1.entry-title: {entry_title.count()} elements")
                    
                    # Method 5: Look in data-table elements (from memory)
                    data_tables = frame.locator('[data-table]')
                    print(f"Method 5 - data-table elements: {data_tables.count()} elements")
                    
                    # Try Method 4 first (h1.entry-title from memory)
                    if entry_title.count() > 0:
                        print("Using Method 4 - h1.entry-title...")
                        title_text = entry_title.first.inner_text().strip()
                        print(f"Entry title text: {title_text}")
                        # Look for socket patterns in title
                        socket_match = re.search(r'(SM\d+[A-Z]*|ASM\d+[A-Z]*|FVE\d+[A-Z]*)', title_text, re.IGNORECASE)
                        if socket_match:
                            socket_text = socket_match.group(1)
                            print(f"Found socket in title: {socket_text}")
                            # Clean the socket text
                            clean_socket = socket_text.strip()
                            # Filter out original part number
                            filtered_socket = _filter_socket_text(clean_socket, original_part_number)
                            return filtered_socket
                    
                    # Try Method 1 (Socket Adapter)
                    if socket_adapter_rows.count() > 0:
                        print("Using Method 1 - Socket Adapter...")
                        socket_row = socket_adapter_rows.first
                        cells = socket_row.locator('td')
                        if cells.count() >= 2:
                            socket_text = cells.nth(1).inner_text().strip()
                            if _is_banner_text(socket_text):
                                print("Banner-like content detected in iframe adapter cell; skipping.")
                                return "No Socket information found"
                            if socket_text and len(socket_text) > 3:
                                print(f"Found socket adapter: {socket_text}")
                                # Clean the socket text
                                clean_socket = socket_text.replace('\n', ' ').replace('\t', ' ')
                                clean_socket = ' '.join(clean_socket.split())
                                # Filter out original part number
                                filtered_socket = _filter_socket_text(clean_socket, original_part_number)
                                return filtered_socket
                    
                    # Try Method 2 (Socket Modules)
                    if socket_modules_rows.count() > 0:
                        print("Using Method 2 - Socket Modules...")
                        socket_row = socket_modules_rows.first
                        cells = socket_row.locator('td')
                        if cells.count() >= 2:
                            socket_text = cells.nth(1).inner_text().strip()
                            if _is_banner_text(socket_text):
                                print("Banner-like content detected in iframe modules cell; skipping.")
                                return "No Socket information found"
                            if socket_text and len(socket_text) > 3:
                                print(f"Found socket modules: {socket_text}")
                                # Clean the socket text
                                clean_socket = socket_text.replace('\n', ' ').replace('\t', ' ')
                                clean_socket = ' '.join(clean_socket.split())
                                # Filter out original part number
                                filtered_socket = _filter_socket_text(clean_socket, original_part_number)
                                return filtered_socket
                    
                    # Try Method 3 (Pattern matching)
                    if socket_pattern_elements.count() > 0:
                        print("Using Method 3 - Pattern matching...")
                        for i in range(min(3, socket_pattern_elements.count())):
                            element = socket_pattern_elements.nth(i)
                            element_text = element.inner_text().strip()
                            print(f"Pattern element {i}: {element_text}")
                            if len(element_text) > 3:
                                # Clean the socket text
                                clean_socket = element_text.replace('\n', ' ').replace('\t', ' ')
                                clean_socket = ' '.join(clean_socket.split())
                                # Filter out original part number
                                filtered_socket = _filter_socket_text(clean_socket, original_part_number)
                                return filtered_socket
                    
                    # Try Method 5 (data-table)
                    if data_tables.count() > 0:
                        print("Using Method 5 - data-table...")
                        for i in range(data_tables.count()):
                            table = data_tables.nth(i)
                            table_text = table.inner_text()
                            if "Socket" in table_text:
                                print(f"Found socket in data-table {i}: {table_text[:100]}...")
                                # Extract socket patterns from table text
                                socket_matches = re.findall(r'(SM\d+[A-Z]*|ASM\d+[A-Z]*|FVE\d+[A-Z]*)', table_text, re.IGNORECASE)
                                if socket_matches:
                                    socket_text = ', '.join(socket_matches)
                                    print(f"Extracted sockets: {socket_text}")
                                    # Clean the socket text
                                    clean_socket = socket_text.replace('\n', ' ').replace('\t', ' ')
                                    clean_socket = ' '.join(clean_socket.split())
                                    return (clean_socket, part_number)
                    
                    print("No Socket information found with any method")
                    return "No Socket information found"
                            
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
                                    # Clean the socket text
                                    clean_socket = link_text.strip()
                                    return clean_socket
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