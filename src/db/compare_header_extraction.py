import json
import os
import re
import sqlite3
import logging
from pathlib import Path
from datetime import datetime

# --- Configuration ---
FOLDER1_PATH = Path(r"C:\Projects\File_Util_App\data\processed_outputs")
FOLDER2_PATH = Path(r"C:\Projects\File_Util_App\output\header_output")
DATABASE_PATH = Path("./header_comparison_v3.db") # Use a new DB name
FILE1_SUFFIX = "_analysis_result.json"
FILE2_SUFFIX = "_origin_huridocs_analysis_extracted_headers.json"

# Regex to extract the UUID part of the filename
UUID_REGEX = re.compile(r"([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})")

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(asctime)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
# logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(asctime)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S') # Use for detailed extraction logs

# --- Database Functions ---

def create_connection(db_file):
    """Create a database connection."""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        conn.execute("PRAGMA foreign_keys = ON;")
        logging.info(f"Connected to SQLite database: {db_file}")
        return conn
    except sqlite3.Error as e:
        logging.error(f"Error connecting to database {db_file}: {e}")
    return conn

def create_schema(conn):
    """Create database tables based on the comprehensive schema."""
    cursor = conn.cursor()
    try:
        # Documents Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            uuid TEXT PRIMARY KEY,
            file1_path TEXT,
            file2_path TEXT,
            processed_timestamp DATETIME,
            franchise_name TEXT,
            issuance_date TEXT,
            franchise_address TEXT,
            phone_number TEXT,
            email TEXT,
            website TEXT,
            exhibit_for_franchisee_info_letter TEXT,
            original_subfolder_name TEXT,
            original_json_path TEXT,
            original_pdf_path TEXT,
            processed_json_path TEXT
        );
        """)

        # Analysis FDD Sections Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS analysis_fdd_sections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_uuid TEXT NOT NULL,
            item_number INTEGER NOT NULL,
            header_text TEXT,
            original_start_page INTEGER,
            original_end_page INTEGER,
            adjusted_start_page INTEGER,
            adjusted_end_page INTEGER,
            FOREIGN KEY (doc_uuid) REFERENCES documents (uuid) ON DELETE CASCADE,
            UNIQUE(doc_uuid, item_number)
        );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_analysis_sections_uuid ON analysis_fdd_sections(doc_uuid);")

        # Analysis Exhibits Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS analysis_exhibits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_uuid TEXT NOT NULL,
            exhibit_letter TEXT NOT NULL,
            title TEXT,
            original_start_page INTEGER,
            original_end_page INTEGER,
            adjusted_start_page INTEGER,
            adjusted_end_page INTEGER,
            FOREIGN KEY (doc_uuid) REFERENCES documents (uuid) ON DELETE CASCADE,
            UNIQUE(doc_uuid, exhibit_letter)
        );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_analysis_exhibits_uuid ON analysis_exhibits(doc_uuid);")

        # Origin Headers Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS origin_headers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_uuid TEXT NOT NULL,
            item_number INTEGER NOT NULL,
            text TEXT,
            match_score_full REAL,
            match_score_label REAL,
            match_score_keywords REAL,
            match_score_final REAL,
            page_number INTEGER,
            node_index INTEGER,
            start_node_index INTEGER,
            end_node_index INTEGER,
            start_page INTEGER,
            end_page INTEGER,
            alignment_score REAL,
            pdf_file_path TEXT,
            FOREIGN KEY (doc_uuid) REFERENCES documents (uuid) ON DELETE CASCADE,
            UNIQUE(doc_uuid, item_number)
        );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_origin_headers_uuid ON origin_headers(doc_uuid);")

        # Comparison Results Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS comparison_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_uuid TEXT NOT NULL,
            item_number INTEGER NOT NULL,
            analysis_adjusted_start_page INTEGER,
            origin_start_page INTEGER,
            status TEXT NOT NULL,
            needs_review BOOLEAN NOT NULL,
            FOREIGN KEY (doc_uuid) REFERENCES documents (uuid) ON DELETE CASCADE,
            UNIQUE(doc_uuid, item_number)
        );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_comparison_uuid ON comparison_results(doc_uuid);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_comparison_status ON comparison_results(status);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_comparison_needs_review ON comparison_results(needs_review);")

        conn.commit()
        logging.info("Database schema verified/created successfully.")
    except sqlite3.Error as e:
        conn.rollback()
        logging.error(f"Error creating database schema: {e}")
        raise # Reraise after rollback

# --- Helper Functions ---

def extract_uuid_from_filename(filename):
    """Extracts the UUID from a filename string."""
    match = UUID_REGEX.search(str(filename)) # Ensure filename is string
    if match:
        return match.group(1)
    return None

def load_json_safe(file_path):
    """Safely loads JSON data from a file."""
    if not file_path.exists():
        logging.error(f"File not found: {file_path}")
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError:
        logging.error(f"Invalid JSON format in file: {file_path}")
        return None
    except Exception as e:
        logging.error(f"Error reading file {file_path}: {e}")
        return None

def safe_int(value):
    """Safely convert value to int, return None on failure."""
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None

def safe_float(value):
    """Safely convert value to float, return None on failure."""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

# --- Data Extraction Functions ---

def extract_file1_data(data, file_path):
    """Extracts all relevant data structures from File 1 JSON."""
    if not isinstance(data, dict):
        logging.warning(f"File 1 data is not a dictionary in {file_path.name}.")
        return None, [], [] # metadata, sections, exhibits

    # 1. Document Metadata
    metadata = {
        "franchise_name": data.get("franchise_name"),
        "issuance_date": data.get("issuance_date"),
        "franchise_address": data.get("franchise_address"),
        "phone_number": data.get("phone_number"),
        "email": data.get("email"),
        "website": data.get("website"),
        "exhibit_for_franchisee_info_letter": data.get("exhibit_for_franchisee_information"),
        "original_subfolder_name": data.get("original_subfolder_name"),
        "original_json_path": data.get("original_json_path"),
        "original_pdf_path": data.get("original_pdf_path"),
        "processed_json_path": data.get("processed_json_path"),
    }

    # 2. FDD Sections
    sections_data = []
    fdd_sections = data.get("fdd_sections")
    if isinstance(fdd_sections, list):
        for item in fdd_sections:
            if not isinstance(item, dict): continue
            orig_start = safe_int(item.get("start_page"))
            orig_end = safe_int(item.get("end_page"))
            adj_start = orig_start + 1 if orig_start is not None else None
            adj_end = orig_end + 1 if orig_end is not None else None

            sections_data.append({
                "item_number": safe_int(item.get("item_number")),
                "header_text": item.get("header"),
                "original_start_page": orig_start,
                "original_end_page": orig_end,
                "adjusted_start_page": adj_start,
                "adjusted_end_page": adj_end,
            })
            logging.debug(f"Extracted Section: Item {item.get('item_number')}, OrigStart {orig_start}, AdjStart {adj_start}")
    else:
        logging.warning(f"'fdd_sections' missing or not a list in {file_path.name}")


    # 3. Exhibits
    exhibits_data = []
    exhibits = data.get("exhibits")
    if isinstance(exhibits, list):
         for item in exhibits:
            if not isinstance(item, dict): continue
            orig_start = safe_int(item.get("start_page"))
            orig_end = safe_int(item.get("end_page"))
            adj_start = orig_start + 1 if orig_start is not None else None
            adj_end = orig_end + 1 if orig_end is not None else None

            exhibits_data.append({
                "exhibit_letter": item.get("exhibit_letter"),
                "title": item.get("title"),
                "original_start_page": orig_start,
                "original_end_page": orig_end,
                "adjusted_start_page": adj_start,
                "adjusted_end_page": adj_end,
            })
            logging.debug(f"Extracted Exhibit: Letter {item.get('exhibit_letter')}, OrigStart {orig_start}, AdjStart {adj_start}")
    else:
        logging.warning(f"'exhibits' missing or not a list in {file_path.name}")

    return metadata, sections_data, exhibits_data


def extract_file2_data(data, file_path):
    """Extracts all relevant data structures from File 2 JSON."""
    origin_headers_data = []
    if not isinstance(data, list):
        logging.warning(f"File 2 data is not a list in {file_path.name}.")
        return origin_headers_data

    for item in data:
        if not isinstance(item, dict): continue
        scores = item.get("match_scores", {}) # Handle missing scores dict

        origin_headers_data.append({
            "item_number": safe_int(item.get("item_number")),
            "text": item.get("text"),
            "match_score_full": safe_float(scores.get("full")),
            "match_score_label": safe_float(scores.get("label")),
            "match_score_keywords": safe_float(scores.get("keywords")),
            "match_score_final": safe_float(scores.get("final")),
            "page_number": safe_int(item.get("page_number")),
            "node_index": safe_int(item.get("node_index")),
            "start_node_index": safe_int(item.get("start_node_index")),
            "end_node_index": safe_int(item.get("end_node_index")),
            "start_page": safe_int(item.get("start_page")),
            "end_page": safe_int(item.get("end_page")),
            "alignment_score": safe_float(item.get("alignment_score")),
            "pdf_file_path": item.get("pdf_file_path"),
        })
        logging.debug(f"Extracted Origin Header: Item {item.get('item_number')}, StartPage {item.get('start_page')}")

    return origin_headers_data

# --- Database Insertion Functions ---

def insert_document_data(conn, uuid, file1_path, file2_path, metadata):
    """Insert or update a document record with all metadata."""
    # Use INSERT OR REPLACE to handle updates if UUID exists
    sql = """
    INSERT OR REPLACE INTO documents (
        uuid, file1_path, file2_path, processed_timestamp, franchise_name,
        issuance_date, franchise_address, phone_number, email, website,
        exhibit_for_franchisee_info_letter, original_subfolder_name,
        original_json_path, original_pdf_path, processed_json_path
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (
            uuid, str(file1_path), str(file2_path), datetime.now(),
            metadata.get("franchise_name"), metadata.get("issuance_date"),
            metadata.get("franchise_address"), metadata.get("phone_number"),
            metadata.get("email"), metadata.get("website"),
            metadata.get("exhibit_for_franchisee_info_letter"),
            metadata.get("original_subfolder_name"), metadata.get("original_json_path"),
            metadata.get("original_pdf_path"), metadata.get("processed_json_path")
        ))
        return True
    except sqlite3.Error as e:
        logging.error(f"Error inserting/replacing document {uuid}: {e}")
        return False

