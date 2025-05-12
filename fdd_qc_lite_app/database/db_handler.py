import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import List, Optional, Dict, Any
from contextlib import contextmanager

from .models import Base, Item1Data, PdfPaths, ProcessingError, Item1Detail # Assuming models.py is in the same directory

DATABASE_URL = "sqlite:///./fdd_qc_lite.db" # Default database file name

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}) # check_same_thread for SQLite with Qt
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db(db_path: Optional[str] = None):
    """Initializes the database and creates tables if they don't exist."""
    global engine, SessionLocal # Allow modification of global engine if db_path changes
    actual_db_url = DATABASE_URL
    if db_path:
        # Ensure the directory for the db_path exists
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
        actual_db_url = f"sqlite:///{db_path}"
        engine = create_engine(actual_db_url, connect_args={"check_same_thread": False})
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    Base.metadata.create_all(bind=engine)
    print(f"Database initialized and tables created at {actual_db_url}")

@contextmanager
def get_db_session() -> Session:
    """Provides a transactional scope around a series of operations."""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def add_item1_data(db: Session, uuid: str, data: Dict[str, Any], original_json_path: str, pdf_path: Optional[str] = None):
    """Adds or updates Item 1 data and its associated PDF path."""
    # Standardize keys from Item1Detail model to Item1Data model
    db_item_data = Item1Data(
        uuid=uuid,
        item1_brand_name=data.get('brand_name'),
        item1_legal_name=data.get('legal_name'),
        item1_parent_company=data.get('parent_company'),
        item1_address=data.get('address'),
        item1_city=data.get('city'),
        item1_state=data.get('state'),
        item1_zip_code=data.get('zip_code'),
        item1_website=str(data.get('website')) if data.get('website') else None,
        item1_phone=data.get('phone'),
        item1_email=str(data.get('email')) if data.get('email') else None,
        item1_founded_year=data.get('founded_year'),
        item1_franchising_since=data.get('franchising_since'),
        item1_business_description=data.get('business_description'),
        item1_fdd_issue_date=str(data.get('fdd_issue_date')) if data.get('fdd_issue_date') else None,
        item1_fdd_amendment_date=str(data.get('fdd_amendment_date')) if data.get('fdd_amendment_date') else None,
        original_json_path=original_json_path,
        review_status='pending' # Default status
    )
    db.merge(db_item_data) # Use merge to insert or update if exists

    if pdf_path:
        db_pdf_path = PdfPaths(uuid=uuid, pdf_file_path=pdf_path)
        db.merge(db_pdf_path)
    db.commit()

def get_all_item1_records_summary(db: Session) -> List[Dict[str, str]]:
    """Retrieves a list of all Item 1 UUIDs and their review status."""
    records = db.query(Item1Data.uuid, Item1Data.review_status).all()
    return [{"uuid": r.uuid, "status": r.review_status} for r in records]

def get_item1_data_by_uuid(db: Session, uuid: str) -> Optional[Item1Data]:
    """Retrieves a single Item1Data record by its UUID."""
    return db.query(Item1Data).filter(Item1Data.uuid == uuid).first()

def get_pdf_path_by_uuid(db: Session, uuid: str) -> Optional[str]:
    """Retrieves the PDF path for a given UUID."""
    pdf_record = db.query(PdfPaths.pdf_file_path).filter(PdfPaths.uuid == uuid).first()
    return pdf_record.pdf_file_path if pdf_record else None

def update_item1_data_fields(db: Session, uuid: str, data_to_update: Dict[str, Any]):
    """Updates specific fields of an Item1Data record."""
    db.query(Item1Data).filter(Item1Data.uuid == uuid).update(data_to_update)
    db.commit()

def update_item1_review_status(db: Session, uuid: str, status: str):
    """Updates the review status of an Item 1 record."""
    db.query(Item1Data).filter(Item1Data.uuid == uuid).update({"review_status": status})
    db.commit()

def get_original_json_path(db: Session, uuid: str) -> Optional[str]:
    """Retrieves the original JSON file path for a given UUID."""
    item_data = db.query(Item1Data.original_json_path).filter(Item1Data.uuid == uuid).first()
    return item_data.original_json_path if item_data else None

def log_processing_error(db: Session, file_path: str, error_message: str):
    """Logs a processing error to the database."""
    error_entry = ProcessingError(file_path=file_path, error_message=error_message)
    db.add(error_entry)
    db.commit()

def get_all_processing_errors(db: Session) -> List[ProcessingError]:
    """Retrieves all logged processing errors."""
    return db.query(ProcessingError).order_by(ProcessingError.error_timestamp.desc()).all()

def get_paths_for_uuid(db: Session, uuid: str) -> Dict[str, Optional[str]]:
    """
    Retrieves the original Item 1 JSON path and the PDF file path for a given UUID.

    Args:
        db (Session): The database session.
        uuid (str): The UUID to search for.

    Returns:
        Dict[str, Optional[str]]: A dictionary with keys 'item1_json_path' and 'pdf_path'.
                                  Values will be None if not found.
    """
    paths = {
        'item1_json_path': None,
        'pdf_path': None
    }

    item1_record = db.query(Item1Data.original_json_path).filter(Item1Data.uuid == uuid).first()
    if item1_record:
        paths['item1_json_path'] = item1_record.original_json_path
    
    pdf_record = db.query(PdfPaths.pdf_file_path).filter(PdfPaths.uuid == uuid).first()
    if pdf_record:
        paths['pdf_path'] = pdf_record.pdf_file_path
        
    return paths

