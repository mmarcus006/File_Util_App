"""
File processor for extracting file IDs from CSV, finding corresponding files,
and extracting header data into the database using SQLAlchemy ORM.
"""

import os
import csv
import glob
import json
import logging
from typing import List, Optional, Dict
from pathlib import Path

# PDF processing and file system operations
# import fitz # PyMuPDF --- Removed, moved to pdf_splitter
# import shutil # --- Removed, moved to pdf_splitter

from config import Config
from database import (
    init_database, 
    add_or_update_file,
    check_if_output_file_exists,
    get_file_by_id,
    get_items_for_file # Import the new function
)
# Import the new splitter function
from pdf_splitter import split_pdf_by_items

logger = logging.getLogger(__name__)

def extract_file_ids_from_csv(csv_path: str) -> List[str]:
    """
    Extract file IDs from the second column of the CSV file.
    Skips the first two header rows.
    
    Args:
        csv_path: Path to the CSV file
        
    Returns:
        List[str]: List of file IDs
    """
    if not check_if_output_file_exists(csv_path):
        logger.error(f"Input CSV file not found: {csv_path}")
        return []
    
    file_ids = []
    try:
        with open(csv_path, 'r', encoding='utf-8') as csv_file:
            csv_reader = csv.reader(csv_file)
            
            # Skip the first two header rows
            try:
                next(csv_reader, None) # Skip first header
                next(csv_reader, None) # Skip second header
            except StopIteration:
                logger.warning(f"CSV file {csv_path} has less than 2 rows. No data to process.")
                return []

            # Process data rows
            row_count = 2 # Start counting after headers
            for row in csv_reader:
                row_count += 1
                if len(row) >= 2:
                    file_id = row[1].strip()
                    if file_id:
                        file_ids.append(file_id)
                    else:
                         logger.warning(f"Row {row_count} has empty file ID in column 2.")
                else:
                    logger.warning(f"Row {row_count} has insufficient columns (expected at least 2): {row}")
        
        logger.info(f"Extracted {len(file_ids)} file IDs from CSV: {csv_path}")
        return file_ids
    except FileNotFoundError:
        logger.error(f"Input CSV file not found during open: {csv_path}")
        return []
    except Exception as e:
        logger.error(f"Error reading CSV file {csv_path}: {e}", exc_info=True)
        return []

def find_matching_file(directory: str, file_id: str) -> Optional[str]:
    """
    Find a file in the given directory that contains the file ID in its name.
    Uses glob for pattern matching.
    
    Args:
        directory: Directory path to search in.
        file_id: File ID pattern to match within filenames.
        
    Returns:
        Optional[str]: Full path to the first matching file or None if not found/error.
    """
    if not directory or not check_if_output_file_exists(directory):
        logger.warning(f"Search directory not found or not specified: {directory}")
        return None
    
    try:
        # Construct a glob pattern to find files containing the file_id
        # Use Pathlib for better path joining, though os.path.join is fine too
        pattern = os.path.join(directory, f"*{file_id}*")
        matches = glob.glob(pattern)
        
        if matches:
            # Log if multiple matches are found, but return the first one
            if len(matches) > 1:
                 logger.warning(f"Multiple files matched file_id '{file_id}' in {directory}. Using first match: {matches[0]}")
            return matches[0]
        else:
            logger.debug(f"No file matching file_id '{file_id}' found in {directory}")
            return None
    except Exception as e:
        logger.error(f"Error during file search in {directory} for {file_id}: {e}", exc_info=True)
        return None

def read_header_json(file_path: Optional[str]) -> Optional[List[Dict]]:
    """
    Reads and parses JSON data (expected to be a list of objects) from the given file path.

    Args:
        file_path: Path to the JSON file.

    Returns:
        Parsed JSON data as a list of dictionaries, or None if file not found, invalid JSON, or not a list.
    """
    if not file_path or not check_if_output_file_exists(file_path):
        logger.info(f"JSON item file path not provided or file not found: {file_path}") 
        return None
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # --- Validate that the loaded data is a list --- 
            if not isinstance(data, list):
                logger.error(f"Invalid format in JSON item file {file_path}: Expected a list, got {type(data)}.")
                return None
            
            # Optional: Validate structure of items within the list (basic check)
            # if data and not all(isinstance(item, dict) for item in data):
            #     logger.error(f"Invalid format in JSON item file {file_path}: List items are not all dictionaries.")
            #     return None
                
            logger.debug(f"Successfully read and parsed JSON list from: {file_path}")
            return data # Return the list
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in item file {file_path}: {e}", exc_info=True)
        return None
    except FileNotFoundError:
        logger.error(f"Item file not found during open: {file_path}")
        return None
    except Exception as e:
        logger.error(f"Error reading item file {file_path}: {e}", exc_info=True)
        return None

