"""Main script to process FDD introduction PDFs using Gemini."""

import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Import components from our modules
from LLM.schemas import ExtractionOutput
from LLM.llm_config import SYSTEM_PROMPT_TEMPLATE
from LLM.pdf_processor import find_fdd_intro_pdfs, extract_fdd_data_with_gemini

# --- Configuration --- #

# Load environment variables (especially GOOGLE_API_KEY)
load_dotenv()

# Define directories to search for PDFs
# Replace with your actual directories containing FDD PDFs
# Example: PDF_SEARCH_DIRECTORIES = ["/path/to/fdd_folder1", "/path/to/fdd_folder2"]
PDF_SEARCH_DIRECTORIES = ["/Users/miller/Library/CloudStorage/OneDrive-Personal/FDD_PDFS/split_pdfs"]

# Keywords to identify the target PDF files (intro/item 1 sections)
PDF_KEYWORDS = ["intro", "item_1"]

# Output file for results
OUTPUT_FILENAME = "fdd_intro_extractions.json"

# --- Main Logic --- #

def main():
    """Orchestrates the PDF finding and extraction process."""
    print("Starting FDD Introduction Extraction Process...")

    # 1. Find relevant PDF files
    target_pdfs = find_fdd_intro_pdfs(PDF_SEARCH_DIRECTORIES, PDF_KEYWORDS)

    if not target_pdfs:
        print("No relevant PDF files found. Exiting.")
        return

    print(f"\nFound {len(target_pdfs)} target PDFs to process.")

    # 2. Process each PDF
    results = {}
    for pdf_path in target_pdfs:
        print(f"\n--- Processing: {pdf_path.name} ---")

        # Perform extraction using Gemini
        extracted_data = extract_fdd_data_with_gemini(
            pdf_path=pdf_path,
            pydantic_schema=ExtractionOutput, # Pass the Pydantic model class
            system_prompt=SYSTEM_PROMPT_TEMPLATE
        )

        if extracted_data:
            results[pdf_path.name] = extracted_data
            print(f"Success for {pdf_path.name}.")
        else:
            results[pdf_path.name] = None # Mark as failed
            print(f"Failed for {pdf_path.name}.")

    # 3. Save results
    print(f"\n--- Saving Results to {OUTPUT_FILENAME} --- ")
    try:
        output_path = Path(OUTPUT_FILENAME)
        with output_path.open('w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print("Results saved successfully.")
    except Exception as e:
        print(f"Error saving results: {e}")

    print("\nExtraction process finished.")

if __name__ == "__main__":
    main() 