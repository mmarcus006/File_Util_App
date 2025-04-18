"""Schema definitions for FDD data extraction."""

from typing import Optional, List
from pydantic import BaseModel, Field

class FranchiseeContact(BaseModel):
    """Contact information for a franchisee reference"""
    name: Optional[str] = Field(None, description="Name of the franchisee contact")
    location: Optional[str] = Field(None, description="Location/address of the franchisee")
    phone: Optional[str] = Field(None, description="Phone number of the franchisee")
    email: Optional[str] = Field(None, description="Email address of the franchisee")

class FranchiseInfo(BaseModel):
    """Information about the franchise business"""
    brand_name: Optional[str] = Field(None, description="Brand name of the franchise")
    legal_name: Optional[str] = Field(None, description="Legal name of the franchisor company")
    parent_company: Optional[str] = Field(None, description="Parent company name, if applicable")
    address: Optional[str] = Field(None, description="Headquarters address")
    city: Optional[str] = Field(None, description="City of headquarters")
    state: Optional[str] = Field(None, description="State of headquarters")
    zip_code: Optional[str] = Field(None, description="ZIP code of headquarters")
    website: Optional[str] = Field(None, description="Company website URL")
    phone: Optional[str] = Field(None, description="Company phone number")
    email: Optional[str] = Field(None, description="Company contact email")
    founded_year: Optional[int] = Field(None, description="Year the company was founded")
    franchising_since: Optional[int] = Field(None, description="Year franchising operations began")
    business_description: Optional[str] = Field(None, description="Brief description of the business")

class FDDInfo(BaseModel):
    """Information about the FDD document itself"""
    fiscal_year: Optional[int] = Field(None, description="Fiscal year the FDD covers")
    issue_date: Optional[str] = Field(None, description="Date the FDD was issued (YYYY-MM-DD format if possible)")
    amendment_date: Optional[str] = Field(None, description="Date the FDD was amended (YYYY-MM-DD format if possible)")
    

class ExtractionOutput(BaseModel):
    """Primary output schema for FDD Introduction extraction"""
    franchise: FranchiseInfo = Field(..., description="Information about the franchise")
    fdd: FDDInfo = Field(..., description="Information about the FDD document")
    franchisee_contacts: Optional[List[FranchiseeContact]] = Field(None, description="List of franchisee contacts if mentioned")
    raw_text_sample: Optional[str] = Field(None, description="A sample of the raw text that was processed (for verification)") 