"""
Interface for Cloudflare R2 object storage
"""
import boto3
from botocore.exceptions import ClientError
from pathlib import Path
import logging
import sys
from typing import Optional
import os

# Add parent directory to path for direct script execution
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fdd_pipeline.config import (
    R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_ENDPOINT_URL,
    R2_BUCKET_PDFS, R2_BUCKET_LAYOUTJSON, R2_BUCKET_HEADERSJSON,
    R2_BUCKET_EXTRACTEDDATA, R2_BUCKET_COMPANYLOGOS, R2_BUCKET_BLOG,
    PROJECT_ROOT
)

logger = logging.getLogger(__name__)

class R2Client:
    def __init__(self, default_bucket_name: Optional[str] = None):
        if not all([R2_ENDPOINT_URL, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY]):
            logger.error("R2 client not configured. Please set R2_ENDPOINT_URL, R2_ACCESS_KEY_ID, and R2_SECRET_ACCESS_KEY.")
            raise ValueError("R2 client configuration is incomplete.")
        
        self.s3 = boto3.client(
            's3',
            endpoint_url=R2_ENDPOINT_URL,
            aws_access_key_id=R2_ACCESS_KEY_ID,
            aws_secret_access_key=R2_SECRET_ACCESS_KEY,
            region_name='auto' # R2 uses 'auto'
        )
        
        # Explicitly set default_bucket to None if default_bucket_name is None
        if default_bucket_name is None:
            self.default_bucket = None
            logger.info("R2Client initialized without a default bucket name. Bucket name must be provided per call.")
        elif default_bucket_name: # If a name is provided, use it
            self.default_bucket = default_bucket_name
        else: # If default_bucket_name is an empty string or other falsey value (but not None), try fallback
            self.default_bucket = R2_BUCKET_PDFS # Fallback to default PDF bucket from config
            if not self.default_bucket: # If R2_BUCKET_PDFS is also not set
                 logger.warning("Default R2 bucket name (default_bucket_name parameter or R2_BUCKET_PDFS from config) is not set. Operations requiring a bucket name will need it explicitly provided.")
                 self.default_bucket = None # Ensure it's None if fallback is also not set

    def _get_target_bucket(self, target_bucket_name: Optional[str] = None) -> str:
        """Determines the target bucket, ensuring one is available."""
        bucket = target_bucket_name
        if bucket is None: # If no specific bucket is passed for the call, use default
            bucket = self.default_bucket
        
        if not bucket: # Covers None or empty string
            logger.error("No target bucket specified and no valid default bucket is configured for the client.")
            raise ValueError("R2 bucket name must be provided either as default_bucket_name during client initialization, as a specific bucket for the operation, or R2_BUCKET_PDFS must be configured if no default is given.")
        return bucket

    def list_objects(self, prefix='', target_bucket_name: Optional[str] = None):
        """List objects in the specified bucket (optionally with a prefix)."""
        bucket_to_list = self._get_target_bucket(target_bucket_name)
        try:
            response = self.s3.list_objects_v2(Bucket=bucket_to_list, Prefix=prefix)
            objects = [obj['Key'] for obj in response.get('Contents', [])]

            return objects
        except ClientError as e:
            logger.error(f"Error listing objects in bucket '{bucket_to_list}' with prefix '{prefix}': {e}")
            return []

    def upload_file(self, local_path: str, object_name: Optional[str] = None, target_bucket_name: Optional[str] = None) -> bool:
        """Upload a file to the specified bucket."""
        bucket_to_upload_to = self._get_target_bucket(target_bucket_name)
        
        if not Path(local_path).is_file():
            logger.error(f"Local file '{local_path}' does not exist or is not a file.")
            return False

        if object_name is None:
            object_name = Path(local_path).name
        try:
            self.s3.upload_file(str(local_path), bucket_to_upload_to, object_name)
            logger.info(f"Uploaded '{local_path}' to bucket '{bucket_to_upload_to}' as '{object_name}'")
            return True
        except ClientError as e:
            logger.error(f"ClientError uploading file '{local_path}' to bucket '{bucket_to_upload_to}' as '{object_name}': {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error uploading file '{local_path}' to bucket '{bucket_to_upload_to}' as '{object_name}': {e}")
            return False

    def download_file(self, object_name: str, local_path: str, source_bucket_name: Optional[str] = None) -> bool:
        """Download a file from the specified bucket."""
        bucket_to_download_from = self._get_target_bucket(source_bucket_name)
        try:
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)
            self.s3.download_file(bucket_to_download_from, object_name, str(local_path))
            logger.info(f"Downloaded '{object_name}' from bucket '{bucket_to_download_from}' to '{local_path}'")
            return True
        except ClientError as e:
            logger.error(f"Error downloading file '{object_name}' from bucket '{bucket_to_download_from}': {e}")
            return False

    def delete_object(self, object_name: str, target_bucket_name: Optional[str] = None) -> bool:
        """Delete an object from the specified bucket."""
        bucket_to_delete_from = self._get_target_bucket(target_bucket_name)
        try:
            self.s3.delete_object(Bucket=bucket_to_delete_from, Key=object_name)
            logger.info(f"Deleted '{object_name}' from bucket '{bucket_to_delete_from}'")
            return True
        except ClientError as e:
            logger.error(f"Error deleting object '{object_name}' from bucket '{bucket_to_delete_from}': {e}")
            return False

    def object_exists(self, object_name: str, target_bucket_name: Optional[str] = None) -> bool:
        """Check if an object exists in the specified bucket."""
        bucket_to_check = self._get_target_bucket(target_bucket_name)
        try:
            self.s3.head_object(Bucket=bucket_to_check, Key=object_name)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == "404":
                return False
            else:
                logger.error(f"Error checking if object '{object_name}' exists in bucket '{bucket_to_check}': {e}")
                return False # Or raise error depending on desired behavior for unexpected errors

    def get_object_metadata(self, object_name: str, target_bucket_name: Optional[str] = None):
        """Get metadata for an object in the specified bucket."""
        bucket_to_get_from = self._get_target_bucket(target_bucket_name)
        try:
            response = self.s3.head_object(Bucket=bucket_to_get_from, Key=object_name)
            return response
        except ClientError as e:
            logger.error(f"Error getting object metadata for '{object_name}' from bucket '{bucket_to_get_from}': {e}")
            return None

    def generate_presigned_url(self, object_name: str, expiration: int = 3600, target_bucket_name: Optional[str] = None):
        """Generate a presigned URL for an object in the specified bucket."""
        bucket_for_url = self._get_target_bucket(target_bucket_name)
        try:
            response = self.s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_for_url, 'Key': object_name},
                ExpiresIn=expiration
            )
            return response
        except ClientError as e:
            logger.error(f"Error generating presigned URL for '{object_name}' in bucket '{bucket_for_url}': {e}")
            return None

    def list_buckets(self):
        """List all available buckets (this operation is not bucket-specific)."""
        try:
            response = self.s3.list_buckets()
            buckets = [bucket['Name'] for bucket in response.get('Buckets', [])]
            return buckets
        except ClientError as e:
            logger.error(f"Error listing buckets: {e}")
            return []

    def upload_directory(self, local_dir: str, prefix: str = '', target_bucket_name: Optional[str] = None) -> bool:
        """Upload all files in a directory to the specified bucket."""
        bucket_to_upload_to = self._get_target_bucket(target_bucket_name)
        local_path_obj = Path(local_dir)
        if not local_path_obj.is_dir():
            logger.error(f"Local directory '{local_dir}' does not exist or is not a directory.")
            return False
            
        all_successful = True
        for file_path in local_path_obj.glob('**/*'):
            if file_path.is_file():
                relative_path = file_path.relative_to(local_path_obj)
                object_name_parts = []
                if prefix:
                    object_name_parts.append(prefix.strip('/'))
                object_name_parts.extend(relative_path.parts)
                object_name = "/".join(object_name_parts)
                
                if not self.upload_file(str(file_path), object_name, target_bucket_name=bucket_to_upload_to):
                    all_successful = False
                    
        if all_successful:
            logger.info(f"Successfully uploaded directory '{local_dir}' to bucket '{bucket_to_upload_to}' with prefix '{prefix}'")
        else:
            logger.warning(f"Failed to upload some files from directory '{local_dir}' to bucket '{bucket_to_upload_to}' with prefix '{prefix}'")
        return all_successful

    def download_directory(self, prefix: str, local_dir: str, source_bucket_name: Optional[str] = None) -> bool:
        """Download all objects with a given prefix from a specified bucket to a local directory."""
        bucket_to_download_from = self._get_target_bucket(source_bucket_name)
        local_path_obj = Path(local_dir)
        local_path_obj.mkdir(parents=True, exist_ok=True)
        
        all_successful = True
        try:
            objects = self.list_objects(prefix=prefix, target_bucket_name=bucket_to_download_from)
            if not objects:
                logger.info(f"No objects found in bucket '{bucket_to_download_from}' with prefix '{prefix}' to download.")
                return True 
            
            for object_key in objects:
                rel_path_str = object_key
                # Correctly strip prefix for local path construction
                current_prefix = prefix.strip('/')
                if current_prefix and object_key.startswith(current_prefix + '/'):
                    rel_path_str = object_key[len(current_prefix)+1:]
                elif current_prefix and object_key == current_prefix: # Edge case: prefix is the object_key
                    rel_path_str = Path(object_key).name
                elif not current_prefix: # No prefix, use key as is
                    pass # rel_path_str is already object_key
                else: # Object key doesn't fit expected prefix pattern for sub-pathing
                    rel_path_str = Path(object_key).name

                if not rel_path_str: # If stripping prefix results in empty string (e.g. prefix was the full key)
                    rel_path_str = Path(object_key).name

                local_file_path = local_path_obj / rel_path_str
                local_file_path.parent.mkdir(parents=True, exist_ok=True)
                
                if not self.download_file(object_key, str(local_file_path), source_bucket_name=bucket_to_download_from):
                    all_successful = False
            
            if all_successful:
                logger.info(f"Successfully downloaded directory from prefix '{prefix}' in bucket '{bucket_to_download_from}' to '{local_dir}'")
            else:
                logger.warning(f"Failed to download some files from prefix '{prefix}' in bucket '{bucket_to_download_from}' to '{local_dir}'")
            return all_successful
        except Exception as e:
            logger.error(f"Error downloading directory from prefix '{prefix}' in bucket '{bucket_to_download_from}': {e}")
            return False
            
    # --- PDF Specific Methods ---
    def upload_pdf(self, local_path: str, object_name: Optional[str] = None) -> bool:
        return self.upload_file(local_path, object_name, target_bucket_name=R2_BUCKET_PDFS)

    def download_pdf(self, object_name: str, local_path: str) -> bool:
        return self.download_file(object_name, local_path, source_bucket_name=R2_BUCKET_PDFS)

    # --- LayoutJSON Specific Methods ---
    def upload_layoutjson(self, local_path: str, object_name: Optional[str] = None) -> bool:
        return self.upload_file(local_path, object_name, target_bucket_name=R2_BUCKET_LAYOUTJSON)

    def download_layoutjson(self, object_name: str, local_path: str) -> bool:
        return self.download_file(object_name, local_path, source_bucket_name=R2_BUCKET_LAYOUTJSON)

    # --- HeadersJSON Specific Methods ---
    def upload_headersjson(self, local_path: str, object_name: Optional[str] = None) -> bool:
        return self.upload_file(local_path, object_name, target_bucket_name=R2_BUCKET_HEADERSJSON)

    def download_headersjson(self, object_name: str, local_path: str) -> bool:
        return self.download_file(object_name, local_path, source_bucket_name=R2_BUCKET_HEADERSJSON)

    # --- ExtractedData Specific Methods ---
    def upload_extracteddata(self, local_path: str, object_name: Optional[str] = None) -> bool:
        return self.upload_file(local_path, object_name, target_bucket_name=R2_BUCKET_EXTRACTEDDATA)

    def download_extracteddata(self, object_name: str, local_path: str) -> bool:
        return self.download_file(object_name, local_path, source_bucket_name=R2_BUCKET_EXTRACTEDDATA)
        
    # --- CompanyLogos Specific Methods ---
    def upload_companylogo(self, local_path: str, object_name: Optional[str] = None) -> bool:
        return self.upload_file(local_path, object_name, target_bucket_name=R2_BUCKET_COMPANYLOGOS)

    def download_companylogo(self, object_name: str, local_path: str) -> bool:
        return self.download_file(object_name, local_path, source_bucket_name=R2_BUCKET_COMPANYLOGOS)

    # --- Blog Specific Methods ---
    def upload_blogfile(self, local_path: str, object_name: Optional[str] = None) -> bool: # Renamed from upload_blog to upload_blogfile
        return self.upload_file(local_path, object_name, target_bucket_name=R2_BUCKET_BLOG)

    def download_blogfile(self, object_name: str, local_path: str) -> bool: # Renamed from download_blog to download_blogfile
        return self.download_file(object_name, local_path, source_bucket_name=R2_BUCKET_BLOG)

