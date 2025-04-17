import os
import json
# import fitz # No longer needed
# from fitz import Page # No longer needed
from openai import OpenAI
# Import specific exception types for better error handling
from openai import APIError, APIConnectionError, RateLimitError, AuthenticationError
from typing import Dict, List, Optional, Any

# --- Configuration ---
# Ensure the OpenAI API key is set as an environment variable
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY") # Changed variable name
# Define the directory containing the PDF files
PDF_DIRECTORY = "/Users/miller/Library/CloudStorage/OneDrive-Personal/FDD_PDFS/split_pdfs"
# Define paths for the schema and prompt files relative to the workspace root
SCHEMA_PATH = "prompts/item_20_schema.json"
PROMPT_PATH = "prompts/Item_20_Prompt.md"
# Specify the OpenAI model - ensure it supports file input and structured outputs
# gpt-4o is a good choice, but confirm compatibility if issues arise.
MODEL_NAME = "gpt-4o" # Changed model to standard OpenAI model
# Keyword to identify relevant PDFs
KEYWORD = "ITEM_20"

# --- Helper Functions ---

def load_json_schema(schema_path: str) -> Optional[Dict[str, Any]]:
    """Loads JSON schema from file, removing comments starting with #."""
    if not os.path.exists(schema_path):
        print(f"Error: Schema file not found at {schema_path}")
        return None
    try:
        schema_str_no_comments = ""
        with open(schema_path, 'r', encoding='utf-8') as f:
            for line in f:
                stripped_line = line.strip()
                if not stripped_line.startswith("#"):
                    schema_str_no_comments += line
        return json.loads(schema_str_no_comments)
    except json.JSONDecodeError as e:
        print(f"Error: Could not parse JSON schema from {schema_path}. Details: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred loading schema {schema_path}: {e}")
        return None

def load_prompt(prompt_path: str) -> Optional[str]:
    """Loads the system prompt text from a file."""
    if not os.path.exists(prompt_path):
        print(f"Error: Prompt file not found at {prompt_path}")
        return None
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"An unexpected error occurred loading prompt {prompt_path}: {e}")
        return None

def find_target_pdfs(directory: str, keyword: str) -> List[str]:
    """Finds PDF files containing a specific keyword in the specified directory."""
    pdf_files = []
    if not os.path.isdir(directory):
        print(f"Error: Directory not found or is not a directory: {directory}")
        return pdf_files
    try:
        for filename in os.listdir(directory):
            if keyword in filename and filename.lower().endswith(".pdf"):
                full_path = os.path.join(directory, filename)
                pdf_files.append(full_path)
        print(f"Found {len(pdf_files)} PDFs containing '{keyword}' in '{directory}'.")
    except Exception as e:
         print(f"Error listing directory {directory}: {e}")
    return pdf_files

# Removed extract_text_from_pdf function

