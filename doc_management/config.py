"""
Configuration module for the FDD document management system.
Loads environment variables and provides configuration for the application.
"""

import os
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from pathlib import Path

# Calculate the path to the .env file in the same directory as config.py
dotenv_path = Path(__file__).parent / ".env"

# Load environment variables from the specified .env file
load_dotenv(dotenv_path=dotenv_path)

# Configure logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class Config:
    """Configuration class for the application."""
    # Define configuration variables
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    
    # CSV file path
    MATCH_RESULTS_CSV = os.getenv("MATCH_RESULTS_CSV", "C:\\Projects\\File_Util_App\\csvs\\MatchResults.csv")
    
    # Directory paths for file lookup
    HURIDOC_ANALYSIS_DIR = os.getenv("HURIDOC_ANALYSIS_DIR", "C:\\Projects\\File_Util_App\\data\\huridoc_analysis_output")
    PROCESSED_OUTPUTS_DIR = os.getenv("PROCESSED_OUTPUTS_DIR", "C:\\Projects\\File_Util_App\\data\\processed_outputs")
    HEADER_OUTPUT_DIR = os.getenv("HEADER_OUTPUT_DIR", "C:\\Projects\\File_Util_App\\output\\header_output")
    
    # Directory for split PDF outputs
    SPLIT_PDF_DIR = os.getenv("SPLIT_PDF_DIR", "C:\\Projects\\File_Util_App\\output\\split_pdfs")
    
    # SQLite database path
    DATABASE_PATH = os.getenv("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "database.db"))

    
