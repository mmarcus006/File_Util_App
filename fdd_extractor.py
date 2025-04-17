# fdd_extractor.py

import os
import json
import pathlib
import google.generativeai as genai
from pydantic import BaseModel, Field, ValidationError, field_validator
from typing import Optional, List, Dict, Any
from datetime import date, datetime
import PyPDF2 # Using PyPDF2 for simplicity, consider pymupdf for robustness
from PyPDF2 import errors # Import specific errors module
import logging
import re

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration ---
# Ensure you have your Google API Key set as an environment variable
# e.g., export GOOGLE_API_KEY='your_api_key'
try:
    # Use a placeholder if running in an environment where the key isn't set for testing
    # Replace with actual key loading in production
    GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "YOUR_API_KEY_HERE")
    if GOOGLE_API_KEY == "YOUR_API_KEY_HERE":
        logging.warning("GOOGLE_API_KEY environment variable not set. Using placeholder.")
    genai.configure(api_key=GOOGLE_API_KEY)
except Exception as e:
    logging.error(f"Failed to configure Google API: {e}")
    exit(1)

# Specify the root directory containing the FDD PDF folders
# IMPORTANT: Change this to the actual path where your FDD documents are stored
PDF_ROOT_DIRECTORY = pathlib.Path("./fdd_documents_root") # EXAMPLE PATH

# --- Pydantic Models Based on Schema ---

class FddDocumentInfo(BaseModel):
    """Represents metadata about the FDD document itself."""
    fiscal_year: Optional[int] = Field(None, description="The fiscal year the FDD pertains to, often found near the issue date or cover page.")
    issue_date: Optional[date] = Field(None, description="The exact date the FDD was issued, usually prominent on the cover page or first few pages.")
    source_file: Optional[str] = Field(None, description="The relative path to the source PDF file.") # Added source_file field

    @field_validator('issue_date', mode='before')
    @classmethod
    def parse_date(cls, value):
        if isinstance(value, str):
            try:
                # Attempt to parse common date formats
                return datetime.strptime(value, '%Y-%m-%d').date()
            except ValueError:
                try:
                    return datetime.strptime(value, '%m/%d/%Y').date()
                except ValueError:
                     try:
                         # Handle dates like "March 1, 2023"
                         return datetime.strptime(value, '%B %d, %Y').date()
                     except ValueError:
                        logging.warning(f"Could not parse date: {value}. Leaving as None.")
                        return None
        return value

class FranchisorInfo(BaseModel):
    """Represents detailed information about the franchisor."""
    brand_name: Optional[str] = Field(None, description="The primary brand name used by the franchisor (e.g., 'McDonald's'). Often prominent on the cover.")
    legal_name: Optional[str] = Field(None, description="The full legal name of the franchisor entity (e.g., 'McDonald's Corporation'). Check the cover page or introductory paragraphs.")
    parent_company: Optional[str] = Field(None, description="Name of the parent company, if applicable and mentioned (e.g., 'Yum! Brands' for KFC). Look for mentions like 'a subsidiary of...'.")
    phone_number: Optional[str] = Field(None, description="Primary contact phone number for the franchisor, often found in the contact information section.")
    website_url: Optional[str] = Field(None, description="The official website URL of the franchisor or franchise (e.g., 'www.mcdonalds.com').")
    email_contact: Optional[str] = Field(None, description="Primary contact email address, often near the phone number or address.")
    headquarters_address: Optional[str] = Field(None, description="Full street address of the principal business address (headquarters).")
    headquarters_city: Optional[str] = Field(None, description="City of the headquarters.")
    headquarters_state: Optional[str] = Field(None, description="State or province of the headquarters.")
    headquarters_zip: Optional[str] = Field(None, description="Postal code of the headquarters.")
    headquarters_country: Optional[str] = Field(None, description="Country of the headquarters (assume USA if not specified).")
    year_founded: Optional[int] = Field(None, description="The year the original business (not necessarily the franchise) was founded. Look for phrases like 'founded in...' or 'established in...'.")
    year_franchising_began: Optional[int] = Field(None, description="The year the company began offering franchises. Look for phrases like 'began franchising in...' or 'offering franchises since...'.")
    business_description: Optional[str] = Field(None, description="A brief summary description of the type of business operated by the franchisor and its franchisees (e.g., 'operates and franchises quick-service restaurants'). Usually found in Item 1.")
    company_history: Optional[str] = Field(None, description="A brief narrative of the company's history, often included in Item 1.")
    # logo_url is typically not extractable from text

