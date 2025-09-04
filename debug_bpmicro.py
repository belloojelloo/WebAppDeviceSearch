#!/usr/bin/env python3

from playwright.sync_api import sync_playwright
import time

def debug_bpmicro_simple():
    """Simple debug version to see what's happening"""
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=False)  # Not headless for debugging
        page = browser.new_page()
        
        try:
            print("1. Navigating to BPMicro...")
            page.goto("https://www.bpmmicro.com/device-search/", wait_until="domcontentloaded")
            
            print("2. Waiting for iframe...")
            iframe = page.wait_for_selector('iframe#myIframe', timeout=30000)
            
            print("3. Getting frame...")
            frame = page.frame_locator('iframe#myIframe')
            
            print("4. Waiting for search input...")
            frame.locator('input[placeholder="Type to search for a device..."]').wait_for(timeout=30000)
            
            print("5. Filling search...")
            search_input = frame.locator('input[placeholder="Type to search for a device..."]')
            search_input.fill("AT89C51")
            
            print("6. Waiting for results...")
            time.sleep(3)
            frame.locator('div[id="search-results"]').wait_for(state="visible", timeout=15000)
            
            print("7. Clicking first result...")
            first_result = frame.locator('div[id="search-results"] ul li').first
            first_result.click()
            
            print("8. Waiting after click...")
            time.sleep(5)
            
            print("9. Checking current URL...")
            current_url = page.url
            print(f"Current URL: {current_url}")
            
            print("10. Checking for Socket Modules on main page...")
            if "bpmmicro.com" in current_url and "device-search" not in current_url:
                print("On main page - checking content...")
                page_text = page.locator('body').inner_text()
                if "Socket Modules" in page_text:
                    print("✓ Found 'Socket Modules' on main page!")
                    return "Found on main page"
                else:
                    print("✗ No 'Socket Modules' on main page")
            
            print("11. Checking iframe content...")
            iframe_text = frame.locator('body').inner_text()
            if "Socket Modules" in iframe_text:
                print("✓ Found 'Socket Modules' in iframe!")
                return "Found in iframe"
            else:
                print("✗ No 'Socket Modules' in iframe")
                
            print("12. Saving page content for inspection...")
            with open('debug_page_content.txt', 'w', encoding='utf-8') as f:
                f.write("=== MAIN PAGE ===\n")
                f.write(page.locator('body').inner_text())
                f.write("\n\n=== IFRAME ===\n")
                f.write(iframe_text)
            
            print("Page content saved to debug_page_content.txt")
            
            # Keep browser open for manual inspection
            input("Press Enter to close browser...")
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    debug_bpmicro_simple()
