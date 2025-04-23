"""Main orchestration script for the FDD email extraction process."""

import logging
import os
import sys
import glob # Added for finding PDF files
from datetime import datetime # Added for consistent timestamping
from PyPDF2 import PdfReader
from PyPDF2.errors import PdfReadError
from sqlalchemy.engine import Engine # Import Engine type for hinting

# Project specific imports
import config
import database_manager
import pdf_processor
import ocr_handler
import email_extractor
import csv_writer # Added for CSV output

# --- Corrected Logging Setup using Handlers ---
log_format = '%(asctime)s - %(levelname)s - %(module)s - %(message)s'
log_level = logging.DEBUG # Set desired level here

# Get root logger
logger = logging.getLogger()
logger.setLevel(log_level) # Set root logger level

# Create formatter
formatter = logging.Formatter(log_format)

# Create console handler and set level
ch = logging.StreamHandler() # Default is sys.stderr, use logging.StreamHandler(sys.stdout) for stdout
ch.setLevel(log_level)
ch.setFormatter(formatter)
logger.addHandler(ch)

# Create file handler and set level
fh = logging.FileHandler('scraper.log', mode='a') # Append mode
fh.setLevel(log_level)
fh.setFormatter(formatter)
logger.addHandler(fh)

# Prevent duplicate logging if script is reloaded in interactive session (optional but good practice)
logger.propagate = False 

# --- --- --- --- --- --- --- --- --- --- --- ---

def process_single_pdf(pdf_path: str, engine: Engine, output_csv_dir: str) -> None:
    """Processes a single PDF document for email extraction, saving to CSV and DB using SQLAlchemy.

    Args:
        pdf_path: Path to the input PDF file.
        engine: SQLAlchemy Engine instance for database interaction.
        output_csv_dir: Path to the directory where CSV output should be saved.
    """
    logging.info(f"Starting processing for PDF: {pdf_path}")

    # 1. Prepare source document info
    try:
        abs_pdf_path = os.path.abspath(pdf_path)
        pdf_filename = os.path.basename(pdf_path)
        # Construct CSV path for this specific PDF
        csv_filename = os.path.splitext(pdf_filename)[0] + '.csv'
        csv_path = os.path.join(output_csv_dir, csv_filename)
    except Exception as e:
        logging.error(f"Error processing input file path {pdf_path}: {e}")
        return

    # 2. Open and Process PDF
    pdf_reader: PdfReader | None = None
    try:
        with open(pdf_path, 'rb') as pdf_file:
            pdf_reader = PdfReader(pdf_file)
            page_count = len(pdf_reader.pages)
            logging.info(f"Opened PDF: {pdf_filename}, found {page_count} pages.")

            # 3. Iterate through pages
            for page_num in range(page_count):
                logging.info(f"Processing page {page_num + 1}/{page_count}...")
                text = None

                # 3a. Try direct text extraction
                direct_text = pdf_processor.extract_text_from_page(pdf_reader, page_num)

                if direct_text:
                    text = direct_text
                else:
                    # 3b. If direct fails, try OCR
                    logging.warning(f"Direct text extraction failed or empty for page {page_num + 1}. Attempting OCR.")
                    ocr_text = ocr_handler.extract_text_via_ocr(abs_pdf_path, page_num)
                    if ocr_text:
                        text = ocr_text
                    else:
                        logging.error(f"OCR also failed for page {page_num + 1}. Skipping page.")
                        continue # Skip to next page if no text obtained

                # 3c. Extract emails from obtained text
                if text:
                    found_emails = email_extractor.find_emails(text)
                    if found_emails:
                        logging.info(f"Found {len(found_emails)} emails on page {page_num + 1}.")
                        # 3d. Save emails to CSV and DB
                        for email in found_emails:
                            # Generate timestamp once for consistency
                            timestamp = datetime.now().isoformat()
                            email_data = {
                                'email_address': email,
                                'source_document_path': abs_pdf_path,
                                'source_document_filename': pdf_filename,
                                'page_number': page_num + 1, # Store 1-based page number
                                'extraction_timestamp': timestamp
                            }
                            # Write to CSV first
                            csv_writer.write_email_to_csv(csv_path, email_data)
                            # Then write to Database using the engine
                            inserted = database_manager.insert_email(engine, email_data)
                    else:
                        logging.info(f"No emails found on page {page_num + 1}.")
                # else: Handled by the continue statement above

    except FileNotFoundError:
        logging.error(f"Input PDF file not found: {pdf_path}")
    except PdfReadError as e:
        logging.error(f"Error reading PDF file {pdf_filename}: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred during processing {pdf_filename}: {e}", exc_info=True)
    finally:
        logging.info(f"Finished processing PDF: {pdf_filename}")

if __name__ == "__main__":
    # --- Configuration ---
    input_folder = config.INPUT_FOLDER_PATH
    db_file = config.DATABASE_PATH # Still need the file name for the URL
    csv_dir_name = config.OUTPUT_CSV_DIR
    # --- ---------------

    # --- Construct Database URL ---
    # Assuming db_file is just the filename, place it in the script directory
    # Adjust this logic if DATABASE_PATH is an absolute path or elsewhere
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_file_abs = os.path.join(script_dir, db_file)
    db_url = f"sqlite:///{db_file_abs}" # Create SQLite URL
    # --- ---------------------- ---

    # Get absolute path for CSV output directory relative to this script's location
    output_csv_dir_abs = os.path.join(script_dir, csv_dir_name)

    # 1. Ensure CSV output directory exists
    try:
        csv_writer.ensure_dir_exists(output_csv_dir_abs)
    except Exception as e:
        logging.critical(f"Failed to create output CSV directory {output_csv_dir_abs}. Exiting. Error: {e}")
        sys.exit(1)

    # 2. Initialize Database using SQLAlchemy and get the engine
    engine: Engine | None = None # Initialize engine variable
    try:
        engine = database_manager.init_db(db_url) # Call SQLAlchemy init_db
        logging.info(f"SQLAlchemy engine created and schema ensured for {db_url}")
    except Exception as e:
        logging.critical(f"Failed to initialize database via SQLAlchemy at {db_url}. Cannot proceed. Error: {e}")
        sys.exit(1)
    # --- Removed check: if engine is None: sys.exit(1) --- # init_db raises on failure

    # 3. Find PDF files in the input folder
    if not os.path.isdir(input_folder):
        logging.error(f"Input folder does not exist or is not a directory: {input_folder}")
        sys.exit(1)

    pdf_files = glob.glob(os.path.join(input_folder, '*.pdf'))
    if not pdf_files:
        logging.warning(f"No PDF files found in the input folder: {input_folder}")
        sys.exit(0)

    logging.info(f"Found {len(pdf_files)} PDF files to process in {input_folder}.")

    # 4. Process each PDF file, passing the engine
    for pdf_file_path in pdf_files:
        process_single_pdf(pdf_file_path, engine, output_csv_dir_abs) # Pass engine

    logging.info("--- All PDF processing complete ---") 