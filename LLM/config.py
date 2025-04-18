"""Configuration file for FDD data extraction application."""

import os
import sys
import platform
from pathlib import Path

# --- OS Detection --- #
# Detect operating system and import the appropriate configuration
CURRENT_OS = platform.system()

# Import platform-specific configurations
if CURRENT_OS == "Windows":
    print("Detected Windows OS, loading Windows configuration...")
    from LLM.config_windows import PDF_SEARCH_DIRECTORIES, PROMPT_DIR, SCHEMA_DIR, OUTPUT_DIR, OUTPUT_FILENAMES
elif CURRENT_OS == "Darwin":  # macOS
    print("Detected macOS, loading Mac configuration...")
    from LLM.config_mac import PDF_SEARCH_DIRECTORIES, PROMPT_DIR, SCHEMA_DIR, OUTPUT_DIR, OUTPUT_FILENAMES
else:  # Linux or other systems
    print(f"Detected {CURRENT_OS} OS, using default configuration...")
    # Base directory (parent of the LLM module)
    BASE_DIR = Path(__file__).resolve().parent.parent
    
    # Default PDF Search Directories for other platforms
    PDF_SEARCH_DIRECTORIES = [
        # Default test directory within the project
        str(BASE_DIR / "test_data" / "pdfs"),
    ]
    
    # Default file paths
    PROMPT_DIR = BASE_DIR / "prompts"
    SCHEMA_DIR = PROMPT_DIR / "schemas"
    OUTPUT_DIR = BASE_DIR / "output"
    
    # Default output filenames
    OUTPUT_FILENAMES = {
        "intro": "fdd_intro_extractions.json",
        "item_20": "fdd_item20_extractions.json",
    }

# --- API Keys --- #
# Look for API keys in environment variables
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY2")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# --- PDF Processing --- #
# Keywords used to identify different types of PDFs
PDF_KEYWORDS = {
    "intro": ["intro", "item_1"],
    "item_20": ["ITEM_20"],
}

# --- Model Configuration --- #
# LLM model names
GEMINI_MODEL_NAME = "gemini-2.5-pro-preview-03-25"
OPENAI_MODEL_NAME = "gpt-4o"

# System prompts
SYSTEM_PROMPT_TEMPLATE = """
You are an expert AI assistant specialized in extracting structured information from Franchise Disclosure Documents (FDDs).

Your task is to analyze the provided PDF file content, which represents the **beginning sections of an FDD, starting from the very first page up to (but not including) the section explicitly titled 'ITEM 2'**. 

Carefully read this initial part of the document and extract the information required to populate a JSON object adhering to the provided schema (passed separately in the API request). Pay close attention to the field descriptions implicit in the schema.

**Extraction Rules:**
1.  **Scope:** Only extract information found BEFORE the start of 'ITEM 2'. Do not infer information from later sections.
2.  **Accuracy:** Extract values exactly as they appear in the text whenever possible. For dates, standardize to YYYY-MM-DD if possible, otherwise use the text format.
3.  **Completeness:** Fill in all fields for which information is present in the specified text section. If information for a field is not found in this section, omit the field or use `null`.
4.  **Schema Adherence:** Structure your output strictly according to the JSON schema provided via the API's `response_schema` parameter. Ensure correct data types.
5.  **Focus:** Prioritize extracting details about the Franchisor (brand name, legal name, contact info, history snippets if present) and the FDD Document itself (fiscal year, issue date).

Provide ONLY the JSON object containing the extracted data. Do not include any explanations or introductory text outside the JSON structure.
""" 