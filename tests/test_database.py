"""
Unit tests for database functionality.

This module contains tests for the database interface and models.
"""

import os
import unittest
import tempfile
from pathlib import Path
from datetime import datetime, date

from app.config import Config
from app.utils.database import DatabaseInterface
from app.models.db_models import (
    Institution, Account, Statement, 
    TransactionType, Security, Transaction
)

class TestDatabase(unittest.TestCase):
    """Test database operations."""

    def setUp(self):
        """Set up test database."""
        # Create temporary database file
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        
        # Override database path in config
        self.original_db_path = Config.DB_PATH
        Config.DB_PATH = self.temp_db.name
        
        # Reset database connection
        DatabaseInterface._engine = None
        DatabaseInterface._session_factory = None
        
        # Create tables
        DatabaseInterface.create_tables()
    
    def tearDown(self):
        """Clean up after tests."""
        # Close database connection
        if DatabaseInterface._engine:
            DatabaseInterface._engine.dispose()
        
        # Delete temporary database file
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
        
        # Restore original database path
        Config.DB_PATH = self.original_db_path
    
    def test_create_and_get_institution(self):
        """Test creating and retrieving an institution."""
        # Create institution
        institution = Institution(institution_name="Test Bank")
        saved_institution = DatabaseInterface.add(institution)
        
        # Verify saved data
        self.assertIsNotNone(saved_institution.institution_id)
        self.assertEqual(saved_institution.institution_name, "Test Bank")
        
        # Retrieve institution
        retrieved = DatabaseInterface.get_by_id(Institution, saved_institution.institution_id)
        self.assertEqual(retrieved.institution_name, "Test Bank")
    
    def test_create_and_query_account(self):
        """Test creating and querying an account."""
        # Create institution
        institution = Institution(institution_name="Test Bank")
        saved_institution = DatabaseInterface.add(institution)
        
        # Create account
        account = Account(
            institution_id=saved_institution.institution_id,
            account_number="12345",
            account_holder_name="John Doe"
        )
        saved_account = DatabaseInterface.add(account)
        
        # Verify saved data
        self.assertIsNotNone(saved_account.account_id)
        self.assertEqual(saved_account.account_number, "12345")
        
        # Query account
        accounts = DatabaseInterface.query(
            Account, 
            institution_id=saved_institution.institution_id,
            account_number="12345"
        )
        self.assertEqual(len(accounts), 1)
        self.assertEqual(accounts[0].account_holder_name, "John Doe")
    
    def test_create_statement_with_relationships(self):
        """Test creating a statement with related records."""
        # Create institution
        institution = Institution(institution_name="Test Bank")
        saved_institution = DatabaseInterface.add(institution)
        
        # Create account
        account = Account(
            institution_id=saved_institution.institution_id,
            account_number="12345",
            account_holder_name="John Doe"
        )
        saved_account = DatabaseInterface.add(account)
        
        # Create statement
        statement = Statement(
            account_id=saved_account.account_id,
            statement_period_start_date=date(2023, 1, 1),
            statement_period_end_date=date(2023, 1, 31),
            beginning_market_value=10000.0,
            ending_market_value=10500.0,
            change_in_market_value=500.0
        )
        saved_statement = DatabaseInterface.add(statement)
        
        # Verify saved data
        self.assertIsNotNone(saved_statement.statement_id)
        
        # Verify relationships
        with DatabaseInterface.get_session() as session:
            stmt = session.get(Statement, saved_statement.statement_id)
            self.assertEqual(stmt.account.account_holder_name, "John Doe")
            self.assertEqual(stmt.account.institution.institution_name, "Test Bank")


if __name__ == "__main__":
    unittest.main() 