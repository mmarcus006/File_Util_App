import sqlite3
import os
import sys
import fitz  # PyMuPDF
from typing import Optional

# --- Configuration ---
# Path to the integrated database file
DATABASE_PATH = r"C:\Projects\File_Util_App\src\data\development.db"
# Base directory where the split PDFs will be saved
OUTPUT_BASE_DIR = r"C:\Projects\File_Util_App\data\split_fdds"

# --- Helper Functions ---

def connect_db(db_path: str) -> Optional[sqlite3.Connection]:
    """Connects to the SQLite database and enables foreign keys."""
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row  # Access columns by name
        print(f"Successfully connected to database: {db_path}")
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database {db_path}: {e}", file=sys.stderr)
        return None

def sanitize_filename(name: str) -> str:
    """Removes potentially problematic characters for filenames."""
    # Remove leading/trailing whitespace
    name = str(name).strip()
    # Replace common problematic characters with underscore
    name = name.replace('/', '_').replace('\\', '_').replace(':', '_')
    name = name.replace('*', '_').replace('?', '_').replace('"', '_')
    name = name.replace('<', '_').replace('>', '_').replace('|', '_')
    # Replace multiple underscores with one
    name = '_'.join(filter(None, name.split('_')))
    return name if name else "Unnamed"  # Ensure there's always a name

def extract_pages_pymupdf(pdf_doc: fitz.Document, start_page: int, end_page: int, output_pdf_path: str) -> bool:
    """
    Extracts a range of pages from a PyMuPDF Document and saves to a new PDF.
    Handles 1-based page numbers from the database.
    """
    num_pages_in_pdf = len(pdf_doc)
    
    # Validate page numbers (adjusting for 0-based index)
    start_index = start_page - 1  # Convert to 0-based index
    end_index = end_page - 1  # Convert to 0-based index
    
    if start_index < 0 or start_index >= num_pages_in_pdf:
        print(f"    Warning: Start page {start_page} is out of bounds for PDF (1-{num_pages_in_pdf}). "
              f"Skipping extraction for {os.path.basename(output_pdf_path)}.", file=sys.stderr)
        return False
    
    if end_index < 0 or end_index >= num_pages_in_pdf:
        print(f"    Warning: End page {end_page} is out of bounds for PDF (1-{num_pages_in_pdf}). "
              f"Adjusting end page for {os.path.basename(output_pdf_path)}.", file=sys.stderr)
        end_index = num_pages_in_pdf - 1  # Adjust to the last valid page index
    
    if start_index > end_index:
        print(f"    Warning: Start page {start_page} is greater than end page {end_page}. "
              f"Skipping extraction for {os.path.basename(output_pdf_path)}.", file=sys.stderr)
        return False
    
    try:
        # Create a new PDF document with the selected pages
        new_doc = fitz.open()  # Create empty PDF
        
        # Copy the pages from source to new document
        new_doc.insert_pdf(pdf_doc, from_page=start_index, to_page=end_index)
        
        # Save the new document
        new_doc.save(output_pdf_path)
        new_doc.close()
        
        return True
    except Exception as e:
        print(f"    Error extracting pages for {os.path.basename(output_pdf_path)}: {e}", file=sys.stderr)
        # Attempt to remove partially written file if error occurs
        if os.path.exists(output_pdf_path):
            try:
                os.remove(output_pdf_path)
            except OSError:
                pass
        return False

