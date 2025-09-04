# Import the original working search functions directly
from systemgeneralsearch import search_part_number_in_system_general_limited as original_system_general_search
from dataiosearch import search_part_number_in_dataio as original_dataio_search  
from bpmicrosearch import search_part_number_in_bpmicro as original_bpmicro_search


def search_part_number_in_system_general_limited(original_part_number):
    """Use the original working System General search function with Playwright"""
    try:
        print(f"Starting System General search for: {original_part_number}")
        result = original_system_general_search(original_part_number)
        if result:
            print(f"System General search completed successfully: {result}")
        else:
            print("System General search completed - no results found")
        return result
    except Exception as e:
        print(f"Error in System General search: {e}")
        return None


def search_part_number_in_dataio(original_part_number):
    """Use the original working DataIO search function with Playwright"""
    try:
        print(f"Starting DataIO search for: {original_part_number}")
        result = original_dataio_search(original_part_number)
        if result:
            print(f"DataIO search completed successfully: {result}")
        else:
            print("DataIO search completed - no results found")
        return result
    except Exception as e:
        print(f"Error in DataIO search: {e}")
        return None


def search_part_number_in_bpmicro(original_part_number):
    """Use the original working BPMicro search function with Playwright"""
    try:
        print(f"Starting BPMicro search for: {original_part_number}")
        result = original_bpmicro_search(original_part_number)
        if result:
            print(f"BPMicro search completed successfully: {result}")
        else:
            print("BPMicro search completed - no results found")
        return result
    except Exception as e:
        print(f"Error in BPMicro search: {e}")
        return None
