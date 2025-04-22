"""Handles writing extracted email data to CSV files."""

import csv
import logging
import os
from typing import Dict, Any

# Define the expected header row for consistency
CSV_HEADER = [
    'email_address',
    'source_document_path',
    'source_document_filename',
    'page_number',
    'extraction_timestamp' # Match DB column
]

def ensure_dir_exists(dir_path: str) -> None:
    """Creates the directory if it doesn't exist."""
    try:
        os.makedirs(dir_path, exist_ok=True)
        logging.debug(f"Ensured output directory exists: {dir_path}")
    except OSError as e:
        logging.error(f"Could not create directory {dir_path}: {e}")
        raise # Re-raise to potentially stop processing

def write_email_to_csv(csv_path: str, email_data: Dict[str, Any]) -> None:
    """Appends a single email record to a CSV file.

    Creates the file and writes the header if it doesn't exist.

    Args:
        csv_path: The full path to the target CSV file.
        email_data: A dictionary containing the email record details.
                    Expected keys match CSV_HEADER.
    """
    file_exists = os.path.exists(csv_path)

    try:
        # Include the extraction timestamp from the database logic if available,
        # otherwise generate it here? For consistency, let's assume it's passed
        # in email_data similar to how it's added before DB insertion.
        if 'extraction_timestamp' not in email_data:
            logging.warning(f"'extraction_timestamp' missing in email_data for CSV write. Using current time.")
            # This should ideally be passed from main.py for consistency with DB
            from datetime import datetime
            email_data['extraction_timestamp'] = datetime.now().isoformat()

        # Ensure all header keys are present
        row_data = {header: email_data.get(header, '') for header in CSV_HEADER}

        with open(csv_path, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=CSV_HEADER)

            if not file_exists:
                writer.writeheader()
                logging.info(f"Created new CSV file and wrote header: {csv_path}")

            writer.writerow(row_data)
            logging.debug(f"Appended email to CSV: {row_data['email_address']} in {os.path.basename(csv_path)}")

    except IOError as e:
        logging.error(f"Could not write to CSV file {csv_path}: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred writing to CSV {csv_path}: {e}") 