def process_pdf_with_openai(client: OpenAI, system_prompt: str, pdf_path: str, schema: Dict[str, Any], model: str) -> Optional[Dict[str, Any]]:
    """Uploads PDF, calls OpenAI API for structured data using file_id, then deletes the file."""
    if not system_prompt:
        print("Error: System prompt is missing.")
        return None
    if not schema:
        print("Error: Schema is missing.")
        return None
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found at {pdf_path}")
        return None

    file_id = None
    try:
        # 1. Upload the file
        print(f"Uploading {os.path.basename(pdf_path)}...")
        # Open the file in binary read mode
        with open(pdf_path, "rb") as pdf_file_obj:
            file_response = client.files.create(
                file=pdf_file_obj, # Pass the file object
                purpose="user_data"
            )
        # file_id = file_response.id # Correct variable name used
        file_id = file_response.id
        print(f"File uploaded successfully. File ID: {file_id}")

        # 2. Call the responses API with file reference
        print(f"Sending request to model '{model}' with file ID {file_id}...")
        response = client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_file",
                            "file_id": file_id,
                        },
                        {
                            "type": "input_text",
                            # Simple instruction referencing the file and task
                            "text": "Extract table data from the provided FDD Item 20 PDF according to the specified JSON schema.",
                        },
                    ]
                }
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "fdd_item20_extraction",
                    "schema": schema,
                    "strict": True
                }
            }
            # max_output_tokens=4096 # Consider adding if needed
        )

        # 3. Process the response
        if response.status == "incomplete":
            reason = response.incomplete_details.reason if response.incomplete_details else "unknown"
            print(f"Warning: API response incomplete. Reason: {reason}")
            return None

        if hasattr(response, 'output_text') and response.output_text:
             try:
                 parsed_data = json.loads(response.output_text)
                 print("Successfully parsed structured data from API response.")
                 return parsed_data
             except json.JSONDecodeError as e:
                 print(f"Error: Could not parse JSON response from API. Details: {e}")
                 # print(f"Raw API response text: {response.output_text[:500]}...")
                 return None
        elif response.output and len(response.output) > 0 and response.output[0].content and len(response.output[0].content) > 0:
            # Handle refusal if structured differently
            output_content = response.output[0].content[0]
            if output_content.type == "refusal":
                refusal_message = output_content.refusal if hasattr(output_content, 'refusal') else "No details provided."
                print(f"Warning: API refused the request. Refusal message: {refusal_message}")
                return None
            else:
                 print(f"Warning: API response structure unexpected. Content type: {output_content.type}")
                 return None
        else:
            print("Warning: API response structure unexpected or missing output_text.")
            return None

    # Specific OpenAI error handling
    except AuthenticationError as e:
        print(f"OpenAI Authentication Error: {e}. Check your API key and permissions.")
        return None
    except RateLimitError as e:
        print(f"OpenAI Rate Limit Error: {e}. Please wait and try again.")
        return None # Or implement retry logic
    except APIConnectionError as e:
        print(f"OpenAI Connection Error: {e}. Check your network connection.")
        return None
    except APIError as e:
        print(f"OpenAI API Error: {e}")
        return None
    except Exception as e:
        # Catch-all for other errors (e.g., file not found during open)
        print(f"An unexpected error occurred during processing: {e}")
        return None

    finally:
        # 4. Delete the file (always attempt this)
        if file_id:
            try:
                print(f"Attempting to delete file ID: {file_id}...")
                client.files.delete(file_id)
                print(f"Successfully deleted file ID: {file_id}.")
            except Exception as delete_error:
                # Log deletion error but don't prevent returning data if extraction succeeded
                print(f"Warning: Failed to delete file ID {file_id}. Error: {delete_error}")

# --- Main Execution ---
def main():
    """Main function to orchestrate the PDF processing workflow."""
    print("Starting FDD Item 20 extraction process using OpenAI file upload...")

    if not OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY environment variable not set. Please set it and retry.")
        return

    # Initialize standard OpenAI client
    try:
        # Removed base_url and adjusted api_key parameter name if needed (usually inferred from env)
        client = OpenAI()
        # Test connectivity (optional but recommended)
        client.models.list() # Simple call to check authentication
        print("OpenAI client initialized and authenticated successfully.")
    except AuthenticationError:
         print("Authentication Error: Failed to initialize OpenAI client. Check OPENAI_API_KEY.")
         return
    except Exception as e:
        print(f"Error initializing OpenAI client: {e}")
        return

    print("Loading schema and prompt...")
    schema = load_json_schema(SCHEMA_PATH)
    system_prompt = load_prompt(PROMPT_PATH)

    if not schema or not system_prompt:
        print("Failed to load necessary schema or prompt file(s). Exiting.")
        return

    print(f"Scanning for PDFs containing '{KEYWORD}' in: {PDF_DIRECTORY}")
    pdf_files = find_target_pdfs(PDF_DIRECTORY, KEYWORD)

    if not pdf_files:
        print(f"No PDF files containing '{KEYWORD}' found in the specified directory.")
        return

    print(f"Ready to process {len(pdf_files)} PDF file(s).")

    results = {}
    for pdf_path in pdf_files:
        pdf_filename = os.path.basename(pdf_path)
        print(f"\n--- Processing: {pdf_filename} ---")

        # Call the function that handles upload, API call, and deletion
        extracted_data = process_pdf_with_openai(
            client=client,
            system_prompt=system_prompt,
            pdf_path=pdf_path,
            schema=schema,
            model=MODEL_NAME
        )

        if extracted_data:
            print(f"Successfully retrieved and parsed data for {pdf_filename}.")
            results[pdf_filename] = extracted_data
        else:
            print(f"Failed processing for {pdf_filename}.")
            results[pdf_filename] = None # Mark as failed

    print("\n--- Processing Summary ---")
    successful_extractions = sum(1 for result in results.values() if result is not None)
    failed_count = len(pdf_files) - successful_extractions
    print(f"Successfully processed: {successful_extractions} file(s)")
    print(f"Failed to process:    {failed_count} file(s)")

    # Save results
    output_file = "fdd_item20_extractions.json"
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"Results saved to {output_file}")
    except Exception as e:
        print(f"Error saving results to {output_file}: {e}")

if __name__ == "__main__":
    main()