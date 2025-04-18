#!/usr/bin/env python3
"""
Scans a directory containing split FDD PDFs, extracts metadata from filenames,
and populates the FDDFileIndex table in the franchise_directory database.
"""

import os
import re
from pathlib import Path
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import logging

# Assuming the schema definitions are in LLM.franchise_directory_schema relative to project root
# Adjust the import path if your project structure is different
try:
    from LLM.franchise_directory_schema import Base, FDDFileIndex, _enable_sqlite_fk, State # Import necessary items
except ImportError:
    print("Error: Could not import schema definitions. Make sure LLM/franchise_directory_schema.py is accessible.")
    print("Attempting import from parent directory...")
    # This is a common fallback if the script is run from a different location
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from LLM.franchise_directory_schema import Base, FDDFileIndex, _enable_sqlite_fk, State


# --- Configuration ---
DEFAULT_DB_PATH = "franchise_directory.sqlite"
# IMPORTANT: Update this path to the actual location of your split PDFs
DEFAULT_PDF_SPLIT_DIR = "/Users/miller/Library/CloudStorage/OneDrive-Personal/FDD_PDFS/split_pdfs"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Helper Functions ---

def check_db_exists(db_path: str) -> bool:
    """Checks if the SQLite database file exists."""
    return Path(db_path).is_file()

def extract_section_info(filename: str) -> tuple[str | None, str | None, int | None]:
    """
    Extracts section information from a filename.
    Handles patterns like 'ITEM_XX.pdf', 'intro.pdf', etc.
    Returns: (section_identifier, section_type, extracted_item_number)
    """
    name_part = Path(filename).stem.lower() # Use lowercase for consistency
    identifier = Path(filename).stem # Keep original case for identifier if needed

    item_match = re.match(r"item_?(\d+)", name_part)
    intro_match = name_part == "intro"
    # Add more patterns here if needed (e.g., exhibits)
    # exhibit_match = re.match(r"exhibit_?([a-z0-9]+)", name_part)

    if item_match:
        item_number = int(item_match.group(1))
        return identifier, "ITEM", item_number
    elif intro_match:
        return identifier, "INTRO", None
    # elif exhibit_match:
    #     exhibit_id = exhibit_match.group(1)
    #     return identifier, "EXHIBIT", None # Or parse exhibit_id further if needed
    else:
        # Default for unrecognized patterns
        return identifier, "OTHER", None

# --- Main Population Logic ---

def populate_fdd_index(db_path: str, pdf_split_dir: str):
    """
    Scans the pdf_split_dir, extracts info, and populates the FDDFileIndex table.
    Verifies the presence of 'intro.pdf' for each filing_id.
    """
    logging.info(f"Starting FDD file indexing process.")
    logging.info(f"Database path: {db_path}")
    logging.info(f"Scanning directory: {pdf_split_dir}")

    if not check_db_exists(db_path):
        logging.error(f"Database file not found at {db_path}. Please create it first (e.g., by running franchise_directory_schema.py).")
        return

    pdf_dir = Path(pdf_split_dir)
    if not pdf_dir.is_dir():
        logging.error(f"PDF split directory not found or is not a directory: {pdf_split_dir}")
        return

    db_url = f"sqlite:///{Path(db_path).resolve()}"
    engine = create_engine(db_url, echo=False, future=True)
    # Ensure FKs are enabled if relationships are added later
    # sqlalchemy.event.listen(engine, "connect", _enable_sqlite_fk)

    # Check if the table exists, create if not (though schema script should handle this)
    # FDDFileIndex.__table__.create(engine, checkfirst=True)

    processed_filings = 0
    processed_files = 0
    filings_with_intro = 0
    filings_missing_intro = 0

    with Session(engine) as session:
        # Get existing file paths to avoid duplicates efficiently
        existing_paths = set(row[0] for row in session.execute(select(FDDFileIndex.file_path)).all())
        logging.info(f"Found {len(existing_paths)} existing file paths in the index.")

        for filing_dir in pdf_dir.iterdir():
            if filing_dir.is_dir(): # Process only directories
                filing_id = filing_dir.name
                logging.debug(f"Processing filing ID: {filing_id}")

                # Basic UUID format check (optional, but good practice)
                if not re.match(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", filing_id.lower()):
                    logging.warning(f"Skipping directory '{filing_id}' - name does not look like a UUID.")
                    continue

                processed_filings += 1
                has_intro = False
                files_in_filing = 0
                new_files_added = 0

                for file_path in filing_dir.glob('*.pdf'): # Look specifically for PDFs
                    files_in_filing += 1
                    abs_file_path_str = str(file_path.resolve())

                    # Skip if already processed
                    if abs_file_path_str in existing_paths:
                        logging.debug(f"Skipping already indexed file: {abs_file_path_str}")
                        # Still check for intro even if files are skipped
                        if file_path.name.lower() == 'intro.pdf':
                            has_intro = True
                        continue

                    identifier, section_type, item_number = extract_section_info(file_path.name)

                    if file_path.name.lower() == 'intro.pdf':
                        has_intro = True

                    index_entry = FDDFileIndex(
                        filing_id=filing_id,
                        file_path=abs_file_path_str,
                        section_identifier=identifier,
                        section_type=section_type,
                        extracted_item_number=item_number
                    )
                    session.add(index_entry)
                    existing_paths.add(abs_file_path_str) # Add to set to prevent re-adding in this run
                    processed_files += 1
                    new_files_added += 1

                if files_in_filing > 0:
                    logging.info(f"Filing '{filing_id}': Found {files_in_filing} PDFs, added {new_files_added} new index entries.")
                    if has_intro:
                        logging.info(f"  -> Confirmed 'intro.pdf' is present.")
                        filings_with_intro += 1
                    else:
                        logging.warning(f"  -> 'intro.pdf' NOT found in this filing directory.")
                        filings_missing_intro += 1
                else:
                     logging.debug(f"No PDF files found in directory: {filing_dir}")


        try:
            session.commit()
            logging.info("Successfully committed changes to the database.")
        except IntegrityError as e:
            logging.error(f"Database integrity error during commit: {e}")
            logging.error("Rolling back changes for this batch.")
            session.rollback()
        except Exception as e:
            logging.error(f"An unexpected error occurred during commit: {e}")
            logging.error("Rolling back changes.")
            session.rollback()


    logging.info("--- Indexing Summary ---")
    logging.info(f"Total filing directories processed: {processed_filings}")
    logging.info(f"Total new file index entries added: {processed_files}")
    logging.info(f"Filings confirmed with 'intro.pdf': {filings_with_intro}")
    logging.info(f"Filings missing 'intro.pdf': {filings_missing_intro}")
    logging.info("FDD file indexing process finished.")


# --- Entrypoint ---

if __name__ == "__main__":
    # In a real application, consider using argparse for command-line arguments
    db_path = os.getenv("FRANCHISE_DB_PATH", DEFAULT_DB_PATH)
    pdf_dir = os.getenv("PDF_SPLIT_DIR", DEFAULT_PDF_SPLIT_DIR)

    populate_fdd_index(db_path=db_path, pdf_split_dir=pdf_dir) 