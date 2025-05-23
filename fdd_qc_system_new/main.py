import os
import sys
import tkinter as tk
from tkinter import messagebox
import re
import json
from typing import Optional, Dict, List, Any, Set

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import necessary classes after adding to sys.path
try:
    from fdd_verification.ui.fdd_qc_app import FDDQualityControlApp
    from fdd_verification.core.pdf_processor import PDFProcessor, JSONProcessor
    from fdd_verification.core.verification_engine import VerificationEngine
except ImportError as e:
    # Can't use messagebox here as root Tk is not defined yet
    print(f"[FATAL] Failed to import required modules: {str(e)}")
    sys.exit(1)


def _extract_id_from_filename(filename: str) -> Optional[str]:
    """Extracts the ID part (before '_origin') from a filename."""
    match = re.match(r"^(.*?)_origin", filename)
    if match:
        return match.group(1)
    # Fallback for filenames without '_origin' (might be less common)
    base_name = os.path.splitext(filename)[0]
    # Check if it looks like a UUID (common ID format)
    if re.match(
        r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$",
        base_name,
    ):
        return base_name
    return None  # Or return base_name if you want to use the full name as ID if no pattern matches


def _load_corrected_files() -> Set[str]:
    """Load the list of already corrected file IDs."""
    corrected_files = set()
    corrected_file_path = os.path.join(
        os.path.dirname(__file__), "output", "corrected_files.json"
    )
    if os.path.exists(corrected_file_path):
        try:
            with open(corrected_file_path, "r") as f:
                corrected_files = set(json.load(f))
            print(f"Loaded {len(corrected_files)} previously corrected files.")
        except Exception as e:
            print(f"Error loading corrected files list: {e}")

    # Also scan for manually saved corrected files in case they weren't tracked
    corrected_output_dir = os.path.join(
        os.path.dirname(__file__), "output", "corrected_json"
    )
    if os.path.isdir(corrected_output_dir):
        try:
            for filename in os.listdir(corrected_output_dir):
                if filename.lower().endswith("_corrected.json"):
                    file_id = _extract_id_from_filename(filename)
                    if file_id:
                        corrected_files.add(file_id)
        except OSError as e:
            print(f"Error scanning corrected output directory: {e}")

    return corrected_files


def _discover_files(
    pdf_source_dir_win: str, json_source_dir_win: str
) -> Dict[str, Dict[str, str]]:
    """Discovers matching PDF and JSON files from source directories."""
    pdf_files_by_id = {}
    json_files_by_id = {}

    # Scan PDF directory - Use Windows path directly
    if os.path.isdir(pdf_source_dir_win):
        try:
            for filename in os.listdir(pdf_source_dir_win):
                if filename.lower().endswith(".pdf"):
                    file_id = _extract_id_from_filename(filename)
                    if file_id:
                        pdf_files_by_id[file_id] = os.path.join(
                            pdf_source_dir_win, filename
                        )
        except OSError as e:
            print(f"Error reading PDF directory {pdf_source_dir_win}: {e}")
    else:
        print(f"PDF source directory not found: {pdf_source_dir_win}")

    # Scan JSON directory - Use Windows path directly
    if os.path.isdir(json_source_dir_win):
        try:
            for filename in os.listdir(json_source_dir_win):
                if filename.lower().endswith(".json"):
                    file_id = _extract_id_from_filename(filename)
                    if file_id:
                        json_files_by_id[file_id] = os.path.join(
                            json_source_dir_win, filename
                        )
        except OSError as e:
            print(f"Error reading JSON directory {json_source_dir_win}: {e}")
    else:
        print(f"JSON source directory not found: {json_source_dir_win}")

    # Find matching pairs
    discovered_pairs = {}
    common_ids = set(pdf_files_by_id.keys()) & set(json_files_by_id.keys())

    for file_id in common_ids:
        discovered_pairs[file_id] = {
            "pdf": pdf_files_by_id[file_id],
            "json": json_files_by_id[file_id],
        }

    print(f"Discovered {len(discovered_pairs)} matching file pairs.")
    return discovered_pairs


