import os
import shutil
import re
from typing import List, Tuple, Optional, Dict
import json

# Need Session for type hinting in the refactored copy_approved_file
from sqlalchemy.orm import Session 

# To call db_handler functions, we need to import them.
# Assuming db_handler is in a sibling directory 'database'
from database import db_handler # Relative import for sibling package
from database.models import Item1Data, PdfPaths # For test setup

# Regex to extract UUID from filenames like <UUID>_item1.json or <UUID>.pdf
UUID_PATTERN = re.compile(r"^([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})")

def extract_uuid_from_filename(filename: str) -> Optional[str]:
    """Extracts UUID from the beginning of a filename."""
    match = UUID_PATTERN.match(filename)
    return match.group(1) if match else None

def check_output_file_exists(output_path: str) -> bool:
    """Checks if the given output file or directory already exists."""
    return os.path.exists(output_path)

def scan_input_directory(
    sections_input_dir: str, 
    source_pdfs_dir: str
) -> Tuple[List[Dict[str, str]], List[str]]:
    """
    Scans the sections input directory (specifically its 'item_1' subdirectory) for Item 1 JSON files
    and attempts to find corresponding PDF files in the source_pdfs_dir.
    This function discovers files to be potentially added to the database.

    Args:
        sections_input_dir (str): The root directory containing FDD sections (e.g., .../output/sections/).
                                   The function will look into sections_input_dir/item_1/.
        source_pdfs_dir (str): The directory where source PDF files are located.

    Returns:
        Tuple[List[Dict[str, str]], List[str]]:
            - A list of dictionaries, where each dictionary contains:
                {'uuid': str, 'json_path': str, 'pdf_path': Optional[str]}
            - A list of error messages encountered during scanning (e.g., PDF not found).
    """
    processed_files_info: List[Dict[str, str]] = []
    errors: List[str] = []
    
    item1_json_dir = os.path.join(sections_input_dir, "item_1")

    if not os.path.isdir(item1_json_dir):
        errors.append(f"Item 1 JSON directory not found: {item1_json_dir}")
        return processed_files_info, errors

    if not os.path.isdir(source_pdfs_dir):
        errors.append(f"Source PDFs directory not found: {source_pdfs_dir}")
        # Continue to process JSONs, but PDFs will be marked as not found

    for filename in os.listdir(item1_json_dir):
        if filename.endswith("_item1.json"):
            uuid = extract_uuid_from_filename(filename)
            if uuid:
                json_file_path = os.path.join(item1_json_dir, filename)
                pdf_file_name = f"{uuid}.pdf"
                pdf_file_path = os.path.join(source_pdfs_dir, pdf_file_name)
                
                file_info = {
                    "uuid": uuid,
                    "json_path": os.path.abspath(json_file_path)
                }
                
                if os.path.exists(pdf_file_path):
                    file_info["pdf_path"] = os.path.abspath(pdf_file_path)
                else:
                    file_info["pdf_path"] = None # Explicitly set to None if not found
                    errors.append(f"Warning: PDF file not found for UUID {uuid} at {pdf_file_path}")
                
                processed_files_info.append(file_info)
            else:
                errors.append(f"Could not extract UUID from JSON filename: {filename} in {item1_json_dir}")
                
    return processed_files_info, errors

