import csv
import json
import os
import pathlib
import typing
from glob import glob

# --- Constants ---

CSV_FILE_PATH: typing.Final[str] = "db_replica/fdd.csv"
OUTPUT_JSON_PATH: typing.Final[str] = "pdf_processing_status.json"
UNPROCESSED_OUTPUT_PATH: typing.Final[str] = "unprocessed_pdfs.json"
HURIDOC_OUTPUT_DIR: typing.Final[str] = r"C:\Projects\File_Util_App\data\huridoc_analysis_output"

# Column indices (0-based) in the CSV file
ORIGINAL_PDF_PATH_IDX: typing.Final[int] = 4
LAYOUT_ANALYSIS_JSON_PATH_IDX: typing.Final[int] = 12

# --- Helper Functions ---

def extract_id_from_path(pdf_path_str: str) -> typing.Optional[str]:
    """
    Extracts the ID from the PDF filename.
    Assumes the format is '<ID>_origin.pdf'.

    Args:
        pdf_path_str: The full path to the original PDF file.

    Returns:
        The extracted ID string, or None if the format is incorrect.
    """
    try:
        pdf_path = pathlib.Path(pdf_path_str)
        filename = pdf_path.name
        if filename.endswith("_origin.pdf"):
            return filename[:-len("_origin.pdf")]
    except Exception: # Catch potential errors during path parsing
        # TODO: Consider logging this error for debugging malformed paths
        pass
    return None

def find_processed_ids() -> set[str]:
    """
    Scans the HURIDOC_OUTPUT_DIR for analysis JSON files and extracts their IDs.
    
    Returns:
        A set of IDs for which analysis files exist.
    """
    processed_ids = set()
    
    # Ensure directory exists
    if not os.path.exists(HURIDOC_OUTPUT_DIR):
        print(f"Warning: Huridoc output directory not found: {HURIDOC_OUTPUT_DIR}")
        return processed_ids
    
    # Find all JSON files in the huridoc output directory
    json_pattern = os.path.join(HURIDOC_OUTPUT_DIR, "*.json")
    json_files = glob(json_pattern)
    
    for json_file in json_files:
        # Extract the ID part from the filename
        filename = os.path.basename(json_file)
        if "_huridocs_analysis.json" in filename:
            # Remove the suffix "_huridocs_analysis.json"
            pdf_id = filename.replace("_huridocs_analysis.json", "")
            
            # Also remove "_origin" suffix if present (to match CSV IDs)
            if pdf_id.endswith("_origin"):
                pdf_id = pdf_id[:-len("_origin")]
                
            if pdf_id:
                processed_ids.add(pdf_id)
    
    # Debug: Print some example IDs found in the output directory
    print(f"Found {len(processed_ids)} already processed files in {HURIDOC_OUTPUT_DIR}")
    print("Examples of processed IDs (first 5):")
    for i, id_value in enumerate(list(processed_ids)[:5]):
        print(f"  {i+1}. {id_value}")
    
    return processed_ids

def get_pdf_records_from_csv(
    csv_filepath: str,
    original_pdf_idx: int
) -> list[dict[str, typing.Any]]:
    """
    Reads the CSV and extracts information about all PDF files.

    Args:
        csv_filepath: Path to the input CSV file.
        original_pdf_idx: Index of the original PDF path column.

    Returns:
        A list of dictionaries, each representing a PDF file.

    Raises:
        FileNotFoundError: If the csv_filepath does not exist.
    """
    csv_path = pathlib.Path(csv_filepath)
    if not csv_path.is_file():
        raise FileNotFoundError(f"CSV file not found: {csv_filepath}")
    
    pdf_records: list[dict[str, typing.Any]] = []

    with csv_path.open('r', newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile, delimiter='|')
        header = next(reader) # Skip header row

        for i, row in enumerate(reader):
            try:
                original_pdf_path = row[original_pdf_idx]
            except IndexError:
                # Skip malformed rows
                print(f"Skipping row {i+2}: Incorrect number of columns.")
                continue 

            extracted_id = extract_id_from_path(original_pdf_path)
            if not extracted_id:
                print(f"Skipping row {i+2}: Could not extract ID from path '{original_pdf_path}'.")
                continue # Skip rows where ID couldn't be extracted
            
            # Add entry for this PDF
            pdf_records.append({
                "id": extracted_id,
                "original_pdf_path": original_pdf_path,
                "original_pdf_filename": pathlib.Path(original_pdf_path).name
            })

    print(f"Found {len(pdf_records)} PDF records in CSV file.")
    # Debug: Print some example IDs found in the CSV
    print("Examples of IDs in CSV (first 5):")
    for i, record in enumerate(pdf_records[:5]):
        print(f"  {i+1}. {record['id']}")
    
    return pdf_records

