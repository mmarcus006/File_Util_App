"""Handles SQLite database interactions for storing extracted emails."""

import logging
import os
from datetime import datetime
from typing import Dict, Any

# SQLAlchemy imports
from sqlalchemy import create_engine, Column, Integer, String, Text, Index, inspect, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

# --- ORM Definition ---

class Base(DeclarativeBase):
    pass

class ExtractedEmail(Base):
    __tablename__ = 'extracted_emails'

    id = Column(Integer, primary_key=True)
    email_address = Column(Text, nullable=False)
    source_document_path = Column(Text, nullable=False)
    source_document_filename = Column(Text, nullable=False) # Added nullable=False based on schema
    page_number = Column(Integer, nullable=False)
    extraction_timestamp = Column(Text, nullable=False) # Storing as ISO string

    # Composite index for efficient duplicate checking (email + source)
    __table_args__ = (Index('idx_email_source', 'email_address', 'source_document_path'), )

    def __repr__(self):
        return f"<ExtractedEmail(email='{self.email_address}', source='{self.source_document_filename}', page={self.page_number})>"

# --- Database Initialization ---

def init_db(db_url: str):
    """Initializes the database using SQLAlchemy.

    Creates the engine, ensures the table and index exist using SQLAlchemy metadata.
    Also handles potential legacy tables with UNIQUE constraints on email_address.

    Args:
        db_url: The database connection URL (e.g., "sqlite:///extracted_emails.db").

    Returns:
        The SQLAlchemy Engine instance.
    """
    try:
        engine = create_engine(db_url)
        logging.debug(f"SQLAlchemy engine created for: {db_url}")

        # --- Legacy Table Check --- (Using raw SQL via Inspector for simplicity)
        inspector = inspect(engine)
        if inspector.has_table('extracted_emails'):
            try:
                # Use a connection to execute raw SQL for introspection
                with engine.connect() as connection:
                    result = connection.execute(
                        text("SELECT sql FROM sqlite_master WHERE type='table' AND name='extracted_emails';")
                    )
                    ddl_row = result.fetchone()
                    if ddl_row and ddl_row[0]:
                        ddl: str = ddl_row[0]
                        if "UNIQUE" in ddl.upper() and "EMAIL_ADDRESS" in ddl.upper() and "CONSTRAINT" in ddl.upper():
                            logging.warning(
                                "Legacy 'extracted_emails' table contains a UNIQUE constraint on email_address. "
                                "Backing up and recreating table."
                            )
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            backup_table = f"extracted_emails_backup_{timestamp}"
                            # Use connection.execute for DDL within the transaction context
                            connection.execute(text(f"ALTER TABLE extracted_emails RENAME TO {backup_table};"))
                            connection.commit() # Explicit commit needed for DDL via raw SQL
                            logging.info(
                                f"Legacy table backed up as '{backup_table}'. "
                                "A fresh table will be created by SQLAlchemy."
                            )
            except Exception as inspect_err:
                logging.error(f"Error during legacy table inspection/backup: {inspect_err}", exc_info=True)
                # Decide if this is fatal; for now, log and let create_all proceed/potentially fail

        # --- Create Table and Index (if not exists) ---
        Base.metadata.create_all(engine)
        logging.info(f"SQLAlchemy schema (table/index) ensured for {db_url}")
        return engine

    except SQLAlchemyError as e:
        logging.error(f"SQLAlchemy error during database initialization for {db_url}: {e}", exc_info=True)
        raise
    except Exception as e:
        logging.error(f"Unexpected error during database initialization for {db_url}: {e}", exc_info=True)
        raise

# --- Data Insertion ---

def insert_email(engine, email_data: Dict[str, Any]) -> bool:
    """Inserts a single email record using SQLAlchemy ORM if it doesn't already exist
    based on the combination of email_address and source_document_path.

    Args:
        engine: The SQLAlchemy Engine instance obtained from init_db.
        email_data: A dictionary containing the email record details.
                    Expected keys: 'email_address', 'source_document_path',
                                   'source_document_filename', 'page_number'.
                    'extraction_timestamp' is added if missing.

    Returns:
        True if the record was newly inserted, False if it already existed or an error occurred.
    """
    required_keys = {'email_address', 'source_document_path', 'source_document_filename', 'page_number'}
    email = email_data.get('email_address')
    source_path = email_data.get('source_document_path')

    logging.debug(f"Attempting ORM insert: Email='{email}', Source='{source_path}'")

    if not email or not source_path:
        logging.warning(f"Missing email or source_path for ORM insert: {email_data}")
        return False

    if not required_keys.issubset(email_data.keys()):
        logging.warning(f"Missing other required keys for ORM insert: {required_keys - email_data.keys()}")
        # Allow proceeding if email and source_path are present, but log warning

    timestamp = email_data.get('extraction_timestamp') or datetime.now().isoformat()

    # Create a Session
    SessionLocal = sessionmaker(bind=engine)
    with SessionLocal() as session:
        try:
            # 1. Check if the email+source combination already exists using ORM query
            exists = session.query(ExtractedEmail).filter_by(
                email_address=email,
                source_document_path=source_path
            ).first() is not None

            if exists:
                logging.debug(f"ORM: Record already exists: Email='{email}', Source='{source_path}'. Skipping.")
                return False # Indicate already exists
            else:
                # 2. If not exists, create ORM object and add to session
                logging.debug(f"ORM: Record does not exist. Inserting: Email='{email}', Source='{source_path}'")
                new_email = ExtractedEmail(
                    email_address=email,
                    source_document_path=source_path,
                    source_document_filename=email_data.get('source_document_filename', 'Unknown'), # Provide default
                    page_number=email_data.get('page_number', -1), # Provide default
                    extraction_timestamp=timestamp
                )
                session.add(new_email)
                session.commit() # Commit the transaction
                logging.info(f"ORM: Successfully inserted new record: Email='{email}', Source='{os.path.basename(source_path)}'")
                return True # Indicate successful insertion

        except IntegrityError as e:
            session.rollback() # Rollback on error
            # This might happen if the pre-check fails due to race condition or unexpected constraints
            logging.warning(
                f"ORM Integrity error (probable duplicate) for Email='{email}', "
                f"Source='{source_path}': {e.orig}" # Access original DBAPI error
            )
            return False
        except SQLAlchemyError as e:
            session.rollback()
            logging.error(f"ORM Database error during check/insert for Email='{email}', Source='{source_path}': {e}", exc_info=True)
            return False
        except Exception as e:
            session.rollback()
            logging.error(f"ORM Unexpected error during database operation for Email='{email}', Source='{source_path}': {e}", exc_info=True)
            return False 