"""
Schema definitions for Gemini API structured output.

This module defines the schemas used for structured output from the Gemini API.
Only using types directly supported by Gemini API: int, float, bool, str, list[Type], dict[str, Type]
"""

from typing import Dict, List, Any, TypedDict, Optional

# Define schema types using TypedDict and supported primitive types
class AccountInfoDict(TypedDict):
    account_number: str
    account_holder_name: str

class StatementPeriodDict(TypedDict):
    statement_period_start_date: str  # Date as string in format YYYY-MM-DD
    statement_period_end_date: str    # Date as string in format YYYY-MM-DD

class StatementSummaryDict(TypedDict):
    beginning_market_value: float
    ending_market_value: float
    change_in_market_value: float
    net_contributions_withdrawals_period: float
    beginning_cash_balance: float
    ending_cash_balance: float

class TaxSummaryDataDict(TypedDict):
    total_dividends_period: float
    total_dividends_ytd: float
    total_taxable_interest_period: float
    total_taxable_interest_ytd: float
    total_tax_exempt_interest_period: float
    total_tax_exempt_interest_ytd: float
    total_realized_gain_loss_period: float
    total_realized_gain_loss_ytd: float
    total_realized_st_gain_loss_period: float
    total_realized_st_gain_loss_ytd: float
    total_realized_lt_gain_loss_period: float
    total_realized_lt_gain_loss_ytd: float

class HoldingDataDict(TypedDict):
    security_description: str
    cusip: str
    ticker_symbol: str
    quantity: float
    market_price: float
    market_value: float
    adjusted_cost_basis: float
    unrealized_gain_loss: float
    unrealized_gain_loss_term: str    # 'Short', 'Long', 'Mixed', or None
    estimated_annual_income: float
    current_yield: float
    accrued_interest: float
    coupon_rate: float
    maturity_date: str  # Date as string in format YYYY-MM-DD

class TransactionDataDict(TypedDict):
    transaction_date: str  # Date as string in format YYYY-MM-DD
    settlement_date: str   # Date as string in format YYYY-MM-DD
    transaction_type: str
    security_description: str
    cusip: str
    ticker_symbol: str
    quantity: float
    price_per_unit: float
    net_amount: float
    realized_gain_loss: float
    realized_gain_loss_term: str  # 'Short', 'Long', 'Mixed', or None
    description_notes: str

# Schema for the entire statement data
class StatementDataDict(TypedDict):
    institution_name: str
    account_info: AccountInfoDict
    statement_period: StatementPeriodDict
    statement_summary: StatementSummaryDict
    tax_summary: TaxSummaryDataDict
    holdings: List[HoldingDataDict]
    transactions: List[TransactionDataDict]

# Export a simplified schema definition for direct use with Gemini API
# This is the format that Gemini expects for the response_schema parameter
StatementData = {
    "type": "OBJECT",
    "properties": {
        "institution_name": {"type": "STRING"},
        "account_info": {
            "type": "OBJECT",
            "properties": {
                "account_number": {"type": "STRING"},
                "account_holder_name": {"type": "STRING"}
            }
        },
        "statement_period": {
            "type": "OBJECT",
            "properties": {
                "statement_period_start_date": {"type": "STRING"},
                "statement_period_end_date": {"type": "STRING"}
            }
        },
        "statement_summary": {
            "type": "OBJECT",
            "properties": {
                "beginning_market_value": {"type": "NUMBER"},
                "ending_market_value": {"type": "NUMBER"},
                "change_in_market_value": {"type": "NUMBER"},
                "net_contributions_withdrawals_period": {"type": "NUMBER"},
                "beginning_cash_balance": {"type": "NUMBER"},
                "ending_cash_balance": {"type": "NUMBER"}
            }
        },
        "tax_summary": {
            "type": "OBJECT",
            "properties": {
                "total_dividends_period": {"type": "NUMBER"},
                "total_dividends_ytd": {"type": "NUMBER"},
                "total_taxable_interest_period": {"type": "NUMBER"},
                "total_taxable_interest_ytd": {"type": "NUMBER"},
                "total_tax_exempt_interest_period": {"type": "NUMBER"},
                "total_tax_exempt_interest_ytd": {"type": "NUMBER"},
                "total_realized_gain_loss_period": {"type": "NUMBER"},
                "total_realized_gain_loss_ytd": {"type": "NUMBER"},
                "total_realized_st_gain_loss_period": {"type": "NUMBER"},
                "total_realized_st_gain_loss_ytd": {"type": "NUMBER"},
                "total_realized_lt_gain_loss_period": {"type": "NUMBER"},
                "total_realized_lt_gain_loss_ytd": {"type": "NUMBER"}
            }
        },
        "holdings": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "security_description": {"type": "STRING"},
                    "cusip": {"type": "STRING"},
                    "ticker_symbol": {"type": "STRING"},
                    "quantity": {"type": "NUMBER"},
                    "market_price": {"type": "NUMBER"},
                    "market_value": {"type": "NUMBER"},
                    "adjusted_cost_basis": {"type": "NUMBER"},
                    "unrealized_gain_loss": {"type": "NUMBER"},
                    "unrealized_gain_loss_term": {"type": "STRING"},
                    "estimated_annual_income": {"type": "NUMBER"},
                    "current_yield": {"type": "NUMBER"},
                    "accrued_interest": {"type": "NUMBER"},
                    "coupon_rate": {"type": "NUMBER"},
                    "maturity_date": {"type": "STRING"}
                }
            }
        },
        "transactions": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "transaction_date": {"type": "STRING"},
                    "settlement_date": {"type": "STRING"},
                    "transaction_type": {"type": "STRING"},
                    "security_description": {"type": "STRING"},
                    "cusip": {"type": "STRING"},
                    "ticker_symbol": {"type": "STRING"},
                    "quantity": {"type": "NUMBER"},
                    "price_per_unit": {"type": "NUMBER"},
                    "net_amount": {"type": "NUMBER"},
                    "realized_gain_loss": {"type": "NUMBER"},
                    "realized_gain_loss_term": {"type": "STRING"},
                    "description_notes": {"type": "STRING"}
                }
            }
        }
    }
} 