def main():
    """Main function to run the application"""

    # --- Batch Processing ---
    print("Starting batch verification...")
    pdf_source_dir_win = r"C:\Projects\File_Util_App\processed_fdds"
    json_source_dir_win = r"C:\Projects\File_Util_App\output\header_output"
    results_output_dir = os.path.join(
        os.path.dirname(__file__), "output", "verification_results"
    )
    os.makedirs(results_output_dir, exist_ok=True)

    # Create directory for corrected JSON output if it doesn't exist
    corrected_output_dir = os.path.join(
        os.path.dirname(__file__), "output", "corrected_json"
    )
    os.makedirs(corrected_output_dir, exist_ok=True)

    discovered_pairs = _discover_files(pdf_source_dir_win, json_source_dir_win)
    corrected_files = _load_corrected_files()

    flagged_for_review = (
        {}
    )  # {file_id: {'pdf': pdf_path, 'json': json_path, 'results': results_path}}
    processed_count = 0
    auto_copied_count = 0

    for file_id, paths in discovered_pairs.items():
        # Skip already corrected files
        if file_id in corrected_files:
            print(f"Skipping {file_id} - already corrected.")
            continue

        pdf_path = paths["pdf"]
        json_path = paths["json"]
        print(f"Processing pair ID: {file_id}...")
        results_path = os.path.join(results_output_dir, f"{file_id}_results.json")

        # Skip if results already exist and just load them to check for flags
        if os.path.exists(results_path):
            print(f"  Loading existing results: {results_path}")
            try:
                with open(results_path, "r") as f_in:
                    verification_results = json.load(f_in)

                # Check for flags
                is_flagged = False
                for item_number, result in verification_results.items():
                    status = result.get("status")
                    if status in ["needs_review", "likely_incorrect", "not_found"]:
                        is_flagged = True
                        break

                if is_flagged:
                    print(f"  Flagged for review based on existing results.")
                    flagged_for_review[file_id] = {
                        "pdf": pdf_path,
                        "json": json_path,
                        "results": results_path,
                    }
            except Exception as e:
                print(f"  Error loading existing results: {e}")
                # If error loading, try to regenerate
                pass
            else:
                # If results were loaded successfully, continue with next file
                continue

        try:
            pdf_processor = PDFProcessor(pdf_path)
            json_processor = JSONProcessor(json_path)
            verification_engine = VerificationEngine(pdf_processor, json_processor)

            verification_results = verification_engine.verify_all_headers()

            # Save verification results
            with open(results_path, "w") as f_out:
                json.dump(verification_results, f_out, indent=2)
            print(f"  Saved results to {results_path}")

            # NEW FEATURE: Check if all headers are verified and can be auto-copied
            if verification_engine.should_auto_copy_to_corrected():
                print(f"  All headers verified. Auto-copying to corrected_json...")
                saved_path = verification_engine.auto_copy_to_corrected_json(
                    corrected_output_dir
                )
                if saved_path:
                    print(f"  Auto-copied to {os.path.basename(saved_path)}")
                    # Add to corrected files list
                    corrected_files.add(file_id)
                    auto_copied_count += 1
                    # Continue to next file since this one is now corrected
                    continue
                else:
                    print(f"  Failed to auto-copy. Flagging for review.")

            # Check for flags
            is_flagged = False
            for item_number, result in verification_results.items():
                status = result.get("status")
                if status in ["needs_review", "likely_incorrect", "not_found"]:
                    is_flagged = True
                    break

            if is_flagged:
                print(f"  Flagged for review.")
                flagged_for_review[file_id] = {
                    "pdf": pdf_path,
                    "json": json_path,
                    "results": results_path,
                }

            processed_count += 1
            # Optional: Limit the number processed for testing?
            # if processed_count >= 10:
            #     print("Reached processing limit for testing.")
            #     break

        except Exception as e:
            print(f"[ERROR] Failed to process pair ID {file_id}: {e}")
            # Optionally log the error or add to a separate error list

    # Save updated corrected files list
    corrected_file_path = os.path.join(
        os.path.dirname(__file__), "output", "corrected_files.json"
    )
    try:
        with open(corrected_file_path, "w") as f:
            json.dump(list(corrected_files), f)
        print(f"Saved {len(corrected_files)} corrected files to list.")
    except Exception as e:
        print(f"Error saving corrected files list: {e}")

    print(
        f"Batch verification complete. {len(flagged_for_review)} pairs flagged for review."
    )
    print(f"{auto_copied_count} files were automatically copied to corrected_json.")
    print(
        f"{len(corrected_files) - auto_copied_count} files were already corrected and skipped."
    )

    # --- Launch UI ---
    if not flagged_for_review:
        print("No files flagged for review. Exiting.")
        # Optionally show a simple tk message box
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        messagebox.showinfo("Batch Complete", "No files flagged for review.")
        root.destroy()
        sys.exit(0)

    print("Launching review application...")
    root = tk.Tk()
    app = FDDQualityControlApp(root, flagged_for_review=flagged_for_review)
    root.mainloop()


if __name__ == "__main__":
    main()
