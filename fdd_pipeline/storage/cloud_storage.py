"""
Interface for Cloudflare R2 object storage
"""
import boto3
from botocore.exceptions import ClientError
from pathlib import Path
import logging
import sys

# Add parent directory to path for direct script execution
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fdd_pipeline.config import R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_ENDPOINT_URL, R2_BUCKET_NAME

logger = logging.getLogger(__name__)

class R2Client:
    def __init__(self, bucket_name=None):
        self.s3 = boto3.client(
            's3',
            endpoint_url=R2_ENDPOINT_URL,
            aws_access_key_id=R2_ACCESS_KEY_ID,
            aws_secret_access_key=R2_SECRET_ACCESS_KEY,
            region_name='auto'
        )
        self.bucket = bucket_name if bucket_name else R2_BUCKET_NAME

    def list_objects(self, prefix=''):
        """List objects in the bucket (optionally with a prefix)."""
        try:
            response = self.s3.list_objects_v2(Bucket=self.bucket, Prefix=prefix)
            objects = [obj['Key'] for obj in response.get('Contents', [])]
            print(f"Objects in bucket '{self.bucket}': {objects}")
            return objects
        except ClientError as e:
            print(f"Error listing objects: {e}")
            return []

    def upload_file(self, local_path, object_name=None):
        """Upload a file to the bucket."""
        if object_name is None:
            object_name = local_path.split('/')[-1]
        try:
            self.s3.upload_file(local_path, self.bucket, object_name)
            print(f"Uploaded '{local_path}' as '{object_name}'")
            return True
        except ClientError as e:
            print(f"Error uploading file: {e}")
            return False

    def download_file(self, object_name, local_path):
        """Download a file from the bucket."""
        try:
            self.s3.download_file(self.bucket, object_name, local_path)
            print(f"Downloaded '{object_name}' to '{local_path}'")
            return True
        except ClientError as e:
            print(f"Error downloading file: {e}")
            return False

    def delete_object(self, object_name):
        """Delete an object from the bucket."""
        try:
            self.s3.delete_object(Bucket=self.bucket, Key=object_name)
            print(f"Deleted '{object_name}' from bucket")
            return True
        except ClientError as e:
            print(f"Error deleting object: {e}")
            return False

    def object_exists(self, object_name):
        """Check if an object exists in the bucket."""
        try:
            self.s3.head_object(Bucket=self.bucket, Key=object_name)
            print(f"Object '{object_name}' exists in bucket")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == "404":
                print(f"Object '{object_name}' does not exist in bucket")
                return False
            else:
                print(f"Error checking object: {e}")
                return False

    def get_object_metadata(self, object_name):
        """Get metadata for an object."""
        try:
            response = self.s3.head_object(Bucket=self.bucket, Key=object_name)
            return response
        except ClientError as e:
            print(f"Error getting object metadata: {e}")
            return None

    def generate_presigned_url(self, object_name, expiration=3600):
        """Generate a presigned URL for an object."""
        try:
            response = self.s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket, 'Key': object_name},
                ExpiresIn=expiration
            )
            return response
        except ClientError as e:
            print(f"Error generating presigned URL: {e}")
            return None

    def list_buckets(self):
        """List all available buckets."""
        try:
            response = self.s3.list_buckets()
            buckets = [bucket['Name'] for bucket in response.get('Buckets', [])]
            print(f"Available buckets: {buckets}")
            return buckets
        except ClientError as e:
            print(f"Error listing buckets: {e}")
            return []

    def upload_directory(self, local_dir, prefix=''):
        """Upload all files in a directory to the bucket."""
        local_path = Path(local_dir)
        if not local_path.is_dir():
            print(f"Error: {local_dir} is not a directory")
            return False
            
        success = True
        for file_path in local_path.glob('**/*'):
            if file_path.is_file():
                # Create relative path for the object key
                relative_path = file_path.relative_to(local_path)
                object_name = f"{prefix}/{relative_path}".replace('\\', '/')
                
                # Remove leading slash if present
                if object_name.startswith('/'):
                    object_name = object_name[1:]
                    
                if not self.upload_file(str(file_path), object_name):
                    success = False
                    
        return success

    def download_directory(self, prefix, local_dir):
        """Download all objects with a given prefix to a local directory."""
        local_path = Path(local_dir)
        local_path.mkdir(parents=True, exist_ok=True)
        
        try:
            # List all objects with the prefix
            objects = self.list_objects(prefix=prefix)
            
            success = True
            for object_key in objects:
                # Create relative local path
                rel_path = object_key
                if prefix and object_key.startswith(prefix):
                    rel_path = object_key[len(prefix):]
                    if rel_path.startswith('/'):
                        rel_path = rel_path[1:]
                
                # Create local file path
                local_file_path = local_path / rel_path
                local_file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Download the file
                if not self.download_file(object_key, str(local_file_path)):
                    success = False
            
            return success
        except Exception as e:
            print(f"Error downloading directory: {e}")
            return False
            

# Example usage:
if __name__ == "__main__":
    # Basic operations
    file_path = r"C:\projects\File_Util_App\processed_fdds\0a6a4155-b831-4d28-a7bf-f7eb1da5d2ad_origin.pdf"
    r2 = R2Client()
    
    # List all available buckets
    buckets = r2.list_buckets()
    
    # Switch to a different bucket
    alt_client = R2Client(bucket_name="my-backup-bucket")
    
    # List objects in a bucket 
    r2.list_objects(prefix="documents/")
    
    # Upload a file
    r2.upload_file(file_path, "documents/example.pdf")
    
    # Generate a temporary access URL
    url = r2.generate_presigned_url("documents/example.pdf", expiration=3600)
    if url:
        print(f"Access URL: {url}")
    
    # Upload an entire directory
    r2.upload_directory("C:/projects/File_Util_App/data/inputs", prefix="batch_upload")
    
    # Download a directory of files
    r2.download_directory("batch_upload", "C:/projects/File_Util_App/data/downloads")
