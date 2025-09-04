#!/usr/bin/env python3

from bpmicrosearch import search_part_number_in_bpmicro

def test_bpmicro_search():
    """Test the BPMicro search function with a known part number"""
    print("Testing BPMicro search function...")
    
    # Test with a common part number
    test_part = "AT89C51"
    print(f"Searching for part: {test_part}")
    
    try:
        result = search_part_number_in_bpmicro(test_part)
        print(f"Search completed. Result: {result}")
        
        if result:
            socket_info, part_used = result
            print(f"Socket information found: {socket_info}")
            print(f"Part number used: {part_used}")
        else:
            print("No socket information found")
            
    except Exception as e:
        print(f"Error during search: {e}")

if __name__ == "__main__":
    test_bpmicro_search()
