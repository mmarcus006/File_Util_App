from google.cloud import storage
import os
from typing import List, Optional

def upload_file_to_bucket(bucket_name: str, source_file_name: str, destination_blob_name: str) -> None:
    """Uploads a file to the bucket.
    
    Args:
        bucket_name: Name of the GCS bucket
        source_file_name: Path to the local file to upload
        destination_blob_name: Destination path in the bucket
    """
    # Initialize the GCS client
    # The client will automatically authenticate using the GOOGLE_APPLICATION_CREDENTIALS environment variable
    storage_client = storage.Client()

    # Get the bucket object
    bucket = storage_client.bucket(bucket_name)

    # Create a blob object (representing the file to be uploaded)
    blob = bucket.blob(destination_blob_name)

    # Upload the file to the bucket
    blob.upload_from_filename(source_file_name)

    print(f"File {source_file_name} uploaded to gs://{bucket_name}/{destination_blob_name}")

def check_destination_exists(bucket_name: str, destination_blob_name: str) -> bool:
    """Check if a file already exists in the GCS bucket.
    
    Args:
        bucket_name: Name of the GCS bucket
        destination_blob_name: Path to check in the bucket
        
    Returns:
        True if the file exists, False otherwise
    """
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    return blob.exists()

def list_files_in_directory(directory_path: str) -> List[str]:
    """Lists all files in the specified directory.
    
    Args:
        directory_path: Path to the directory
        
    Returns:
        List of file paths in the directory
    """
    if not os.path.exists(directory_path):
        raise FileNotFoundError(f"Directory not found: {directory_path}")
    
    # Get all files in the directory
    files = []
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        if os.path.isfile(file_path):
            files.append(file_path)
    
    return files

def upload_directory_to_bucket(
    bucket_name: str,
    source_directory: str,
    destination_folder: str,
    overwrite: bool = False
) -> None:
    """Uploads all files from a directory to a GCS bucket folder.
    
    Args:
        bucket_name: Name of the GCS bucket
        source_directory: Path to the local directory containing files to upload
        destination_folder: Destination folder path in the bucket (without trailing slash)
        overwrite: Whether to overwrite existing files in the bucket
    """
    # Get all files in the directory
    try:
        files = list_files_in_directory(source_directory)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return
    
    if not files:
        print(f"No files found in {source_directory}")
        return
    
    # Upload each file
    print(f"Uploading {len(files)} files to gs://{bucket_name}/{destination_folder}/")
    
    for file_path in files:
        # Get just the filename from the full path
        filename = os.path.basename(file_path)
        
        # Create the destination blob name
        destination_blob_name = f"{destination_folder}/{filename}"
        
        # Check if file already exists in bucket
        if not overwrite and check_destination_exists(bucket_name, destination_blob_name):
            print(f"File {filename} already exists in bucket. Skipping.")
            continue
        
        # Upload the file
        upload_file_to_bucket(bucket_name, file_path, destination_blob_name)

# Example Usage:
if __name__ == "__main__":
    project_id = "calcium-petal-456313-r8"
    bucket_name = "fddsearchbucket"  # Fixed the space in the bucket name
    source_directory = r"C:\Projects\File_Util_App\processed_fdds"
    destination_folder = "processed_fdds"
    
    upload_directory_to_bucket(bucket_name, source_directory, destination_folder)
