from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import datetime

class FDDLayoutSectionModel(BaseModel):
    """Represents a layout section identified within an FDD PDF."""
    section_id: Optional[int] = None # Primary key, assigned by DB
    fdd_id: int = Field(..., description="The ID of the FDD this section belongs to.")
    identified_item_number: Optional[int] = Field(None, description="The ITEM number identified (1-23).")
    identified_header_text: Optional[str] = Field(None, description="The header text identified.")
    start_page: Optional[int] = Field(None, description="The starting page number of the section.")
    end_page: Optional[int] = Field(None, description="The ending page number of the section.")

class FDDLayoutExhibitModel(BaseModel):
    """Represents a layout exhibit identified within an FDD PDF."""
    exhibit_id: Optional[int] = None # Primary key, assigned by DB
    fdd_id: int = Field(..., description="The ID of the FDD this exhibit belongs to.")
    identified_exhibit_letter: Optional[str] = Field(None, description="The letter designation identified (e.g., 'A').")
    identified_title: Optional[str] = Field(None, description="The title identified.")
    start_page: Optional[int] = Field(None, description="The starting page number of the exhibit.")
    end_page: Optional[int] = Field(None, description="The ending page number of the exhibit.")

class FDDDocumentModel(BaseModel):
    """Represents a tracked FDD document and its processing state."""
    id: Optional[int] = None # Primary key, assigned by DB
    fdd_id: Optional[int] = Field(None, description="Link to the specific FDD record if matched.")
    file_hash: Optional[str] = Field(None, description="Hash of the PDF file content.")
    file_path: Optional[str] = Field(None, description="Original storage path of the document.")
    franchisor: Optional[str] = Field(None, description="Extracted or matched franchisor name.")
    issuance_date: Optional[datetime.date] = Field(None, description="The date the FDD was issued.")
    amendment_status: Optional[str] = Field(None, description="Status like 'Original' or 'Amended'.")
    amendment_date: Optional[datetime.date] = Field(None, description="Date of the amendment, if applicable.")
    processed_status: Optional[str] = Field('Pending', description="Processing status (e.g., Pending, Complete, Error).")
    docling_processed: Optional[bool] = Field(False, description="Flag indicating specific processor completion.")
    is_duplicate: Optional[bool] = Field(False, description="Flag indicating if this document is a duplicate.")
    extracted_text: Optional[str] = Field(None, description="Full extracted text content.") # Consider large text handling
    markdown_path: Optional[str] = Field(None, description="Path to the generated Markdown output.")
    json_path: Optional[str] = Field(None, description="Path to the generated JSON output.")
    html_path: Optional[str] = Field(None, description="Path to the generated HTML output.")
    created_at: Optional[datetime.datetime] = None # Assigned by DB
    updated_at: Optional[datetime.datetime] = None # Assigned by DB
    error_message: Optional[str] = Field(None, description="Error message if processing failed.")
    original_doc_id: Optional[str] = Field(None, description="Identifier from the source system/scrape.")

# You might need other models corresponding to other tables like:
# - FranchiseModel
# - FDDModel (representing the main fdd table)
# - AppUserModel
# - BlogPostModel
# etc. 