# Example Usage (for testing - typically called from other modules)
if __name__ == '__main__':
    # Initialize DB (creates fdd_qc_lite.db in the current dir)
    # You might want to specify a path for testing, e.g., init_db("test_data/test.db")
    if os.path.exists("fdd_qc_lite.db"): # Simple cleanup for re-running tests
        os.remove("fdd_qc_lite.db")
    init_db() 

    # Sample data (matching Pydantic model structure)
    sample_item_data_dict = {
        "brand_name": "Sweet Treats Cafe",
        "legal_name": "Sweet Treats Global LLC",
        "parent_company": "Foodies Inc.",
        "address": "123 Main St",
        "city": "Anytown",
        "state": "CA",
        "zip_code": "90210",
        "website": "http://sweettreatscafe.com",
        "phone": "555-1234",
        "email": "contact@sweettreatscafe.com",
        "founded_year": 2010,
        "franchising_since": 2012,
        "business_description": "A cozy cafe offering a variety of sweets and beverages.",
        "fdd_issue_date": "2023-03-15", # Pydantic converts this to date, DB stores as string
        "fdd_amendment_date": None
    }
    test_uuid = "test-uuid-12345"
    test_json_path = "/path/to/test-uuid-12345_item1.json"
    test_pdf_path = "/path/to/test-uuid-12345.pdf"

    with get_db_session() as session:
        # Add data
        add_item1_data(session, test_uuid, sample_item_data_dict, test_json_path, test_pdf_path)
        print(f"Added item data for UUID: {test_uuid}")

        # Retrieve and verify
        retrieved_data = get_item1_data_by_uuid(session, test_uuid)
        retrieved_pdf_path = get_pdf_path_by_uuid(session, test_uuid)
        print(f"Retrieved item: {retrieved_data}")
        print(f"Retrieved PDF path: {retrieved_pdf_path}")
        assert retrieved_data is not None
        assert retrieved_data.item1_brand_name == "Sweet Treats Cafe"
        assert retrieved_pdf_path == test_pdf_path

        # Update status
        update_item1_review_status(session, test_uuid, "approved")
        updated_record = get_item1_data_by_uuid(session, test_uuid)
        print(f"Updated status: {updated_record.review_status if updated_record else 'Not found'}")
        assert updated_record and updated_record.review_status == "approved"

        # Update fields
        update_item1_data_fields(session, test_uuid, {"item1_city": "Newville", "item1_phone": "555-5678"})
        updated_fields_record = get_item1_data_by_uuid(session, test_uuid)
        print(f"Updated city: {updated_fields_record.item1_city if updated_fields_record else 'Not found'}")
        assert updated_fields_record and updated_fields_record.item1_city == "Newville"
        assert updated_fields_record and updated_fields_record.item1_phone == "555-5678"

        # Log an error
        log_processing_error(session, "/path/to/bad_file.json", "Failed to parse JSON.")
        errors = get_all_processing_errors(session)
        print(f"Logged errors: {errors}")
        assert len(errors) > 0

        # Get all records summary
        summary = get_all_item1_records_summary(session)
        print(f"All records summary: {summary}")
        assert any(s['uuid'] == test_uuid for s in summary)

        # Get original JSON path
        original_path = get_original_json_path(session, test_uuid)
        print(f"Original JSON path: {original_path}")
        assert original_path == test_json_path

        # Test get_paths_for_uuid
        print(f"\n--- Testing get_paths_for_uuid for {test_uuid} ---")
        retrieved_paths = get_paths_for_uuid(session, test_uuid)
        print(f"Retrieved paths: {retrieved_paths}")
        assert retrieved_paths['item1_json_path'] == test_json_path
        assert retrieved_paths['pdf_path'] == test_pdf_path

        # Test get_paths_for_uuid for a UUID that might only have one path (e.g., only PDF initially)
        test_uuid_pdf_only = "test-uuid-pdf-only-67890"
        # Add only a PDF path for this UUID for testing purposes
        pdf_only_path = "/path/to/test-uuid-pdf-only-67890.pdf"
        db_pdf_only_path = PdfPaths(uuid=test_uuid_pdf_only, pdf_file_path=pdf_only_path)
        session.merge(db_pdf_only_path)
        session.commit() # Commit this separate addition
        
        retrieved_paths_pdf_only = get_paths_for_uuid(session, test_uuid_pdf_only)
        print(f"Retrieved paths for PDF only UUID ({test_uuid_pdf_only}): {retrieved_paths_pdf_only}")
        assert retrieved_paths_pdf_only['item1_json_path'] is None
        assert retrieved_paths_pdf_only['pdf_path'] == pdf_only_path

    print("db_handler.py test operations completed.")
    # Clean up the test database file
    if os.path.exists("fdd_qc_lite.db"): 
        os.remove("fdd_qc_lite.db") 