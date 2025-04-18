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

def extract_structured_data_from_pdfs(
    pdf_paths: List[Path], # Changed to accept a list of paths
    system_prompt: str,
    user_prompt: str,
    schema_dict: Dict[str, Any],
    model_name: str = DEFAULT_MODEL_NAME,
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
        model_name: The Gemini model to use (defaults to DEFAULT_MODEL_NAME).
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
                # Use a short timeout for the upload operation if it tends to hang
                # Note: upload_file itself doesn't have a direct timeout parameter.
                # Consider wrapping in threading/async logic if hangs are frequent.
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


if __name__ == '__main__':
    # Example usage demonstrating modularity

    # --- Configuration (Set these paths/values) --- #
    # Use absolute paths or paths relative to where the script is run
    pdf_dir = Path("/Users/miller/projects/File_Util_App/prompts/pdf_example/ITEM_1")
    pdf_files_to_process = [
        pdf_dir / "ce6d8ac9-6268-4796-8e4b-6483406b4640_ITEM_1.pdf",
        pdf_dir / "INTRO" / "intro_BOSSESPIZZACHICKEN.pdf"
    ]
    prompt_dir = Path("/Users/miller/projects/File_Util_App/prompts")
    system_prompt_file = prompt_dir / "system_prompts" / "Item_1_Intro_Prompt.md"
    schema_file = prompt_dir / "schemas" / "ITEM_1_INTRO_schema.json"
    user_prompt_text = "Follow your instructions and extract the structured data from the provided PDF pages covering the introduction and Item 1, stopping before Item 2."
    # --- End Configuration --- #

    # Load System Prompt
    try:
        with open(system_prompt_file, 'r') as file:
            system_prompt = file.read()
    except FileNotFoundError:
        print(f"Error: System prompt file not found at {system_prompt_file}")
        exit(1)
    except Exception as e:
        print(f"Error reading system prompt file: {e}")
        exit(1)

    # Load Schema
    try:
        with open(schema_file, 'r') as file:
            schema_dict = json.load(file)
    except FileNotFoundError:
        print(f"Error: Schema file not found at {schema_file}")
        exit(1)
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from schema file: {schema_file}")
        exit(1)
    except Exception as e:
        print(f"Error reading schema file: {e}")
        exit(1)

    # Check if PDF files exist before processing
    missing_files = [p for p in pdf_files_to_process if not p.exists()]
    if missing_files:
        print("Error: The following PDF files were not found:")
        for p in missing_files:
            print(f" - {p}")
        exit(1)

    # Call the processing function
    # Assumes GEMINI_API_KEY2 is set in the environment
    # Or pass api_key="YOUR_API_KEY" directly
    extracted_data = extract_structured_data_from_pdfs(
        pdf_paths=pdf_files_to_process,
        system_prompt=system_prompt,
        user_prompt=user_prompt_text,
        schema_dict=schema_dict
        # model_name="gemini-1.5-pro-latest" # Optionally specify a different model
    )

    if extracted_data:
        print("\n--- Extracted Data --- ")
        # Pretty print the JSON output
        print(json.dumps(extracted_data, indent=2))
        # Optionally save to a file
        # output_path = Path("extracted_output.json")
        # with open(output_path, 'w') as f:
        #     json.dump(extracted_data, f, indent=2)
        # print(f"\nExtracted data saved to {output_path}")
    else:
        print("\nExtraction failed.")
