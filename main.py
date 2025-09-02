from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time
from systemgeneralsearch import search_part_number_in_system_general_limited
from dataiosearch import search_part_number_in_dataio
from bpmicrosearch import search_part_number_in_bpmicro


def choose_search_function(website, part_number):
    """Choose and execute the appropriate search function based on website selection"""
    if website == "systemgeneral":
        return search_part_number_in_system_general_limited(part_number)
    elif website == "dataio":
        return search_part_number_in_dataio(part_number)
    elif website == "BPMicro":
        return search_part_number_in_bpmicro(part_number)
    else:
        raise ValueError(f"Unknown website: {website}")

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
        # Search using the chosen function (with built-in variations)
        result = choose_search_function(website, part_number)
        
        if result:
            socket_info, actual_part = result
            # Save result to file
            save_result_to_file(actual_part, socket_info)
            
            print(f"\nFinal Result:")
            print(f"Original Part Number: {part_number}")
            print(f"Part Number Used: {actual_part}")
            print(f"Result: {socket_info}")
        else:
            print(f"No results found for part number '{part_number}' on {website}")
            # Save failure to file
            with open("search_results.txt", "w") as f:
                f.write(f"Part Number: {part_number}\n")
                f.write(f"Website: {website}\n")
                f.write(f"Status: NO RESULTS FOUND\n")
                f.write(f"Search Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            print("No results status saved to search_results.txt")
        
    except Exception as e:
        print(f"Search failed: {e}")
        # Save failure to file
        try:
            with open("search_results.txt", "w") as f:
                f.write(f"Part Number: {part_number}\n")
                f.write(f"Website: {website}\n")
                f.write(f"Status: FAILED\n")
                f.write(f"Error: {str(e)}\n")
                f.write(f"Search Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            print("Failure details saved to search_results.txt")
        except Exception as save_error:
            print(f"Error saving failure to file: {save_error}")

