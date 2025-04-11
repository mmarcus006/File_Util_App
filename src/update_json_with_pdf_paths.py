import os
import json
import shutil
from pathlib import Path
from typing import List, Optional

def find_pdf_by_id(pdf_id: str, search_dir: Path) -> Optional[str]:
    """
    Search for a PDF file containing the given ID in its filename.
    
    Args:
        pdf_id: The ID to search for in PDF filenames
        search_dir: Root directory to search in (including all subdirectories)
        
    Returns:
        Full path to the matching PDF file or None if not found
    """
    # Check if directory exists
    if not search_dir.exists() or not search_dir.is_dir():
        return None
        
    # Search recursively for PDF files matching the ID
    for pdf_file in search_dir.glob("**/*.pdf"):
        if pdf_id in pdf_file.name:
            return str(pdf_file.resolve())
            
    # If no match found
    return None

def get_pdf_search_directory() -> Optional[Path]:
    """
    Returns the root directory to search for PDF files using the FDD_PDF_FOLDER environment variable.
    
    Returns:
        Path object for the main search directory or None if not found
    """
    folder_str: str = os.environ.get("FDD_PDF_FOLDER", "")
    if folder_str:
        env_path = Path(folder_str).resolve()
        if env_path.is_dir():
            return env_path
    
    # If env var not set, try some common locations
    project_root = Path(__file__).parent.parent
        
    # If all else fails, return project root
    return project_root

def copy_pdf_to_destination(pdf_path: str, destination_dir: Path) -> Optional[str]:
    """
    Copy a PDF file to the destination directory if it doesn't already exist there.
    
    Args:
        pdf_path: Path to the source PDF file
        destination_dir: Directory to copy the PDF to
        
    Returns:
        Path to the PDF in the destination directory or None if copy failed
    """
    # Ensure destination directory exists
    destination_dir.mkdir(parents=True, exist_ok=True)
    
    # Get the PDF filename
    pdf_file = Path(pdf_path)
    dest_file = destination_dir / pdf_file.name
    
    # Check if file already exists in destination
    if dest_file.exists():
        print(f"PDF already exists in destination: {dest_file}")
        return str(dest_file)
    
    try:
        # Copy the file
        shutil.copy2(pdf_path, dest_file)
        print(f"Copied PDF to: {dest_file}")
        return str(dest_file)
    except Exception as e:
        print(f"Error copying PDF file: {str(e)}")
        return None

def update_json_with_pdf_path(json_file_path: Path, search_dir: Path, destination_dir: Path) -> bool:
    """
    Update a TOC JSON file with the path to its corresponding PDF file
    and copy the PDF to the destination directory.
    
    Args:
        json_file_path: Path to the TOC JSON file
        search_dir: Root directory to search for PDFs
        destination_dir: Directory to copy PDFs to
        
    Returns:
        True if the JSON was successfully updated, False otherwise
    """
    try:
        # Extract the ID from the JSON filename
        filename = json_file_path.name
        # Remove "_toc.json" from the end to get the ID
        pdf_id = filename.replace("_origin_huridocs_analysis_extracted_headers.json", "")
        
        # Read the current JSON content
        with open(json_file_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)
        
        pdf_path = None
            
        # Check if the PDF path is already in the JSON
        if isinstance(json_data, dict) and "pdf_file_path" in json_data:
            pdf_path = json_data["pdf_file_path"]
            print(f"PDF path already exists in {filename}: {pdf_path}")
        elif isinstance(json_data, list) and json_data and isinstance(json_data[0], dict) and "pdf_file_path" in json_data[0]:
            pdf_path = json_data[0]["pdf_file_path"]
            print(f"PDF path already exists in list item in {filename}: {pdf_path}")
        
        # If PDF path not in JSON, find the matching PDF file
        if not pdf_path:
            pdf_path = find_pdf_by_id(pdf_id, search_dir)
            
            if pdf_path:
                # Add the PDF path to the JSON
                if isinstance(json_data, dict):
                    json_data["pdf_file_path"] = pdf_path
                elif isinstance(json_data, list):
                    # For list structure, add pdf_path to each item in the list
                    for item in json_data:
                        if isinstance(item, dict):
                            if "pdf_file_path" not in item:
                                item["pdf_file_path"] = pdf_path
                    print(f"Added PDF path to list items in {filename}")
                else:
                    print(f"Unsupported JSON structure in {filename}")
                    return False
                
                # Write the updated JSON back to the file
                with open(json_file_path, "w", encoding="utf-8") as f:
                    json.dump(json_data, f, indent=2, ensure_ascii=False)
                    
                print(f"Updated {filename} with PDF path: {pdf_path}")
            else:
                print(f"No matching PDF found for {pdf_id}")
                return False
        
        # If we have a PDF path (either from JSON or newly found), copy it to destination
        if pdf_path:
            pdf_file = Path(pdf_path)
            if pdf_file.exists():
                copy_pdf_to_destination(pdf_path, destination_dir)
                return True
            else:
                print(f"PDF file does not exist at path: {pdf_path}")
                return False
                
        return True
            
    except Exception as e:
        print(f"Error processing {json_file_path}: {str(e)}")
        return False

def main() -> None:
    """
    Main function to update all TOC JSON files with PDF paths and copy PDFs.
    """
    # Get the project root
    project_root = Path(__file__).parent.parent
    
    # Path to the output/toc_json directory
    toc_json_dir = project_root / "output" / "header_output"
    
    # Path to the destination directory for PDFs
    destination_dir = Path(r"C:\Projects\File_Util_App\processed_fdds")
    
    if not toc_json_dir.exists() or not toc_json_dir.is_dir():
        print(f"Error: {toc_json_dir} directory does not exist")
        return
        
    # Get the search directory for PDFs
    search_dir = get_pdf_search_directory()
    if not search_dir:
        print("Error: Could not find a valid directory to search for PDFs")
        return
        
    print(f"Will search for PDFs in: {search_dir}")
    print(f"Will copy PDFs to: {destination_dir}")
    
    # Get all JSON files in the toc_json directory
    json_files = list(toc_json_dir.glob("*_huridocs_analysis_extracted_headers.json"))
    total_files = len(json_files)
    
    print(f"Found {total_files} TOC JSON files to process")
    
    # Process each JSON file
    updated_count = 0
    failed_count = 0
    
    for json_file in json_files:
        if update_json_with_pdf_path(json_file, search_dir, destination_dir):
            updated_count += 1
        else:
            failed_count += 1
            
    print("\n--- Processing Summary ---")
    print(f"Successfully updated: {updated_count}")
    print(f"Failed to update: {failed_count}")
    print(f"Total processed: {total_files}")

if __name__ == "__main__":
    main() 