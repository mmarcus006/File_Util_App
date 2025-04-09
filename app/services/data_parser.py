"""
Data Parser for Bank Statement Analyzer.

This module handles validation and parsing of the data extracted by the LLM.
It converts the raw JSON into CSV files.
"""

import json
import logging
import csv
import os
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List, Union, cast, TypedDict
from datetime import date, datetime

# Import the TypedDict classes to define expected structure
from app.models.models import (
    StatementDataDict, AccountInfoDict, StatementPeriodDict, StatementSummaryDict,
    HoldingDataDict, TransactionDataDict, TaxSummaryDataDict
)
# Remove database imports
# from app.models.db_models import (
#     Institution, Account, Statement, TaxSummary,
#     Security, Holding, TransactionType, Transaction
# )
# from app.utils.database import DatabaseInterface # Use the centralized DB interface
from app.utils.error_handler import BankStatementError #, DatabaseError # Import custom errors

# Configure logging
logger = logging.getLogger(__name__)

class DataParser:
    """Class for parsing and validating extracted data, and saving to CSV files."""

    # Define the mapping between data sections and their expected TypedDicts
    # This helps in determining the headers for CSV files
    SECTION_SCHEMAS: Dict[str, type] = {
        "account_info": AccountInfoDict,
        "statement_period": StatementPeriodDict,
        "statement_summary": StatementSummaryDict,
        "tax_summary": TaxSummaryDataDict,
        "holdings": HoldingDataDict,
        "transactions": TransactionDataDict,
    }

    @staticmethod
    def _normalize_holding_data(holding: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize holding data to match our model expectation."""
        # Map field names to our expected model
        field_mappings = {
            'market_price': 'market_price',
            'market_value': 'market_value',
            'cost_basis': 'adjusted_cost_basis',
            'unrealized_gain_loss': 'unrealized_gain_loss',
            'unrealized_gain_loss_term': 'unrealized_gain_loss_term',
            'estimated_annual_income': 'estimated_annual_income',
            'yield_percent': 'current_yield',
            'yield_percentage': 'current_yield',
            'accrued_interest': 'accrued_interest'
        }
        
        # Copy holding to avoid modifying the original
        normalized_holding = holding.copy()
        
        # Apply mappings
        for src, dst in field_mappings.items():
            if src in normalized_holding and normalized_holding.get(src) is not None and not normalized_holding.get(dst):
                normalized_holding[dst] = normalized_holding[src]
                
        return normalized_holding

    @staticmethod
    def _preprocess_data_dict(data_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Helper function to pre-process the data dictionary before validation."""
        processed_dict = data_dict.copy()
        
        # Map fields from LLM extraction format to our expected model format
        
        # Handle institution_name from account_information
        if 'account_information' in processed_dict and 'institution_name' in processed_dict['account_information']:
            processed_dict['institution_name'] = processed_dict['account_information']['institution_name']
        
        # Map account_information to account_info if needed
        if 'account_information' in processed_dict and not processed_dict.get('account_info'):
            processed_dict['account_info'] = {
                'account_number': processed_dict['account_information'].get('account_number', 'UNKNOWN'),
                'account_holder_name': processed_dict['account_information'].get('account_holder_name', 'UNKNOWN')
            }
            
        # Map summary to statement_summary if needed
        if 'summary' in processed_dict and not processed_dict.get('statement_summary'):
            processed_dict['statement_summary'] = processed_dict['summary']
            
        # Fix statement_period format if needed
        if 'statement_period' in processed_dict:
            period = processed_dict['statement_period']
            if 'start_date' in period and not period.get('statement_period_start_date'):
                period['statement_period_start_date'] = period['start_date']
            if 'end_date' in period and not period.get('statement_period_end_date'):
                period['statement_period_end_date'] = period['end_date']
            if 'statement_period_start' in period and not period.get('statement_period_start_date'):
                period['statement_period_start_date'] = period['statement_period_start']
            if 'statement_period_end' in period and not period.get('statement_period_end_date'):
                period['statement_period_end_date'] = period['statement_period_end']
        
        # Map tax_summary fields to expected format if needed
        if 'tax_summary' in processed_dict:
            tax = processed_dict['tax_summary']
            # Map tax fields if they use different names
            field_mappings = {
                'dividends_period': 'total_dividends_period',
                'dividends_ytd': 'total_dividends_ytd',
                'interest_period': 'total_taxable_interest_period',
                'interest_income_period': 'total_taxable_interest_period',
                'interest_ytd': 'total_taxable_interest_ytd',
                'interest_income_ytd': 'total_taxable_interest_ytd',
                'tax_exempt_interest_period': 'total_tax_exempt_interest_period',
                'tax_exempt_interest_ytd': 'total_tax_exempt_interest_ytd',
                'realized_gain_loss_total_period': 'total_realized_gain_loss_period',
                'realized_gain_loss_total_ytd': 'total_realized_gain_loss_ytd',
                'realized_gain_loss_short_term_period': 'total_realized_st_gain_loss_period',
                'realized_gain_loss_short_term_ytd': 'total_realized_st_gain_loss_ytd',
                'realized_gain_loss_long_term_period': 'total_realized_lt_gain_loss_period',
                'realized_gain_loss_long_term_ytd': 'total_realized_lt_gain_loss_ytd'
            }
            for src, dst in field_mappings.items():
                if src in tax and tax.get(src) is not None and not tax.get(dst):
                    tax[dst] = tax[src]
        
        # Normalize holdings data
        if 'holdings' in processed_dict and isinstance(processed_dict['holdings'], list):
            processed_dict['holdings'] = [DataParser._normalize_holding_data(holding) for holding in processed_dict['holdings']]
            
        # Fix transaction fields if needed
        if 'transactions' in processed_dict and isinstance(processed_dict['transactions'], list):
            for transaction in processed_dict['transactions']:
                if isinstance(transaction, dict):
                    # Convert 'date' to 'transaction_date' if transaction_date is missing
                    if 'date' in transaction and not transaction.get('transaction_date'):
                        transaction['transaction_date'] = transaction['date']
                    # Convert 'price' to 'price_per_unit' if missing
                    if 'price' in transaction and not transaction.get('price_per_unit'):
                        transaction['price_per_unit'] = transaction['price']
                    # Convert 'price_per_share' to 'price_per_unit' if missing
                    if 'price_per_share' in transaction and not transaction.get('price_per_unit'):
                        transaction['price_per_unit'] = transaction['price_per_share']
        
        # Create default empty objects for required nested structures if they are missing or None
        if processed_dict.get('account_info') is None:
            processed_dict['account_info'] = {'account_number': 'UNKNOWN', 'account_holder_name': 'UNKNOWN'}
            
        if processed_dict.get('statement_period') is None:
            processed_dict['statement_period'] = {}
            
        if processed_dict.get('statement_summary') is None:
            processed_dict['statement_summary'] = {}
        
        # Ensure holdings and transactions lists exist
        if 'holdings' not in processed_dict:
            processed_dict['holdings'] = []
            
        if 'transactions' not in processed_dict:
            processed_dict['transactions'] = []
            
        return processed_dict

    @staticmethod
    def parse_and_validate_dict(data_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Pre-process dictionary and validate basic structure.
        
        Args:
            data_dict: Raw dictionary extracted by the LLM (or loaded from JSON)
            
        Returns:
            Processed dictionary
            
        Raises:
            BankStatementError: If validation fails
        """
        try:
            # Check if it's a completely empty dictionary
            if not data_dict:
                raise ValueError("Empty data dictionary provided")
            
            # Verify model compatibility and log warnings
            is_compatible, warnings, _ = DataParser.verify_model_compatibility(data_dict)
            
            if warnings:
                logger.info("Data structure compatibility check results:")
                for warning in warnings:
                    logger.info(f"  - {warning}")
                
                if not is_compatible:
                    logger.warning("Data structure has critical incompatibilities that may prevent parsing")
            
            # Check for critical required elements in any format
            has_institution = ('institution_name' in data_dict or 
                             ('account_information' in data_dict and 'institution_name' in data_dict['account_information']))
            
            if not has_institution:
                raise ValueError("Missing institution information. Expected 'institution_name' at root level or inside 'account_information'")
            
            # Pre-process the dictionary to normalize structure
            processed_dict = DataParser._preprocess_data_dict(data_dict)
                
            return processed_dict
        except ValueError as e:
            logger.error(f"Validation error: {str(e)}")
            raise BankStatementError(
                message=f"Data validation failed: {str(e)}",
                error_code="DATA_VALIDATION_ERROR"
            )
        except Exception as e:
            logger.error(f"Unexpected error during dictionary validation: {str(e)}")
            raise BankStatementError(
                message=f"Unexpected error during dictionary validation: {str(e)}",
                error_code="PARSING_VALIDATION_ERROR"
            )

    @staticmethod
    def parse_and_validate_json(json_data: str) -> Dict[str, Any]:
        """
        Parse JSON string, pre-process, and validate basic structure.
        
        Args:
            json_data: Raw JSON string extracted by the LLM
            
        Returns:
            Processed dictionary
            
        Raises:
            BankStatementError: If JSON parsing or validation fails
        """
        try:
            # Parse JSON to dictionary
            data_dict = json.loads(json_data)
            # Reuse the dictionary validation logic
            return DataParser.parse_and_validate_dict(data_dict)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {str(e)}")
            # Include snippet of problematic JSON in details
            error_pos = e.pos
            snippet_start = max(0, error_pos - 50)
            snippet_end = min(len(json_data), error_pos + 50)
            snippet = json_data[snippet_start:snippet_end]
            
            raise BankStatementError(
                message=f"Invalid JSON format: {str(e)}",
                error_code="JSON_PARSE_ERROR",
                details={"error_position": error_pos, "context": snippet}
            )
        # Catch validation errors raised by parse_and_validate_dict
        except BankStatementError: 
            raise # Re-raise the specific BankStatementError from validation
        except Exception as e: # Catch other unexpected errors during JSON parsing
            logger.error(f"Unexpected error during JSON parsing: {str(e)}")
            raise BankStatementError(
                message=f"Unexpected error during JSON parsing: {str(e)}",
                error_code="JSON_PARSE_ERROR"
            )

    @classmethod
    def save_data_to_csv(cls, statement_data: Dict[str, Any], pdf_file_path: str) -> str:
        """
        Save the extracted and validated statement data into separate CSV files.

        Args:
            statement_data: Validated statement data dictionary.
            pdf_file_path: The path to the original PDF file.

        Returns:
            The path to the directory where CSV files were saved.

        Raises:
            BankStatementError: If there's an error creating the directory or writing files.
        """
        try:
            pdf_path = Path(pdf_file_path)
            # Create a directory name based on the PDF filename (without extension)
            output_dir_name = f"{pdf_path.stem}_extracted_data"
            # Place this directory inside the same folder as the PDF
            output_dir_path = pdf_path.parent / output_dir_name
            output_dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Saving extracted data to directory: {output_dir_path}")

            # Save institution name and general info to a simple text or JSON file
            info_file_path = output_dir_path / "statement_info.json"
            general_info = {
                "institution_name": statement_data.get("institution_name", "Unknown"),
                # You could add other top-level non-tabular info here if needed
            }
            with open(info_file_path, 'w', encoding='utf-8') as f:
                json.dump(general_info, f, indent=2)

            # Iterate through the main sections and save them as CSV
            for section_name, schema_type in cls.SECTION_SCHEMAS.items():
                section_data = statement_data.get(section_name)

                if not section_data:
                    logger.debug(f"Section '{section_name}' is empty or missing, skipping CSV generation.")
                    continue

                # Determine CSV file path
                csv_file_path = output_dir_path / f"{section_name}.csv"

                # Get headers from the TypedDict definition
                # We need an instance or the __annotations__
                headers = list(schema_type.__annotations__.keys())

                # Ensure section_data is a list for writing rows, even if it's a single dict
                if isinstance(section_data, dict):
                    data_list = [section_data]
                elif isinstance(section_data, list):
                    data_list = section_data
                else:
                    logger.warning(f"Unexpected data type for section '{section_name}': {type(section_data)}. Skipping.")
                    continue

                if not data_list: # Skip empty lists
                    logger.debug(f"Section '{section_name}' list is empty, skipping CSV generation.")
                    continue

                try:
                    with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
                        writer = csv.DictWriter(csvfile, fieldnames=headers, extrasaction='ignore') # Ignore extra fields not in headers
                        writer.writeheader()
                        for row_dict in data_list:
                            # Ensure all header fields are present in the row, defaulting to empty string if not
                            row_to_write = {header: row_dict.get(header, '') for header in headers}
                            writer.writerow(row_to_write)
                    logger.info(f"Successfully saved {section_name} to {csv_file_path}")
                except IOError as e:
                    logger.error(f"Failed to write CSV file {csv_file_path}: {str(e)}")
                    raise BankStatementError(
                        message=f"Failed to write CSV file for section '{section_name}'",
                        error_code="FILE_WRITE_ERROR",
                        details={"file_path": str(csv_file_path), "original_error": str(e)}
                    )
                except Exception as e:
                    logger.error(f"Unexpected error writing CSV for section '{section_name}': {str(e)}")
                    raise BankStatementError(
                        message=f"Unexpected error writing CSV for section '{section_name}'",
                        error_code="CSV_WRITE_ERROR",
                        details={"file_path": str(csv_file_path), "original_error": str(e)}
                    )

            return str(output_dir_path)

        except OSError as e:
            logger.error(f"Failed to create output directory {output_dir_path}: {str(e)}")
            raise BankStatementError(
                message="Failed to create output directory for extracted data",
                error_code="DIRECTORY_CREATION_ERROR",
                details={"path": str(output_dir_path), "original_error": str(e)}
            )
        except Exception as e:
            logger.error(f"Unexpected error during CSV saving process: {str(e)}", exc_info=True)
            raise BankStatementError(
                message="Unexpected error saving extracted data to CSV",
                error_code="CSV_SAVE_ERROR",
                details={"original_error": str(e)}
            )

    @staticmethod
    def verify_model_compatibility(data: Dict[str, Any]) -> Tuple[bool, List[str], Dict[str, Any]]:
        """
        Verify compatibility between received data and our expected model.
        
        Args:
            data: The data to check for compatibility
            
        Returns:
            Tuple of (is_compatible, warnings, transformed_data)
            where:
                is_compatible: Boolean indicating if data can be transformed to match our model
                warnings: List of warning messages for fields that needed transformation
                transformed_data: Transformed data that matches our model structure
        """
        warnings = []
        transformed = data.copy()
        
        # Check and transform key fields
        
        # 1. Institution name
        if 'institution_name' not in data:
            if 'account_information' in data and 'institution_name' in data['account_information']:
                transformed['institution_name'] = data['account_information']['institution_name']
                warnings.append("institution_name was moved from account_information to root level")
            else:
                warnings.append("Missing institution_name field")
                transformed['institution_name'] = "Unknown Institution"
        
        # 2. Account info
        if 'account_info' not in data:
            if 'account_information' in data:
                transformed['account_info'] = {
                    'account_number': data['account_information'].get('account_number', 'UNKNOWN'),
                    'account_holder_name': data['account_information'].get('account_holder_name', 'UNKNOWN')
                }
                warnings.append("account_information was transformed to account_info")
            else:
                warnings.append("Missing account_info or account_information")
                transformed['account_info'] = {'account_number': 'UNKNOWN', 'account_holder_name': 'UNKNOWN'}
        
        # 3. Statement period
        if 'statement_period' in data:
            period = data['statement_period']
            transformed_period = {}
            
            # Check for start date field variants
            for field in ['statement_period_start_date', 'start_date', 'statement_period_start']:
                if field in period:
                    transformed_period['statement_period_start_date'] = period[field]
                    if field != 'statement_period_start_date':
                        warnings.append(f"Field {field} was mapped to statement_period_start_date")
                    break
            
            # Check for end date field variants
            for field in ['statement_period_end_date', 'end_date', 'statement_period_end']:
                if field in period:
                    transformed_period['statement_period_end_date'] = period[field]
                    if field != 'statement_period_end_date':
                        warnings.append(f"Field {field} was mapped to statement_period_end_date")
                    break
                    
            transformed['statement_period'] = transformed_period
        else:
            warnings.append("Missing statement_period")
            transformed['statement_period'] = {}
        
        # 4. Statement summary
        if 'statement_summary' not in data:
            if 'summary' in data:
                transformed['statement_summary'] = data['summary']
                warnings.append("summary was transformed to statement_summary")
            else:
                warnings.append("Missing statement_summary or summary")
                transformed['statement_summary'] = {}
        
        # 5. Check transaction fields for compatibility
        if 'transactions' in data and isinstance(data['transactions'], list):
            for i, transaction in enumerate(data['transactions']):
                if isinstance(transaction, dict):
                    # Check for date field
                    if 'transaction_date' not in transaction and 'date' in transaction:
                        warnings.append(f"Transaction {i}: date was mapped to transaction_date")
                    
                    # Check for price field
                    if 'price_per_unit' not in transaction:
                        if 'price' in transaction:
                            warnings.append(f"Transaction {i}: price was mapped to price_per_unit")
                        elif 'price_per_share' in transaction:
                            warnings.append(f"Transaction {i}: price_per_share was mapped to price_per_unit")
        
        # Ensure holdings and transactions lists exist, even if empty
        if 'holdings' not in transformed:
            transformed['holdings'] = []
        if 'transactions' not in transformed:
            transformed['transactions'] = []
        # Ensure other sections exist if they might be used later, even if empty dicts
        if 'account_info' not in transformed: transformed['account_info'] = {}
        if 'statement_period' not in transformed: transformed['statement_period'] = {}
        if 'statement_summary' not in transformed: transformed['statement_summary'] = {}
        if 'tax_summary' not in transformed: transformed['tax_summary'] = {}

        # Return results
        is_compatible = len(warnings) == 0 or all('mapped' in w or 'transformed' in w for w in warnings)
        
        return is_compatible, warnings, transformed 

    @staticmethod
    def diagnose_json_file(json_file_path: str) -> Dict[str, Any]:
        """
        Diagnostic method to load a JSON file and check its structure against our model.
        
        Args:
            json_file_path: Path to the JSON file to check
            
        Returns:
            Dictionary with diagnostic information
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            BankStatementError: If the JSON is invalid
        """
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                json_data = f.read()
                
            # Try to parse the JSON
            data_dict = json.loads(json_data)
            
            # Check compatibility
            is_compatible, warnings, transformed = DataParser.verify_model_compatibility(data_dict)
            
            # Create diagnostic result
            result = {
                "file_path": json_file_path,
                "is_valid_json": True,
                "is_compatible": is_compatible,
                "warnings": warnings,
                "top_level_keys": list(data_dict.keys()),
                "transformed_keys": list(transformed.keys())
            }
            
            # Check for critical fields based on TypedDicts we expect to save
            # Note: institution_name is handled separately now
            critical_sections = ["account_info", "statement_period", "statement_summary"] # Holdings/Transactions are lists, tax_summary optional
            missing_critical = [section for section in critical_sections if section not in transformed or not transformed[section]]
            if "institution_name" not in transformed:
                 missing_critical.append("institution_name")

            result["missing_critical_fields_or_sections"] = missing_critical

            # Add additional info about data
            if "holdings" in transformed:
                result["holdings_count"] = len(transformed["holdings"])
                
            if "transactions" in transformed:
                result["transactions_count"] = len(transformed["transactions"])
            
            return result
            
        except FileNotFoundError:
            raise FileNotFoundError(f"JSON file not found: {json_file_path}")
        except json.JSONDecodeError as e:
            raise BankStatementError(
                message=f"Invalid JSON format in file {json_file_path}: {str(e)}",
                error_code="JSON_PARSE_ERROR"
            ) 