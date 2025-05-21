"""
Pydantic data models for FDD Pipeline
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class ProcessingStageEnum(str, Enum):
    PENDING = "Pending"
    LAYOUT_DONE = "LayoutDone"
    HEADERS_EXTRACTED = "HeadersExtracted"
    SECTIONING = "Sectioning"
    LLM_PROCESSING = "LLMProcessing"
    EXTRACTED = "Extracted"
    COMPLETE = "Complete"
    COMPLETE_WITH_WARNINGS = "CompleteWithWarnings"
    ERROR = "Error"

class DocumentStatus(BaseModel):
    """Status tracking for a document in processing."""
    current_stage: Optional[ProcessingStageEnum] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    error_message: Optional[str] = None
    
class SectionHeader(BaseModel):
    """Information about an identified FDD section header."""
    item_number: int
    header_text: str
    start_page: int
    end_page: Optional[int] = None
    page_count: Optional[int] = None
    confidence_score: float = 0.0

class FDDDocument(BaseModel):
    """Core tracking model for an FDD document."""
    document_id: str
    file_name: str
    file_hash: str
    status: DocumentStatus = Field(default_factory=DocumentStatus)
    sections: List[SectionHeader] = []
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
    parent_company: Optional[str] = Field(
        default=None, 
        description="Name of the parent company that owns or controls the franchisor entity"
    )
    address: Optional[str] = Field(None, description="Headquarters address")
    city: Optional[str] = Field(None, description="City of headquarters")
    state: Optional[str] = Field(None, description="State of headquarters")
    zip_code: Optional[str] = Field(None, description="ZIP code of headquarters")
    founded_year: Optional[int] = Field(None, description="Year the company was founded")
    franchising_since: Optional[int] = Field(None, description="Year franchising operations began")
    business_description: Optional[str] = Field(None, description="Brief description of the business")
    email:Optional[str] = Field(
        default=None, 
        description="Primary contact email address for the franchisor"
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