def copy_approved_file(
    db_session: Session, 
    uuid: str, 
    approved_files_base_dir: str
) -> Tuple[Optional[str], Optional[str]]:
    """
    Retrieves the original Item 1 JSON file path from the database using the UUID
    and copies it to the designated 'approved_files/item_1' directory.

    Args:
        db_session (Session): The SQLAlchemy database session.
        uuid (str): The UUID of the record to approve and copy.
        approved_files_base_dir (str): The base directory for approved files (e.g., "approved_files").

    Returns:
        Tuple[Optional[str], Optional[str]]: 
            (destination_path, None) if successful,
            (None, error_message) if an error occurs.
    """
    original_json_path = db_handler.get_original_json_path(db_session, uuid)

    if not original_json_path:
        return None, f"Original JSON path not found in database for UUID: {uuid}"
    
    if not os.path.exists(original_json_path):
        return None, f"Source JSON file (from DB path {original_json_path}) not found on disk for UUID: {uuid}"

    filename = os.path.basename(original_json_path)
    target_item1_dir = os.path.join(approved_files_base_dir, "item_1")
    
    if not os.path.exists(target_item1_dir):
        try:
            os.makedirs(target_item1_dir, exist_ok=True)
        except OSError as e:
            return None, f"Could not create target directory {target_item1_dir}: {e}"
            
    destination_path = os.path.join(target_item1_dir, filename)

    if check_output_file_exists(destination_path):
        # print(f"Warning: Output file {destination_path} already exists. Overwriting.")
        pass # Allow overwrite as per previous logic, PRD doesn't specify alternative.

    try:
        shutil.copy2(original_json_path, destination_path)
        return os.path.abspath(destination_path), None
    except Exception as e:
        return None, f"Error copying file {original_json_path} to {destination_path}: {e}"

