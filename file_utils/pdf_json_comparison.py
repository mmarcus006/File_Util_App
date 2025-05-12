#!/usr/bin/env python3
"""Script to find PDFs that don't have corresponding JSON files listed in a CSV."""

import os
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple


def extract_pdf_name_from_path(path: str) -> str:
    """
    Extract the PDF name from a folder path in the CSV.
    
    Args:
        path: Path string to extract PDF name from
        
    Returns:
        PDF name or empty string if not found
    """
    # Example: "C:\Users\mille\MinerU\1_Tom_Plumber_Global_Inc_FDD_2024_ID636010.pdf-563ddd1a-0cad-4a91-850a-a5250b51c84a"
    # We want "1_Tom_Plumber_Global_Inc_FDD_2024_ID636010.pdf"
    
    # First try to match the pattern where the PDF name is followed by a UUID
    match = re.search(r'([^\\]+\.pdf)-', path)
    if match:
        return match.group(1).lower()
    
    # If that doesn't work, try to find any PDF name in the path
    match = re.search(r'([^\\]+\.pdf)', path)
    if match:
        return match.group(1).lower()
    
    # Fallback: try to get the folder name at least
    parts = path.split('\\')
    if len(parts) >= 2:
        return parts[-2].lower()
    
    return ""


def parse_csv_manually(csv_file: str) -> Set[str]:
    """
    Parse the CSV file manually line by line to handle encoding issues.
    
    Args:
        csv_file: Path to CSV file
        
    Returns:
        Set of PDF names found in the CSV
    """
    pdf_names = set()
    
    # Try different encodings
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            with open(csv_file, 'r', encoding=encoding) as f:
                # Skip header
                header = f.readline()
                
                # Process each line
                for line in f:
                    # Split by comma, but handle cases where commas are in quotes
                    in_quotes = False
                    fields = []
                    current_field = ""
                    
                    for char in line:
                        if char == '"':
                            in_quotes = not in_quotes
                        elif char == ',' and not in_quotes:
                            fields.append(current_field)
                            current_field = ""
                        else:
                            current_field += char
                    
                    # Add the last field
                    fields.append(current_field)
                    
                    # Get the full path from the first column
                    if fields and len(fields) > 0:
                        path = fields[0].strip()
                        
                        if path and "\\MinerU\\" in path:
                            pdf_name = extract_pdf_name_from_path(path)
                            if pdf_name:
                                pdf_names.add(pdf_name)
            
            print(f"Successfully read CSV with encoding: {encoding}")
            print(f"Extracted {len(pdf_names)} PDF names from CSV")
            break
        
        except UnicodeDecodeError:
            print(f"Failed to read CSV with encoding: {encoding}")
            continue
        except Exception as e:
            print(f"Error while parsing CSV with encoding {encoding}: {str(e)}")
            continue
    
    return pdf_names


def scan_directory(directory: str) -> Set[str]:
    """
    Scan directory for PDF files.
    
    Args:
        directory: Directory to scan
        
    Returns:
        Set of normalized PDF filenames
    """
    pdf_files = set()
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.pdf'):
                pdf_files.add(file.lower())  # Normalize to lowercase
    
    return pdf_files


def main(pdf_directory: str, csv_file: str) -> None:
    """
    Find PDFs without corresponding JSON files.
    
    Args:
        pdf_directory: Directory containing PDFs
        csv_file: CSV file with JSON file information
    """
    if not os.path.exists(pdf_directory):
        print(f"Error: Directory {pdf_directory} does not exist.")
        return
        
    if not os.path.exists(csv_file):
        print(f"Error: CSV file {csv_file} does not exist.")
        return
    
    print(f"Scanning PDF directory: {pdf_directory}")
    pdfs_in_directory = scan_directory(pdf_directory)
    print(f"Found {len(pdfs_in_directory)} PDF files")
    
    print(f"Reading JSON mappings from: {csv_file}")
    pdfs_with_json = parse_csv_manually(csv_file)
    print(f"Found {len(pdfs_with_json)} PDFs with JSON files")
    
    # Find PDFs that don't have JSON files
    pdfs_without_json = pdfs_in_directory - pdfs_with_json
    
    print(f"\nResults:")
    print(f"Total PDFs without corresponding JSON files: {len(pdfs_without_json)}")
    
    if pdfs_without_json:
        print("\nPDFs without JSON files (showing first 20):")
        for pdf in sorted(list(pdfs_without_json)[:20]):
            print(f"- {pdf}")
        
        if len(pdfs_without_json) > 20:
            print(f"... and {len(pdfs_without_json) - 20} more")
    else:
        print("All PDFs have corresponding JSON files.")
    
    # Save results to a file
    output_file = "pdfs_without_json.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"PDFs without corresponding JSON files ({len(pdfs_without_json)}):\n\n")
        for pdf in sorted(pdfs_without_json):
            f.write(f"{pdf}\n")
    
    print(f"\nResults saved to {output_file}")


if __name__ == "__main__":
    # Paths from the user's query
    PDF_DIRECTORY = r"C:\Users\mille\OneDrive\FDD_PDFS\FDD_WI"
    CSV_FILE = "All_Json_Files.csv"
    
    main(PDF_DIRECTORY, CSV_FILE) 