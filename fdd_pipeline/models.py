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
    
class Franchise(BaseModel):
    """Core model for franchise information extracted from an FDD document.
    
    Contains key identifying and operational information about the franchise as detailed
    in Item 1 and other sections of the Franchise Disclosure Document.
    """
    brand_name: str = Field(
        description="The commercial brand name or trademark of the franchise as it appears to the public for example, McDonald's Corporation would be 'McDonald's'"
    )
    legal_name: Optional[str] = Field(
        default=None, 
        description="The legal entity name of the franchisor as registered with government authorities"
    )
    parent_company: Optional[str] = Field(
        default=None, 
        description="Name of the parent company that owns or controls the franchisor entity"
    )
    address: Optional[str] = Field(
        default=None, 
        description="Principal business address of the franchisor as listed in Item 1 of the FDD"
    )
    phone_number: Optional[str] = Field(
        default=None, 
        description="Primary contact phone number for the franchisor"
    )
    website: Optional[str] = Field(
        default=None, 
        description="Official website URL for the franchise or franchisor"
    )
    issuance_date: Optional[str] = Field(
        default=None, 
        description="Date when the FDD was formally issued, typically found on the cover page"
    )
    amendment_date: Optional[str] = Field(
        default=None, 
        description="Date of the most recent amendment or update to the FDD, if applicable"
    )
    
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