"""
Database operations module for the FDD document management system.
Contains CRUD operations for franchises, FDD documents, and analysis files.
"""

import uuid
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Union

from supabase.client import Client

logger = logging.getLogger(__name__)


class FDDDatabaseManager:
    """Manages database operations for the FDD document management system."""

    def __init__(self, supabase_client: Client):
        """
        Initialize the FDDDatabaseManager with a Supabase client.
        
        Args:
            supabase_client: Initialized Supabase client.
        """
        self.supabase = supabase_client

    # Franchise Operations
    def create_franchise(self, franchise_name: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Create a new franchise record.
        
        Args:
            franchise_name: Name of the franchise.
            
        Returns:
            Tuple[bool, Optional[Dict]]: (Success status, Created franchise data or None)
        """
        try:
            data = {
                "id": str(uuid.uuid4()),
                "franchise_name": franchise_name
            }
            
            response = self.supabase.table("franchises").insert(data).execute()
            
            if len(response.data) > 0:
                logger.info(f"Created franchise: {franchise_name} with ID: {data['id']}")
                return True, response.data[0]
            else:
                logger.error(f"Failed to create franchise: {franchise_name}")
                return False, None
        except Exception as e:
            logger.error(f"Error creating franchise: {str(e)}")
            return False, None

    def get_franchise(self, franchise_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a franchise by ID.
        
        Args:
            franchise_id: UUID of the franchise.
            
        Returns:
            Optional[Dict]: Franchise data or None if not found.
        """
        try:
            response = (
                self.supabase
                .table("franchises")
                .select("*")
                .eq("id", franchise_id)
                .execute()
            )
            
            if len(response.data) > 0:
                return response.data[0]
            else:
                logger.warning(f"Franchise not found with ID: {franchise_id}")
                return None
        except Exception as e:
            logger.error(f"Error getting franchise: {str(e)}")
            return None

    def get_franchises(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get a list of franchises with pagination.
        
        Args:
            limit: Maximum number of franchises to return.
            offset: Number of franchises to skip.
            
        Returns:
            List[Dict]: List of franchise data dictionaries.
        """
        try:
            response = (
                self.supabase
                .table("franchises")
                .select("*")
                .order("franchise_name")
                .range(offset, offset + limit - 1)
                .execute()
            )
            
            return response.data
        except Exception as e:
            logger.error(f"Error getting franchises: {str(e)}")
            return []

    def update_franchise(self, franchise_id: str, franchise_name: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Update a franchise's name.
        
        Args:
            franchise_id: UUID of the franchise.
            franchise_name: New name for the franchise.
            
        Returns:
            Tuple[bool, Optional[Dict]]: (Success status, Updated franchise data or None)
        """
        try:
            data = {
                "franchise_name": franchise_name,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            response = (
                self.supabase
                .table("franchises")
                .update(data)
                .eq("id", franchise_id)
                .execute()
            )
            
            if len(response.data) > 0:
                logger.info(f"Updated franchise: {franchise_id} with new name: {franchise_name}")
                return True, response.data[0]
            else:
                logger.warning(f"Franchise not found or not updated: {franchise_id}")
                return False, None
        except Exception as e:
            logger.error(f"Error updating franchise: {str(e)}")
            return False, None

    def delete_franchise(self, franchise_id: str) -> bool:
        """
        Delete a franchise by ID (cascades to FDD documents and analysis files).
        
        Args:
            franchise_id: UUID of the franchise to delete.
            
        Returns:
            bool: True if deletion was successful, False otherwise.
        """
        try:
            response = (
                self.supabase
                .table("franchises")
                .delete()
                .eq("id", franchise_id)
                .execute()
            )
            
            if len(response.data) > 0:
                logger.info(f"Deleted franchise: {franchise_id}")
                return True
            else:
                logger.warning(f"Franchise not found or not deleted: {franchise_id}")
                return False
        except Exception as e:
            logger.error(f"Error deleting franchise: {str(e)}")
            return False

    # FDD Document Operations
    def create_fdd_document(
        self,
        franchise_id: str,
        fdd_year: int,
        s3_bucket: str,
        s3_key: str,
        origin_filename: Optional[str] = None,
        md5_checksum: Optional[str] = None,
        status: str = "pending-analysis"
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Create a new FDD document record.
        
        Args:
            franchise_id: UUID of the franchise.
            fdd_year: Year of the FDD document.
            s3_bucket: S3 bucket name where the document is stored.
            s3_key: S3 key (path) where the document is stored.
            origin_filename: Original filename of the document.
            md5_checksum: MD5 checksum of the document for integrity checks.
            status: Processing status of the document.
            
        Returns:
            Tuple[bool, Optional[Dict]]: (Success status, Created document data or None)
        """
        try:
            data = {
                "id": str(uuid.uuid4()),
                "franchise_id": franchise_id,
                "fdd_year": fdd_year,
                "s3_bucket": s3_bucket,
                "s3_key": s3_key,
                "origin_filename": origin_filename,
                "md5_checksum": md5_checksum,
                "status": status,
                "upload_date": datetime.utcnow().isoformat()
            }
            
            response = self.supabase.table("fdd_documents").insert(data).execute()
            
            if len(response.data) > 0:
                logger.info(f"Created FDD document for franchise: {franchise_id}, year: {fdd_year}")
                return True, response.data[0]
            else:
                logger.error(f"Failed to create FDD document for franchise: {franchise_id}")
                return False, None
        except Exception as e:
            logger.error(f"Error creating FDD document: {str(e)}")
            return False, None

    def get_fdd_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get an FDD document by ID.
        
        Args:
            document_id: UUID of the FDD document.
            
        Returns:
            Optional[Dict]: FDD document data or None if not found.
        """
        try:
            response = (
                self.supabase
                .table("fdd_documents")
                .select("*")
                .eq("id", document_id)
                .execute()
            )
            
            if len(response.data) > 0:
                return response.data[0]
            else:
                logger.warning(f"FDD document not found with ID: {document_id}")
                return None
        except Exception as e:
            logger.error(f"Error getting FDD document: {str(e)}")
            return None

    def get_fdd_documents_for_franchise(
        self, 
        franchise_id: str, 
        limit: int = 100, 
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get FDD documents for a specific franchise with pagination.
        
        Args:
            franchise_id: UUID of the franchise.
            limit: Maximum number of documents to return.
            offset: Number of documents to skip.
            
        Returns:
            List[Dict]: List of FDD document data dictionaries.
        """
        try:
            response = (
                self.supabase
                .table("fdd_documents")
                .select("*")
                .eq("franchise_id", franchise_id)
                .order("fdd_year", desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )
            
            return response.data
        except Exception as e:
            logger.error(f"Error getting FDD documents for franchise: {str(e)}")
            return []

    def update_fdd_document_status(self, document_id: str, status: str) -> bool:
        """
        Update the status of an FDD document.
        
        Args:
            document_id: UUID of the FDD document.
            status: New status for the document.
            
        Returns:
            bool: True if update was successful, False otherwise.
        """
        try:
            data = {
                "status": status,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            response = (
                self.supabase
                .table("fdd_documents")
                .update(data)
                .eq("id", document_id)
                .execute()
            )
            
            if len(response.data) > 0:
                logger.info(f"Updated FDD document status: {document_id} to {status}")
                return True
            else:
                logger.warning(f"FDD document not found or not updated: {document_id}")
                return False
        except Exception as e:
            logger.error(f"Error updating FDD document status: {str(e)}")
            return False

    def delete_fdd_document(self, document_id: str) -> bool:
        """
        Delete an FDD document by ID (cascades to analysis files).
        
        Args:
            document_id: UUID of the FDD document to delete.
            
        Returns:
            bool: True if deletion was successful, False otherwise.
        """
        try:
            response = (
                self.supabase
                .table("fdd_documents")
                .delete()
                .eq("id", document_id)
                .execute()
            )
            
            if len(response.data) > 0:
                logger.info(f"Deleted FDD document: {document_id}")
                return True
            else:
                logger.warning(f"FDD document not found or not deleted: {document_id}")
                return False
        except Exception as e:
            logger.error(f"Error deleting FDD document: {str(e)}")
            return False

    # Analysis File Operations
    def create_analysis_file(
        self,
        fdd_document_id: str,
        file_type: str,
        s3_bucket: str,
        s3_key: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Create a new analysis file record.
        
        Args:
            fdd_document_id: UUID of the associated FDD document.
            file_type: Type of the analysis file (e.g. 'huridoc_json', 'header_extraction').
            s3_bucket: S3 bucket name where the file is stored.
            s3_key: S3 key (path) where the file is stored.
            metadata: Optional JSON metadata about the file.
            
        Returns:
            Tuple[bool, Optional[Dict]]: (Success status, Created file data or None)
        """
        try:
            if metadata is None:
                metadata = {}
                
            data = {
                "id": str(uuid.uuid4()),
                "fdd_document_id": fdd_document_id,
                "file_type": file_type,
                "s3_bucket": s3_bucket,
                "s3_key": s3_key,
                "metadata": metadata,
                "uploaded_at": datetime.utcnow().isoformat()
            }
            
            response = self.supabase.table("analysis_files").insert(data).execute()
            
            if len(response.data) > 0:
                logger.info(f"Created analysis file of type: {file_type} for FDD document: {fdd_document_id}")
                return True, response.data[0]
            else:
                logger.error(f"Failed to create analysis file for FDD document: {fdd_document_id}")
                return False, None
        except Exception as e:
            logger.error(f"Error creating analysis file: {str(e)}")
            return False, None

    def get_analysis_files(self, fdd_document_id: str) -> List[Dict[str, Any]]:
        """
        Get all analysis files for a specific FDD document.
        
        Args:
            fdd_document_id: UUID of the FDD document.
            
        Returns:
            List[Dict]: List of analysis file data dictionaries.
        """
        try:
            response = (
                self.supabase
                .table("analysis_files")
                .select("*")
                .eq("fdd_document_id", fdd_document_id)
                .execute()
            )
            
            return response.data
        except Exception as e:
            logger.error(f"Error getting analysis files: {str(e)}")
            return []

    def get_analysis_file_by_type(
        self, 
        fdd_document_id: str, 
        file_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific type of analysis file for an FDD document.
        
        Args:
            fdd_document_id: UUID of the FDD document.
            file_type: Type of the analysis file to retrieve.
            
        Returns:
            Optional[Dict]: Analysis file data or None if not found.
        """
        try:
            response = (
                self.supabase
                .table("analysis_files")
                .select("*")
                .eq("fdd_document_id", fdd_document_id)
                .eq("file_type", file_type)
                .execute()
            )
            
            if len(response.data) > 0:
                return response.data[0]
            else:
                logger.warning(
                    f"Analysis file of type {file_type} not found for FDD document: {fdd_document_id}"
                )
                return None
        except Exception as e:
            logger.error(f"Error getting analysis file by type: {str(e)}")
            return None

    def update_analysis_file_metadata(
        self, 
        file_id: str, 
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Update the metadata of an analysis file.
        
        Args:
            file_id: UUID of the analysis file.
            metadata: New metadata for the file.
            
        Returns:
            bool: True if update was successful, False otherwise.
        """
        try:
            data = {
                "metadata": metadata,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            response = (
                self.supabase
                .table("analysis_files")
                .update(data)
                .eq("id", file_id)
                .execute()
            )
            
            if len(response.data) > 0:
                logger.info(f"Updated analysis file metadata: {file_id}")
                return True
            else:
                logger.warning(f"Analysis file not found or not updated: {file_id}")
                return False
        except Exception as e:
            logger.error(f"Error updating analysis file metadata: {str(e)}")
            return False

    def delete_analysis_file(self, file_id: str) -> bool:
        """
        Delete an analysis file by ID.
        
        Args:
            file_id: UUID of the analysis file to delete.
            
        Returns:
            bool: True if deletion was successful, False otherwise.
        """
        try:
            response = (
                self.supabase
                .table("analysis_files")
                .delete()
                .eq("id", file_id)
                .execute()
            )
            
            if len(response.data) > 0:
                logger.info(f"Deleted analysis file: {file_id}")
                return True
            else:
                logger.warning(f"Analysis file not found or not deleted: {file_id}")
                return False
        except Exception as e:
            logger.error(f"Error deleting analysis file: {str(e)}")
            return False

    # Combined Operations
    def get_fdd_with_analysis_files(self, document_id: str) -> Dict[str, Any]:
        """
        Get an FDD document with all its associated analysis files.
        
        Args:
            document_id: UUID of the FDD document.
            
        Returns:
            Dict: Dictionary with FDD document data and associated analysis files.
        """
        fdd_document = self.get_fdd_document(document_id)
        analysis_files = self.get_analysis_files(document_id)
        
        return {
            "fdd_document": fdd_document,
            "analysis_files": analysis_files
        }

    def search_fdd_documents(
        self, 
        search_term: str = None, #type: ignore
        franchise_id: str = None, #type: ignore
        fdd_year: int = None, #type: ignore
        limit: int = 100, 
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Search for FDD documents by different criteria.
        
        Args:
            search_term: Optional search term for the origin filename.
            franchise_id: Optional franchise ID to filter by.
            fdd_year: Optional FDD year to filter by.
            limit: Maximum number of documents to return.
            offset: Number of documents to skip.
            
        Returns:
            List[Dict]: List of matching FDD document data dictionaries.
        """
        try:
            query = self.supabase.table("fdd_documents").select("*")
            
            if franchise_id:
                query = query.eq("franchise_id", franchise_id)
                
            if fdd_year:
                query = query.eq("fdd_year", fdd_year)
                
            if search_term:
                query = query.ilike("origin_filename", f"%{search_term}%")
                
            # Order and paginate results
            query = query.order("fdd_year", desc=True).range(offset, offset + limit - 1)
            
            response = query.execute()
            return response.data
        except Exception as e:
            logger.error(f"Error searching FDD documents: {str(e)}")
            return []
