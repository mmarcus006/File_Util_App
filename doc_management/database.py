"""
Database module using SQLAlchemy ORM for managing file paths and headers.
"""

import os
import logging
from typing import List, Optional, Dict, Iterator, Sequence
from contextlib import contextmanager

from sqlalchemy import create_engine, select, update
from sqlalchemy.orm import sessionmaker, Session, joinedload
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.exc import NoResultFound

from config import Config
from models import Base, File, JsonItem

logger = logging.getLogger(__name__)

# Define the database URL (using sqlite)
DATABASE_URL = f"sqlite:///{Config.DATABASE_PATH}"

engine = None
SessionLocal = None

def get_engine():
    """Returns the SQLAlchemy engine instance, creating it if necessary."""
    global engine
    if engine is None:
        try:
            # Ensure the directory for the SQLite file exists
            db_dir = os.path.dirname(Config.DATABASE_PATH)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
                logger.info(f"Created database directory: {db_dir}")
            
            engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, echo=False) # Set echo=True for SQL logging
            logger.info(f"Database engine created for: {Config.DATABASE_PATH}")
        except Exception as e:
            logger.error(f"Error creating database engine: {e}", exc_info=True)
            raise
    return engine

def get_session_local():
    """Returns the SQLAlchemy session factory."""
    global SessionLocal
    if SessionLocal is None:
        current_engine = get_engine()
        if current_engine:
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=current_engine)
            logger.info("SQLAlchemy SessionLocal created.")
        else:
            logger.error("Cannot create SessionLocal without a valid engine.")
            raise RuntimeError("Database engine could not be initialized.")
    return SessionLocal

