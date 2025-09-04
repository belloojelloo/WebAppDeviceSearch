#!/usr/bin/env python3

from bpmicrosearch import search_part_number_in_bpmicro

def test_bpmicro_search():
    print("Testing BPM Micro search with updated function...")
    
    # Test with a common part number
    test_part = "AT89C51"
    print(f"\nTesting with part number: {test_part}")
    
    try:
        result = search_part_number_in_bpmicro(test_part)
        if result:
            socket_info, found_part = result
            print(f"SUCCESS! Found socket info: {socket_info}")
            print(f"Found for part: {found_part}")
        else:
            print("No results found")
    except Exception as e:
        print(f"Error during search: {e}")

if __name__ == "__main__":
    test_bpmicro_search()
