from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql import func
from pydantic import BaseModel, HttpUrl, EmailStr, Field
from typing import Optional, List
from datetime import date

Base = declarative_base()

# Pydantic Model for Item 1 JSON validation
class Item1Detail(BaseModel):
    brand_name: Optional[str] = None
    legal_name: Optional[str] = None
    parent_company: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    website: Optional[HttpUrl] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    founded_year: Optional[int] = None
    franchising_since: Optional[int] = None
    business_description: Optional[str] = None
    fdd_issue_date: Optional[date] = None
    fdd_amendment_date: Optional[date] = None

# SQLAlchemy model for item1_data table
class Item1Data(Base):
    __tablename__ = "item1_data"

    uuid = Column(Text, primary_key=True)
    item1_brand_name = Column(Text, nullable=True)
    item1_legal_name = Column(Text, nullable=True)
    item1_parent_company = Column(Text, nullable=True)
    item1_address = Column(Text, nullable=True)
    item1_city = Column(Text, nullable=True)
    item1_state = Column(Text, nullable=True)
    item1_zip_code = Column(Text, nullable=True)
    item1_website = Column(Text, nullable=True)
    item1_phone = Column(Text, nullable=True)
    item1_email = Column(Text, nullable=True)
    item1_founded_year = Column(Integer, nullable=True)
    item1_franchising_since = Column(Integer, nullable=True)
    item1_business_description = Column(Text, nullable=True)
    item1_fdd_issue_date = Column(Text, nullable=True)  # Store as ISO date string
    item1_fdd_amendment_date = Column(Text, nullable=True)  # Store as ISO date string
    review_status = Column(Text, default='pending')  # 'pending', 'approved', 'error'
    original_json_path = Column(Text)
    last_modified_timestamp = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Item1Data(uuid='{self.uuid}', brand_name='{self.item1_brand_name}', status='{self.review_status}')>"

# SQLAlchemy model for pdf_paths table
class PdfPaths(Base):
    __tablename__ = "pdf_paths"

    uuid = Column(Text, primary_key=True)
    pdf_file_path = Column(Text, nullable=False)

    def __repr__(self):
        return f"<PdfPaths(uuid='{self.uuid}', pdf_path='{self.pdf_file_path}')>"

# SQLAlchemy model for processing_errors table
class ProcessingError(Base):
    __tablename__ = "processing_errors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_path = Column(Text)
    error_message = Column(Text)
    error_timestamp = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<ProcessingError(id={self.id}, file_path='{self.file_path}', error='{self.error_message[:50]}...')>"

# Example of how to create an engine and tables (typically in db_handler.py or main)
if __name__ == '__main__':
    # This is for demonstration/testing and should not be in production like this.
    # Actual database setup will be handled by db_handler.
    engine = create_engine('sqlite:///./test_fdd_qc.db')
    Base.metadata.create_all(engine)

    # Example Pydantic usage:
    sample_data_valid = {
        "brand_name": "Test Brand",
        "legal_name": "Test Legal LLC",
        "website": "http://example.com",
        "email": "test@example.com",
        "founded_year": 2000,
        "franchising_since": 2005,
        "fdd_issue_date": "2023-01-15"
    }
    try:
        item1 = Item1Detail(**sample_data_valid)
        print("Pydantic model valid:")
        print(item1.model_dump_json(indent=2))
    except Exception as e:
        print(f"Pydantic validation error: {e}")

    sample_data_invalid_type = {
        "brand_name": "Test Brand Bad",
        "founded_year": "two thousand" # Invalid type
    }
    try:
        item1_bad = Item1Detail(**sample_data_invalid_type)
    except Exception as e:
        print(f"Pydantic validation error for invalid data: {e}") 