def analyze_pdf_status() -> tuple[list[dict[str, typing.Any]], int, int]:
    """
    Analyzes the processing status of all PDFs by cross-referencing
    CSV records with the processed files.

    Returns:
        A tuple containing:
        - A list of dictionaries with PDF info and processing status
        - Count of processed PDFs
        - Count of unprocessed PDFs
    """
    # First, get the set of IDs that already have analysis files
    processed_ids = find_processed_ids()
    
    # Get all PDF records from the CSV
    pdf_records = get_pdf_records_from_csv(CSV_FILE_PATH, ORIGINAL_PDF_PATH_IDX)
    
    # Debug: Look for example matching IDs
    print("\nChecking for ID matches between CSV and processed files...")
    example_found = False
    for i, record in enumerate(pdf_records[:20]):  # Check first 20 records
        if record["id"] in processed_ids:
            print(f"  Match found! ID: {record['id']}")
            example_found = True
    
    if not example_found:
        print("  No matches found in first 20 records.")
        
        # Check if any of the processed IDs exist in the CSV records at all
        csv_id_set = {record["id"] for record in pdf_records}
        common_ids = processed_ids.intersection(csv_id_set)
        print(f"  Total common IDs between CSV and processed files: {len(common_ids)}")
        
        if common_ids:
            print("  Examples of common IDs (max 5):")
            for i, id_val in enumerate(list(common_ids)[:5]):
                print(f"    {i+1}. {id_val}")
    
    # Add processing status to each record
    processed_count = 0
    unprocessed_count = 0
    
    for record in pdf_records:
        # Check if this PDF has been processed
        is_processed = record["id"] in processed_ids
        record["processed"] = is_processed
        
        if is_processed:
            processed_count += 1
        else:
            unprocessed_count += 1
    
    return pdf_records, processed_count, unprocessed_count

def save_results_to_json(data: list[dict[str, typing.Any]], output_filepath: str) -> None:
    """
    Saves the provided data list to a JSON file.

    Args:
        data: The list of dictionaries to save.
        output_filepath: The path where the JSON file will be saved.
    """
    output_path = pathlib.Path(output_filepath)
    # Ensure the parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open('w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def save_unprocessed_to_json(data: list[dict[str, typing.Any]], output_filepath: str) -> int:
    """
    Saves only the unprocessed PDF records to a JSON file.

    Args:
        data: The list of dictionaries to filter and save.
        output_filepath: The path where the JSON file will be saved.
        
    Returns:
        The number of unprocessed records saved.
    """
    unprocessed_records = [record for record in data if not record["processed"]]
    
    output_path = pathlib.Path(output_filepath)
    # Ensure the parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open('w', encoding='utf-8') as f:
        json.dump(unprocessed_records, f, indent=4)
    
    return len(unprocessed_records)

# --- Main Execution ---

if __name__ == "__main__":
    print(f"Starting script: Analyzing PDF processing status...")
    try:
        pdf_status_list, processed_count, unprocessed_count = analyze_pdf_status()

        # Save the full list with processing status
        save_results_to_json(pdf_status_list, OUTPUT_JSON_PATH)
        
        # Save just the unprocessed files to a separate file
        unprocessed_count = save_unprocessed_to_json(pdf_status_list, UNPROCESSED_OUTPUT_PATH)

        print(f"\nProcessing complete.")
        print(f"Results: {processed_count} processed, {unprocessed_count} unprocessed")
        print(f"Total PDFs analyzed: {len(pdf_status_list)}")
        print(f"All files saved to: '{OUTPUT_JSON_PATH}'")
        print(f"Unprocessed files only saved to: '{UNPROCESSED_OUTPUT_PATH}'")

    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        # TODO: Add more specific error handling or logging 