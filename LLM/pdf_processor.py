"""
Module for processing PDF files using the Google Gemini API for structured data extraction.

Provides functionality to:
- Configure the Gemini API key.
- Upload a PDF to the Gemini File API.
- Call the Gemini model with system and user prompts, a PDF file, and a JSON schema.
- Parse the structured JSON output.
- Clean up by deleting the uploaded file.
"""

import os
import json
import time # For potential delays or polling
from pathlib import Path
from typing import Optional, Dict, Any, List, Type
import pydantic

# Use the official Google Generative AI library
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from google.generativeai import types as genai_types
from google.generativeai.generative_models import GenerativeModel

# Import from our own modules
from LLM.config import GEMINI_MODEL_NAME, GEMINI_API_KEY

# Flag to track configuration state
_gemini_configured = False

# --- PDF Finding Functions --- #

def find_fdd_intro_pdfs(search_directories: List[str], keywords: List[str]) -> List[Path]:
    """
    Find PDF files in the specified directories that contain any of the keywords in their filenames.
    
    Args:
        search_directories: List of directory paths to search in.
        keywords: List of keywords to look for in filenames.
        
    Returns:
        List of Path objects for matching PDF files.
    """
    found_pdfs = []
    
    # Convert all keywords to lowercase for case-insensitive matching
    lowercase_keywords = [kw.lower() for kw in keywords]
    
    for directory in search_directories:
        dir_path = Path(directory)
        if not dir_path.exists() or not dir_path.is_dir():
            print(f"Warning: Directory not found or is not a directory: {directory}")
            continue
            
        print(f"Scanning directory: {directory}")
        # Check all files in the directory
        for file_path in dir_path.glob("*.pdf"):
            # Check if any of the keywords appear in the filename (case-insensitive)
            if any(kw in file_path.name.lower() for kw in lowercase_keywords):
                found_pdfs.append(file_path)
                print(f"  Found matching PDF: {file_path.name}")
    
    print(f"Found {len(found_pdfs)} PDF files containing keywords: {keywords}")
    return found_pdfs

def output_file_exists(output_filename: str) -> bool:
    """
    Check if the output file already exists to avoid unnecessary processing.
    
    Args:
        output_filename: The filename for the output JSON.
        
    Returns:
        True if the file exists, False otherwise.
    """
    output_path = Path(output_filename)
    return output_path.exists()

# --- Configuration --- #

def configure_gemini(api_key: Optional[str] = None) -> None:
    """
    Configures the Google Generative AI API key globally.

    Args:
        api_key: The Gemini API key. If None, attempts to load from the
                 environment variable or config.

    Raises:
        ValueError: If the API key is not provided and not found in the environment.
        Exception: If configuration fails for other reasons.
    """
    global _gemini_configured
    if _gemini_configured:
        print("Gemini API already configured.")
        return

    key_to_use = api_key or GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY2")

    if not key_to_use:
        raise ValueError("GEMINI_API_KEY must be provided or set as an environment variable.")

    try:
        genai.configure(api_key=key_to_use) # type: ignore[attr-defined]
        _gemini_configured = True
        print("Gemini API configured successfully.")
    except Exception as e:
        print(f"Error configuring Gemini API: {e}")
        _gemini_configured = False
        raise

