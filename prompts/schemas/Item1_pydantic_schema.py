#CUSTOM SCHEMA:
from typing import Optional
from pydantic import BaseModel, Field


class FranchiseAndFDDInfo(BaseModel):
    """
    Combined schema containing both FranchiseInfo and FDDInfo.

    • Fields originating from FranchiseInfo keep their original names.
    • Fields originating from FDDInfo are prefixed with `fdd_`.
      This makes it trivial to split the data back into two objects:
      - FranchiseInfo(**data)                # ignores the fdd_* keys
      - FDDInfo(**{k[4:]: v for k, v in data.items() if k.startswith("fdd_")})
    """

    # ────────────────────────── FranchiseInfo fields ──────────────────────────
    brand_name: Optional[str] = Field(
        None, description="Brand name of the franchise"
    )
    legal_name: Optional[str] = Field(
        None, description="Legal name of the franchisor company"
    )
    parent_company: Optional[str] = Field(
        None, description="Parent company name, if applicable"
    )
    address: Optional[str] = Field(
        None, description="Headquarters address"
    )
    city: Optional[str] = Field(
        None, description="City of headquarters"
    )
    state: Optional[str] = Field(
        None, description="State of headquarters"
    )
    zip_code: Optional[str] = Field(
        None, description="ZIP code of headquarters"
    )
    website: Optional[str] = Field(
        None, description="Company website URL"
    )
    phone: Optional[str] = Field(
        None, description="Company phone number"
    )
    email: Optional[str] = Field(
        None, description="Company contact email"
    )
    founded_year: Optional[int] = Field(
        None, description="Year the company was founded"
    )
    franchising_since: Optional[int] = Field(
        None, description="The date franchising operations began formatted as 'MM-dd-yyyy' if possible, otherwise return Year franchising operations began"
    )
    business_description: Optional[str] = Field(
        None, description="Brief description of the business, should be summarized by the LLM, not taken directly from document"
    )

    # ──────────────────────────── FDDInfo fields ─────────────────────────────
    fdd_fiscal_year: Optional[int] = Field(
        None, description="Fiscal year the FDD covers"
    )
    fdd_issue_date: Optional[str] = Field(
        None,
        description="Date the FDD was issued (YYYY‑MM‑DD format if possible)",
    )
    fdd_amendment_date: Optional[str] = Field(
        None,
        description="Date the FDD was amended (YYYY‑MM‑DD format if possible)",
    )
