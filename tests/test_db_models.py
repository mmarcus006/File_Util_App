"""
Tests for the database models.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.models.db_models import Base, Institution, Account

class TestDatabaseModels:
    """Test case for database models."""
    
    @pytest.fixture
    def db_session(self) -> Session:
        """Create an in-memory SQLite database for testing."""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        yield session
        session.close()
    
    def test_institution_model(self, db_session: Session):
        """Test the Institution model."""
        # Create an institution
        institution = Institution(institution_name="Test Institution")
        db_session.add(institution)
        db_session.commit()
        
        # Query the institution
        institution_from_db = db_session.query(Institution).filter_by(institution_name="Test Institution").first()
        
        # Check that it was created correctly
        assert institution_from_db is not None
        assert institution_from_db.institution_name == "Test Institution"
    
    def test_account_model(self, db_session: Session):
        """Test the Account model."""
        # Create an institution
        institution = Institution(institution_name="Test Institution")
        db_session.add(institution)
        db_session.commit()
        
        # Create an account
        account = Account(
            institution_id=institution.institution_id,
            account_number="12345",
            account_holder_name="Test User"
        )
        db_session.add(account)
        db_session.commit()
        
        # Query the account
        account_from_db = db_session.query(Account).filter_by(account_number="12345").first()
        
        # Check that it was created correctly
        assert account_from_db is not None
        assert account_from_db.account_number == "12345"
        assert account_from_db.account_holder_name == "Test User"
        assert account_from_db.institution_id == institution.institution_id 