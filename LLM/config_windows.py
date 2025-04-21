"""Windows-specific configuration for FDD data extraction application."""

import os
from pathlib import Path

# --- Base Directory --- #
# Base directory (parent of the LLM module)
BASE_DIR = Path(__file__).resolve().parent.parent

# --- Directories and Paths --- #
# PDF Search Directories for Windows
PDF_SEARCH_DIRECTORIES = [
    # Windows test directory within the project
    str(BASE_DIR / "test_data" / "pdfs"),
    # Example Windows network path
    # "C:\\Users\\Public\\Documents\\FDD_PDFs",
]

# File paths for prompts, schemas and output
PROMPT_DIR = BASE_DIR / "prompts"
SCHEMA_DIR = PROMPT_DIR / "schemas"
OUTPUT_DIR = BASE_DIR / "output"

# --- Output filenames --- #
OUTPUT_FILENAMES = {
    "intro": "fdd_intro_extractions.json",
    "item_20": "fdd_item20_extractions.json",
} 