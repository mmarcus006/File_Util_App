## 4. Pydantic Models (`models.py`)

```python
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Union
from datetime import date

# --- Helper Types ---
TermType = Union[str, None] # Literal['Short', 'Long', 'Mixed', None] would be stricter

# --- Nested Models ---

class AccountInfo(BaseModel):
    account_number: str
    account_holder_name: str

class StatementPeriod(BaseModel):
    statement_period_start_date: date
    statement_period_end_date: date

class StatementSummary(BaseModel):
    beginning_market_value: float
    ending_market_value: float
    change_in_market_value: Optional[float] = None
    net_contributions_withdrawals_period: Optional[float] = None
    beginning_cash_balance: Optional[float] = None # Combined cash/MMF
    ending_cash_balance: Optional[float] = None   # Combined cash/MMF

class TaxSummaryData(BaseModel):
    total_dividends_period: Optional[float] = None
    total_dividends_ytd: Optional[float] = None
    total_taxable_interest_period: Optional[float] = None
    total_taxable_interest_ytd: Optional[float] = None
    total_tax_exempt_interest_period: Optional[float] = None
    total_tax_exempt_interest_ytd: Optional[float] = None
    total_realized_gain_loss_period: Optional[float] = None
    total_realized_gain_loss_ytd: Optional[float] = None
    total_realized_st_gain_loss_period: Optional[float] = None
    total_realized_st_gain_loss_ytd: Optional[float] = None
    total_realized_lt_gain_loss_period: Optional[float] = None
    total_realized_lt_gain_loss_ytd: Optional[float] = None

class HoldingData(BaseModel):
    security_description: str
    cusip: Optional[str] = None
    ticker_symbol: Optional[str] = None
    # asset_class: Optional[str] = None # Let Gemini infer if possible, map later
    quantity: float
    market_price: float
    market_value: float
    adjusted_cost_basis: Optional[float] = None
    unrealized_gain_loss: Optional[float] = None
    unrealized_gain_loss_term: TermType = None
    estimated_annual_income: Optional[float] = None
    current_yield: Optional[float] = None # Store as decimal, e.g., 1.19 for 1.19%
    accrued_interest: Optional[float] = None
    coupon_rate: Optional[float] = None # Store as decimal, e.g., 5.0 for 5.0%
    maturity_date: Optional[date] = None

class TransactionData(BaseModel):
    transaction_date: date
    settlement_date: Optional[date] = None
    transaction_type: str # e.g., 'Buy', 'Sell', 'Dividend', 'Interest', 'Withdrawal', 'Deposit'
    security_description: Optional[str] = None # Null for cash only
    ticker_symbol: Optional[str] = None # Extract if available with description
    cusip: Optional[str] = None # Extract if available with description
    quantity: Optional[float] = None
    price_per_unit: Optional[float] = None
    net_amount: float # Positive for credit, negative for debit
    realized_gain_loss: Optional[float] = None # If available per line item
    realized_gain_loss_term: TermType = None # If available per line item
    description_notes: Optional[str] = None # Capture extra details

    @field_validator('net_amount')
    def check_net_amount_sign(cls, v):
        # Basic check, more specific mapping needed in parsing logic based on type
        return v

# --- Top-Level Model for Gemini Output ---

class StatementData(BaseModel):
    institution_name: str # JPM, MS, GS
    account_info: AccountInfo
    statement_period: StatementPeriod
    statement_summary: StatementSummary
    tax_summary: Optional[TaxSummaryData] = None
    holdings: List[HoldingData] = []
    transactions: List[TransactionData] = []

```
*(Note: SQLAlchemy models (`db_models.py`) would mirror the SQL schema using `DeclarativeBase`, `Mapped`, `mapped_column`, etc. They are omitted here for brevity but would be straightforward to create based on the SQL schema and Pydantic models.)*

---