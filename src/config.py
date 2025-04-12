"""
Configuration file for Supabase database credentials.
"""
import os
from typing import Dict, Any
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.resolve()

# Define paths relative to project root
PATHS: Dict[str, Path] = {
    'DATA_DIR': PROJECT_ROOT / 'data',
    'DB_REPLICA_DIR': PROJECT_ROOT / 'db_replica',
    'SRC_DIR': PROJECT_ROOT / 'src',
    'OUTPUT_DIR': PROJECT_ROOT / 'output',
}

# Create specific paths
TRACKING_FILE = PATHS['SRC_DIR'] / 'processed_files_tracking.json'
FDD_CSV_FILE = PATHS['DB_REPLICA_DIR'] / 'fdd.csv'
HURIDOC_OUTPUT_DIR = PATHS['DATA_DIR'] / 'huridoc_analysis_output'

# Ensure directories exist
for path in PATHS.values():
    path.mkdir(parents=True, exist_ok=True)

# WSL specific paths (only used when running under WSL)
WSL_PATHS = {
    'VENV_PATH': Path('/home/miller/Projects/pdf-document-layout-analysis/.venv/bin/activate.fish')
}

def is_wsl() -> bool:
    """Check if running under Windows Subsystem for Linux"""
    return os.path.exists('/proc/version') and 'microsoft' in open('/proc/version').read().lower()

def get_wsl_path(windows_path: str) -> str:
    """Convert Windows path to WSL path format"""
    if ':' in windows_path:
        drive, rest = windows_path.split(':', 1)
        wsl_path = f"/mnt/{drive.lower()}{rest}"
    else:
        wsl_path = windows_path
    return wsl_path.replace('\\', '/')

# Supabase Configuration
SUPABASE_CONFIG: Dict[str, Any] = {
    "url": os.getenv("SUPABASE_URL"),
    "anon_key": os.getenv("SUPABASE_ANON_KEY"),
    "service_role_key": os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
    "jwt_secret": os.getenv("SUPABASE_JWT_SECRET"),
    "access_token": os.getenv("SUPABASE_ACCESS_TOKEN")
}

# Database schema configuration
DB_SCHEMA = os.getenv("SUPABASE_DB_SCHEMA", "public")  # The default schema in Supabase

# Other configuration settings
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "t") 

# Folder paths
FDD_PDF_FOLDER = os.getenv("FDD_PDF_FOLDER")