@contextmanager
def get_db() -> Iterator[Session]:
    """Provide a transactional scope around a series of operations."""
    session_factory = get_session_local()
    if not session_factory:
        raise RuntimeError("Session factory not initialized.")
        
    db = session_factory()
    try:
        yield db
    except SQLAlchemyError as e:
        logger.error(f"Database error occurred: {e}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()

def check_if_output_file_exists(file_path: str) -> bool:
    """Check if a file exists."""
    return os.path.exists(file_path)

def init_database() -> None:
    """Initialize the database and create tables based on models."""
    try:
        current_engine = get_engine()
        if check_if_output_file_exists(Config.DATABASE_PATH):
            logger.info(f"Database already exists at {Config.DATABASE_PATH}. Checking tables.")
            # Optionally, check if tables exist and log
        else:
             logger.info(f"Database file not found at {Config.DATABASE_PATH}. Creating.")
             
        # Create all tables defined in models.py that inherit from Base
        Base.metadata.create_all(bind=current_engine)
        logger.info("Database tables created/verified successfully (files, headers).")
    except Exception as e:
        logger.error(f"Error initializing database or creating tables: {e}", exc_info=True)
        raise

def add_or_update_file(file_id: str, huridoc_path: Optional[str] = None, 
                         processed_path: Optional[str] = None, 
                         header_path: Optional[str] = None,
                         item_data_list: Optional[List[Dict]] = None) -> Optional[File]:
    """
    Adds a new file record or updates an existing one. 
    Also deletes existing associated items and adds new ones based on item_data_list.

    Args:
        file_id: The unique file identifier.
        huridoc_path: Path to the file in huridoc analysis directory.
        processed_path: Path to the file in processed outputs directory.
        header_path: Path to the JSON file containing the item data list.
        item_data_list: Parsed list of dictionaries from the JSON item file.

    Returns:
        The added or updated File object, or None if an error occurred.
    """
    try:
        with get_db() as db:
            # Try to find existing file
            stmt = select(File).where(File.file_id == file_id)
            # Eagerly load items to facilitate deletion if updating
            # Use joinedload for potentially better performance than selectinload if items list isn't huge
            stmt = stmt.options(joinedload(File.items))
            existing_file = db.scalars(stmt).first()

            if existing_file:
                logger.debug(f"Updating existing file: {file_id}")
                # Update paths if new values are provided
                if huridoc_path is not None:
                    existing_file.huridoc_path = huridoc_path
                if processed_path is not None:
                    existing_file.processed_path = processed_path
                if header_path is not None:
                    existing_file.header_path = header_path # Update path to the item JSON file
                
                file_obj = existing_file
                
                # --- Delete existing JsonItem records associated with this file --- 
                # The relationship cascade="all, delete-orphan" should handle this,
                # but explicit deletion can be clearer or necessary depending on session state.
                # Let's rely on cascade first. If issues arise, uncomment below:
                # logger.debug(f"Deleting existing JsonItem records for file_id: {file_id}")
                # for item in existing_file.items: # Need to ensure items are loaded
                #     db.delete(item)
                # # Clear the collection proxy after deleting items directly
                # existing_file.items.clear() 
                # db.flush() # Flush deletions before adding new items
                # --- Modification: Instead of deleting, clear the collection --- 
                # Relying on cascade="all, delete-orphan" is usually sufficient.
                # Clearing the collection tells SQLAlchemy to manage the orphans.
                if existing_file.items: # Check if the collection exists and has items
                    logger.debug(f"Clearing existing {len(existing_file.items)} JsonItem records for file_id: {file_id}")
                    existing_file.items.clear()
                    db.flush() # Ensure orphans are processed before adding new items

            else:
                logger.debug(f"Adding new file: {file_id}")
                # Create new file record
                file_obj = File(
                    file_id=file_id,
                    huridoc_path=huridoc_path,
                    processed_path=processed_path,
                    header_path=header_path # Store path to the item JSON file
                )
                db.add(file_obj)
                # Flush to get the file_obj.id for the JsonItem foreign key
                db.flush()

            # --- Add new JsonItem records from the list --- 
            if item_data_list is not None and file_obj.id is not None:
                if not isinstance(item_data_list, list):
                    logger.warning(f"Skipping item processing for file_id {file_id}: Expected a list, but got type {type(item_data_list)}.")
                else:
                    logger.debug(f"Adding {len(item_data_list)} new JsonItem records for file_id: {file_id}")
                    for item_dict in item_data_list:
                        if not isinstance(item_dict, dict):
                            logger.warning(f"Skipping item in list for file_id {file_id}: Expected a dictionary, got {type(item_dict)}. Item: {item_dict}")
                            continue # Skip this item
                            
                        # Safely extract data using .get()
                        match_scores = item_dict.get('match_scores', {}) or {} # Ensure it's a dict even if None
                        
                        new_item = JsonItem(
                            file_id_fk=file_obj.id,
                            item_number=item_dict.get('item_number'),
                            text=item_dict.get('text'),
                            # Flatten match_scores
                            match_score_full=match_scores.get('full'),
                            match_score_label=match_scores.get('label'),
                            match_score_keywords=match_scores.get('keywords'),
                            match_score_final=match_scores.get('final'),
                            # Other fields
                            page_number=item_dict.get('page_number'),
                            node_index=item_dict.get('node_index'),
                            start_node_index=item_dict.get('start_node_index'),
                            end_node_index=item_dict.get('end_node_index'),
                            start_page=item_dict.get('start_page'),
                            end_page=item_dict.get('end_page'),
                            alignment_score=item_dict.get('alignment_score'),
                            pdf_file_path=item_dict.get('pdf_file_path')
                        )
                        db.add(new_item)
                        # Optionally add to file_obj.items collection if not relying purely on backref/commit
                        # file_obj.items.append(new_item)
                        
            elif item_data_list is None:
                 logger.debug(f"No item data list provided for file_id: {file_id}. No JsonItem records will be created/updated.")

            db.commit()
            # Refresh to get latest state, including any newly added/updated items 
            # if the relationship loading strategy requires it (e.g., if not using joinedload)
            if file_obj:
                 db.refresh(file_obj) 
                 # If items weren't loaded eagerly or added to collection proxy, refresh might not load them unless configured
                 # Consider db.refresh(file_obj, attribute_names=['items']) if needed
                 
            logger.info(f"Successfully added/updated file record and associated items for file_id: {file_id}")
            return file_obj

    except IntegrityError as e:
         logger.error(f"Integrity error (possibly duplicate file_id?) for {file_id}: {e}", exc_info=True)
         # Don't raise, return None as the operation failed
         return None
    except SQLAlchemyError as e:
        logger.error(f"Database error adding/updating file {file_id}: {e}", exc_info=True)
        # Don't raise, return None
        return None
    except Exception as e:
        logger.error(f"Unexpected error processing file {file_id}: {e}", exc_info=True)
        # Don't raise, return None
        return None

def get_file_by_id(file_id: str) -> Optional[File]:
    """
    Retrieve a file record by its file_id.
    
    Args:
        file_id: The unique file identifier.
        
    Returns:
        Optional[File]: The File object or None if not found.
    """
    try:
        with get_db() as db:
            stmt = select(File).where(File.file_id == file_id)
            file_obj = db.scalars(stmt).one_or_none() # Use one_or_none
            if file_obj:
                 logger.debug(f"Retrieved file with file_id: {file_id}")
            else:
                 logger.debug(f"No file found with file_id: {file_id}")
            return file_obj
    except NoResultFound:
         logger.warning(f"No file found with file_id: {file_id}") # Should not happen with one_or_none but good practice
         return None
    except SQLAlchemyError as e:
        logger.error(f"Database error retrieving file by ID {file_id}: {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Unexpected error retrieving file {file_id}: {e}", exc_info=True)
        return None

def get_all_files() -> Sequence[File]:
    """
    Retrieve all file records from the database.
    
    Returns:
        Sequence[File]: A sequence of File objects.
    """
    try:
        with get_db() as db:
            stmt = select(File).order_by(File.created_at.desc())
            files = db.scalars(stmt).all()
            logger.info(f"Retrieved {len(files)} files from the database.")
            return files
    except SQLAlchemyError as e:
        logger.error(f"Database error retrieving all files: {e}", exc_info=True)
        return []
    except Exception as e:
        logger.error(f"Unexpected error retrieving all files: {e}", exc_info=True)
        return []

def get_items_for_file(file_id: str) -> Sequence[JsonItem]:
    """
    Retrieve all JsonItem records associated with a specific file_id, 
    ordered by item_number.

    Args:
        file_id: The unique file identifier of the parent file.

    Returns:
        Sequence[JsonItem]: A sequence of JsonItem objects, ordered by item_number.
                           Returns an empty list if the file is not found or an error occurs.
    """
    try:
        with get_db() as db:
            # Select JsonItem, join with File to filter by file_id, and order
            stmt = (
                select(JsonItem)
                .join(File, JsonItem.file_id_fk == File.id)
                .where(File.file_id == file_id)
                .order_by(JsonItem.item_number.asc())
                # Consider adding options(joinedload(JsonItem.file)) if you need file info too
            )
            items = db.scalars(stmt).all()
            if not items:
                logger.warning(f"No items found for file_id: {file_id}")
            else:
                logger.info(f"Retrieved {len(items)} items for file_id: {file_id}")
            return items
    except SQLAlchemyError as e:
        logger.error(f"Database error retrieving items for file_id {file_id}: {e}", exc_info=True)
        return []
    except Exception as e:
        logger.error(f"Unexpected error retrieving items for {file_id}: {e}", exc_info=True)
        return []

# --- Comment out get_header_by_file_id as Header model is removed ---
# def get_header_by_file_id(file_id: str) -> Optional[Header]:
#     """
#     Retrieve header data for a specific file_id.
# 
#     Args:
#         file_id: The unique file identifier of the parent file.
# 
#     Returns:
#         Optional[Header]: The Header object or None if not found.
#     """
#     try:
#         with get_db() as db:
#             # Query Header joining with File on file_id
#             stmt = (
#                 select(Header)
#                 .join(File, Header.file_id_fk == File.id)
#                 .where(File.file_id == file_id)
#             )
#             header_obj = db.scalars(stmt).one_or_none()
#             if header_obj:
#                 logger.debug(f"Retrieved header for file_id: {file_id}")
#             else:
#                 logger.debug(f"No header found for file_id: {file_id}")
#             return header_obj
#     except NoResultFound:
#         logger.warning(f"No header found for file_id: {file_id}")
#         return None
#     except SQLAlchemyError as e:
#         logger.error(f"Database error retrieving header for file_id {file_id}: {e}", exc_info=True)
#         return None
#     except Exception as e:
#         logger.error(f"Unexpected error retrieving header for {file_id}: {e}", exc_info=True)
#         return None 