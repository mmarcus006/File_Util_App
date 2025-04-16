"""
FDD Document Management Package.
Includes configuration, ORM models, database operations, file processing, and CLI.
"""

# Configuration
from .config import Config, LOG_LEVEL

# ORM Models
from .models import Base, File, Header

# Database operations (SQLAlchemy based)
from .database import (
    init_database, 
    add_or_update_file, 
    get_file_by_id,
    get_all_files,
    get_header_by_file_id,
    get_db, # Expose session context manager if needed externally
    check_if_output_file_exists # Utility function
)

# File processing logic
from .file_processor import (
    extract_file_ids_from_csv,
    find_matching_file,
    read_header_json,
    process_file_ids,
    main as run_file_processing # Expose the main processing function
)

# CLI main function (useful if imported elsewhere)
from .cli import main as cli_main


__all__ = [
    # Config
    'Config',
    'LOG_LEVEL',
    # Models
    'Base',
    'File',
    'Header',
    # Database
    'init_database',
    'add_or_update_file',
    'get_file_by_id',
    'get_all_files',
    'get_header_by_file_id',
    'get_db',
    'check_if_output_file_exists',
    # File Processor
    'extract_file_ids_from_csv',
    'find_matching_file',
    'read_header_json',
    'process_file_ids',
    'run_file_processing',
    # CLI
    'cli_main'
] 