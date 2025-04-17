"""Functions for finding relevant PDFs and processing them with Gemini API."""

import os
import json
import time # For potential delays or polling
from pathlib import Path
from typing import List, Optional, Dict, Any, Type

# Use the official Google Generative AI library
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from google.generativeai import types as genai_types
from google.generativeai.generative_models import GenerativeModel

# --- Configuration (Consider moving API key loading to main/env) ---
# Load API key from environment variable
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
# Define the model name capable of handling file input and JSON output
# Use a model known to support File API and JSON output
MODEL_NAME = "gemini-2.5-pro"

# Flag to ensure configuration happens only once
_gemini_configured = False

# --- PDF Finding --- #

def find_fdd_intro_pdfs(search_dirs: List[str], keywords: List[str] = ["intro", "item_1"]) -> List[Path]:
    """Finds PDF files containing specified keywords in their names within given directories."""
    found_files: List[Path] = []
    processed_keywords = [k.lower() for k in keywords]

    for directory in search_dirs:
        search_path = Path(directory)
        if not search_path.is_dir():
            print(f"Warning: Directory not found or is not a directory: {directory}")
            continue

        print(f"Scanning {search_path}...")
        try:
            for pdf_path in search_path.rglob("*.pdf"):
                filename_lower = pdf_path.name.lower()
                if any(keyword in filename_lower for keyword in processed_keywords):
                    found_files.append(pdf_path)
        except Exception as e:
            print(f"Error scanning directory {directory}: {e}")

    print(f"Found {len(found_files)} PDFs matching keywords {keywords} in specified directories.")
    return found_files

# --- Gemini API Interaction --- #

def _configure_gemini_globally():
    """Configures the Gemini API key globally if not already done."""
    global _gemini_configured
    if _gemini_configured:
        return

    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY environment variable not set.")
    try:
        # Configure the API key globally for the genai module
        genai.configure(api_key=GEMINI_API_KEY) # type: ignore[attr-defined]
        _gemini_configured = True
        print("Gemini API configured successfully.")
    except Exception as e:
        print(f"Error configuring Gemini API: {e}")
        raise # Re-raise after logging

def extract_fdd_data_with_gemini(
    pdf_path: Path,
    # Change parameter to accept the loaded schema dictionary
    schema_dict: Dict[str, Any], # No longer takes Type[BaseModel]
    system_prompt: str
) -> Optional[Dict[str, Any]]:
    """Uploads a PDF, calls Gemini for structured extraction, and returns the data."""
    if not pdf_path.exists():
        print(f"Error: PDF file not found at {pdf_path}")
        return None

    try:
        _configure_gemini_globally()
    except ValueError as e:
        print(e)
        return None
    except Exception:
        return None

    uploaded_file = None
    try:
        # 1. Upload the file
        print(f"Uploading {pdf_path.name}...", end="", flush=True)
        uploaded_file = genai.upload_file( # type: ignore[attr-defined]
            path=pdf_path,
            display_name=pdf_path.name,
            mime_type="application/pdf"
        )
        print(f" Upload successful. File URI: {uploaded_file.uri}")

        # 2. Schema is now loaded externally and passed in as schema_dict
        # No schema generation needed here.
        print(f"Using loaded schema for Gemini API compatibility")

        # 3. Call the model
        print(f"Sending request to model '{MODEL_NAME}' for {pdf_path.name}...", end="", flush=True)
        model = GenerativeModel(MODEL_NAME)

        response = model.generate_content(
            contents=[
                system_prompt,
                uploaded_file
            ],
            generation_config=genai_types.GenerationConfig(
                response_mime_type="application/json",
                # Pass the loaded dictionary directly
                response_schema=schema_dict,
            )
        )
        print(" Request complete.")

        # 4. Process the response
        if response.candidates and response.candidates[0].content.parts:
            try:
                extracted_data = json.loads(response.text)
                print(f"Successfully parsed structured data for {pdf_path.name}.")
                return extracted_data
            except json.JSONDecodeError as e:
                print(f"Error: Could not decode JSON response from API for {pdf_path.name}. Details: {e}")
                print(f"Raw response text: {response.text[:500]}...")
                return None
            except AttributeError as e:
                 print(f"Error: Could not access response text/parts as expected for {pdf_path.name}. Details: {e}")
                 print(f"Full response: {response}")
                 return None
        else:
            print(f"Warning: No valid candidate or parts found in response for {pdf_path.name}.")
            if hasattr(response, 'prompt_feedback'):
                print(f"Prompt Feedback: {response.prompt_feedback}")
            return None

    except google_exceptions.GoogleAPIError as e:
        print(f"\nGoogle API Error during processing {pdf_path.name}: {e}")
        return None
    except Exception as e:
        print(f"\nAn unexpected error occurred processing {pdf_path.name}: {e}")
        return None
    finally:
        # 5. Delete the uploaded file
        if uploaded_file:
            try:
                print(f"Attempting to delete uploaded file: {uploaded_file.name}...", end="", flush=True)
                genai.delete_file(name=uploaded_file.name) # type: ignore[attr-defined]
                print(" Deleted successfully.")
            except Exception as delete_error:
                print(f"\nWarning: Failed to delete file {uploaded_file.name}. Error: {delete_error}")

