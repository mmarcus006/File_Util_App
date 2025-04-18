#!/usr/bin/env python3
"""
Processes FDD Intro and Item 1 PDFs using Gemini to extract key information
and update the Franchisor records in the database.
"""

import os
import re
import json
import fitz  # PyMuPDF
import google.generativeai as genai
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple

from sqlalchemy import create_engine, select, update
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy.exc import SQLAlchemyError

# Assuming the schema definitions are in LLM.franchise_directory_schema relative to project root
try:
    from LLM.franchise_directory_schema import (
        Base, Franchisor, FDDDocument, FDDFileIndex, _enable_sqlite_fk
    )
except ImportError:
    print("Error: Could not import schema definitions. Make sure LLM/franchise_directory_schema.py is accessible.")
    print("Attempting import from parent directory...")
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from LLM.franchise_directory_schema import (
        Base, Franchisor, FDDDocument, FDDFileIndex, _enable_sqlite_fk
    )

# --- Configuration ---
DEFAULT_DB_PATH = "franchise_directory.sqlite"
# Load API Key from environment variable
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
# Specify the Gemini model to use
DEFAULT_GEMINI_MODEL = "gemini-1.5-flash-latest" # Or choose another appropriate model

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Helper Functions ---

def check_db_exists(db_path: str) -> bool:
    """Checks if the SQLite database file exists."""
    return Path(db_path).is_file()

def extract_text_from_pdf(pdf_path: str) -> Optional[str]:
    """Extracts text content from a PDF file using PyMuPDF."""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        logging.debug(f"Successfully extracted text from: {pdf_path}")
        return text
    except Exception as e:
        logging.error(f"Error extracting text from {pdf_path}: {e}", exc_info=True)
        return None

def get_gemini_client(api_key: str) -> Optional[genai.GenerativeModel]:
    """Initializes and returns the Gemini client."""
    if not api_key:
        logging.error("GOOGLE_API_KEY environment variable not set.")
        return None
    try:
        genai.configure(api_key=api_key)
        return genai.GenerativeModel(DEFAULT_GEMINI_MODEL)
    except Exception as e:
        logging.error(f"Failed to configure or initialize Gemini client: {e}", exc_info=True)
        return None

def call_gemini_api(client: genai.GenerativeModel, intro_text: str, item1_text: str) -> Optional[dict]:
    """Constructs a prompt, calls the Gemini API, and parses the JSON response."""
    # ** Adjust this prompt based on your specific needs and desired JSON structure **
    prompt = f"""
Please analyze the following text extracted from a Franchise Disclosure Document (FDD).

**Introduction Text:**
{intro_text}

**Item 1 Text:**
{item1_text}

Based ONLY on the text provided, extract the following information and return it as a JSON object:
1.  `brand_name`: The primary name of the franchise brand.
2.  `legal_name`: The legal name of the franchisor entity, if mentioned.
3.  `business_description`: A concise summary of the business operated by franchisees.
4.  `year_founded`: The year the original business was founded, if mentioned.
5.  `year_franchising_began`: The year the company began offering franchises, if mentioned.

Return ONLY the JSON object, with null values for any fields not found in the text.
Example Output: {{"brand_name": "Example Franchise", "legal_name": "Example Inc.", "business_description": "Operates fast-food restaurants.", "year_founded": 1990, "year_franchising_began": 1995}}
"""

    try:
        logging.info("Sending request to Gemini API...")
        # Ensure response is treated as JSON
        generation_config = genai.types.GenerationConfig(response_mime_type="application/json")
        response = client.generate_content(prompt, generation_config=generation_config)

        # Accessing the text content which should be JSON
        if response.parts:
             json_text = response.text # Access text directly if using response_mime_type
             logging.debug(f"Received Gemini response (text): {json_text}")
             # Attempt to parse the JSON string
             try:
                 parsed_json = json.loads(json_text)
                 logging.info("Successfully parsed JSON response from Gemini.")
                 return parsed_json
             except json.JSONDecodeError as json_err:
                 logging.error(f"Failed to decode JSON response from Gemini: {json_err}")
                 logging.error(f"Raw response text: {json_text}")
                 return None
        else:
             logging.warning("Gemini response contained no parts.")
             return None

    except Exception as e:
        logging.error(f"Error calling Gemini API: {e}", exc_info=True)
        return None

