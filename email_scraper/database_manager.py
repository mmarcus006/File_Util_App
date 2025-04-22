"""Handles SQLite database interactions for storing extracted emails."""

import sqlite3
import logging
from typing import Dict, Any
from datetime import datetime

# Schema:
# TABLE extracted_emails (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     email_address TEXT NOT NULL UNIQUE,
#     source_document_path TEXT NOT NULL,
#     source_document_filename TEXT NOT NULL,
#     page_number INTEGER NOT NULL,
#     extraction_timestamp TEXT NOT NULL -- ISO 8601 format YYYY-MM-DD HH:MM:SS.ffffff
# );

def init_db(db_path: str) -> None:
    """Initializes the SQLite database and creates the 'extracted_emails' table if it doesn't exist.

    Args:
        db_path: The path to the SQLite database file.
    """
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS extracted_emails (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email_address TEXT NOT NULL UNIQUE,
                    source_document_path TEXT NOT NULL,
                    source_document_filename TEXT NOT NULL,
                    page_number INTEGER NOT NULL,
                    extraction_timestamp TEXT NOT NULL
                )
            ''')
            conn.commit()
            logging.info(f"Database initialized successfully at {db_path}")
    except sqlite3.Error as e:
        logging.error(f"Error initializing database at {db_path}: {e}")
        raise # Re-raise the exception to signal failure

def insert_email(db_path: str, email_data: Dict[str, Any]) -> bool:
    """Inserts a single email record into the database.

    Uses 'INSERT OR IGNORE' to avoid errors if the email address already exists.

    Args:
        db_path: The path to the SQLite database file.
        email_data: A dictionary containing the email record details.
                    Expected keys: 'email_address', 'source_document_path',
                                   'source_document_filename', 'page_number'.

    Returns:
        True if the record was inserted, False if it was ignored (already exists) or an error occurred.
    """
    required_keys = {'email_address', 'source_document_path', 'source_document_filename', 'page_number'}
    if not required_keys.issubset(email_data.keys()):
        logging.error(f"Missing required keys in email_data for insertion: {required_keys - email_data.keys()}")
        return False

    timestamp = datetime.now().isoformat()

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO extracted_emails
                (email_address, source_document_path, source_document_filename, page_number, extraction_timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                email_data['email_address'],
                email_data['source_document_path'],
                email_data['source_document_filename'],
                email_data['page_number'],
                timestamp
            ))
            conn.commit()
            # Check if any row was actually changed (inserted)
            if cursor.rowcount > 0:
                logging.debug(f"Inserted email: {email_data['email_address']}")
                return True
            else:
                logging.debug(f"Email already exists, ignored: {email_data['email_address']}")
                return False # Indicate it was ignored, not inserted
    except sqlite3.Error as e:
        logging.error(f"Error inserting email {email_data.get('email_address', 'N/A')} into {db_path}: {e}")
        return False # Indicate failure 