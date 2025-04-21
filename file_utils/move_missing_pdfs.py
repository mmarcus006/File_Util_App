#!/usr/bin/env python3
"""Script to move PDFs without JSON files to a 'Missing' folder."""

import os
import shutil
import glob
from pathlib import Path
from typing import List, Tuple, Dict


def read_missing_pdfs(file_path: str) -> List[str]:
    """
    Read the list of missing PDFs from the text file.
    
    Args:
        file_path: Path to the text file containing missing PDF names
        
    Returns:
        List of PDF filenames
    """
    pdf_files = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        # Skip the first two lines (header)
        next(f)
        next(f)
        
        for line in f:
            line = line.strip()
            if line and line.lower().endswith('.pdf'):
                pdf_files.append(line)
    
    return pdf_files


def create_missing_folder(base_dir: str) -> str:
    """
    Create a 'Missing' folder in the base directory if it doesn't exist.
    
    Args:
        base_dir: Base directory path
        
    Returns:
        Path to the 'Missing' folder
    """
    missing_folder = os.path.join(base_dir, "Missing")
    
    if not os.path.exists(missing_folder):
        os.makedirs(missing_folder)
        print(f"Created 'Missing' folder at: {missing_folder}")
    else:
        print(f"'Missing' folder already exists at: {missing_folder}")
    
    return missing_folder


def find_pdfs_in_directory(pdf_dir: str) -> Dict[str, str]:
    """
    Find all PDFs in the directory and subdirectories.
    
    Args:
        pdf_dir: Directory to search for PDFs
        
    Returns:
        Dictionary mapping lowercase filenames to full paths
    """
    pdf_paths = {}
    
    # Walk through all directories and subdirectories
    for root, _, files in os.walk(pdf_dir):
        for file in files:
            if file.lower().endswith('.pdf'):
                # Store the mapping of lowercase filename to actual path
                pdf_paths[file.lower()] = os.path.join(root, file)
    
    return pdf_paths


def move_pdfs(pdf_dir: str, missing_folder: str, pdf_files: List[str]) -> Tuple[List[str], List[str]]:
    """
    Move PDF files to the Missing folder.
    
    Args:
        pdf_dir: Directory containing PDF files
        missing_folder: Path to the 'Missing' folder
        pdf_files: List of PDF filenames to move
        
    Returns:
        Tuple containing lists of moved and not found files
    """
    moved_files = []
    not_found_files = []
    
    # First, find all PDFs in the directory and subdirectories
    print("Scanning directory for PDFs (this may take a moment)...")
    pdf_paths = find_pdfs_in_directory(pdf_dir)
    print(f"Found {len(pdf_paths)} PDFs in the directory structure")
    
    # Make sure we don't include the Missing folder in our search
    missing_folder_lower = os.path.basename(missing_folder).lower()
    
    for pdf_file in pdf_files:
        pdf_lower = pdf_file.lower()
        
        # Check if the PDF is in our mapping
        if pdf_lower in pdf_paths:
            source_path = pdf_paths[pdf_lower]
            
            # Skip if the file is already in the Missing folder
            if missing_folder_lower in source_path.lower():
                print(f"File already in Missing folder: {pdf_file}")
                moved_files.append(pdf_file)
                continue
                
            dest_path = os.path.join(missing_folder, os.path.basename(source_path))
            
            # Check if file already exists in destination
            if os.path.exists(dest_path):
                print(f"File already exists in destination: {pdf_file}")
                moved_files.append(pdf_file)
            else:
                try:
                    shutil.copy2(source_path, dest_path)
                    print(f"Copied: {pdf_file}")
                    moved_files.append(pdf_file)
                except Exception as e:
                    print(f"Error copying {pdf_file}: {str(e)}")
                    not_found_files.append(pdf_file)
        else:
            print(f"File not found: {pdf_file}")
            not_found_files.append(pdf_file)
    
    return moved_files, not_found_files


def main():
    """Main function to move missing PDFs to a 'Missing' folder."""
    # Configuration
    pdf_dir = r"C:\Users\mille\OneDrive\FDD_PDFS\FDD_WI"
    missing_pdfs_file = "pdfs_without_json.txt"
    
    # Validate inputs
    if not os.path.exists(pdf_dir):
        print(f"Error: PDF directory not found: {pdf_dir}")
        return
    
    if not os.path.exists(missing_pdfs_file):
        print(f"Error: Missing PDFs file not found: {missing_pdfs_file}")
        return
    
    # Read missing PDFs list
    pdf_files = read_missing_pdfs(missing_pdfs_file)
    print(f"Found {len(pdf_files)} PDFs to move")
    
    # Create Missing folder
    missing_folder = create_missing_folder(pdf_dir)
    
    # Move PDFs
    moved_files, not_found_files = move_pdfs(pdf_dir, missing_folder, pdf_files)
    
    # Summary
    print("\nSummary:")
    print(f"Successfully copied {len(moved_files)} files to: {missing_folder}")
    
    if not_found_files:
        print(f"Could not find {len(not_found_files)} files:")
        for file in not_found_files[:10]:
            print(f"- {file}")
        if len(not_found_files) > 10:
            print(f"... and {len(not_found_files) - 10} more")
    
    # Save a report of files that couldn't be found
    if not_found_files:
        report_file = "missing_pdfs_not_found.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"PDFs that could not be found ({len(not_found_files)}):\n\n")
            for file in not_found_files:
                f.write(f"{file}\n")
        print(f"\nReport of files not found saved to: {report_file}")


if __name__ == "__main__":
    main() 