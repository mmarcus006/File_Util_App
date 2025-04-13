"""
S3 operations module for the FDD document management system.
Contains functions for uploading, downloading, and managing files in S3.
"""

import os
import uuid
import logging
import hashlib
from typing import Dict, Any, List, Optional, Tuple, Union, BinaryIO
from pathlib import Path
import boto3
from botocore.exceptions import ClientError

from config import Config

logger = logging.getLogger(__name__)


class S3Manager:
    """Manages S3 operations for the FDD document management system."""

    def __init__(self, bucket_name: str = None, region: str = None): #type: ignore
        """
        Initialize the S3Manager with AWS credentials from Config.
        
        Args:
            bucket_name: Optional S3 bucket name (defaults to Config.S3_BUCKET_NAME).
            region: Optional AWS region (defaults to Config.AWS_REGION).
        """
        s3_config = Config.get_s3_config()
        
        self.bucket_name = bucket_name or s3_config["bucket_name"]
        if not self.bucket_name:
            raise ValueError("S3 bucket name is required. Check your .env file.")
            
        self.region = region or s3_config["region_name"]
        if not self.region:
            raise ValueError("AWS region is required. Check your .env file.")
            
        # Check if AWS credentials are provided via Config (from .env)
        aws_access_key_id = s3_config["aws_access_key_id"]
        aws_secret_access_key = s3_config["aws_secret_access_key"]

        if not aws_access_key_id or not aws_secret_access_key:
            # Option 1: Raise error if keys are missing (strictest)
            raise ValueError("AWS credentials (ACCESS_KEY_ID, SECRET_ACCESS_KEY) are required in the .env file.")
            
            # Option 2: Fallback to default provider chain if keys are missing (more flexible, but might hide issues)
            # logger.warning("AWS credentials not provided in .env. Using default credentials provider chain.")
            # self.s3_client = boto3.client('s3', region_name=self.region)
            # self.s3_resource = boto3.resource('s3', region_name=self.region)
        else:
            # Use provided credentials from .env
            logger.info("Using AWS credentials loaded from .env file.")
            self.s3_client = boto3.client(
                's3',
                region_name=self.region,
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key
            )
            
            self.s3_resource = boto3.resource(
                's3',
                region_name=self.region,
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key
            )
        
        logger.debug(f"Initialized S3Manager with bucket: {self.bucket_name} in region: {self.region}")

    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize a filename for safe use in S3 keys.
        
        Args:
            filename: Original filename.
            
        Returns:
            str: Sanitized filename.
        """
        # Replace spaces with underscores and remove unsafe characters
        sanitized = filename.replace(' ', '_')
        
        # Remove any characters that might be problematic in S3 keys
        unsafe_chars = ['?', '&', '%', ':', ';', '#', '<', '>', '{', '}', '*', '$', '!', "'", '"', '`', '|', '=']
        for char in unsafe_chars:
            sanitized = sanitized.replace(char, '')
            
        return sanitized

    def generate_s3_key(self, franchise_name: str, fdd_year: int, document_uuid: str, filename: str) -> str:
        """
        Generate an S3 key following the convention:
        fdd_documents/<franchise_name>/<fdd_year>/<document_uuid>/<filename>
        
        Args:
            franchise_name: Name of the franchise.
            fdd_year: Year of the FDD document.
            document_uuid: UUID of the FDD document.
            filename: Name of the file.
            
        Returns:
            str: The generated S3 key.
        """
        sanitized_franchise = self.sanitize_filename(franchise_name)
        return f"fdd_documents/{sanitized_franchise}/{fdd_year}/{document_uuid}/{filename}"

    def generate_document_s3_key(self, franchise_name: str, fdd_year: int, document_uuid: str) -> str:
        """
        Generate an S3 key for the main document PDF.
        
        Args:
            franchise_name: Name of the franchise.
            fdd_year: Year of the FDD document.
            document_uuid: UUID of the FDD document.
            
        Returns:
            str: The generated S3 key for the main document.
        """
        return self.generate_s3_key(franchise_name, fdd_year, document_uuid, "document.pdf")

    def generate_analysis_s3_key(
        self, 
        franchise_name: str, 
        fdd_year: int, 
        document_uuid: str, 
        analysis_type: str, 
        extension: str = "json"
    ) -> str:
        """
        Generate an S3 key for an analysis file.
        
        Args:
            franchise_name: Name of the franchise.
            fdd_year: Year of the FDD document.
            document_uuid: UUID of the FDD document.
            analysis_type: Type of analysis file.
            extension: File extension (default: "json").
            
        Returns:
            str: The generated S3 key for the analysis file.
        """
        return self.generate_s3_key(
            franchise_name, 
            fdd_year, 
            document_uuid, 
            f"analysis/{analysis_type}.{extension}"
        )

    def generate_text_s3_key(
        self, 
        franchise_name: str, 
        fdd_year: int, 
        document_uuid: str, 
        text_type: str = "full", 
        extension: str = "md"
    ) -> str:
        """
        Generate an S3 key for a text file.
        
        Args:
            franchise_name: Name of the franchise.
            fdd_year: Year of the FDD document.
            document_uuid: UUID of the FDD document.
            text_type: Type of text file (default: "full").
            extension: File extension (default: "md").
            
        Returns:
            str: The generated S3 key for the text file.
        """
        return self.generate_s3_key(
            franchise_name, 
            fdd_year, 
            document_uuid, 
            f"text/{text_type}.{extension}"
        )

    def calculate_md5(self, file_path: Union[str, Path]) -> str:
        """
        Calculate MD5 hash for a file.
        
        Args:
            file_path: Path to the file.
            
        Returns:
            str: MD5 hash as a hexadecimal string.
        """
        md5_hash = hashlib.md5()
        with open(file_path, "rb") as f:
            # Read the file in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()

    def upload_file(
        self, 
        file_path: Union[str, Path],
        s3_key: str, 
        content_type: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Upload a file to S3.
        
        Args:
            file_path: Path to the file to upload.
            s3_key: S3 key (path) where to store the file.
            content_type: Optional content type for the file.
            
        Returns:
            Tuple[bool, Optional[str]]: (Success status, MD5 checksum or None)
        """
        try:
            # Calculate MD5 checksum
            md5_checksum = self.calculate_md5(file_path)
            
            # Set up extra args if content type is provided
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type
            
            # Upload the file
            self.s3_client.upload_file(
                str(file_path), 
                self.bucket_name, 
                s3_key, 
                ExtraArgs=extra_args
            )
            
            logger.info(f"Uploaded file {file_path} to {s3_key}")
            return True, md5_checksum
        except Exception as e:
            logger.error(f"Error uploading file {file_path} to {s3_key}: {str(e)}")
            return False, None

    def upload_fileobj(
        self,
        file_obj: BinaryIO,
        s3_key: str,
        content_type: Optional[str] = None
    ) -> bool:
        """
        Upload a file-like object to S3.
        
        Args:
            file_obj: File-like object to upload.
            s3_key: S3 key (path) where to store the file.
            content_type: Optional content type for the file.
            
        Returns:
            bool: True if upload was successful, False otherwise.
        """
        try:
            # Set up extra args if content type is provided
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type
            
            # Upload the file
            self.s3_client.upload_fileobj(
                file_obj, 
                self.bucket_name, 
                s3_key, 
                ExtraArgs=extra_args
            )
            
            logger.info(f"Uploaded file object to {s3_key}")
            return True
        except Exception as e:
            logger.error(f"Error uploading file object to {s3_key}: {str(e)}")
            return False

    def upload_data(
        self,
        data: Union[str, bytes],
        s3_key: str,
        content_type: Optional[str] = None
    ) -> bool:
        """
        Upload string or bytes data directly to S3.
        
        Args:
            data: String or bytes data to upload.
            s3_key: S3 key (path) where to store the data.
            content_type: Optional content type for the data.
            
        Returns:
            bool: True if upload was successful, False otherwise.
        """
        try:
            # Convert string to bytes if needed
            if isinstance(data, str):
                body = data.encode('utf-8')
            else:
                body = data
            
            # Set up extra args if content type is provided
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type
            
            # Upload the data
            self.s3_client.put_object(
                Body=body,
                Bucket=self.bucket_name,
                Key=s3_key,
                **extra_args
            )
            
            logger.info(f"Uploaded data to {s3_key}")
            return True
        except Exception as e:
            logger.error(f"Error uploading data to {s3_key}: {str(e)}")
            return False

    def download_file(self, s3_key: str, destination_path: Union[str, Path]) -> bool:
        """
        Download a file from S3.
        
        Args:
            s3_key: S3 key (path) of the file to download.
            destination_path: Local path where to save the file.
            
        Returns:
            bool: True if download was successful, False otherwise.
        """
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(str(destination_path)), exist_ok=True)
            
            # Download the file
            self.s3_client.download_file(
                self.bucket_name, 
                s3_key, 
                str(destination_path)
            )
            
            logger.info(f"Downloaded {s3_key} to {destination_path}")
            return True
        except Exception as e:
            logger.error(f"Error downloading {s3_key} to {destination_path}: {str(e)}")
            return False

    def download_fileobj(self, s3_key: str) -> Optional[bytes]:
        """
        Download a file from S3 and return its contents as bytes.
        
        Args:
            s3_key: S3 key (path) of the file to download.
            
        Returns:
            Optional[bytes]: File contents as bytes or None if download failed.
        """
        try:
            # Create a bytes buffer
            import io
            file_data = io.BytesIO()
            
            # Download the file to the buffer
            self.s3_client.download_fileobj(
                self.bucket_name, 
                s3_key, 
                file_data
            )
            
            # Reset the buffer position to the beginning
            file_data.seek(0)
            
            logger.info(f"Downloaded {s3_key} as bytes")
            return file_data.read()
        except Exception as e:
            logger.error(f"Error downloading {s3_key} as bytes: {str(e)}")
            return None

    def get_file_content(self, s3_key: str, encoding: str = 'utf-8') -> Optional[str]:
        """
        Get the content of a file from S3 as a string.
        
        Args:
            s3_key: S3 key (path) of the file to get.
            encoding: Encoding to use when decoding the file content (default: utf-8).
            
        Returns:
            Optional[str]: File content as a string or None if download failed.
        """
        try:
            # Get the object
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            # Read and decode the content
            content = response['Body'].read().decode(encoding)
            
            logger.info(f"Read content from {s3_key}")
            return content
        except Exception as e:
            logger.error(f"Error reading content from {s3_key}: {str(e)}")
            return None

    def delete_file(self, s3_key: str) -> bool:
        """
        Delete a file from S3.
        
        Args:
            s3_key: S3 key (path) of the file to delete.
            
        Returns:
            bool: True if deletion was successful, False otherwise.
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            logger.info(f"Deleted {s3_key}")
            return True
        except Exception as e:
            logger.error(f"Error deleting {s3_key}: {str(e)}")
            return False

    def delete_folder(self, folder_prefix: str) -> bool:
        """
        Delete all files in a folder (prefix) from S3.
        
        Args:
            folder_prefix: S3 key prefix (folder path) to delete.
            
        Returns:
            bool: True if deletion was successful, False otherwise.
        """
        try:
            # Ensure the prefix ends with a slash if it's a folder
            if not folder_prefix.endswith('/'):
                folder_prefix += '/'
            
            # List all objects with the prefix
            paginator = self.s3_client.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(
                Bucket=self.bucket_name,
                Prefix=folder_prefix
            )
            
            # Delete the objects
            for page in page_iterator:
                if 'Contents' in page:
                    delete_keys = {'Objects': [{'Key': obj['Key']} for obj in page['Contents']]}
                    self.s3_client.delete_objects(
                        Bucket=self.bucket_name,
                        Delete=delete_keys
                    )
            
            logger.info(f"Deleted folder {folder_prefix}")
            return True
        except Exception as e:
            logger.error(f"Error deleting folder {folder_prefix}: {str(e)}")
            return False

    def file_exists(self, s3_key: str) -> bool:
        """
        Check if a file exists in S3.
        
        Args:
            s3_key: S3 key (path) of the file to check.
            
        Returns:
            bool: True if the file exists, False otherwise.
        """
        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            else:
                logger.error(f"Error checking if {s3_key} exists: {str(e)}")
                return False
        except Exception as e:
            logger.error(f"Error checking if {s3_key} exists: {str(e)}")
            return False

    def list_files(self, prefix: str = None, limit: int = 1000) -> List[Dict[str, Any]]: #type: ignore
        """
        List files in S3 with an optional prefix.
        
        Args:
            prefix: Optional S3 key prefix to list files for.
            limit: Maximum number of files to list.
            
        Returns:
            List[Dict]: List of file information dictionaries.
        """
        try:
            params = {
                'Bucket': self.bucket_name,
                'MaxKeys': limit
            }
            
            if prefix:
                params['Prefix'] = prefix
                
            response = self.s3_client.list_objects_v2(**params)
            
            # Return empty list if no contents
            if 'Contents' not in response:
                return []
                
            # Build list of file info
            files = []
            for item in response['Contents']:
                files.append({
                    'key': item['Key'],
                    'size': item['Size'],
                    'last_modified': item['LastModified'],
                    'etag': item['ETag'].strip('"')
                })
                
            return files
        except Exception as e:
            logger.error(f"Error listing files with prefix {prefix}: {str(e)}")
            return []

    def create_bucket_if_not_exists(self) -> bool:
        """
        Check if the bucket exists and create it if it doesn't.
        
        Returns:
            bool: True if the bucket exists or was created successfully, False otherwise.
        """
        try:
            # Check if the bucket exists
            try:
                self.s3_client.head_bucket(Bucket=self.bucket_name)
                logger.info(f"S3 bucket '{self.bucket_name}' already exists.")
                return True
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code')
                if error_code == '404':
                    # Bucket doesn't exist, create it
                    logger.info(f"Creating S3 bucket '{self.bucket_name}'...")
                    
                    # Different create_bucket call depending on region
                    if self.region == 'us-east-1':
                        self.s3_client.create_bucket(Bucket=self.bucket_name)
                    else:
                        self.s3_client.create_bucket(
                            Bucket=self.bucket_name,
                            CreateBucketConfiguration={'LocationConstraint': self.region}
                        )
                    
                    logger.info(f"S3 bucket '{self.bucket_name}' created successfully.")
                    return True
                elif error_code == '403':
                    # Bucket exists but access is forbidden
                    logger.error(f"Access denied to S3 bucket '{self.bucket_name}'. "
                                f"Check IAM permissions for s3:HeadBucket and s3:CreateBucket. "
                                f"Verify the AWS credentials in your .env file are correct. "
                                f"Error details: {str(e)}")
                    return False
                else:
                    # Other error
                    logger.error(f"Error checking if bucket {self.bucket_name} exists: {str(e)}")
                    return False
        except Exception as e:
            logger.error(f"Error checking if bucket {self.bucket_name} exists: {str(e)}")
            return False