class CombinedFddData(BaseModel):
    """Combined structure for extracting Franchisor and FDD Document info."""
    franchisor: FranchisorInfo
    fdd_document: FddDocumentInfo

# --- LLM Prompt ---

EXTRACTION_PROMPT = """
Analyze the following text extracted from the beginning of a Franchise Disclosure Document (FDD). Your task is to extract specific information about the Franchisor and the FDD document itself, up to the point where "ITEM 2" begins. Structure your output strictly as a JSON object matching the provided schema.

**Extraction Schema:**

```json
{{
  "franchisor": {{
    "brand_name": "string | null",
    "legal_name": "string | null",
    "parent_company": "string | null",
    "phone_number": "string | null",
    "website_url": "string | null",
    "email_contact": "string | null",
    "headquarters_address": "string | null",
    "headquarters_city": "string | null",
    "headquarters_state": "string | null",
    "headquarters_zip": "string | null",
    "headquarters_country": "string | null",
    "year_founded": "integer | null",
    "year_franchising_began": "integer | null",
    "business_description": "string | null",
    "company_history": "string | null"
  }},
  "fdd_document": {{
    "fiscal_year": "integer | null",
    "issue_date": "string (YYYY-MM-DD) | null"
  }}
}}
```

**Instructions:**

1.  **Focus:** Extract information ONLY from the provided text, which represents the start of the FDD up to (but not including) the section explicitly titled "ITEM 2". Do not infer information beyond the text or assume details not present.
2.  **Schema Adherence:** Ensure the output is a valid JSON object exactly matching the schema structure above. Use `null` for any fields where the information cannot be found in the text.
3.  **Data Types:** Pay close attention to data types (string, integer, date format YYYY-MM-DD).
4.  **Specificity:**
    *   `brand_name`: The main commercial name.
    *   `legal_name`: The official company name.
    *   `parent_company`: Only if explicitly stated as a parent or subsidiary relationship.
    *   `headquarters_address`: Include street, city, state, zip if available as a single address block. If components are separate, populate individual fields. Assume USA for country if not specified.
    *   `year_founded`: Year the original business started.
    *   `year_franchising_began`: Year they started selling franchises.
    *   `business_description` / `company_history`: Summarize relevant sentences found, typically within Item 1.
    *   `issue_date`: Find the primary issuance date, often on the cover. Format as YYYY-MM-DD.
    *   `fiscal_year`: The year the FDD covers, sometimes near the issue date.
5.  **Boundaries:** Stop extraction precisely before any text explicitly marking the start of "ITEM 2".

**Input Text:**

```text
{fdd_text}
```

**Output JSON:**
"""

# --- Helper Functions ---

def find_relevant_pdfs(root_dir: pathlib.Path) -> List[pathlib.Path]:
    """
    Recursively finds PDF files within the root directory whose names
    contain 'intro' or 'Item_1' (case-insensitive).
    """
    relevant_files = []
    if not root_dir.is_dir():
        logging.error(f"Provided root directory does not exist or is not a directory: {root_dir}")
        return relevant_files

    logging.info(f"Searching for relevant PDFs in: {root_dir}")
    for path in root_dir.rglob('*.pdf'):
        filename_lower = path.name.lower()
        # Use regex for more flexible matching (e.g., item_1, item 1, item-1)
        if re.search(r'intro', filename_lower) or re.search(r'item_?1', filename_lower):
            relevant_files.append(path)
            logging.info(f"  Found relevant file: {path}")

    if not relevant_files:
        logging.warning(f"No PDFs containing 'intro' or 'Item_1' found in {root_dir}")
    return relevant_files

def extract_text_from_pdf_start(pdf_path: pathlib.Path, max_pages: int = 5) -> Optional[str]:
    """
    Extracts text from the first few pages of a PDF.
    Stops if "ITEM 2" is found.
    """
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            num_pages_to_read = min(len(reader.pages), max_pages)
            logging.info(f"Reading up to {num_pages_to_read} pages from {pdf_path.name}...")

            for i in range(num_pages_to_read):
                page = reader.pages[i]
                page_text = page.extract_text()
                if page_text:
                    # Simple check for ITEM 2 boundary
                    item_2_match = re.search(r'^\s*ITEM\s+2\b', page_text, re.IGNORECASE | re.MULTILINE)
                    if item_2_match:
                        # Take text only up to the start of ITEM 2
                        text += page_text[:item_2_match.start()]
                        logging.info(f"  Found 'ITEM 2' on page {i+1}. Stopping text extraction.")
                        break # Stop reading further pages
                    else:
                        text += page_text + "\n" # Add newline between pages
                else:
                    logging.warning(f"  Could not extract text from page {i+1} of {pdf_path.name}")

            if not text:
                 logging.warning(f"No text could be extracted from the first {num_pages_to_read} pages of {pdf_path.name}")
                 return None
            return text.strip()

    except FileNotFoundError:
        logging.error(f"PDF file not found: {pdf_path}")
        return None
    except errors.PdfReadError as e: # Use imported errors module
        logging.error(f"Error reading PDF file {pdf_path}: {e}")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred while processing {pdf_path}: {e}")
        return None