def find_fdd_files(session: Session, filing_id: str) -> Tuple[Optional[str], Optional[str]]:
    """Finds the file paths for Intro and Item 1 for a given filing_id."""
    intro_path = None
    item1_path = None

    stmt = select(FDDFileIndex.file_path, FDDFileIndex.section_type, FDDFileIndex.extracted_item_number)\
           .where(FDDFileIndex.filing_id == filing_id)\
           .where(
               (FDDFileIndex.section_type == 'INTRO') |
               ((FDDFileIndex.section_type == 'ITEM') & (FDDFileIndex.extracted_item_number == 1))
           )

    results = session.execute(stmt).all()

    for row in results:
        fpath, stype, inum = row
        if stype == 'INTRO':
            intro_path = fpath
        elif stype == 'ITEM' and inum == 1:
            item1_path = fpath

    return intro_path, item1_path

def update_franchisor_data(session: Session, franchisor: Franchisor, gemini_data: dict):
    """Updates Franchisor fields based on parsed Gemini JSON data."""
    # ** Map JSON fields to SQLAlchemy model fields **
    # Use .get() to handle potentially missing keys gracefully
    update_values = {}
    if 'brand_name' in gemini_data and gemini_data['brand_name']:
        update_values['brand_name'] = gemini_data['brand_name']
    if 'legal_name' in gemini_data and gemini_data['legal_name']:
        update_values['legal_name'] = gemini_data['legal_name']
    if 'business_description' in gemini_data and gemini_data['business_description']:
        update_values['business_description'] = gemini_data['business_description']
    if 'year_founded' in gemini_data and isinstance(gemini_data['year_founded'], int):
        update_values['year_founded'] = gemini_data['year_founded']
    if 'year_franchising_began' in gemini_data and isinstance(gemini_data['year_franchising_began'], int):
        update_values['year_franchising_began'] = gemini_data['year_franchising_began']

    if not update_values:
        logging.warning(f"Gemini data for Franchisor ID {franchisor.id} resulted in no fields to update.")
        return False # Indicate no update occurred

    try:
        # Update the specific franchisor instance
        for key, value in update_values.items():
            setattr(franchisor, key, value)
        franchisor.gemini_processed_at = datetime.utcnow()
        logging.info(f"Prepared updates for Franchisor ID {franchisor.id}: {update_values.keys()}")
        return True # Indicate update is ready to be committed

    except Exception as e:
         # This catches errors during setattr, less likely but possible
         logging.error(f"Error preparing update for Franchisor ID {franchisor.id}: {e}", exc_info=True)
         return False