def extract_structured_data_from_pdfs(
    pdf_paths: List[Path], # Changed to accept a list of paths
    system_prompt: str,
    user_prompt: str,
    schema_dict: Dict[str, Any],
    model_name: str = GEMINI_MODEL_NAME,
    api_key: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Uploads one or more PDFs, calls the Gemini model with prompts and schema
    for structured extraction, and returns the parsed data.

    Handles API configuration, file uploads, API call, response parsing,
    and file deletion.

    Args:
        pdf_paths: A list of paths to the PDF files.
        system_prompt: The system instruction for the model.
        user_prompt: The user query or instruction related to the PDF(s).
        schema_dict: A dictionary representing the desired JSON output schema.
        model_name: The Gemini model to use (defaults to GEMINI_MODEL_NAME).
        api_key: Optional API key. If provided, configure_gemini will be called.
                 If None, assumes configuration happened previously or relies on env vars.

    Returns:
        A dictionary containing the extracted structured data, or None if an error occurs.
    """
    # Check if all PDF files exist
    for pdf_path in pdf_paths:
        if not pdf_path.exists():
            print(f"Error: PDF file not found at {pdf_path}")
            return None

    global _gemini_configured
    if not _gemini_configured:
        try:
            configure_gemini(api_key=api_key)
        except ValueError as e:
            print(f"Configuration Error: {e}")
            return None
        except Exception as e:
            print(f"Unexpected Configuration Error: {e}")
            return None

    uploaded_files: List[Any] = [] # Store multiple uploaded files (Type hint adjusted)
    pdf_names = ", ".join([p.name for p in pdf_paths]) # For logging
    try:
        # 1. Upload all files
        for pdf_path in pdf_paths:
            print(f"Uploading {pdf_path.name}...", end="", flush=True)
            try:
                uploaded_file = genai.upload_file( # type: ignore[attr-defined]
                    path=pdf_path,
                    display_name=pdf_path.name,
                    mime_type="application/pdf"
                )
                print(f" Upload successful. File URI: {uploaded_file.uri}")
                uploaded_files.append(uploaded_file)
            except Exception as upload_error:
                print(f"\nError uploading {pdf_path.name}: {upload_error}")
                # Clean up any files already uploaded before returning
                raise # Re-raise to trigger final cleanup

        # 2. Prepare Model and Generation Config
        model = GenerativeModel(model_name)
        generation_config = genai_types.GenerationConfig(
            response_mime_type="application/json",
            response_schema=schema_dict,
        )

        # 3. Construct content with prompts and all uploaded files
        content_parts = [system_prompt, user_prompt]
        for uploaded_file in uploaded_files:
            content_parts.append(uploaded_file)

        print(f"Sending request to model '{model_name}' for files: {pdf_names}...", end="", flush=True)
        response = model.generate_content(
            contents=content_parts, # Use the combined parts
            generation_config=generation_config
        )
        print(" Request complete.")

        # 4. Process the response
        # Accessing response.text should be safe based on documentation for JSON mime type
        if response.text:
            try:
                extracted_data = json.loads(response.text)
                print(f"Successfully parsed structured data for files: {pdf_names}.")
                return extracted_data
            except json.JSONDecodeError as e:
                print(f"Error: Could not decode JSON response from API for files: {pdf_names}. Details: {e}")
                print(f"Raw response text: {response.text[:500]}...")
                return None
        else:
            # Handle cases where response is empty or blocked
            print(f"Warning: No text content found in the response for files: {pdf_names}.")
            if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                print(f"Prompt Feedback: {response.prompt_feedback}")
            if response.candidates and not response.candidates[0].content.parts:
                 print(f"Candidate info: Finish reason={response.candidates[0].finish_reason}")
            return None

    except google_exceptions.GoogleAPIError as e:
        # Catch more specific API errors if possible, e.g., PermissionDenied, InvalidArgument
        print(f"\nGoogle API Error during processing {pdf_names}: {e}")
        return None
    except Exception as e:
        # Catch potential errors during upload or other steps
        print(f"\nAn unexpected error occurred processing {pdf_names}: {e.__class__.__name__}: {e}")
        return None
    finally:
        # 5. Delete all uploaded files - crucial for cleanup
        if uploaded_files:
            print(f"Attempting to delete {len(uploaded_files)} uploaded file(s)...", end="", flush=True)
            deleted_count = 0
            for uploaded_file in uploaded_files:
                try:
                    genai.delete_file(name=uploaded_file.name) # type: ignore[attr-defined]
                    deleted_count += 1
                except Exception as delete_error:
                    # Log non-critical cleanup errors but continue trying to delete others
                    print(f"\nWarning: Failed to delete uploaded file {uploaded_file.name}. "
                          f"Manual cleanup may be required. Error: {delete_error}")
            print(f" {deleted_count}/{len(uploaded_files)} deleted successfully.")

# --- Main extraction function --- #

def extract_fdd_data_with_gemini(
    pdf_path: Path,
    pydantic_schema: Type[pydantic.BaseModel],
    system_prompt: str,
    model_name: str = GEMINI_MODEL_NAME,
    api_key: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Process a single PDF file to extract data using the Gemini API.
    
    Args:
        pdf_path: Path to the PDF file to process.
        pydantic_schema: The Pydantic model class to use for extraction.
        system_prompt: The system prompt to use for the extraction.
        model_name: The name of the Gemini model to use.
        api_key: Optional Gemini API key.
        
    Returns:
        Extracted data as a dictionary, or None if extraction failed.
    """
    print(f"Extracting data from {pdf_path.name} using {model_name}...")
    
    # Generate schema dictionary from Pydantic model
    schema_dict = pydantic_schema.model_json_schema()
    
    # Simple user prompt for the extraction
    user_prompt = f"Extract structured information from the provided PDF file ('{pdf_path.name}') according to the schema."
    
    # Call the extraction function
    extracted_data = extract_structured_data_from_pdfs(
        pdf_paths=[pdf_path],
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        schema_dict=schema_dict,
        model_name=model_name,
        api_key=api_key
    )
    
    return extracted_data

if __name__ == '__main__':
    # Example usage demonstrating modularity
    from LLM.config import PROMPT_DIR, SCHEMA_DIR, PDF_SEARCH_DIRECTORIES, PDF_KEYWORDS
    from LLM.schemas import ExtractionOutput  
    
    # Use paths from config
    system_prompt_file = PROMPT_DIR / "system_prompts" / "Item_1_Intro_Prompt.md"
    schema_file = SCHEMA_DIR / "ITEM_1_INTRO_schema.json"
    user_prompt_text = "Follow your instructions and extract the structured data from the provided PDF pages covering the introduction and Item 1, stopping before Item 2."
    
    # Find PDF files
    pdf_files_to_process = find_fdd_intro_pdfs(PDF_SEARCH_DIRECTORIES, PDF_KEYWORDS["intro"])
    
    if not pdf_files_to_process:
        print("No PDF files found matching the criteria.")
        exit(1)
        
    # Select first PDF for testing
    pdf_path = pdf_files_to_process[0]
    
    # Load system prompt
    try:
        with open(system_prompt_file, 'r') as file:
            system_prompt = file.read()
    except FileNotFoundError:
        print(f"Error: System prompt file not found at {system_prompt_file}")
        system_prompt = None
    
    # Test extraction if system prompt was loaded
    if system_prompt:
        extraction_result = extract_fdd_data_with_gemini(
            pdf_path=pdf_path,
            pydantic_schema=ExtractionOutput,
            system_prompt=system_prompt
        )
        
        if extraction_result:
            print("\n--- Extracted Data ---")
            print(json.dumps(extraction_result, indent=2))
        else:
            print("\nExtraction failed.")