# --- Test Execution Block --- #

if __name__ == "__main__":
    from dotenv import load_dotenv
    # Remove Pydantic schema import
    # try:
    #     from LLM.schemas import ExtractionOutput # Import the Pydantic schema
    # except ImportError:
    #     from schemas import ExtractionOutput
    try:
        # Still need the prompt template
        from LLM.llm_config import SYSTEM_PROMPT_TEMPLATE # Import the prompt
    except ImportError:
        from llm_config import SYSTEM_PROMPT_TEMPLATE

    print("--- Running PDF Processor Test --- ")
    # Load API key from .env file in the project root
    # Construct path relative to this script's location
    project_root = Path(__file__).resolve().parents[1]
    dotenv_path = project_root / '.env'
    if dotenv_path.exists():
        load_dotenv(dotenv_path=dotenv_path)
        print(f"Loaded .env from {dotenv_path}")
    else:
        print(f"Warning: .env file not found at {dotenv_path}")
        # Attempt to load from environment directly if .env is missing
        if not GEMINI_API_KEY:
             print("Error: GEMINI_API_KEY not found in environment or .env file.")
             exit(1)

    # Define the test directory relative to project root
    test_pdf_directory = project_root / "prompts" / "pdf_example" / "ITEM_1"

    # Define the path to the new JSON schema file
    schema_file_path = project_root / "prompts" / "schemas" / "ITEM_1_schema.json"

    # Load the schema from the JSON file
    if not schema_file_path.exists():
        print(f"Error: Schema file not found at {schema_file_path}")
        exit(1)
    try:
        with open(schema_file_path, 'r') as f:
            loaded_schema = json.load(f)
        print(f"Successfully loaded schema from {schema_file_path}")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON schema from {schema_file_path}: {e}")
        exit(1)
    except Exception as e:
        print(f"Error reading schema file {schema_file_path}: {e}")
        exit(1)

    # Find PDFs in the test directory (using default keywords)
    test_pdfs = find_fdd_intro_pdfs([str(test_pdf_directory)]) # Pass directory as string

    if not test_pdfs:
        print(f"No test PDFs found in {test_pdf_directory}. Exiting test.")
    else:
        # Process the first found PDF for testing
        pdf_to_process = test_pdfs[0]
        print(f"\nAttempting to process test file: {pdf_to_process.name}")

        extracted_data = extract_fdd_data_with_gemini(
            pdf_path=pdf_to_process,
            # Pass the loaded schema dictionary
            schema_dict=loaded_schema,
            system_prompt=SYSTEM_PROMPT_TEMPLATE
        )

        if extracted_data:
            print("\n--- Test Extraction Result ---")
            print(json.dumps(extracted_data, indent=2))
            print("--- End Test Extraction Result ---")
        else:
            print("\nTest extraction failed.")

    print("--- PDF Processor Test Finished ---")