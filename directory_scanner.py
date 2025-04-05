#!/usr/bin/env python3
"""Script to scan a directory and output file paths in JSON/CSV format with extracted IDs."""

import os
import json
import csv
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any
from datetime import datetime


def scan_directory(root_path: str) -> List[str]:
    """
    Recursively scan a directory and return all file paths.
    
    Args:
        root_path: Path to the directory to scan
        
    Returns:
        List of absolute file paths
    """
    all_paths: List[str] = []
    
    # Walk through the directory tree
    for dir_path, _, files in os.walk(root_path):
        # Add all directories
        all_paths.append(dir_path)
        
        # Add all files with their full paths
        for file in files:
            file_path = os.path.join(dir_path, file)
            all_paths.append(file_path)
    
    return all_paths


def extract_id(path: str) -> Optional[str]:
    """
    Extract ID from path using pattern matching.
    
    Args:
        path: File path to extract ID from
        
    Returns:
        Extracted ID or None if no ID is found
    """
    # Pattern looks for ID followed by digits at the end of the filename
    id_match = re.search(r'ID(\d+)', path)
    
    if id_match:
        return id_match.group(1)
    return None


def parse_paths(paths: List[str]) -> List[Dict[str, Any]]:
    """
    Parse paths and extract relevant information.
    
    Args:
        paths: List of file paths to parse
        
    Returns:
        List of dictionaries with path information
    """
    result = []
    
    for path in paths:
        path_data = {
            "full_path": path,
            "is_directory": os.path.isdir(path),
            "name": os.path.basename(path),
            "id": extract_id(path)
        }
        result.append(path_data)
    
    return result


def save_to_json(data: List[Dict[str, Any]], output_file: str) -> None:
    """
    Save data to a JSON file.
    
    Args:
        data: List of dictionaries to save
        output_file: Path to output file
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def save_to_csv(data: List[Dict[str, Any]], output_file: str) -> None:
    """
    Save data to a CSV file.
    
    Args:
        data: List of dictionaries to save
        output_file: Path to output file
    """
    if not data:
        return
    
    # Get fieldnames from the first item
    fieldnames = data[0].keys()
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def main(root_path: str, output_format: str = "json") -> None:
    """
    Main function to scan directory and save results.
    
    Args:
        root_path: Directory to scan
        output_format: Output format (json or csv)
    """
    if not os.path.exists(root_path):
        print(f"Error: Directory {root_path} does not exist.")
        return
    
    # Scan directory
    print(f"Scanning directory: {root_path}")
    paths = scan_directory(root_path)
    
    # Parse paths
    parsed_data = parse_paths(paths)
    
    # Generate timestamp for output filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Determine output file
    output_dir = os.getcwd()
    output_basename = f"directory_scan_{Path(root_path).name}_{timestamp}"
    
    if output_format.lower() == "json":
        output_file = os.path.join(output_dir, f"{output_basename}.json")
        save_to_json(parsed_data, output_file)
    else:
        output_file = os.path.join(output_dir, f"{output_basename}.csv")
        save_to_csv(parsed_data, output_file)
    
    print(f"Scan completed! Output saved to {output_file}")
    print(f"Found {len(parsed_data)} items ({sum(1 for item in parsed_data if item['is_directory'])} directories, "
          f"{sum(1 for item in parsed_data if not item['is_directory'])} files)")


if __name__ == "__main__":
    # Default directory from example
    DEFAULT_DIR = r"C:\Users\mille\MinerU"
    
    # Use a timestamp-based filename to avoid overwriting previous runs
    target_dir = DEFAULT_DIR
    output_format = "json"
    
    main(target_dir, output_format)
