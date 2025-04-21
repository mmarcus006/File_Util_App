import os
import shutil
from pathlib import Path
from typing import List, Tuple


def find_pdfs_in_folder(folder_path: str) -> List[Tuple[str, List[str]]]:
    """
    Find all subfolders containing PDF files.
    
    Args:
        folder_path: Path to the root folder to scan
        
    Returns:
        List of tuples containing (subfolder_path, [pdf_files])
    """
    results = []
    
    for root, _, files in os.walk(folder_path):
        pdf_files = [f for f in files if f.lower().endswith('.pdf')]
        
        if pdf_files:
            results.append((root, pdf_files))
    
    return results


def copy_folder_with_pdfs(source_folder: str, pdf_files: List[str], 
                          source_root: str, destination_root: str) -> None:
    """
    Copy a folder containing PDFs to the destination.
    
    Args:
        source_folder: Path to source folder
        pdf_files: List of PDF files in the folder
        source_root: Path to source root folder
        destination_root: Path to destination root folder
    """
    # Create relative path to maintain folder structure
    rel_path = os.path.relpath(source_folder, source_root)
    dest_folder = os.path.join(destination_root, rel_path)
    
    # Create destination folder if it doesn't exist
    os.makedirs(dest_folder, exist_ok=True)
    
    # Copy each PDF file
    for pdf_file in pdf_files:
        source_file = os.path.join(source_folder, pdf_file)
        dest_file = os.path.join(dest_folder, pdf_file)
        shutil.copy2(source_file, dest_file)
        print(f"Copied {source_file} to {dest_file}")


def main() -> None:
    """
    Main function to copy subfolders with PDFs from source to destination.
    """
    # Define source and destination folders
    folder1 = r"C:\Users\mille\MinerU"
    destination_folder = r"F:\MinerU"
    
    # Ensure destination folder exists
    os.makedirs(destination_folder, exist_ok=True)
    
    # Find all subfolders with PDFs
    folders_with_pdfs = find_pdfs_in_folder(folder1)
    
    # Copy each folder with PDFs to destination
    for folder_path, pdf_files in folders_with_pdfs:
        copy_folder_with_pdfs(folder_path, pdf_files, folder1, destination_folder)
    
    print(f"Copied {len(folders_with_pdfs)} folders containing PDFs.")


if __name__ == "__main__":
    main()
