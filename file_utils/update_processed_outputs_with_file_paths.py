import os
import json
import csv
import glob
from typing import Dict, Tuple, Optional, List


# --- Configuration ---
PROCESSED_DIR = r"C:\Projects\File_Util_App\data\processed_outputs"
CSV_FILE_PATH = r"C:\Projects\File_Util_App\data\processed_files.csv"


def get_uuid_from_processed_filename(filename: str) -> Optional[str]:
    """Extracts the UUID part from the processed filename."""
    if filename.endswith("_analysis_result.json"):
        return filename.replace("_analysis_result.json", "")
    return None


def create_uuid_mapping(csv_path: str) -> Dict[str, str]:
    """Creates a mapping from UUID to original JSON path using the CSV."""
    uuid_to_original_json = {}
    try:
        with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                output_path = row.get('output_path')
                original_path = row.get('original_path')
                if output_path and original_path:
                    output_filename = os.path.basename(output_path)
                    uuid = get_uuid_from_processed_filename(output_filename)
                    if uuid:
                        uuid_to_original_json[uuid] = original_path
                    else:
                        print(f"Warning: Could not extract UUID from output path in CSV: {output_path}")
                else:
                    print(f"Warning: Skipping row due to missing data: {row}")

    except FileNotFoundError:
        print(f"Error: CSV file not found at {csv_path}")
        return {}
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return {}

    if not uuid_to_original_json:
        print("Error: No valid mappings found in the CSV file.")
    else:
        print(f"Successfully created mapping for {len(uuid_to_original_json)} files from CSV.")

    return uuid_to_original_json


def find_pdf_in_folder(folder_path: str) -> Optional[str]:
    """Find the first PDF file in a folder."""
    pdf_files = glob.glob(os.path.join(folder_path, "*.pdf"))
    if pdf_files:
        if len(pdf_files) > 1:
            print(f"Warning: Multiple PDFs found in {folder_path}. Using first one: {pdf_files[0]}")
        return pdf_files[0]  # Return the first PDF found
    return None


def update_processed_file(processed_file_path: str, original_json_path: str, 
                          original_pdf_path: Optional[str]) -> bool:
    """Update a processed JSON file with original file information."""
    try:
        with open(processed_file_path, 'r', encoding='utf-8') as f_in:
            data = json.load(f_in)

        # Extract subfolder name
        original_subfolder_path = os.path.dirname(original_json_path)
        original_subfolder_name = os.path.basename(original_subfolder_path)

        # Add the new information
        data['original_subfolder_name'] = original_subfolder_name
        data['original_json_path'] = original_json_path
        data['original_pdf_path'] = original_pdf_path  # Will be None if not found
        data['processed_json_path'] = processed_file_path

        # Write the updated data back
        with open(processed_file_path, 'w', encoding='utf-8') as f_out:
            json.dump(data, f_out, indent=4)  # Use indent for readability

        return True

    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {os.path.basename(processed_file_path)}")
    except IOError as e:
        print(f"Error reading/writing file {os.path.basename(processed_file_path)}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred processing {os.path.basename(processed_file_path)}: {e}")
    
    return False


def process_files(processed_dir: str, uuid_mapping: Dict[str, str]) -> Tuple[int, int, int, int]:
    """Process all files in the processed directory and update them with original paths."""
    processed_files_updated = 0
    processed_files_skipped = 0
    processed_files_not_found_in_csv = 0
    pdf_not_found_count = 0

    for processed_filename in os.listdir(processed_dir):
        processed_file_path = os.path.join(processed_dir, processed_filename)

        # Ensure it's a file and matches the expected pattern
        if not os.path.isfile(processed_file_path) or not processed_filename.endswith("_analysis_result.json"):
            continue

        uuid = get_uuid_from_processed_filename(processed_filename)
        if not uuid:
            print(f"Warning: Could not extract UUID from processed file: {processed_filename}")
            processed_files_skipped += 1
            continue

        # Find original file info using the mapping
        original_json_path = uuid_mapping.get(uuid)

        if not original_json_path:
            print(f"Warning: No original file mapping found in CSV for UUID: {uuid} (File: {processed_filename})")
            processed_files_not_found_in_csv += 1
            continue

        if not os.path.exists(original_json_path):
            print(f"Warning: Original JSON path from CSV does not exist: {original_json_path} (for {processed_filename})")
            processed_files_skipped += 1
            continue

        # Find the PDF within the original subfolder
        original_subfolder_path = os.path.dirname(original_json_path)
        original_pdf_path = find_pdf_in_folder(original_subfolder_path)
        
        if not original_pdf_path:
            print(f"Warning: No PDF found in folder: {original_subfolder_path} (for {processed_filename})")
            pdf_not_found_count += 1

        # Update the processed JSON file
        if update_processed_file(processed_file_path, original_json_path, original_pdf_path):
            processed_files_updated += 1

    return processed_files_updated, processed_files_skipped, processed_files_not_found_in_csv, pdf_not_found_count


def print_summary(stats: Tuple[int, int, int, int]) -> None:
    """Print a summary of the processing results."""
    updated, skipped, not_found, pdf_missing = stats
    
    print("\n--- Processing Summary ---")
    print(f"Processed files updated: {updated}")
    print(f"Processed files skipped (error/format issue): {skipped}")
    print(f"Processed files not found in CSV mapping: {not_found}")
    print(f"Original PDFs not found: {pdf_missing}")
    print("--------------------------")


def main() -> None:
    """Main function to orchestrate the update process."""
    # Create mapping from UUID to original JSON path
    uuid_mapping = create_uuid_mapping(CSV_FILE_PATH)
    if not uuid_mapping:
        return
    
    # Process files and update them
    stats = process_files(PROCESSED_DIR, uuid_mapping)
    
    # Print summary of results
    print_summary(stats)


if __name__ == "__main__":
    main()