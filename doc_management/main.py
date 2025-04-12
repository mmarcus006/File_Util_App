"""
Main module for the FDD document management system.
Contains example usage of the system components.
"""

import os
import json
import logging
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
import tempfile

from config import Config
from db_schema import setup_database
from db_operations import FDDDatabaseManager
from s3_operations import S3Manager

logger = logging.getLogger(__name__)


class FDDManager:
    """Main class for managing FDD documents and analysis files."""

    def __init__(self):
        """Initialize the FDDManager."""
        # Set up database connection
        success, supabase_client = setup_database()
        if not success or not supabase_client:
            raise RuntimeError("Failed to set up database connection")
        
        # Initialize the managers
        self.db_manager = FDDDatabaseManager(supabase_client)
        
        try:
            # Try to initialize S3 manager with the configured bucket
            self.s3_manager = S3Manager()
            
            # Check bucket access or try to create it
            if not self.s3_manager.create_bucket_if_not_exists():
                logger.warning(
                    f"Could not access or create the S3 bucket: {self.s3_manager.bucket_name}. "
                    "Will try to create a fallback bucket."
                )
                
                # Try with a fallback bucket name using a unique identifier
                fallback_bucket_name = f"fdd-documents-{uuid.uuid4().hex[:8]}"
                logger.info(f"Attempting to create fallback bucket: {fallback_bucket_name}")
                
                # Re-initialize S3 manager with fallback bucket
                self.s3_manager = S3Manager(bucket_name=fallback_bucket_name)
                
                if not self.s3_manager.create_bucket_if_not_exists():
                    raise RuntimeError(f"Failed to create fallback S3 bucket: {fallback_bucket_name}")
                
                logger.info(f"Successfully created and using fallback S3 bucket: {fallback_bucket_name}")
                
        except Exception as e:
            raise RuntimeError(f"Failed to initialize S3 manager: {str(e)}")
        
        logger.info("FDDManager initialized successfully")

    def upload_fdd_document(
        self,
        file_path: Union[str, Path],
        franchise_name: str,
        fdd_year: int
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Upload an FDD document and create database records.
        
        Args:
            file_path: Path to the FDD PDF file.
            franchise_name: Name of the franchise.
            fdd_year: Year of the FDD document.
            
        Returns:
            Tuple[bool, Optional[Dict]]: (Success status, FDD document data or None)
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                logger.error(f"File not found: {file_path}")
                return False, None
                
            # Get or create the franchise
            franchise_success, franchise_data = self.db_manager.create_franchise(franchise_name)
            if not franchise_success or not franchise_data:
                logger.error(f"Failed to create franchise: {franchise_name}")
                return False, None
                
            franchise_id = franchise_data["id"]
            
            # Generate a UUID for the document
            document_uuid = str(uuid.uuid4())
            
            # Generate S3 key for the document
            s3_key = self.s3_manager.generate_document_s3_key(
                franchise_name, 
                fdd_year, 
                document_uuid
            )
            
            # Upload the file to S3
            upload_success, md5_checksum = self.s3_manager.upload_file(
                file_path,
                s3_key,
                content_type="application/pdf"
            )
            
            if not upload_success:
                logger.error(f"Failed to upload file to S3: {file_path}")
                return False, None
            
            # Ensure bucket name is not None before passing
            assert self.s3_manager.bucket_name is not None, "S3 bucket name should be set after initialization"
                
            # Create the FDD document record in the database
            doc_success, doc_data = self.db_manager.create_fdd_document(
                franchise_id=franchise_id,
                fdd_year=fdd_year,
                s3_bucket=self.s3_manager.bucket_name,
                s3_key=s3_key,
                origin_filename=file_path.name,
                md5_checksum=md5_checksum,
                status="uploaded"
            )
            
            if not doc_success or not doc_data:
                logger.error(f"Failed to create FDD document record for: {file_path}")
                # Clean up the uploaded file
                self.s3_manager.delete_file(s3_key)
                return False, None
                
            logger.info(
                f"Successfully uploaded FDD document for {franchise_name}, "
                f"year {fdd_year}, document ID: {doc_data['id']}"
            )
            
            return True, doc_data
        except Exception as e:
            logger.error(f"Error uploading FDD document: {str(e)}")
            return False, None

    def upload_analysis_file(
        self,
        fdd_document_id: str,
        analysis_data: Union[Dict[str, Any], str],
        file_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Upload an analysis file for an FDD document.
        
        Args:
            fdd_document_id: UUID of the associated FDD document.
            analysis_data: Analysis data (dict or string) to upload.
            file_type: Type of the analysis file.
            metadata: Optional metadata about the analysis file.
            
        Returns:
            Tuple[bool, Optional[Dict]]: (Success status, Analysis file data or None)
        """
        try:
            # Get the FDD document
            fdd_document = self.db_manager.get_fdd_document(fdd_document_id)
            if not fdd_document:
                logger.error(f"FDD document not found: {fdd_document_id}")
                return False, None
                
            # Get the franchise
            franchise = self.db_manager.get_franchise(fdd_document["franchise_id"])
            if not franchise:
                logger.error(f"Franchise not found: {fdd_document['franchise_id']}")
                return False, None
                
            # Extract document UUID from S3 key
            # Format: fdd_documents/<franchise_name>/<fdd_year>/<document_uuid>/document.pdf
            parts = fdd_document["s3_key"].split("/")
            document_uuid = parts[-2]
            
            # Generate S3 key for the analysis file
            s3_key = self.s3_manager.generate_analysis_s3_key(
                franchise["franchise_name"], 
                fdd_document["fdd_year"], 
                document_uuid,
                file_type
            )
            
            # Prepare the data
            if isinstance(analysis_data, dict):
                data_to_upload = json.dumps(analysis_data, indent=2)
                content_type = "application/json"
            else:
                data_to_upload = analysis_data
                # Use plain text for non-JSON data
                content_type = "text/plain"
            
            # Upload the data to S3
            upload_success = self.s3_manager.upload_data(
                data_to_upload,
                s3_key,
                content_type=content_type
            )
            
            if not upload_success:
                logger.error(f"Failed to upload analysis file to S3: {file_type}")
                return False, None
            
            # Ensure bucket name is not None before passing
            assert self.s3_manager.bucket_name is not None, "S3 bucket name should be set after initialization"
                
            # Create the analysis file record in the database
            file_success, file_data = self.db_manager.create_analysis_file(
                fdd_document_id=fdd_document_id,
                file_type=file_type,
                s3_bucket=self.s3_manager.bucket_name,
                s3_key=s3_key,
                metadata=metadata
            )
            
            if not file_success or not file_data:
                logger.error(f"Failed to create analysis file record for: {file_type}")
                # Clean up the uploaded file
                self.s3_manager.delete_file(s3_key)
                return False, None
                
            logger.info(
                f"Successfully uploaded analysis file {file_type} "
                f"for FDD document: {fdd_document_id}"
            )
            
            return True, file_data
        except Exception as e:
            logger.error(f"Error uploading analysis file: {str(e)}")
            return False, None

    def download_fdd_document(
        self,
        fdd_document_id: str,
        output_dir: Union[str, Path] = None #type: ignore
    ) -> Optional[Path]:
        """
        Download an FDD document.
        
        Args:
            fdd_document_id: UUID of the FDD document to download.
            output_dir: Optional directory to save the file to (defaults to temp dir).
            
        Returns:
            Optional[Path]: Path to the downloaded file or None if download failed.
        """
        try:
            # Get the FDD document
            fdd_document = self.db_manager.get_fdd_document(fdd_document_id)
            if not fdd_document:
                logger.error(f"FDD document not found: {fdd_document_id}")
                return None
                
            # Determine output directory
            resolved_output_dir: Path
            if output_dir:
                resolved_output_dir = Path(output_dir)
                os.makedirs(resolved_output_dir, exist_ok=True)
            else:
                resolved_output_dir = Path(tempfile.gettempdir())
                
            # Determine output filename (use original filename if available)
            if fdd_document.get("origin_filename"):
                filename = fdd_document["origin_filename"]
            else:
                # Extract a simple name from S3 key
                parts = fdd_document["s3_key"].split("/")
                filename = f"fdd_document_{parts[-2]}.pdf"
                
            output_file = resolved_output_dir / filename
            
            # Download the file
            download_success = self.s3_manager.download_file(
                fdd_document["s3_key"],
                output_file
            )
            
            if not download_success:
                logger.error(f"Failed to download FDD document: {fdd_document_id}")
                return None
                
            logger.info(f"Downloaded FDD document to: {output_file}")
            return output_file
        except Exception as e:
            logger.error(f"Error downloading FDD document: {str(e)}")
            return None

    def download_analysis_file(
        self,
        fdd_document_id: str,
        file_type: str,
        output_dir: Union[str, Path] = None, #type: ignore
        as_text: bool = True
    ) -> Optional[Union[Path, Dict[str, Any], str]]:
        """
        Download an analysis file.
        
        Args:
            fdd_document_id: UUID of the associated FDD document.
            file_type: Type of the analysis file to download.
            output_dir: Optional directory to save the file to (defaults to temp dir).
            as_text: If True, return file content instead of file path.
            
        Returns:
            Optional[Union[Path, Dict, str]]: 
                - If as_text=False: Path to the downloaded file
                - If as_text=True and JSON: Parsed JSON data
                - If as_text=True and not JSON: File content as string
                - None if download failed
        """
        try:
            # Get the analysis file
            analysis_file = self.db_manager.get_analysis_file_by_type(fdd_document_id, file_type)
            if not analysis_file:
                logger.error(
                    f"Analysis file of type {file_type} not found "
                    f"for FDD document: {fdd_document_id}"
                )
                return None
                
            # If just want the content, get it directly
            if as_text:
                content = self.s3_manager.get_file_content(analysis_file["s3_key"])
                if not content:
                    logger.error(f"Failed to get content from: {analysis_file['s3_key']}")
                    return None
                    
                # If it's a JSON file, parse it
                if file_type.endswith("_json") or analysis_file["s3_key"].endswith(".json"):
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError:
                        # Return as string if not valid JSON
                        logger.warning(f"Analysis file {analysis_file['s3_key']} is not valid JSON, returning as text.")
                        return content
                else:
                    return content
            
            # Determine output directory
            resolved_output_dir: Path
            if output_dir:
                resolved_output_dir = Path(output_dir)
                os.makedirs(resolved_output_dir, exist_ok=True)
            else:
                resolved_output_dir = Path(tempfile.gettempdir())
                
            # Determine output filename
            # Use the s3 key's last part as a base for the filename
            filename_base = analysis_file["s3_key"].split("/")[-1]
            output_file = resolved_output_dir / filename_base
            
            # Download the file
            download_success = self.s3_manager.download_file(
                analysis_file["s3_key"],
                output_file
            )
            
            if not download_success:
                logger.error(f"Failed to download analysis file: {analysis_file['s3_key']}")
                return None
                
            logger.info(f"Downloaded analysis file to: {output_file}")
            return output_file
        except Exception as e:
            logger.error(f"Error downloading analysis file: {str(e)}")
            return None

    def get_fdd_with_all_files(self, fdd_document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get an FDD document with all its analysis files.
        
        Args:
            fdd_document_id: UUID of the FDD document.
            
        Returns:
            Optional[Dict]: Dictionary with FDD document data, franchise data, and analysis files.
        """
        try:
            # Get the FDD document
            fdd_document = self.db_manager.get_fdd_document(fdd_document_id)
            if not fdd_document:
                logger.error(f"FDD document not found: {fdd_document_id}")
                return None
                
            # Get the franchise
            franchise = self.db_manager.get_franchise(fdd_document["franchise_id"])
            if not franchise:
                logger.error(f"Franchise not found: {fdd_document['franchise_id']}")
                return None
                
            # Get all analysis files
            analysis_files = self.db_manager.get_analysis_files(fdd_document_id)
            
            return {
                "fdd_document": fdd_document,
                "franchise": franchise,
                "analysis_files": analysis_files
            }
        except Exception as e:
            logger.error(f"Error getting FDD with all files: {str(e)}")
            return None

    def delete_fdd_document_and_files(self, fdd_document_id: str) -> bool:
        """
        Delete an FDD document and all its files from both S3 and the database.
        
        Args:
            fdd_document_id: UUID of the FDD document.
            
        Returns:
            bool: True if deletion was successful, False otherwise.
        """
        try:
            # Get the FDD document
            fdd_document = self.db_manager.get_fdd_document(fdd_document_id)
            if not fdd_document:
                logger.error(f"FDD document not found: {fdd_document_id}")
                return False
                
            # Extract folder prefix from S3 key
            # Format: fdd_documents/<franchise_name>/<fdd_year>/<document_uuid>/document.pdf
            parts = fdd_document["s3_key"].split("/")
            folder_prefix = "/".join(parts[:-1])
            
            # Delete all files in the folder from S3
            s3_delete_success = self.s3_manager.delete_folder(folder_prefix)
            if not s3_delete_success:
                logger.error(f"Failed to delete S3 folder: {folder_prefix}")
                # Continue with database deletion anyway
                
            # Delete the FDD document from the database (this will cascade to analysis files)
            db_delete_success = self.db_manager.delete_fdd_document(fdd_document_id)
            if not db_delete_success:
                logger.error(f"Failed to delete FDD document from database: {fdd_document_id}")
                return False
                
            logger.info(f"Successfully deleted FDD document and files: {fdd_document_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting FDD document and files: {str(e)}")
            return False


def demo():
    """Demo function to show basic usage of the system."""
    try:
        # Initialize the manager
        manager = FDDManager()
        
        # Create a temporary PDF file for testing
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_file.write(b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Contents 4 0 R/Resources<<>>>>endobj\n4 0 obj<</Length 10>>stream\nHello, FDD\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000010 00000 n\n0000000056 00000 n\n0000000111 00000 n\n0000000212 00000 n\ntrailer<</Size 5/Root 1 0 R>>\nstartxref\n295\n%%EOF")
            temp_pdf_path = temp_file.name
        
        # 1. Upload an FDD document
        franchise_name = "MINERU"
        fdd_year = 2024
        print(f"\n1. Uploading FDD document for {franchise_name}, year {fdd_year}...")
        
        success, fdd_document = manager.upload_fdd_document(
            temp_pdf_path,
            franchise_name,
            fdd_year
        )
        
        if not success or not fdd_document:
            print("Failed to upload FDD document")
            return
            
        fdd_document_id = fdd_document["id"]
        print(f"Uploaded FDD document with ID: {fdd_document_id}")
        
        # 2. Upload some analysis files
        print("\n2. Uploading analysis files...")
        
        # Huridoc JSON
        huridoc_data = {
            "version": "1.0",
            "pages": [
                {
                    "page_num": 1,
                    "width": 612,
                    "height": 792,
                    "elements": [
                        {
                            "type": "text",
                            "text": "Sample FDD Document",
                            "x": 100,
                            "y": 700,
                            "width": 400,
                            "height": 20
                        }
                    ]
                }
            ]
        }
        
        success, huridoc_file = manager.upload_analysis_file(
            fdd_document_id,
            huridoc_data,
            "huridoc_json",
            metadata={"pages_count": 1, "elements_count": 1}
        )
        
        if not success:
            print("Failed to upload huridoc_json file")
        else:
            # Check if huridoc_file is not None before accessing its key
            if huridoc_file:
                print(f"Uploaded huridoc_json file with ID: {huridoc_file['id']}")
            else:
                print("huridoc_json upload returned None, cannot get ID.")
        
        # Header extraction JSON
        headers_data = {
            "headers": [
                {
                    "level": 1,
                    "text": "FRANCHISE DISCLOSURE DOCUMENT",
                    "page": 1
                },
                {
                    "level": 2,
                    "text": "ITEM 1: THE FRANCHISOR",
                    "page": 2
                }
            ]
        }
        
        success, headers_file = manager.upload_analysis_file(
            fdd_document_id,
            headers_data,
            "header_extraction",
            metadata={"headers_count": 2}
        )
        
        if not success:
            print("Failed to upload header_extraction file")
        else:
            # Check if headers_file is not None before accessing its key
            if headers_file:
                print(f"Uploaded header_extraction file with ID: {headers_file['id']}")
            else:
                print("header_extraction upload returned None, cannot get ID.")
        
        # Sample markdown text
        markdown_text = """# FRANCHISE DISCLOSURE DOCUMENT

## ITEM 1: THE FRANCHISOR

This is a sample FDD document content.

## ITEM 2: BUSINESS EXPERIENCE

Information about business experience would be here.
"""
        
        success, markdown_file = manager.upload_analysis_file(
            fdd_document_id,
            markdown_text,
            "full_text",
            metadata={"format": "markdown", "word_count": 30}
        )
        
        if not success:
            print("Failed to upload full_text file")
        else:
            # Check if markdown_file is not None before accessing its key
            if markdown_file:
                print(f"Uploaded full_text file with ID: {markdown_file['id']}")
            else:
                print("full_text upload returned None, cannot get ID.")
        
        # 3. Get FDD with all analysis files
        print("\n3. Getting FDD with all analysis files...")
        
        fdd_data = manager.get_fdd_with_all_files(fdd_document_id)
        if not fdd_data:
            print("Failed to get FDD data")
        else:
            print(f"FDD Document: {fdd_data['fdd_document']['id']}")
            print(f"Franchise: {fdd_data['franchise']['franchise_name']}")
            print(f"Analysis Files Count: {len(fdd_data['analysis_files'])}")
            
            for file in fdd_data['analysis_files']:
                print(f"  - {file['file_type']}: {file['s3_key']}")
        
        # 4. Download an analysis file as content
        print("\n4. Downloading an analysis file (header_extraction)...")
        
        headers_content = manager.download_analysis_file(
            fdd_document_id,
            "header_extraction",
            as_text=True
        )
        
        if not headers_content:
            print("Failed to download header_extraction file")
        else:
            print("Header Extraction Content:")
            if isinstance(headers_content, dict):
                print(json.dumps(headers_content, indent=2)[:200] + "...")
            else:
                # Ensure headers_content is a string before slicing
                if isinstance(headers_content, str):
                    print(headers_content[:200] + "...")
                else:
                    # Handle the case where it might be Path or None unexpectedly
                    print(f"Downloaded content is not text: {type(headers_content)}")
        
        # 5. Clean up
        print("\n5. Cleaning up...")
        
        success = manager.delete_fdd_document_and_files(fdd_document_id)
        if success:
            print(f"Successfully deleted FDD document and all files: {fdd_document_id}")
        else:
            print(f"Failed to completely delete FDD document: {fdd_document_id}")
        
        # Remove the temporary PDF file
        os.unlink(temp_pdf_path)
        print(f"Removed temporary PDF file: {temp_pdf_path}")
        
        print("\nDemo completed successfully!")
    
    except Exception as e:
        print(f"Error in demo: {str(e)}")


if __name__ == "__main__":
    # Call the demo function directly or provide other default behavior
    # For example, just run the demo:
    demo()
    # Or leave it empty if the script is only meant to be imported:
    # pass 