def process_file_ids(file_ids: List[str]) -> int:
    """
    Processes a list of file IDs:
    1. Finds corresponding files in configured directories.
    2. Reads JSON item data from the corresponding file (if found).
    3. Adds or updates file and associated item information in the database via ORM.
    
    Args:
        file_ids: List of file IDs to process.
        
    Returns:
        int: Count of file IDs successfully processed and added/updated in the DB.
    """
    processed_count = 0
    total_ids = len(file_ids)
    logger.info(f"Starting processing for {total_ids} file IDs.")
    
    for index, file_id in enumerate(file_ids, 1):
        logger.debug(f"Processing file ID {index}/{total_ids}: {file_id}")
        
        # 1. Find matching files
        huridoc_path = find_matching_file(Config.HURIDOC_ANALYSIS_DIR, file_id)
        processed_path = find_matching_file(Config.PROCESSED_OUTPUTS_DIR, file_id)
        item_data_path = find_matching_file(Config.HEADER_OUTPUT_DIR, file_id)
        
        # 2. Read JSON item data
        item_data_list = read_header_json(item_data_path) # Pass the found path

        # 3. Add/Update database record using ORM
        # The database function now handles File and the new JsonItem table
        result_file_obj = add_or_update_file(
            file_id=file_id,
            huridoc_path=huridoc_path,
            processed_path=processed_path,
            header_path=item_data_path, # Pass the path to the JSON file itself
            item_data_list=item_data_list  # Pass the parsed list of JSON item data
        )
        
        if result_file_obj:
            processed_count += 1
            logger.debug(f"Successfully processed and stored data for file_id: {file_id}")
        else:
            # Error is logged within add_or_update_file
            logger.error(f"Failed to process/store data for file_id: {file_id}")
            # Consider adding to a list of failed IDs if needed for reporting
    
    logger.info(f"Successfully processed {processed_count} out of {total_ids} file IDs.")
    return processed_count

def main() -> None:
    """
    Main execution function:
    1. Initializes the database (creates tables if needed).
    2. Extracts file IDs from the configured CSV.
    3. Processes the extracted file IDs (find files, extract item data, update DB).
    4. Splits the PDF for the processed file IDs.
    """
    logger.info("Starting file processing script...")
    
    try:
        # 1. Initialize database (ensure tables exist)
        init_database()
        
        # 2. Extract file IDs from CSV
        file_ids = extract_file_ids_from_csv(Config.MATCH_RESULTS_CSV)
        
        if not file_ids:
            logger.warning("No file IDs extracted from CSV. Exiting.")
            return
        
        # 3. Process file IDs (find files, extract item data, update DB)
        processed_count = process_file_ids(file_ids)
        
        if processed_count == 0:
            logger.warning("No files were successfully processed into the database. Skipping PDF splitting.")
            return
            
        # 4. Split PDFs for the processed file IDs
        logger.info(f"Starting PDF splitting for {len(file_ids)} file IDs.")
        split_success_count = 0
        split_failure_count = 0
        # Iterate through the *original* list of file_ids extracted from CSV.
        # Assumes process_file_ids logged errors for failures but didn't prevent this step.
        # Alternatively, query the DB for successfully processed file IDs.
        for file_id in file_ids: 
            # --- Add check to skip if already processed and split --- 
            file_in_db = get_file_by_id(file_id)
            split_output_dir = Path(Config.SPLIT_PDF_DIR) / file_id
            if file_in_db and split_output_dir.exists():
                logger.info(f"Skipping PDF splitting for {file_id}: Already processed and output directory exists.")
                # Increment success count here if skipping implies success for this stage
                # split_success_count += 1 
                continue # Move to the next file_id
            # --- End check --- 

            # Check if the file exists in DB before attempting split (optional but safer)
            file_obj = get_file_by_id(file_id) 
            if not file_obj: 
                logger.warning(f"Skipping split for {file_id}: Not found in database (likely processing failed).")
                split_failure_count += 1
                continue
            
            # Call the imported split_pdf_by_items function
            success = split_pdf_by_items(file_id) 
            if success:
                split_success_count += 1
            else:
                # Error is logged within split_pdf_by_items
                split_failure_count += 1
                
        logger.info(f"PDF splitting complete. Success: {split_success_count}, Failures: {split_failure_count}")
        
    except Exception as e:
        # Catch any broad errors during initialization or processing
        logger.critical(f"Critical error during main execution: {e}", exc_info=True)
        # Depending on deployment, sys.exit(1) might be appropriate here
        
    logger.info("File processing script finished.")

# Standard Python entry point check
if __name__ == "__main__":
    # Basic logging setup if run directly (useful for testing)
    # In a larger app, logging might be configured elsewhere
    logging.basicConfig(level=logging.DEBUG, 
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    main() 