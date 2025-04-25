from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

class FeeItem(BaseModel):
    """
    Represents a single fee listed in Item 6 of an FDD.

    Attributes:
        fee_type: The type or name of the fee.
        note_reference: Reference to an explanatory note, if applicable (Optional).
        amount: The amount or calculation method for the fee.
        due_date: When the fee is due or payment frequency.
        remarks: Additional information or context about the fee (Optional).
    """
    fee_type: str = Field(..., description="The type or name of the fee")
    note_reference: Optional[str] = Field(None, description="Reference to an explanatory note, if applicable")
    amount: str = Field(..., description="The amount or calculation method for the fee")
    due_date: str = Field(..., description="When the fee is due or payment frequency")
    remarks: Optional[str] = Field(None, description="Additional information or context about the fee")

class ExplanatoryNote(BaseModel):
    """
    Represents an explanatory note relevant to Item 6 fees.

    Attributes:
        note_number: The identifier for the note (e.g., '1', 'Note 1').
        note_text: The full text content of the explanatory note.
    """
    note_number: str = Field(..., description="The identifier for the note (e.g., '1', 'Note 1')")
    note_text: str = Field(..., description="The full text content of the explanatory note")

class FDDItem6(BaseModel):
    """
    Structure for holding extracted data from FDD Item 6 (Other Fees).
    
    Attributes:
        item_6_heading: The exact heading text for Item 6.
        introductory_text: Any introductory text preceding the fee table (Optional).
        fees: List of all fees detailed in Item 6.
        uniformity_statement: Statement about fee uniformity across franchisees, if present (Optional).
        explanatory_notes: All explanatory notes referenced in the fee table (Optional list).
    """
    item_6_heading: str = Field(..., description="The exact heading text for Item 6")
    introductory_text: Optional[str] = Field(None, description="Any introductory text preceding the fee table")
    fees: List[FeeItem] = Field(..., description="List of all fees detailed in Item 6")
    uniformity_statement: Optional[str] = Field(None, description="Statement about fee uniformity across franchisees, if present")
    explanatory_notes: Optional[List[ExplanatoryNote]] = Field(None, description="All explanatory notes referenced in the fee table")

    model_config = ConfigDict(
        json_schema_extra={"description": "Schema for parsing Item 6 (Other Fees) from a Franchise Disclosure Document (FDD), excluding Item 7."}
    )