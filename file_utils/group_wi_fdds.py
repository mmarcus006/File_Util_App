import os
import shutil
import math
from typing import List

def group_pdfs_into_folders(source_dir: str, batch_size: int = 20) -> None:
    """
    Groups PDF files in a source directory into subfolders alphabetically.

    Args:
        source_dir: The absolute path to the directory containing PDF files.
        batch_size: The number of PDF files per group (folder).
    """
    # Validate source directory
    if not os.path.isdir(source_dir):
        print(f"Error: Source directory not found: {source_dir}")
        return

    try:
        # List all files in the source directory
        all_files: List[str] = os.listdir(source_dir)

        # Filter for PDF files and get their full paths
        pdf_files: List[str] = sorted(
            [f for f in all_files if f.lower().endswith(".pdf")]
        )

        if not pdf_files:
            print(f"No PDF files found in {source_dir}")
            return

        # Calculate the total number of folders needed
        num_folders: int = math.ceil(len(pdf_files) / batch_size)
        print(f"Found {len(pdf_files)} PDF files. Creating {num_folders} folders...")

        # Loop through each batch/folder
        for i in range(num_folders):
            # Determine the start and end index for the current batch
            start_index: int = i * batch_size
            end_index: int = start_index + batch_size
            current_batch: List[str] = pdf_files[start_index:end_index]

            # Create the destination folder name (e.g., Folder1, Folder2)
            folder_name: str = f"Folder{i + 1}"
            dest_folder_path: str = os.path.join(source_dir, folder_name)

            # Create the destination folder if it doesn't exist
            os.makedirs(dest_folder_path, exist_ok=True)
            print(f"Processing batch {i+1}/{num_folders} into {dest_folder_path}...")

            # Move each file in the current batch to the destination folder
            for pdf_file in current_batch:
                source_file_path: str = os.path.join(source_dir, pdf_file)
                dest_file_path: str = os.path.join(dest_folder_path, pdf_file)

                # Check if the source is actually a file before moving
                if os.path.isfile(source_file_path):
                    try:
                        shutil.move(source_file_path, dest_file_path)
                        # print(f"  Moved: {pdf_file}") # Uncomment for verbose output
                    except Exception as move_error:
                        print(f"  Error moving file {pdf_file}: {move_error}")
                else:
                     print(f"  Skipping {pdf_file}, not a file.") # Should not happen with listdir filter but good practice


        print("Finished grouping PDF files.")

    except OSError as e:
        print(f"An OS error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


# Example usage:
if __name__ == "__main__":
    # Specify the directory containing the PDF files
    # IMPORTANT: Replace with the actual path on your system
    fdd_directory: str = r"C:\Users\mille\OneDrive\FDD_PDFS\FDD_WI"

    # Call the function to group the PDFs
    group_pdfs_into_folders(fdd_directory, batch_size=20)

    # You can change the batch size if needed:
    # group_pdfs_into_folders(fdd_directory, batch_size=10)
