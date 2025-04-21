"""
Test data utilities for FDD verification tests.
"""

import os
import json
from typing import Dict, List, Any

def load_test_json(filename: str) -> Dict[str, Any]:
    """
    Load a test JSON file from the data directory.
    
    Args:
        filename: Name of the JSON file to load
        
    Returns:
        Loaded JSON data as a dictionary
    """
    data_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(data_dir, filename)
    
    with open(file_path, 'r') as f:
        return json.load(f)

def get_sample_headers() -> List[Dict[str, Any]]:
    """
    Get a list of sample headers from the test data.
    
    Returns:
        List of header dictionaries
    """
    # Use the first sample file
    sample_file = "00a72862-7472-473d-87c4-863010fa4835_origin_huridocs_analysis_extracted_headers.json"
    data = load_test_json(sample_file)
    
    # Extract headers based on the JSON structure
    headers = []
    if 'headers' in data:
        headers = data['headers']
    elif 'items' in data:
        for item in data['items']:
            header = {
                'item_number': item.get('item_number'),
                'text': item.get('header_text', ''),
                'page_number': item.get('page_number')
            }
            headers.append(header)
    
    return headers

def get_all_sample_files() -> List[str]:
    """
    Get a list of all sample JSON files in the data directory.
    
    Returns:
        List of filenames
    """
    data_dir = os.path.dirname(os.path.abspath(__file__))
    return [f for f in os.listdir(data_dir) if f.endswith('.json')]