# Example usage:
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO) # Enable logging for example
    
    # Ensure PROJECT_ROOT is defined if you are running this directly and it's used for paths
    # It's imported from config now, so should be fine.

    example_file_path = PROJECT_ROOT / "example_upload_main.txt"
    if not example_file_path.exists():
        with open(example_file_path, "w") as f:
            f.write("This is a test file created by cloud_storage.py main block.")

    r2_client = R2Client() # Uses R2_BUCKET_NAME as default

    print(f"\n--- Listing All Buckets ---")
    all_buckets = r2_client.list_buckets()
    print(f"Available buckets: {all_buckets}")
    if not all_buckets:
        logger.warning("No buckets found or error listing. Ensure R2 is configured and buckets exist.")
    
    # Example: Using specific PDF upload/download (assuming R2_BUCKET_PDFS is set in .env and exists)
    if R2_BUCKET_PDFS and R2_BUCKET_PDFS in all_buckets:
        print(f"\n--- PDF Bucket Operations ({R2_BUCKET_PDFS}) ---")
        pdf_object_name = "test_documents/example.pdf"
        if r2_client.upload_pdf(str(example_file_path), pdf_object_name):
            downloaded_pdf_path = PROJECT_ROOT / "downloaded_example.pdf"
            if r2_client.download_pdf(pdf_object_name, str(downloaded_pdf_path)):
                logger.info(f"Successfully downloaded PDF to {downloaded_pdf_path}")
                downloaded_pdf_path.unlink(missing_ok=True) # Clean up downloaded file
            r2_client.delete_object(pdf_object_name, target_bucket_name=R2_BUCKET_PDFS) # Cleanup uploaded object
    else:
        logger.warning(f"Skipping PDF specific bucket operations. R2_BUCKET_PDFS ('{R2_BUCKET_PDFS}') not found or not configured.")

    # Example: Using specific LayoutJSON upload/download
    if R2_BUCKET_LAYOUTJSON and R2_BUCKET_LAYOUTJSON in all_buckets:
        print(f"\n--- LayoutJSON Bucket Operations ({R2_BUCKET_LAYOUTJSON}) ---")
        layout_object_name = "test_layouts/example_layout.json"
        # Create a dummy json string for layout file
        example_layout_path = PROJECT_ROOT / "example_layout.json"
        with open(example_layout_path, "w") as f:
            f.write('{"page": 1, "text": "dummy layout"}')
        
        if r2_client.upload_layoutjson(str(example_layout_path), layout_object_name):
            downloaded_layout_path = PROJECT_ROOT / "downloaded_layout.json"
            if r2_client.download_layoutjson(layout_object_name, str(downloaded_layout_path)):
                logger.info(f"Successfully downloaded LayoutJSON to {downloaded_layout_path}")
                downloaded_layout_path.unlink(missing_ok=True)
            r2_client.delete_object(layout_object_name, target_bucket_name=R2_BUCKET_LAYOUTJSON)
        example_layout_path.unlink(missing_ok=True) # Clean up local dummy layout file
    else:
        logger.warning(f"Skipping LayoutJSON specific bucket operations. R2_BUCKET_LAYOUTJSON ('{R2_BUCKET_LAYOUTJSON}') not found or not configured.")

    # General upload to default bucket
    if r2_client.default_bucket and r2_client.default_bucket in all_buckets:
        print(f"\n--- Default Bucket Operations ({r2_client.default_bucket}) ---")
        default_object_name = "test_generic/example_default.txt"
        if r2_client.upload_file(str(example_file_path), default_object_name): # Uses client's default bucket
            downloaded_default_path = PROJECT_ROOT / "downloaded_default_main.txt"
            if r2_client.download_file(default_object_name, str(downloaded_default_path)): # Uses client's default
                logger.info(f"Successfully downloaded from default bucket to {downloaded_default_path}")
                downloaded_default_path.unlink(missing_ok=True)
            r2_client.delete_object(default_object_name) # Uses client's default
    else:
        logger.warning(f"Skipping default bucket operations. R2_BUCKET_NAME ('{r2_client.default_bucket}') not found or not configured.")

    if example_file_path.exists():
        example_file_path.unlink()
    print("\n--- Example Main Block Finished ---")
