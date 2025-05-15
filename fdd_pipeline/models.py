"""
Pydantic data models for FDD Pipeline
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class FileInfo(BaseModel):
    """Information about a file in the system."""
    file_id: str
    filename: str
    file_path: str
    file_size: Optional[int] = None
    file_hash: Optional[str] = None
    upload_timestamp: Optional[datetime] = None

class DocumentStatus(BaseModel):
    """Status tracking for a document in processing."""
    status: str = "pending"  # pending, processing, completed, error
    current_stage: Optional[str] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    error_message: Optional[str] = None
    completion_percentage: float = 0.0
    
class SectionHeader(BaseModel):
    """Information about an identified FDD section header."""
    item_number: int
    header_text: str
    start_page: int
    end_page: Optional[int] = None
    page_count: Optional[int] = None
    confidence_score: float = 0.0
    
class ExhibitHeader(BaseModel):
    """Information about an identified FDD exhibit."""
    exhibit_letter: str
    title: str
    start_page: int
    end_page: Optional[int] = None
    page_count: Optional[int] = None

class FDDDocument(BaseModel):
    """Core tracking model for an FDD document."""
    document_id: str
    file_info: FileInfo
    status: DocumentStatus = Field(default_factory=DocumentStatus)
    sections: List[SectionHeader] = []
    exhibits: List[ExhibitHeader] = []
    layout_json_path: Optional[str] = None
    extracted_data_path: Optional[str] = None
    franchise_name: Optional[str] = None
    publication_year: Optional[int] = None
    processing_metadata: Dict[str, Any] = {}
    
# Add item-specific models for extraction
class FDDItem1(BaseModel):
    """Item 1: Franchisor Information"""
    brand_name: str
    legal_name: Optional[str] = None
    parent_company: Optional[str] = None
    address: Optional[str] = None
    phone_number: Optional[str] = None
    website: Optional[str] = None
    state_of_incorporation: Optional[str] = None
    predecessors: Optional[List[str]] = None
    affiliates: Optional[List[str]] = None