def insert_analysis_fdd_sections_data(conn, doc_uuid, sections_data):
    """Insert analysis FDD sections data."""
    sql = """
    INSERT OR REPLACE INTO analysis_fdd_sections (
        doc_uuid, item_number, header_text, original_start_page, original_end_page,
        adjusted_start_page, adjusted_end_page
    ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    data_to_insert = [
        (doc_uuid, s.get("item_number"), s.get("header_text"),
         s.get("original_start_page"), s.get("original_end_page"),
         s.get("adjusted_start_page"), s.get("adjusted_end_page"))
        for s in sections_data if s.get("item_number") is not None # Ensure item_number exists
    ]
    if not data_to_insert: return True
    try:
        cursor = conn.cursor()
        cursor.executemany(sql, data_to_insert)
        return True
    except sqlite3.Error as e:
        logging.error(f"Error inserting analysis sections for {doc_uuid}: {e}")
        return False

def insert_analysis_exhibits_data(conn, doc_uuid, exhibits_data):
    """Insert analysis exhibits data."""
    sql = """
    INSERT OR REPLACE INTO analysis_exhibits (
        doc_uuid, exhibit_letter, title, original_start_page, original_end_page,
        adjusted_start_page, adjusted_end_page
    ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    data_to_insert = [
        (doc_uuid, e.get("exhibit_letter"), e.get("title"),
         e.get("original_start_page"), e.get("original_end_page"),
         e.get("adjusted_start_page"), e.get("adjusted_end_page"))
        for e in exhibits_data if e.get("exhibit_letter") is not None # Ensure exhibit_letter exists
    ]
    if not data_to_insert: return True
    try:
        cursor = conn.cursor()
        cursor.executemany(sql, data_to_insert)
        return True
    except sqlite3.Error as e:
        logging.error(f"Error inserting analysis exhibits for {doc_uuid}: {e}")
        return False

def insert_origin_headers_data(conn, doc_uuid, origin_headers_data):
    """Insert origin headers data."""
    sql = """
    INSERT OR REPLACE INTO origin_headers (
        doc_uuid, item_number, text, match_score_full, match_score_label,
        match_score_keywords, match_score_final, page_number, node_index,
        start_node_index, end_node_index, start_page, end_page,
        alignment_score, pdf_file_path
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    data_to_insert = [
        (doc_uuid, h.get("item_number"), h.get("text"), h.get("match_score_full"),
         h.get("match_score_label"), h.get("match_score_keywords"), h.get("match_score_final"),
         h.get("page_number"), h.get("node_index"), h.get("start_node_index"),
         h.get("end_node_index"), h.get("start_page"), h.get("end_page"),
         h.get("alignment_score"), h.get("pdf_file_path"))
        for h in origin_headers_data if h.get("item_number") is not None # Ensure item_number exists
    ]
    if not data_to_insert: return True
    try:
        cursor = conn.cursor()
        cursor.executemany(sql, data_to_insert)
        return True
    except sqlite3.Error as e:
        logging.error(f"Error inserting origin headers for {doc_uuid}: {e}")
        return False

# --- Data Population Orchestration ---

def populate_database(conn):
    """Find file pairs, extract data, and populate all database tables."""
    logging.info("--- Starting Comprehensive Database Population ---")
    # ... (folder existence checks remain the same) ...
    if not FOLDER1_PATH.is_dir() or not FOLDER2_PATH.is_dir():
         logging.error("Input folder(s) not found.")
         return []

    processed_uuids = []
    skipped_count = 0

    for file1_path in FOLDER1_PATH.glob(f"*{FILE1_SUFFIX}"):
        file_id = extract_uuid_from_filename(file1_path.name)
        if not file_id:
            logging.warning(f"Could not extract ID from file: {file1_path.name}. Skipping.")
            skipped_count += 1
            continue

        file2_name = f"{file_id}{FILE2_SUFFIX}"
        file2_path = FOLDER2_PATH / file2_name
        if not file2_path.exists():
            logging.warning(f"Corresponding file for ID {file_id} not found: {file2_path}")
            skipped_count += 1
            continue

        logging.info(f"Processing pair for UUID: {file_id}")
        data1 = load_json_safe(file1_path)
        data2 = load_json_safe(file2_path)

        if data1 is None or data2 is None:
            logging.error(f"Skipping pair {file_id} due to JSON loading errors.")
            skipped_count += 1
            continue

        # --- Extract all data ---
        metadata, sections_data, exhibits_data = extract_file1_data(data1, file1_path)
        origin_headers_data = extract_file2_data(data2, file2_path)

        if metadata is None: # Indicates fundamental issue with File 1 structure
             logging.error(f"Could not extract metadata from {file1_path.name}. Skipping pair {file_id}.")
             skipped_count += 1
             continue

        # --- Database Transaction ---
        try:
            conn.execute("BEGIN TRANSACTION;") # Start transaction

            # Clear old data for this UUID first (optional, but good for reruns)
            cursor = conn.cursor()
            logging.debug(f"Clearing old data for UUID: {file_id}")
            cursor.execute("DELETE FROM analysis_fdd_sections WHERE doc_uuid = ?", (file_id,))
            cursor.execute("DELETE FROM analysis_exhibits WHERE doc_uuid = ?", (file_id,))
            cursor.execute("DELETE FROM origin_headers WHERE doc_uuid = ?", (file_id,))
            cursor.execute("DELETE FROM comparison_results WHERE doc_uuid = ?", (file_id,))
            # Don't delete from documents, use INSERT OR REPLACE

            # Insert new data
            success_doc = insert_document_data(conn, file_id, file1_path, file2_path, metadata)
            success_sections = insert_analysis_fdd_sections_data(conn, file_id, sections_data)
            success_exhibits = insert_analysis_exhibits_data(conn, file_id, exhibits_data)
            success_origin = insert_origin_headers_data(conn, file_id, origin_headers_data)

            if success_doc and success_sections and success_exhibits and success_origin:
                conn.commit() # Commit all insertions for this UUID
                processed_uuids.append(file_id)
                logging.info(f"Successfully stored all data for UUID: {file_id}")
            else:
                conn.rollback() # Rollback if any insertion failed
                logging.error(f"Failed to insert one or more data parts for UUID: {file_id}. Rolling back.")
                skipped_count += 1

        except sqlite3.Error as e:
            conn.rollback()
            logging.error(f"Database transaction error for UUID {file_id}: {e}. Rolling back.")
            skipped_count += 1
        except Exception as e: # Catch potential non-DB errors during processing
             conn.rollback()
             logging.error(f"Unexpected error during processing/DB insertion for UUID {file_id}: {e}. Rolling back.")
             skipped_count += 1


    logging.info(f"--- Database Population Finished ---")
    logging.info(f"Successfully processed and stored data for {len(processed_uuids)} UUIDs.")
    logging.info(f"Skipped {skipped_count} file pairs during data population.")
    return processed_uuids


# --- Comparison Logic (Populating comparison_results table) ---

def perform_and_store_comparison(conn, uuid):
    """Compares adjusted analysis start pages with origin start pages and stores results."""
    logging.info(f"\n--- Comparing and Storing Results for UUID: {uuid} ---")
    cursor = conn.cursor()
    comparison_data_to_insert = []
    overall_match = True

    try:
        # Fetch pages needed for comparison
        cursor.execute("SELECT item_number, adjusted_start_page FROM analysis_fdd_sections WHERE doc_uuid = ?", (uuid,))
        analysis_pages = {row[0]: row[1] for row in cursor.fetchall()}

        cursor.execute("SELECT item_number, start_page FROM origin_headers WHERE doc_uuid = ?", (uuid,))
        origin_pages = {row[0]: row[1] for row in cursor.fetchall()}

    except sqlite3.Error as e:
        logging.error(f"Error fetching comparison data from database for UUID {uuid}: {e}")
        return False

    if not analysis_pages and not origin_pages:
        logging.warning(f"No section/header data found in database for UUID: {uuid} to compare.")
        # Ensure no stale comparison results exist
        try:
            cursor.execute("DELETE FROM comparison_results WHERE doc_uuid = ?", (uuid,))
            conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Error clearing stale comparison results for UUID {uuid}: {e}")
            conn.rollback()
        return True # No data, no mismatch

    all_item_numbers = set(analysis_pages.keys()) | set(origin_pages.keys())

    for item_num in sorted(list(all_item_numbers)):
        page1_adj = analysis_pages.get(item_num) # Adjusted page from analysis
        page2_orig = origin_pages.get(item_num) # Original page from origin
        status = ''
        needs_review = False

        # Handle cases where pages might be None (if extraction failed for an item)
        if page1_adj is not None and page2_orig is not None:
            if page1_adj == page2_orig:
                status = 'MATCH'
                needs_review = False
                logging.info(f"  Item {item_num}: MATCH (Page: {page1_adj})")
            else:
                status = 'MISMATCH'
                needs_review = True
                overall_match = False
                logging.warning(f"  Item {item_num}: MISMATCH (Analysis Adj. Page: {page1_adj}, Origin Page: {page2_orig})")
        elif page1_adj is not None: # Found in analysis but not origin
            status = 'MISSING_IN_ORIGIN'
            needs_review = True
            overall_match = False
            logging.warning(f"  Item {item_num}: Found in Analysis (Adj. Page: {page1_adj}), MISSING in Origin DB")
        elif page2_orig is not None: # Found in origin but not analysis
            status = 'MISSING_IN_ANALYSIS'
            needs_review = True
            overall_match = False
            logging.warning(f"  Item {item_num}: MISSING in Analysis DB, Found in Origin (Page: {page2_orig})")
        else: # Missing in both (shouldn't happen if all_item_numbers is derived correctly)
             status = 'MISSING_BOTH'
             needs_review = True
             overall_match = False
             logging.error(f"  Item {item_num}: Data missing in both analysis and origin tables (Error in logic?)")


        comparison_data_to_insert.append((uuid, item_num, page1_adj, page2_orig, status, needs_review))

    # --- Store results in the database ---
    try:
        # Use a transaction for delete + insert
        conn.execute("BEGIN TRANSACTION;")
        # Clear previous results for this UUID
        cursor.execute("DELETE FROM comparison_results WHERE doc_uuid = ?", (uuid,))

        # Insert new results
        sql_insert_comparison = '''
            INSERT INTO comparison_results(doc_uuid, item_number, analysis_adjusted_start_page, origin_start_page, status, needs_review)
            VALUES(?,?,?,?,?,?)
        '''
        if comparison_data_to_insert:
            cursor.executemany(sql_insert_comparison, comparison_data_to_insert)
            logging.info(f"Stored {len(comparison_data_to_insert)} comparison results for UUID {uuid}.")

        conn.commit() # Commit the delete and insert operations

    except sqlite3.Error as e:
        logging.error(f"Database error storing comparison results for UUID {uuid}: {e}. Rolling back.")
        conn.rollback()
        return False # Indicate comparison storage failure

    if overall_match:
        logging.info(f">>> Overall Result for UUID {uuid}: All compared items matched.")
    else:
        logging.warning(f">>> Overall Result for UUID {uuid}: Mismatches or missing items found (Needs Review).")

    return overall_match


# --- Main Execution ---

def main():
    """Main function: setup DB, populate all tables, run comparisons."""
    conn = create_connection(DATABASE_PATH)
    if conn is None: return

    try:
        create_schema(conn)

        # Phase 1: Populate all data tables
        processed_uuids = populate_database(conn)

        # Phase 2: Perform comparison and store results
        logging.info("\n--- Starting Comparison and Storing Results ---")
        if not processed_uuids:
            logging.warning("No UUIDs were successfully populated. No comparison to run.")
            return # Exit if population failed

        successful_matches_count = 0
        needs_review_count = 0
        comparison_errors = 0

        for uuid in processed_uuids:
            try:
                match_result = perform_and_store_comparison(conn, uuid)
                if match_result:
                    successful_matches_count += 1
                else:
                    needs_review_count += 1
            except Exception as e:
                logging.error(f"Unexpected error during comparison/storage for UUID {uuid}: {e}")
                comparison_errors += 1

        logging.info("\n--- Final Summary ---")
        logging.info(f"Total UUIDs processed for comparison: {len(processed_uuids)}")
        logging.info(f"UUIDs with perfect matches on compared items: {successful_matches_count}")
        logging.info(f"UUIDs requiring review (mismatches/missing): {needs_review_count}")
        if comparison_errors > 0:
            logging.error(f"UUIDs skipped during comparison/storage due to errors: {comparison_errors}")

        logging.info(f"\nAll extracted data and comparison results stored in {DATABASE_PATH}")
        logging.info("Query 'comparison_results' table where 'needs_review' is 1 to find specific items needing attention.")

    finally:
        if conn:
            conn.close()
            logging.info("Database connection closed.")

if __name__ == "__main__":
    main()