"""
PDF Splitting module using data from the database.
"""

import os
import logging
import shutil
from pathlib import Path
from typing import Sequence

# PDF processing and file system operations
import fitz # PyMuPDF

from config import Config
from database import get_items_for_file, check_if_output_file_exists # Import necessary functions
from models import JsonItem # Import the model for type hinting

logger = logging.getLogger(__name__)

def split_pdf_by_items(file_id: str) -> bool:
    """
    Splits a PDF document based on page ranges defined in JsonItem records 
    associated with the given file_id.

    Creates an output directory named after the file_id within Config.SPLIT_PDF_DIR.
    Saves an 'intro.pdf' and '{file_id}_ITEM_{item_number}.pdf' for each item.

    Args:
        file_id: The unique file identifier (string) for which to split the PDF.

    Returns:
        bool: True if splitting was successful, False otherwise.
    """
    logger.info(f"Starting PDF splitting process for file_id: {file_id}")

    # 1. Get item data from database, ordered by item_number
    items: Sequence[JsonItem] = get_items_for_file(file_id)
    if not items:
        logger.error(f"Cannot split PDF for {file_id}: No associated item data found in the database.")
        return False

    # 2. Get source PDF path and check existence
    # Assume all items for a file_id reference the same source PDF
    # Find the first item that actually has a pdf_file_path
    source_pdf_path_str: str | None = None
    for item in items:
        if item.pdf_file_path:
            source_pdf_path_str = item.pdf_file_path
            break # Found the path, stop looking

    if not source_pdf_path_str:
        logger.error(f"Cannot split PDF for {file_id}: pdf_file_path is missing in all associated database item records.")
        return False
        
    source_pdf_path = Path(source_pdf_path_str)
    if not check_if_output_file_exists(str(source_pdf_path)):
        logger.error(f"Cannot split PDF for {file_id}: Source PDF not found at {source_pdf_path}")
        return False
        
    # 3. Prepare output directory
    output_dir = Path(Config.SPLIT_PDF_DIR) / file_id
    try:
        # Use shutil.rmtree to remove existing directory if it exists, then recreate
        if output_dir.exists():
            shutil.rmtree(output_dir)
            logger.debug(f"Removed existing output directory: {output_dir}")
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured output directory exists: {output_dir}")
    except OSError as e:
        logger.error(f"Error creating output directory {output_dir}: {e}", exc_info=True)
        return False

    # 4. Open source PDF and perform splitting
    source_doc = None # Initialize to None
    try:
        source_doc = fitz.open(str(source_pdf_path))
        total_pages = len(source_doc)
        logger.info(f"Opened source PDF: {source_pdf_path} ({total_pages} pages)")

        # 5. Extract Intro Section
        # Intro is pages before the start_page of the *first* item (which is items[0] due to ordering)
        first_item = items[0]
        intro_end_page_idx = -1 # Default: no intro pages if first item starts on page 1 or has no start_page
        
        # Ensure start_page is not None and greater than 1
        if first_item.start_page is not None and first_item.start_page > 1:
            intro_end_page_idx = first_item.start_page - 2 # 0-based index of the page *before* the first item starts
            
            # Sanity check: intro_end_page_idx must be within the doc bounds
            if intro_end_page_idx >= total_pages:
                 logger.warning(f"Calculated intro end page index ({intro_end_page_idx}) is out of bounds for PDF with {total_pages} pages. Skipping intro.")
                 intro_end_page_idx = -1 # Reset to skip intro extraction
                 
        if intro_end_page_idx >= 0:
            # Save as intro.pdf as originally requested, not tied to file_id yet
            intro_pdf_path = output_dir / "intro.pdf" 
            intro_doc = None # Initialize
            try:
                intro_doc = fitz.open() # Create empty PDF
                intro_doc.insert_pdf(source_doc, from_page=0, to_page=intro_end_page_idx)
                intro_doc.save(str(intro_pdf_path))
                logger.info(f"Saved intro section (pages 1-{intro_end_page_idx + 1}) to: {intro_pdf_path}") # Log 1-based pages
            except Exception as intro_err:
                 logger.error(f"Error saving intro PDF to {intro_pdf_path}: {intro_err}", exc_info=True)
                 # Continue to process items even if intro fails
            finally:
                 if intro_doc:
                     intro_doc.close()
        else:
            logger.info(f"No intro pages to save for {file_id} (first item starts on page 1, start_page is missing, or invalid).")

        # 6. Extract Item Sections
        for item in items:
            if item.item_number is None or item.start_page is None or item.end_page is None:
                logger.warning(f"Skipping item for {file_id} due to missing data (item_number/start_page/end_page): Item ID {item.id}")
                continue
            
            # Convert 1-based DB pages to 0-based fitz indices
            start_idx = item.start_page - 1
            end_idx = item.end_page - 1
            
            # Basic validation of page numbers against total document pages
            if not (0 <= start_idx < total_pages and 0 <= end_idx < total_pages and start_idx <= end_idx):
                 logger.warning(f"Skipping item {item.item_number} for {file_id}: Invalid page range ({item.start_page}-{item.end_page}) for PDF with {total_pages} pages. Calculated indices: ({start_idx}-{end_idx}). Item ID: {item.id}")
                 continue
                 
            # Use the requested output filename format
            item_pdf_filename = f"{file_id}_ITEM_{item.item_number}.pdf"
            item_pdf_path = output_dir / item_pdf_filename
            item_doc = None # Initialize
            try:
                item_doc = fitz.open()
                item_doc.insert_pdf(source_doc, from_page=start_idx, to_page=end_idx)
                item_doc.save(str(item_pdf_path))
                item_doc.close()
                item_doc = None # Set to None after successful close
                logger.info(f"Saved section for Item {item.item_number} (pages {item.start_page}-{item.end_page}) to: {item_pdf_path}")
            except Exception as item_err:
                 logger.error(f"Error saving item PDF {item_pdf_path} for item {item.item_number} (ID: {item.id}): {item_err}", exc_info=True)
                 # Continue to next item even if one fails
            finally:
                 # This check is now safe: if try succeeded, item_doc is None.
                 # If try failed before close(), item_doc might still be open.
                 if item_doc: 
                      item_doc.close()

        logger.info(f"Finished splitting PDF for file_id: {file_id}")
        return True

    except Exception as e:
        # Catch PyMuPDF errors or other issues during splitting
        logger.error(f"Error during PDF splitting for {file_id}: {e}", exc_info=True)
        return False
    finally:
        # 7. Ensure source document is closed if it was opened
        if source_doc and not source_doc.is_closed:
             try:
                 source_doc.close()
                 logger.debug(f"Closed source PDF for {file_id}.")
             except Exception as close_err:
                 logger.error(f"Error closing source PDF for {file_id} after processing/failure: {close_err}", exc_info=True)

# Example of how to potentially call this (e.g., from main script or another function)
# if __name__ == '__main__':
#     logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#     
#     # --- Database Setup (Required if running standalone) ---
#     from database import init_database
#     try:
#         init_database() # Ensure DB and tables exist
#     except Exception as db_err:
#         logger.critical(f"Failed to initialize database: {db_err}", exc_info=True)
#         exit(1) # Cant proceed without DB
#     # --- End Database Setup ---
#         
#     test_file_id = "some_file_id_from_db" # Replace with a valid file_id that exists in your DB
#     if not test_file_id or test_file_id == "some_file_id_from_db":
#          logger.warning("Please replace 'some_file_id_from_db' with a real file_id for testing.")
#     else:
#          success = split_pdf_by_items(test_file_id)
#          if success:
#              logger.info(f"Standalone test: PDF splitting for {test_file_id} completed successfully.")
#          else:
#              logger.error(f"Standalone test: PDF splitting for {test_file_id} failed.") 