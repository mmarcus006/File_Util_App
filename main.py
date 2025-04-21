"""Main script to process FDD introduction PDFs using Gemini."""

import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Import components from our modules
from LLM.schemas import ExtractionOutput
from LLM.config import (
    SYSTEM_PROMPT_TEMPLATE,
    PDF_SEARCH_DIRECTORIES,
    PDF_KEYWORDS,
    OUTPUT_FILENAMES,
    PROMPT_DIR,
    SCHEMA_DIR,
    OUTPUT_DIR
)
from LLM.pdf_processor import (
    find_fdd_intro_pdfs,
    extract_fdd_data_with_gemini,
    output_file_exists
)

# --- Configuration --- #

# Load environment variables (especially API keys)
load_dotenv()

# --- Helper Functions --- #

def ensure_directories_exist():
    """Create necessary directories if they don't exist."""
    # Create directories defined in config
    for directory in [PROMPT_DIR, SCHEMA_DIR, OUTPUT_DIR]:
        directory.mkdir(parents=True, exist_ok=True)
    
    # Create PDF search directories if they're local to the project
    for directory in PDF_SEARCH_DIRECTORIES:
        dir_path = Path(directory)
        # Only create directories that are within our project
        if str(dir_path).startswith(str(Path.cwd())):
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")

# --- Main Logic --- #

def main():
    """Orchestrates the PDF finding and extraction process."""
    print("Starting FDD Introduction Extraction Process...")
    
    # Ensure necessary directories exist
    ensure_directories_exist()
    
    # Debug: Print out configuration
    print("\n--- Configuration ---")
    print(f"PDF search directories: {PDF_SEARCH_DIRECTORIES}")
    print(f"PDF keywords: {PDF_KEYWORDS['intro']}")
    print(f"Output filename: {OUTPUT_FILENAMES['intro']}")
    
    # Determine output filename from config
    output_filename = OUTPUT_FILENAMES["intro"]
    
    # Check if output file already exists
    if output_file_exists(output_filename):
        print(f"Output file {output_filename} already exists. To reprocess, delete or rename this file.")
        user_response = input("Do you want to continue anyway? (y/n): ").strip().lower()
        if user_response != 'y':
            print("Exiting without processing.")
            return

    # 1. Find relevant PDF files
    print("\nSearching for PDF files...")
    target_pdfs = find_fdd_intro_pdfs(PDF_SEARCH_DIRECTORIES, PDF_KEYWORDS["intro"])

    if not target_pdfs:
        print("No relevant PDF files found.")
        print("\nTo add PDF files for processing:")
        for directory in PDF_SEARCH_DIRECTORIES:
            print(f"1. Place PDF files in: {directory}")
            print(f"2. Ensure filenames contain one of these keywords: {PDF_KEYWORDS['intro']}")
        print("\nExiting.")
        return

    print(f"\nFound {len(target_pdfs)} target PDFs to process.")

    # 2. Process each PDF
    results = {}
    for pdf_path in target_pdfs:
        print(f"\n--- Processing: {pdf_path.name} ---")

        # Perform extraction using Gemini
        extracted_data = extract_fdd_data_with_gemini(
            pdf_path=pdf_path,
            pydantic_schema=ExtractionOutput,
            system_prompt=SYSTEM_PROMPT_TEMPLATE
        )

        if extracted_data:
            results[pdf_path.name] = extracted_data
            print(f"Success for {pdf_path.name}.")
        else:
            results[pdf_path.name] = None # Mark as failed
            print(f"Failed for {pdf_path.name}.")

    # 3. Save results
    print(f"\n--- Saving Results to {output_filename} --- ")
    try:
        output_path = Path(output_filename)
        with output_path.open('w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print("Results saved successfully.")
    except Exception as e:
        print(f"Error saving results: {e}")

    print("\nExtraction process finished.")

if __name__ == "__main__":
    main() 