# --- Main Processing Logic ---=
def process_filings(db_path: str, api_key: str):
    """Main function to iterate through filings, process files, call LLM, and update DB."""
    logging.info("Starting FDD Intro/Item 1 processing.")

    if not check_db_exists(db_path):
        logging.error(f"Database file not found at {db_path}. Exiting.")
        return

    gemini_client = get_gemini_client(api_key)
    if not gemini_client:
        logging.error("Failed to initialize Gemini client. Exiting.")
        return

    db_url = f"sqlite:///{Path(db_path).resolve()}"
    engine = create_engine(db_url, echo=False, future=True)
    # sqlalchemy.event.listen(engine, "connect", _enable_sqlite_fk)

    processed_count = 0
    skipped_already_processed = 0
    skipped_missing_files = 0
    skipped_pdf_error = 0
    skipped_api_error = 0
    updated_count = 0
    error_count = 0

    with Session(engine) as session:
        # Get distinct filing IDs that have associated files
        filing_id_stmt = select(FDDFileIndex.filing_id).distinct()
        filing_ids = [row[0] for row in session.execute(filing_id_stmt).all()]
        logging.info(f"Found {len(filing_ids)} unique filing IDs in the index.")

        for filing_id in filing_ids:
            logging.info(f"--- Processing Filing ID: {filing_id} ---")
            try:
                # Find the FDDDocument first, then get the Franchisor
                fdd_doc = session.query(FDDDocument).options(
                    joinedload(FDDDocument.franchisor)
                ).get(filing_id)

                if not fdd_doc:
                    logging.warning(f"No FDDDocument found for filing_id {filing_id}. Skipping.")
                    error_count += 1
                    continue

                franchisor = fdd_doc.franchisor
                if not franchisor:
                    logging.warning(f"FDDDocument {filing_id} has no associated Franchisor. Skipping.")
                    error_count += 1
                    continue

                # Check if already processed
                if franchisor.gemini_processed_at:
                    logging.info(f"Franchisor {franchisor.id} (Filing {filing_id}) already processed on {franchisor.gemini_processed_at}. Skipping.")
                    skipped_already_processed += 1
                    continue

                # Find Intro and Item 1 PDF paths
                intro_pdf_path, item1_pdf_path = find_fdd_files(session, filing_id)

                if not intro_pdf_path or not item1_pdf_path:
                    logging.warning(f"Could not find both Intro and Item 1 file paths for filing {filing_id}. Skipping.")
                    skipped_missing_files += 1
                    continue

                # Verify files exist on disk
                if not Path(intro_pdf_path).is_file() or not Path(item1_pdf_path).is_file():
                    logging.warning(f"Intro ({intro_pdf_path}) or Item 1 ({item1_pdf_path}) file not found on disk for filing {filing_id}. Skipping.")
                    skipped_missing_files += 1
                    continue

                # Extract text
                intro_text = extract_text_from_pdf(intro_pdf_path)
                item1_text = extract_text_from_pdf(item1_pdf_path)

                if intro_text is None or item1_text is None:
                    logging.warning(f"Failed to extract text from Intro or Item 1 PDF for filing {filing_id}. Skipping.")
                    skipped_pdf_error += 1
                    continue

                # Call Gemini
                gemini_data = call_gemini_api(gemini_client, intro_text, item1_text)

                if gemini_data is None:
                    logging.warning(f"Failed to get valid data from Gemini API for filing {filing_id}. Skipping.")
                    skipped_api_error += 1
                    continue

                # Prepare and attempt update
                update_prepared = update_franchisor_data(session, franchisor, gemini_data)

                if update_prepared:
                    try:
                        session.commit() # Commit changes for this specific franchisor
                        logging.info(f"Successfully updated and committed Franchisor {franchisor.id} (Filing {filing_id}).")
                        updated_count += 1
                    except SQLAlchemyError as db_err:
                        logging.error(f"Database error committing update for Franchisor {franchisor.id} (Filing {filing_id}): {db_err}", exc_info=True)
                        session.rollback() # Rollback only this franchisor's changes
                        error_count += 1
                else:
                    # No update was made based on Gemini data, or error during prep
                    logging.warning(f"No update performed for Franchisor {franchisor.id} (Filing {filing_id}) based on Gemini data.")
                    # Optionally mark as processed even if no data found? Depends on desired logic.
                    # franchisor.gemini_processed_at = datetime.utcnow()
                    # session.commit() # Commit the timestamp update

                processed_count += 1 # Count successful processing cycle, even if no update made

            except Exception as e:
                logging.error(f"Unexpected error processing filing {filing_id}: {e}", exc_info=True)
                session.rollback() # Rollback any potential changes from this iteration
                error_count += 1

    logging.info("--- Processing Summary ---")
    logging.info(f"Total Filing IDs Found: {len(filing_ids)}")
    logging.info(f"Successfully Processed Cycles: {processed_count}")
    logging.info(f"Franchisor Records Updated: {updated_count}")
    logging.info(f"Skipped (Already Processed): {skipped_already_processed}")
    logging.info(f"Skipped (Missing DB Paths/Files): {skipped_missing_files}")
    logging.info(f"Skipped (PDF Text Error): {skipped_pdf_error}")
    logging.info(f"Skipped (Gemini API/JSON Error): {skipped_api_error}")
    logging.info(f"Errors During Processing/DB Commit: {error_count}")
    logging.info("FDD Intro/Item 1 processing finished.")

# --- Entrypoint ---

if __name__ == "__main__":
    db_path = os.getenv("FRANCHISE_DB_PATH", DEFAULT_DB_PATH)
    api_key = GOOGLE_API_KEY # Loaded globally

    if not api_key:
        print("Error: GOOGLE_API_KEY environment variable is not set.")
    else:
        process_filings(db_path=db_path, api_key=api_key) 