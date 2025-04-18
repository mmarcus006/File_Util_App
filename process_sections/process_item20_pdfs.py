import os
import json
from pathlib import Path
from typing import Dict, Tuple, Optional, List, Any
import importlib.util
import sys

# Add parent directory to path to resolve imports
sys.path.append(str(Path(__file__).parent.parent))

from pydantic import BaseModel

# Import our Gemini API functions
from LLM.new_gemini_api import combine_pdfs, extract_structured_data_api, save_structured_data_to_json

# Constants
BASE_DIR = Path(r"C:\Projects\File_Util_App")
SPLIT_PDFS_DIR = BASE_DIR / "output" / "split_pdfs"
OUTPUT_DIR = BASE_DIR / "output" / "sections" / "item_20"
SCHEMA_PATH = BASE_DIR / "prompts" / "schemas" / "Item20_pydantic_schema.py"
SYSTEM_PROMPT_PATH = BASE_DIR / "prompts" / "system_prompts" / "Item_20_Prompt.md"
KEYWORD_IN_FILENAME = "ITEM_20"

def ensure_directories_exist():
    """Create all necessary directories for the workflow."""
    directories = [
        BASE_DIR / "output",
        SPLIT_PDFS_DIR,
        OUTPUT_DIR,
        OUTPUT_DIR.parent  # sections directory
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Directory exists: {directory} - {directory.exists()}")

def already_processed(folder_id: str) -> bool:
    """Check if a folder has already been processed by looking for output file.
    
    Args:
        folder_id: ID of the folder to check
        
    Returns:
        bool: True if already processed, False otherwise
    """
    output_file = OUTPUT_DIR / f"{folder_id}_item20.json"
    return output_file.exists()

def load_schema_model():
    """Load the Pydantic model from the schema file."""
    spec = importlib.util.spec_from_file_location("schema_module", SCHEMA_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load schema from {SCHEMA_PATH}")
    
    schema_module = importlib.util.module_from_spec(spec)
    sys.modules["schema_module"] = schema_module
    spec.loader.exec_module(schema_module)
    
    # Return the FranchiseAndFDDInfo class
    return schema_module.Item20FranchiseTables

def read_system_prompt() -> str:
    """Read the system prompt from file."""
    with open(SYSTEM_PROMPT_PATH, 'r', encoding='utf-8') as f:
        return f.read()

def find_target_pdfs(folder_path: Path) -> Optional[str]:
    """Find the ITEM_20 PDF file in the specified folder.
    
    Args:
        folder_path: Path to the folder to search
        
    Returns:
        Optional[str]: Path to the item20 file if found, None otherwise
    """
    item_file = None
    
    print(f"Searching for PDFs in: {folder_path}")
    
    # Check if directory exists
    if not folder_path.exists():
        print(f"Warning: Folder {folder_path} does not exist.")
        return None
    
    # List all files for debugging
    for file in folder_path.glob("*"):
        filename = file.name
        #print(f"Checking PDF file: {filename}")
            
        # Find ITEM_20 files
        if KEYWORD_IN_FILENAME in filename:
            print(f"Found file: {filename}")
            item_file = str(file)
            return item_file
    
    # Return None if no matching file was found
    return None

def process_subfolder(folder_id: str, folder_path: Path) -> None:
    """Process a single subfolder to extract and combine PDFs.
    
    Args:
        folder_id: ID of the folder (subfolder name)
        folder_path: Path to the subfolder
    """
    # Skip if already processed
    if already_processed(folder_id):
        print(f"Folder {folder_id} already processed. Skipping.")
        return
    
    # Find target PDF files
    item_file = find_target_pdfs(folder_path)
    
    # Skip if file is missing
    if not item_file:
        print(f"Missing required files in folder {folder_id}. Skipping.")
        return
    
    # Create combined file path
    #combined_file = str(Path(folder_path) / f"{folder_id}_combined_item1_intro.pdf")
    
    # Combine PDFs
    # try:
    #     combine_pdfs(item1_file, intro_file, combined_file)
    #     print(f"Combined PDFs for {folder_id}")
    # except Exception as e:
    #     print(f"Error combining PDFs for {folder_id}: {e}")
    #     return
    
    # Load schema and read system prompt
    try:
        schema_model = load_schema_model()
        system_prompt = read_system_prompt()
        user_prompt = f"Follow your system prompt exactly as its stated, and apply those extraction rules to the file attached"
    except Exception as e:
        print(f"Error loading schema or system prompt: {e}")
        return
    
    # Extract data using Gemini API
    try:
        result = extract_structured_data_api(
            file_path=item_file,
            model=schema_model,
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )
        
        # Create a new instance of the schema model with the result data
        schema_class = load_schema_model()
        
        # Handle different possible return types from the API
        if isinstance(result, dict):
            model_instance = schema_class(**result)
        elif isinstance(result, BaseModel):
            model_instance = result
        else:
            raise TypeError(f"Unexpected result type: {type(result)}")
        
        # Ensure model_instance is a BaseModel
        if not isinstance(model_instance, BaseModel):
            raise TypeError(f"Expected BaseModel instance, got {type(model_instance)}")
        
        # Save results to JSON
        save_structured_data_to_json(model_instance, str(OUTPUT_DIR), f"{folder_id}_{KEYWORD_IN_FILENAME}.json")
        print(f"Successfully processed {folder_id}")
    except Exception as e:
        print(f"Error extracting data for {folder_id}: {e}")

def main_workflow():
    """Main workflow to process all subfolders."""
    print("Starting Item 1 PDF processing workflow")
    
    # Ensure all directories exist
    ensure_directories_exist()
    
    # Get and process all subfolders
    if not SPLIT_PDFS_DIR.exists():
        print(f"Split PDFs directory does not exist: {SPLIT_PDFS_DIR}")
        return
    
    # Find all subfolders
    subfolders = [f for f in SPLIT_PDFS_DIR.iterdir() if f.is_dir()]
    if not subfolders:
        print(f"No subfolders found in {SPLIT_PDFS_DIR}")
        return
    
    # Process each subfolder
    for folder_path in subfolders:
        folder_id = folder_path.name
        print(f"Processing folder: {folder_id}")
        process_subfolder(folder_id, folder_path)
    
    print("Processing complete!")

if __name__ == "__main__":
    main_workflow() 