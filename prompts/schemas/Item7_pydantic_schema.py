"""
item7_initial_investment.py

Pydantic models that mirror the JSON schema for **Estimated Initial Investment**
(Item 7 of an FDD).  They preserve every required field, supply human-readable
descriptions, and forbid unexpected keys.
"""

from __future__ import annotations

from typing import List, Optional, Union

from pydantic import BaseModel, Field, ConfigDict

# --------------------------------------------------------------------------- #
# Type aliases
# --------------------------------------------------------------------------- #

Amount = Union[float, str, None]  # number if parsable, otherwise the raw string


# --------------------------------------------------------------------------- #
# Models
# --------------------------------------------------------------------------- #

class InvestmentRow(BaseModel):
    """A single line in an Estimated Initial Investment table."""
    model_config = ConfigDict(extra="ignore")

    expenditure_type: str = Field(
        ...,
        description="Type of cost or fee (e.g., 'Initial Franchise Fee', 'Signage', 'Total'). All footnote markers should be stripped."
    )
    amount_low: Optional[Amount] = Field(
        None,
        description=(
            "Low estimate for the expenditure.  Prefer a numeric value; fall back "
            "to the raw string if parsing fails.  For one-off amounts this also "
            "holds the only value.  Currency symbols and thousands separators "
            "should already be removed."
        ),
    )
    amount_high: Optional[Amount] = Field(
        None,
        description=(
            "High estimate for the expenditure.  Same rules as **amount_low**.  "
            "For single-value rows this repeats that value."
        ),
    )
    method_of_payment: Optional[str] = Field(
        None,
        description='How payment is made (e.g., "Lump Sum", "As Incurred").',
    )
    when_due: Optional[str] = Field(
        None,
        description='Timing of the payment (e.g., "Upon execution of Agreement", "Before Opening").',
    )
    paid_to: Optional[str] = Field(
        None,
        description='Recipient of the payment (e.g., "Payable to us", "Vendors").',
    )


class InvestmentTable(BaseModel):
    """One distinct Estimated Initial Investment table (Standard, Conversion, Multi-Unit, …)."""
    model_config = ConfigDict(extra="ignore")

    title: Optional[str] = Field(
        None,
        description='Optional specific title (e.g., "Standard Franchise", "Conversion Model").',
    )
    columns: List[str] = Field(
        default_factory=lambda: [
            "expenditure_type",
            "amount_low",
            "amount_high",
            "method_of_payment",
            "when_due",
            "paid_to",
        ],
        description=(
            "Exact column order for every **rows** element.  These names are "
            "standardized and *must* stay in this sequence."
        ),
    )
    rows: List[InvestmentRow] = Field(
        ...,
        description=(
            "All data rows for this table in the same order as **columns**.  "
            "Include any interpreted header rows and the grand-total row."
        ),
    )


class Item7InitialInvestment(BaseModel):
    """
    Root model that aggregates every Initial-Investment table extracted from
    Item 7 of an FDD.
    """
    model_config = ConfigDict(extra="ignore")

    investment_tables: List[InvestmentTable] = Field(
        ...,
        description=(
            "Every distinct Initial-Investment table found (e.g., Standard, "
            "Conversion, Multi-Unit).  Order should follow the PDF appearance."
        ),
    )