# Example Usage
if __name__ == '__main__':
    # --- Setup for file_handler tests ---
    test_base_dir = "./temp_file_handler_test"
    sections_dir = os.path.join(test_base_dir, "output", "sections")
    item1_json_s_dir = os.path.join(sections_dir, "item_1")
    pdfs_dir = os.path.join(test_base_dir, "processed_fdds")
    approved_dir = os.path.join(test_base_dir, "approved_files_fh_test") # Unique name for this test
    db_test_dir = os.path.join(test_base_dir, "database")
    db_test_file = os.path.join(db_test_dir, "fh_test.db")

    if os.path.exists(test_base_dir):
        shutil.rmtree(test_base_dir)

    os.makedirs(item1_json_s_dir, exist_ok=True)
    os.makedirs(pdfs_dir, exist_ok=True)
    os.makedirs(db_test_dir, exist_ok=True) 
    # approved_dir will be created by copy_approved_file if needed

    # --- Initialize a temporary DB for testing copy_approved_file --- 
    # This requires access to db_handler.init_db and get_db_session
    # We also need the Item1Data model to insert a test record.
    from ..database.db_handler import init_db, get_db_session, add_item1_data
    # from ..database.models import Item1Data # Already imported

    init_db(db_test_file) # Initialize test DB

    uuid1 = "11111111-1111-1111-1111-111111111111"
    uuid2 = "22222222-2222-2222-2222-222222222222"
    uuid3_no_pdf = "33333333-3333-3333-3333-333333333333"

    # Create sample JSON files that will be "found" by scan_input_directory
    # and whose paths will be added to the test DB for copy_approved_file test.
    source_json_for_uuid1_content = {"brand_name": "BrandForCopyTest"}
    source_json_for_uuid1_on_disk_path = os.path.abspath(os.path.join(item1_json_s_dir, f"{uuid1}_item1.json"))
    with open(source_json_for_uuid1_on_disk_path, 'w') as f:
         json.dump(source_json_for_uuid1_content, f) # Need to import json for this
    import json # Moved import here, only needed for test setup

    with open(os.path.join(item1_json_s_dir, f"{uuid2}_item1.json"), 'w') as f: json.dump({},f)
    with open(os.path.join(pdfs_dir, f"{uuid1}.pdf"), 'w') as f: f.write("dummy pdf content")
    with open(os.path.join(item1_json_s_dir, f"{uuid3_no_pdf}_item1.json"), 'w') as f: json.dump({},f)
    with open(os.path.join(item1_json_s_dir, f"no_uuid_item1.json"), 'w') as f: json.dump({},f)

    print("--- Testing scan_input_directory ---")
    file_infos, errors = scan_input_directory(sections_dir, pdfs_dir)
    print(f"Found {len(file_infos)} processable files.")
    for info in file_infos:
        print(f"  UUID: {info['uuid']}, JSON: {info['json_path']}, PDF: {info['pdf_path']}")
    print(f"Scan errors: {errors}")
    assert len(file_infos) == 3
    assert any(f['uuid'] == uuid1 and f['pdf_path'] is not None for f in file_infos)
    assert any(f['uuid'] == uuid2 and f['pdf_path'] is None for f in file_infos)
    assert any(f['uuid'] == uuid3_no_pdf and f['pdf_path'] is None for f in file_infos)
    assert any("PDF file not found for UUID 33333333-3333-3333-3333-333333333333" in e for e in errors)
    assert any("Could not extract UUID from JSON filename: no_uuid_item1.json" in e for e in errors)
    
    # Test 2: Create PDF for uuid2 and rescan
    print("\nScenario 2: Creating uuid2.pdf and rescanning")
    with open(os.path.join(pdfs_dir, f"{uuid2}.pdf"), 'w') as f: f.write("dummy pdf content for uuid2")
    file_infos, errors = scan_input_directory(sections_dir, pdfs_dir)
    print(f"Found {len(file_infos)} processable files.")
    for info in file_infos:
        print(f"  UUID: {info['uuid']}, JSON: {info['json_path']}, PDF: {info['pdf_path']}")
    assert any(f['uuid'] == uuid2 and f['pdf_path'] is not None for f in file_infos)

    print("\n--- Testing copy_approved_file (refactored) ---")
    # Add the path for uuid1 to the test database
    with get_db_session() as session:
        # Use the actual path of the file created on disk for the test
        test_item_data = {"brand_name": "Test Brand 1"} # Minimal data for Pydantic model
        # The add_item1_data function in db_handler expects a dictionary that can be unpacked into Item1Detail.
        # It will then map these to Item1Data columns.
        add_item1_data(session, uuid1, test_item_data, source_json_for_uuid1_on_disk_path, os.path.join(pdfs_dir, f"{uuid1}.pdf"))
        session.commit()
    
    # Now call the refactored copy_approved_file
    with get_db_session() as session:
        dest_path, error = copy_approved_file(session, uuid1, approved_dir)
        if error:
            print(f"Error copying file: {error}")
        else:
            print(f"File for UUID {uuid1} copied successfully to: {dest_path}")
            assert os.path.exists(dest_path)
            assert os.path.basename(dest_path) == f"{uuid1}_item1.json"
            assert os.path.dirname(dest_path) == os.path.join(approved_dir, "item_1")

    # Test copying with a UUID not in DB
    print("\nTesting copy_approved_file with UUID not in DB")
    with get_db_session() as session:
        _, error_uuid_not_found = copy_approved_file(session, "fake-uuid-not-in-db", approved_dir)
        assert error_uuid_not_found is not None
        print(f"Correctly caught error for UUID not in DB: {error_uuid_not_found}")

    # Test copying where DB has path but file doesn't exist on disk
    print("\nTesting copy_approved_file with DB path to non-existent file")
    uuid_for_missing_file_test = "44444444-4444-4444-4444-444444444444"
    path_to_non_existent_file = os.path.join(item1_json_s_dir, f"{uuid_for_missing_file_test}_item1.json")
    with get_db_session() as session:
        add_item1_data(session, uuid_for_missing_file_test, {"brand_name": "Missing File Brand"} , path_to_non_existent_file, None)
        session.commit()
        # Ensure the file *really* doesn't exist for the test
        if os.path.exists(path_to_non_existent_file):
             os.remove(path_to_non_existent_file)
        
        _, error_disk_file_missing = copy_approved_file(session, uuid_for_missing_file_test, approved_dir)
        assert error_disk_file_missing is not None
        print(f"Correctly caught error for missing disk file: {error_disk_file_missing}")

    # Clean up
    shutil.rmtree(test_base_dir)
    print("\nfile_handler.py test operations completed and cleanup done.") 