from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time
from systemgeneralsearch import search_part_number_in_system_general_limited
from dataiosearch import search_part_number_in_dataio
from bpmicrosearch import search_part_number_in_bpmicro


def search_with_variations(original_part_number,website):
    """Try searching with different part number variations by removing characters from the end"""
    part_variations = [original_part_number]
    
    # Generate variations by removing one character at a time
    current_part = original_part_number
    for i in range(4):  # Try 4 more times
        if len(current_part) > 1:  # Make sure we don't end up with empty string
            current_part = current_part[:-1]  # Remove last character
            part_variations.append(current_part)
    
    print(f"Will try these part number variations: {part_variations}")
    
    for i, part_number in enumerate(part_variations):
        print(f"\n--- Attempt {i+1}: Trying part number '{part_number}' ---")
        
        try:
            if website == "systemgeneral":
                result = search_part_number_in_system_general_limited(part_number)
            elif website == "dataio":
                result = search_part_number_in_dataio(part_number)
            elif website == "BPMicro":
                result = search_part_number_in_bpmicro(part_number);
            if result:
                print(f"SUCCESS! Found result for part number '{part_number}': {result}")
                return part_number, result
            else:
                print(f"No results found for part number '{part_number}'")
        except Exception as e:
            print(f"Error searching for part number '{part_number}': {e}")
            continue
    
    # If we get here, no results were found for any variation
    raise Exception(f"No results found for any variation of part number '{original_part_number}' after trying {len(part_variations)} variations")

def save_result_to_file(part_number, skb_name, filename="search_results.txt"):
    """Save the search result to a text file"""
    try:
        with open(filename, "w") as f:
            f.write(f"Part Number: {part_number}\n")
            f.write(f"SKB Name: {skb_name}\n")
            f.write(f"Search Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        print(f"Result saved to {filename}")
    except Exception as e:
        print(f"Error saving to file: {e}")




if __name__ == "__main__":
    # Get part number from user input
    part_number = input("Enter the part number to search for: ").strip()
    
    if not part_number:
        print("No part number provided. Exiting.")
        exit(1)
    
    websitenumber = int(input("Enter the website to search for: " +
        "\n1 for System General, " +
        "\n2 for Data IO, " +
        "\n3 for BPMicro: "))
    match websitenumber:
        case 1:
            website = "systemgeneral"
        case 2:
            website = "dataio"
        case 3:
            website = "BPMicro"
        case _:
            website = ""
        
            
    if not website:
        print("No website provided. Exiting.")
        exit(1)

    try:
        # Search with variations
        successful_part, skb_name = search_with_variations(part_number,website)
        
        # Save result to file
        save_result_to_file(successful_part, skb_name)
        
        print(f"\nFinal Result:")
        print(f"Part Number: {successful_part}")
        print(f"SKB Name: {skb_name}")
        
    except Exception as e:
        print(f"Search failed: {e}")
        # Save failure to file
        try:
            
            with open("search_results.txt", "w") as f:
                f.write(f"Part Number: {part_number}\n")
                f.write(f"Status: FAILED\n")
                f.write(f"Error: {str(e)}\n")
                f.write(f"Search Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            print("Failure details saved to search_results.txt")
        except Exception as save_error:
            print(f"Error saving failure to file: {save_error}")

