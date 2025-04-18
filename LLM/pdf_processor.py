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
# Use List for type hint consistency
from typing import Optional, Dict, Any, List

# Use the official Google Generative AI library
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from google.generativeai import types as genai_types
from google.generativeai.generative_models import GenerativeModel

# --- Constants ---
DEFAULT_MODEL_NAME = "gemini-2.5-pro-preview-03-25"

# Flag to track configuration state
_gemini_configured = False

# --- Configuration --- #

def configure_gemini(api_key: Optional[str] = None) -> None:
    """
    Configures the Google Generative AI API key globally.

    Args:
        api_key: The Gemini API key. If None, attempts to load from the
                 GEMINI_API_KEY environment variable.

    Raises:
        ValueError: If the API key is not provided and not found in the environment.
        Exception: If configuration fails for other reasons.
    """
    global _gemini_configured
    if _gemini_configured:
        print("Gemini API already configured.")
        return

    key_to_use = api_key or os.environ.get("GEMINI_API_KEY2")

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

def extract_structured_data_from_pdf(
    pdf_path: Path,
    system_prompt: str,
    user_prompt: str, # Added user prompt
    schema_dict: Dict[str, Any],
    model_name: str = DEFAULT_MODEL_NAME,
    api_key: Optional[str] = None, # Allow passing API key directly
) -> Optional[Dict[str, Any]]:
    """
    Uploads a PDF, calls the Gemini model with prompts and schema for structured
    extraction, and returns the parsed data.

    Handles API configuration, file upload, API call, response parsing,
    and file deletion.

    Args:
        pdf_path: Path to the PDF file.
        system_prompt: The system instruction for the model.
        user_prompt: The user query or instruction related to the PDF.
        schema_dict: A dictionary representing the desired JSON output schema.
        model_name: The Gemini model to use (defaults to DEFAULT_MODEL_NAME).
        api_key: Optional API key. If provided, configure_gemini will be called.
                 If None, assumes configuration happened previously or relies on env vars.

    Returns:
        A dictionary containing the extracted structured data, or None if an error occurs.
    """
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

    uploaded_file = None
    try:
        # 1. Upload the file
        print(f"Uploading {pdf_path.name}...", end="", flush=True)
        # Use a short timeout for the upload operation if it tends to hang
        # Note: upload_file itself doesn't have a direct timeout parameter.
        # Consider wrapping in threading/async logic if hangs are frequent.
        uploaded_file = genai.upload_file( # type: ignore[attr-defined]
            path=pdf_path,
            display_name=pdf_path.name,
            mime_type="application/pdf"
        )
        print(f" Upload successful. File URI: {uploaded_file.uri}")

        # 2. Prepare Model and Generation Config
        model = GenerativeModel(model_name)
        generation_config = genai_types.GenerationConfig(
            response_mime_type="application/json",
            response_schema=schema_dict,
        )

        # 3. Call the model with System Prompt, User Prompt, and File
        print(f"Sending request to model '{model_name}' for {pdf_path.name}...", end="", flush=True)
        response = model.generate_content(
            contents=[system_prompt, user_prompt, uploaded_file], # Added user_prompt
            generation_config=generation_config
        )
        print(" Request complete.")

        # 4. Process the response
        # Accessing response.text should be safe based on documentation for JSON mime type
        if response.text:
            try:
                extracted_data = json.loads(response.text)
                print(f"Successfully parsed structured data for {pdf_path.name}.")
                return extracted_data
            except json.JSONDecodeError as e:
                print(f"Error: Could not decode JSON response from API for {pdf_path.name}. Details: {e}")
                print(f"Raw response text: {response.text[:500]}...")
                return None
        else:
            # Handle cases where response is empty or blocked
            print(f"Warning: No text content found in the response for {pdf_path.name}.")
            if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                print(f"Prompt Feedback: {response.prompt_feedback}")
            if response.candidates and not response.candidates[0].content.parts:
                 print(f"Candidate info: Finish reason={response.candidates[0].finish_reason}")
            return None

    except google_exceptions.GoogleAPIError as e:
        # Catch more specific API errors if possible, e.g., PermissionDenied, InvalidArgument
        print(f"\nGoogle API Error during processing {pdf_path.name}: {e}")
        return None
    except Exception as e:
        # Catch potential errors during upload or other steps
        print(f"\nAn unexpected error occurred processing {pdf_path.name}: {e.__class__.__name__}: {e}")
        return None
    finally:
        # 5. Delete the uploaded file - crucial for cleanup
        if uploaded_file:
            try:
                print(f"Attempting to delete uploaded file: {uploaded_file.name}...", end="", flush=True)
                # Use file name for deletion
                genai.delete_file(name=uploaded_file.name) # type: ignore[attr-defined]
                print(" Deleted successfully.")
            except Exception as delete_error:
                # Log non-critical cleanup errors
                print(f"\nWarning: Failed to delete uploaded file {uploaded_file.name}. " \
                      f"Manual cleanup may be required. Error: {delete_error}")


if __name__ == '__main__':
    # Example usage
    pdf_path_Item_1 = Path("/Users/miller/projects/File_Util_App/prompts/pdf_example/ITEM_1/ce6d8ac9-6268-4796-8e4b-6483406b4640_ITEM_1.pdf")
    
    pdf_path_intro = Path("/Users/miller/projects/File_Util_App/prompts/pdf_example/ITEM_1/INTRO/intro_BOSSESPIZZACHICKEN.pdf")
    
    system_prompt_path=Path("/Users/miller/projects/File_Util_App/prompts/system_prompts/Item_1_Intro_Prompt.md")
    
    with open(system_prompt_path, 'r') as file:
        system_prompt = file.read()
        
    schema_path = Path("/Users/miller/projects/File_Util_App/prompts/schemas/ITEM_1_INTRO_schema.json")
    
    with open(schema_path, 'r') as file:
        schema_dict = json.load(file)
        
    user_prompt = "Follow your instructions and extract the structured data from the PDF."
    
    # Combine the pages from both PDFs
    from PyPDF2 import PdfMerger
    
    merger = PdfMerger()
    merger.append(pdf_path_Item_1)
    merger.append(pdf_path_intro)
    
    # Create a temporary combined PDF
    combined_pdf_path = Path("temp_combined.pdf")
    merger.write(combined_pdf_path)
    merger.close()
    
    # Process the combined PDF
    result = extract_structured_data_from_pdf(combined_pdf_path, system_prompt, user_prompt, schema_dict)
    
    # Clean up the temporary file
    combined_pdf_path.unlink()
