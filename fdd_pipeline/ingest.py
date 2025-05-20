"""
PDF ingestion functionality for FDD Pipeline
"""

import os
import hashlib
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import logging
from datetime import datetime
import sys

# Add parent directory to path for direct script execution
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fdd_pipeline.models import FileInfo, FDDDocument, DocumentStatus
from fdd_pipeline.storage.cloud_storage import R2Storage
from fdd_pipeline.storage.baserow import BaserowClient
from fdd_pipeline.config import DATA_DIR

logger = logging.getLogger(__name__)

def compute_file_hash(file_path: str) -> str:
    """
    Compute an MD5 hash of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Hex digest of the file hash
    """
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def generate_document_id() -> str:
    """Generate a unique document ID."""
    return str(uuid.uuid4())

def ingest_pdf(file_path: str, table_id: int) -> Optional[FDDDocument]:
    """
    Ingest a PDF file into the system.
    
    Args:
        file_path: Path to the PDF file
        table_id: Baserow table ID for documents
        
    Returns:
        FDDDocument object if successful, None otherwise
    """
    try:
        # Ensure file exists
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return None
            
        # Compute file hash and size
        file_hash = compute_file_hash(file_path)
        file_size = os.path.getsize(file_path)
        
        # Check if file already exists in system
        baserow = BaserowClient()
        existing_docs = baserow.query_records(
            table_id=table_id,
            filters=[{"field": "file_hash", "type": "equal", "value": file_hash}]
        )
        
        if existing_docs:
            logger.info(f"File already exists in system: {file_path}")
            doc_id = existing_docs[0].get("id")
            # Could return existing document info here
            return None
            
        # Generate document ID and prepare document record
        document_id = generate_document_id()
        filename = os.path.basename(file_path)
        
        # Upload to cloud storage
        r2 = R2Storage()
        remote_key = f"pdfs/{document_id}/{filename}"
        if not r2.upload_file(file_path, remote_key):
            logger.error(f"Failed to upload file to R2: {file_path}")
            return None
            
        # Create file info
        file_info = FileInfo(
            file_id=document_id,
            filename=filename,
            file_path=remote_key,
            file_size=file_size,
            file_hash=file_hash,
            upload_timestamp=datetime.utcnow()
        )
        
        # Create document record
        document = FDDDocument(
            document_id=document_id,
            file_info=file_info,
            status=DocumentStatus(status="pending", current_stage="ingested")
        )
        
        # Create record in Baserow
        record = {
            "document_id": document_id,
            "file_path": remote_key,
            "file_hash": file_hash,
            "filename": filename,
            "file_size": file_size,
            "status": "pending",
            "current_stage": "ingested"
        }
        
        result = baserow.create_record(table_id, record)
        if not result:
            logger.error(f"Failed to create record in Baserow for {file_path}")
            # Could delete the uploaded file here
            return None
            
        logger.info(f"Successfully ingested document: {filename} (ID: {document_id})")
        return document
        
    except Exception as e:
        logger.error(f"Error ingesting PDF {file_path}: {str(e)}")
        return None

def scan_directory(directory: str, table_id: int) -> List[FDDDocument]:
    """
    Scan a directory for PDF files and ingest them.
    
    Args:
        directory: Directory to scan
        table_id: Baserow table ID for documents
        
    Returns:
        List of successfully ingested FDDDocument objects
    """
    ingested_docs = []
    
    try:
        # Check if directory exists
        if not os.path.exists(directory):
            logger.error(f"Directory not found: {directory}")
            return []
            
        # Find all PDF files
        pdf_files = []
        for root, _, files in os.walk(directory):
            for file in files:
                if file.lower().endswith(".pdf"):
                    pdf_files.append(os.path.join(root, file))
                    
        logger.info(f"Found {len(pdf_files)} PDF files in {directory}")
        
        # Ingest each file
        for file_path in pdf_files:
            document = ingest_pdf(file_path, table_id)
            if document:
                ingested_docs.append(document)
                
        logger.info(f"Successfully ingested {len(ingested_docs)} documents")
        return ingested_docs
        
    except Exception as e:
        logger.error(f"Error scanning directory {directory}: {str(e)}")
        return ingested_docs 