def extract_fdd_data_with_gemini(fdd_text: str) -> Optional[CombinedFddData]:
    """
    Calls the Gemini API to extract structured data from FDD text.
    """
    if not fdd_text:
        logging.warning("No text provided to Gemini.")
        return None
    if GOOGLE_API_KEY == "YOUR_API_KEY_HERE":
         logging.error("Cannot call Gemini without a valid API key.")
         return None

    try:
        model = genai.GenerativeModel('gemini-pro') # Or specify a newer/different model if needed
        prompt = EXTRACTION_PROMPT.format(fdd_text=fdd_text)

        logging.info("Sending request to Gemini API...")
        response = model.generate_content(prompt)

        # Clean the response: Gemini might wrap the JSON in ```json ... ```
        cleaned_response_text = re.sub(r'^```json\s*|\s*```$', '', response.text.strip(), flags=re.MULTILINE)

        logging.info("Received response from Gemini. Attempting to parse JSON.")
        # print(f"--- Gemini Raw Response ---\n{response.text}\n--------------------------")
        # print(f"--- Cleaned Response ---\n{cleaned_response_text}\n--------------------------")


        try:
            data = json.loads(cleaned_response_text)
            validated_data = CombinedFddData(**data)
            logging.info("Successfully parsed and validated Gemini response.")
            return validated_data
        except json.JSONDecodeError as e:
            logging.error(f"Failed to decode JSON from Gemini response: {e}")
            logging.error(f"Problematic response text: {cleaned_response_text}")
            return None
        except ValidationError as e:
            logging.error(f"Failed to validate Pydantic model from Gemini response: {e}")
            logging.error(f"Data received: {cleaned_response_text}")
            return None

    except Exception as e:
        logging.error(f"An error occurred during the Gemini API call: {e}")
        # Log more details if available, e.g., response status code if using requests
        return None

# --- Main Execution ---

if __name__ == "__main__":
    logging.info("Starting FDD extraction process...")

    if not PDF_ROOT_DIRECTORY.exists():
        logging.error(f"Root directory '{PDF_ROOT_DIRECTORY}' not found. Please check the path.")
        exit(1)

    relevant_pdfs = find_relevant_pdfs(PDF_ROOT_DIRECTORY)
    all_extracted_data = []

    if not relevant_pdfs:
        logging.info("No relevant PDF files found to process.")
    else:
        logging.info(f"Found {len(relevant_pdfs)} relevant PDF(s). Processing...")
        for pdf_path in relevant_pdfs:
            logging.info(f"\n--- Processing: {pdf_path.name} ---")
            extracted_text = extract_text_from_pdf_start(pdf_path, max_pages=5) # Adjust max_pages if needed

            if extracted_text:
                logging.info(f"Extracted {len(extracted_text)} characters. Sending to Gemini...")
                # print(f"--- Extracted Text Snippet ---\n{extracted_text[:500]}...\n-----------------------------") # Uncomment for debugging
                extracted_data = extract_fdd_data_with_gemini(extracted_text)

                if extracted_data:
                    # Add the source file path to the document info
                    extracted_data.fdd_document.source_file = str(pdf_path.relative_to(PDF_ROOT_DIRECTORY))
                    all_extracted_data.append(extracted_data.model_dump(mode='json')) # Use model_dump for Pydantic v2
                    logging.info(f"Successfully extracted data for {pdf_path.name}")
                else:
                    logging.warning(f"Could not extract structured data for {pdf_path.name}")
            else:
                logging.warning(f"Skipping {pdf_path.name} due to text extraction failure.")

    # --- Output ---
    output_filename = "extracted_fdd_data.json"
    if all_extracted_data:
        try:
            with open(output_filename, 'w') as f:
                json.dump(all_extracted_data, f, indent=2, default=str) # Use default=str to handle dates
            logging.info(f"Successfully wrote {len(all_extracted_data)} extracted records to {output_filename}")
        except IOError as e:
            logging.error(f"Failed to write output file {output_filename}: {e}")
    else:
        logging.info("No data was extracted successfully.")

    logging.info("FDD extraction process finished.")
