import os
import json
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

def update_json_with_pdf_path(json_file_path: Path, search_dir: Path) -> bool:
    """
    Update a TOC JSON file with the path to its corresponding PDF file.
    
    Args:
        json_file_path: Path to the TOC JSON file
        search_dir: Root directory to search for PDFs
        
    Returns:
        True if the JSON was successfully updated, False otherwise
    """
    try:
        # Extract the ID from the JSON filename
        filename = json_file_path.name
        # Remove "_toc.json" from the end to get the ID
        pdf_id = filename.replace("_toc.json", "")
        
        # Read the current JSON content
        with open(json_file_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)
            
        # Check if the PDF path is already in the JSON
        if "pdf_file_path" in json_data:
            print(f"PDF path already exists in {filename}")
            return True
            
        # Find the matching PDF file
        pdf_path = find_pdf_by_id(pdf_id, search_dir)
        
        if pdf_path:
            # Add the PDF path to the JSON
            json_data["pdf_file_path"] = pdf_path
            
            # Write the updated JSON back to the file
            with open(json_file_path, "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
                
            print(f"Updated {filename} with PDF path: {pdf_path}")
            return True
        else:
            print(f"No matching PDF found for {pdf_id}")
            return False
            
    except Exception as e:
        print(f"Error processing {json_file_path}: {str(e)}")
        return False

def main() -> None:
    """
    Main function to update all TOC JSON files with PDF paths.
    """
    # Get the project root
    project_root = Path(__file__).parent.parent
    
    # Path to the output/toc_json directory
    toc_json_dir = project_root / "output" / "toc_json"
    
    if not toc_json_dir.exists() or not toc_json_dir.is_dir():
        print(f"Error: {toc_json_dir} directory does not exist")
        return
        
    # Get the search directory for PDFs
    search_dir = get_pdf_search_directory()
    if not search_dir:
        print("Error: Could not find a valid directory to search for PDFs")
        return
        
    print(f"Will search for PDFs in: {search_dir}")
    
    # Get all JSON files in the toc_json directory
    json_files = list(toc_json_dir.glob("*_toc.json"))
    total_files = len(json_files)
    
    print(f"Found {total_files} TOC JSON files to process")
    
    # Process each JSON file
    updated_count = 0
    failed_count = 0
    
    for json_file in json_files:
        if update_json_with_pdf_path(json_file, search_dir):
            updated_count += 1
        else:
            failed_count += 1
            
    print("\n--- Processing Summary ---")
    print(f"Successfully updated: {updated_count}")
    print(f"Failed to update: {failed_count}")
    print(f"Total processed: {total_files}")

if __name__ == "__main__":
    main() 