def create_split_pdf_table(conn: sqlite3.Connection) -> bool:
    """Create a table to track split PDF files if it doesn't exist."""
    try:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Split_PDF_Files (
            split_pdf_id INTEGER PRIMARY KEY AUTOINCREMENT,
            fdd_id INTEGER NOT NULL,
            franchise_id INTEGER NOT NULL,
            original_pdf_path TEXT NOT NULL,
            split_pdf_path TEXT NOT NULL,
            content_type TEXT NOT NULL,  -- 'Intro', 'Item', 'Exhibit'
            content_identifier TEXT,     -- Item number or Exhibit letter or 'Intro'
            start_page INTEGER,
            end_page INTEGER,
            FOREIGN KEY (fdd_id) REFERENCES FDD(fdd_id) ON DELETE CASCADE,
            FOREIGN KEY (franchise_id) REFERENCES Franchise(franchise_id) ON DELETE CASCADE,
            UNIQUE(fdd_id, content_type, content_identifier)
        )
        """)
        conn.commit()
        print("Split_PDF_Files table created or verified successfully.")
        return True
    except sqlite3.Error as e:
        print(f"Error creating Split_PDF_Files table: {e}", file=sys.stderr)
        return False

def record_split_pdf(conn: sqlite3.Connection, fdd_id: int, franchise_id: int, 
                    original_pdf_path: str, split_pdf_path: str, content_type: str, 
                    content_identifier: str, start_page: int, end_page: int) -> bool:
    """Record a split PDF file in the tracking table."""
    try:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT OR REPLACE INTO Split_PDF_Files 
        (fdd_id, franchise_id, original_pdf_path, split_pdf_path, content_type, 
         content_identifier, start_page, end_page)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (fdd_id, franchise_id, original_pdf_path, split_pdf_path, 
              content_type, content_identifier, start_page, end_page))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"    Error recording split PDF in database: {e}", file=sys.stderr)
        return False

# --- Main Processing Logic ---

def main():
    conn = connect_db(DATABASE_PATH)
    if not conn:
        return
    
    # Create the tracking table if it doesn't exist
    if not create_split_pdf_table(conn):
        conn.close()
        return
    
    cursor = conn.cursor()
    processed_fdd_count = 0
    extracted_file_count = 0
    error_count = 0
    missing_pdf_count = 0
    
    # Ensure base output directory exists
    os.makedirs(OUTPUT_BASE_DIR, exist_ok=True)
    print(f"Output directory: {OUTPUT_BASE_DIR}")
    
    try:
        # Fetch all FDDs that have an original PDF path
        cursor.execute("""
            SELECT fdd_id, franchise_id, original_pdf_path
            FROM FDD
            WHERE original_pdf_path IS NOT NULL AND original_pdf_path != ''
            ORDER BY franchise_id, fdd_id -- Process systematically
        """)
        fdds_to_process = cursor.fetchall()
        
        print(f"\nFound {len(fdds_to_process)} FDD records with PDF paths to process.")
        
        for fdd_row in fdds_to_process:
            fdd_id = fdd_row['fdd_id']
            franchise_id = fdd_row['franchise_id']
            original_pdf_path = fdd_row['original_pdf_path']
            processed_fdd_count += 1
            
            print(f"\nProcessing FDD ID: {fdd_id} (Franchise ID: {franchise_id})")
            print(f"  Source PDF: {original_pdf_path}")
            
            # --- Create Output Directories ---
            franchise_dir = os.path.join(OUTPUT_BASE_DIR, str(franchise_id))
            fdd_dir = os.path.join(franchise_dir, str(fdd_id))
            try:
                os.makedirs(fdd_dir, exist_ok=True)
            except OSError as e:
                print(f"  Error creating directory {fdd_dir}: {e}. Skipping FDD.", file=sys.stderr)
                error_count += 1
                continue
            
            # --- Check if PDF exists and open it ---
            if not os.path.exists(original_pdf_path):
                print(f"  Error: Source PDF not found at '{original_pdf_path}'. Skipping FDD.", file=sys.stderr)
                missing_pdf_count += 1
                error_count += 1
                continue
            
            try:
                # Open the PDF with PyMuPDF
                pdf_doc = fitz.open(original_pdf_path)
                
                # --- Find the first section page to extract intro pages ---
                cursor.execute("""
                    SELECT MIN(start_page) as first_section_page
                    FROM FDD_Layout_Section
                    WHERE fdd_id = ? AND start_page IS NOT NULL
                """, (fdd_id,))
                first_section_result = cursor.fetchone()
                first_section_page = first_section_result['first_section_page'] if first_section_result else None
                
                # --- Extract Intro Pages (before the first section) ---
                if first_section_page is not None and first_section_page > 1:
                    print("  Processing Intro Pages...")
                    intro_start_page = 1
                    intro_end_page = first_section_page - 1
                    output_filename = "Intro_Pages.pdf"
                    output_path = os.path.join(fdd_dir, output_filename)
                    
                    if extract_pages_pymupdf(pdf_doc, intro_start_page, intro_end_page, output_path):
                        extracted_file_count += 1
                        # Record in database
                        record_split_pdf(
                            conn, fdd_id, franchise_id, original_pdf_path, output_path,
                            'Intro', 'Intro', intro_start_page, intro_end_page
                        )
                    else:
                        error_count += 1
                
                # --- Process Sections ---
                print("  Processing Sections...")
                cursor.execute("""
                    SELECT identified_item_number, start_page, end_page
                    FROM FDD_Layout_Section
                    WHERE fdd_id = ? AND identified_item_number IS NOT NULL
                      AND start_page IS NOT NULL AND end_page IS NOT NULL
                    ORDER BY identified_item_number
                """, (fdd_id,))
                sections = cursor.fetchall()
                
                for section in sections:
                    item_num = section['identified_item_number']
                    start_page = section['start_page']
                    end_page = section['end_page']
                    output_filename = f"Item_{item_num}.pdf"
                    output_path = os.path.join(fdd_dir, output_filename)
                    
                    if extract_pages_pymupdf(pdf_doc, start_page, end_page, output_path):
                        extracted_file_count += 1
                        # Record in database
                        record_split_pdf(
                            conn, fdd_id, franchise_id, original_pdf_path, output_path,
                            'Item', item_num, start_page, end_page
                        )
                    else:
                        error_count += 1
                
                # --- Process Exhibits ---
                print("  Processing Exhibits...")
                cursor.execute("""
                    SELECT identified_exhibit_letter, start_page, end_page
                    FROM FDD_Layout_Exhibit
                    WHERE fdd_id = ? AND identified_exhibit_letter IS NOT NULL AND identified_exhibit_letter != ''
                      AND start_page IS NOT NULL AND end_page IS NOT NULL
                    ORDER BY identified_exhibit_letter -- Sort exhibits alphabetically
                """, (fdd_id,))
                exhibits = cursor.fetchall()
                
                for exhibit in exhibits:
                    exhibit_letter = exhibit['identified_exhibit_letter']
                    start_page = exhibit['start_page']
                    end_page = exhibit['end_page']
                    # Sanitize letter in case it contains odd characters, though unlikely
                    safe_letter = sanitize_filename(exhibit_letter)
                    output_filename = f"Exhibit_{safe_letter}.pdf"
                    output_path = os.path.join(fdd_dir, output_filename)
                    
                    if extract_pages_pymupdf(pdf_doc, start_page, end_page, output_path):
                        extracted_file_count += 1
                        # Record in database
                        record_split_pdf(
                            conn, fdd_id, franchise_id, original_pdf_path, output_path,
                            'Exhibit', exhibit_letter, start_page, end_page
                        )
                    else:
                        error_count += 1
                
                # Close the PDF document when done
                pdf_doc.close()
                
            except Exception as e:
                print(f"  Unexpected error processing FDD ID {fdd_id}: {e}", file=sys.stderr)
                error_count += 1
    
    except sqlite3.Error as db_err:
        print(f"Database error during FDD fetching: {db_err}", file=sys.stderr)
        error_count += 1
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        error_count += 1
    finally:
        if conn:
            conn.close()
            print("\nDatabase connection closed.")
    
    # --- Summary ---
    print("\n--- PDF Splitting Summary ---")
    print(f"Total FDD records processed: {processed_fdd_count}")
    print(f"Total individual PDF files created: {extracted_file_count}")
    print(f"FDDs skipped due to missing source PDF: {missing_pdf_count}")
    print(f"Errors encountered (DB/PDF/File IO): {error_count}")
    print("-----------------------------")

# --- Run the script ---
if __name__ == '__main__':
    main()