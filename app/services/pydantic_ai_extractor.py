import logging
import json
import os
from typing import Dict, Any, Optional, Type
from pathlib import Path

from pydantic import BaseModel, ValidationError
from pydantic_ai import Agent
from pydantic_ai.exceptions import PydanticAIError

from app.config import Config
from app.utils.error_handler import LLMError
from app.models.models import StatementData  # Import the Pydantic model

# Configure logging
logger = logging.getLogger(__name__)

# --- Constants ---

# Prompt file paths (relative to project root)
PROMPT_FILES: Dict[str, str] = {
    'JPMorgan Chase': 'prompts/jpmorgan_chase.txt',
    'Morgan Stanley': 'prompts/morgan_stanley.txt',
    'Goldman Sachs': 'prompts/goldman_sachs.txt'
    # Add more institutions as needed
}

# Core instructions file (relative to project root)
CORE_INSTRUCTIONS_FILE: str = 'prompts/core_instructions.txt'

# Cache directory relative to project root
CACHE_DIR_NAME: str = "cache/pydanticai_extractions"

# --- Helper Functions ---

def _load_prompt_file(file_path: str) -> str:
    """Loads prompt content from a file relative to the project root.

    Args:
        file_path: The relative path to the prompt file.

    Returns:
        The content of the prompt file as a string.

    Raises:
        FileNotFoundError: If the prompt file cannot be found.
        IOError: If there is an error reading the file.
    """
    try:
        # Assume the script runs from a location where this relative path makes sense
        # Usually, this would be the project root or handled by how the app starts.
        base_path = Path(__file__).resolve().parent.parent.parent
        full_path = base_path / file_path
        logger.debug(f"Attempting to load prompt file from: {full_path}")
        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        logger.error(f"Prompt file not found: {full_path}")
        raise FileNotFoundError(f"Prompt file not found: {full_path}")
    except IOError as e:
        logger.error(f"Error reading prompt file {file_path}: {str(e)}")
        raise IOError(f"Error reading prompt file {file_path}: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error loading prompt file {file_path}: {str(e)}")
        raise # Re-raise unexpected errors


def _get_cached_extraction_path(markdown_content: str, institution_name: str) -> Path:
    """Generates the path for a cached extraction result file.

    Args:
        markdown_content: The markdown content (used for hashing).
        institution_name: The name of the financial institution.

    Returns:
        A Path object representing the cache file path.
    """
    # Create a safe, unique filename based on a hash of the first 200 chars
    # and institution name to identify this specific extraction.
    content_hash = str(hash(markdown_content[:200]))
    sanitized_institution = institution_name.lower().replace(' ', '_').replace('&', 'and')
    extraction_filename = f"extraction_{sanitized_institution}_{content_hash}.json"

    # Save to a dedicated cache directory relative to the project root
    base_path = Path(__file__).resolve().parent.parent.parent
    cache_dir = base_path / CACHE_DIR_NAME
    cache_dir.mkdir(parents=True, exist_ok=True) # Ensure cache directory exists

    return cache_dir / extraction_filename


def _save_extraction_result(extraction_path: Path, extraction_data: BaseModel) -> None:
    """Saves the Pydantic model data to a JSON cache file.

    Args:
        extraction_path: The Path object for the cache file.
        extraction_data: The Pydantic model instance containing the extracted data.
    """
    try:
        with open(extraction_path, 'w', encoding='utf-8') as f:
            # Use Pydantic's built-in JSON serialization
            f.write(extraction_data.model_dump_json(indent=2))
        logger.info(f"Saved PydanticAI extraction result to {extraction_path}")
    except IOError as e:
        logger.error(f"Failed to write extraction result to {extraction_path}: {str(e)}")
        # Decide if this should raise an error or just log
    except Exception as e:
        logger.error(f"Unexpected error saving extraction result to {extraction_path}: {str(e)}")
        # Decide if this should raise an error or just log


def _load_extraction_result(extraction_path: Path, result_model: Type[BaseModel]) -> Optional[BaseModel]:
    """Loads and validates extraction result from a JSON cache file into a Pydantic model.

    Args:
        extraction_path: The Path object for the cache file.
        result_model: The Pydantic model class to validate against.

    Returns:
        A Pydantic model instance if the cache file exists and is valid, None otherwise.
    """
    if not extraction_path.exists():
        return None

    try:
        with open(extraction_path, 'r', encoding='utf-8') as f:
            # Load and validate directly using the Pydantic model
            data = json.load(f)
            validated_data = result_model.model_validate(data)
        logger.info(f"Loaded and validated PydanticAI extraction result from {extraction_path}")
        return validated_data
    except (IOError, json.JSONDecodeError) as e:
        logger.error(f"Failed to load or parse cache file {extraction_path}: {str(e)}")
        return None # Treat as cache miss
    except ValidationError as e:
        logger.warning(f"Cached data in {extraction_path} failed validation: {str(e)}. Treating as cache miss.")
        # Optionally delete the invalid cache file: os.remove(extraction_path)
        return None # Treat as cache miss
    except Exception as e:
        logger.error(f"Unexpected error loading cache file {extraction_path}: {str(e)}")
        return None # Treat as cache miss

# --- Core Extraction Function ---

def extract_structured_data_with_pydanticai(
    markdown_content: str,
    institution_name: str
) -> StatementData:
    """Extracts structured data from markdown using PydanticAI and Gemini.

    Args:
        markdown_content: The bank statement content in markdown format.
        institution_name: The name of the financial institution (e.g., 'JPMorgan Chase').

    Returns:
        A StatementData Pydantic model instance containing the extracted data.

    Raises:
        LLMError: If the extraction fails due to API issues, validation errors,
                  or missing prompts.
        FileNotFoundError: If required prompt files are missing.
        IOError: If there's an issue reading prompt files.
    """
    # 1. Check Cache
    extraction_path = _get_cached_extraction_path(markdown_content, institution_name)
    cached_data = _load_extraction_result(extraction_path, StatementData)
    if cached_data:
        logger.info(f"Using cached PydanticAI extraction result for {institution_name}")
        # Ensure the loaded data is of the correct type
        if isinstance(cached_data, StatementData):
            return cached_data
        else:
             logger.warning("Cached data type mismatch. Proceeding with fresh extraction.")
             # Fall through to perform fresh extraction


    logger.info(f"Cache miss or invalid cache for {institution_name}. Performing fresh extraction with PydanticAI.")

    # 2. Load Prompts
    try:
        core_instructions = _load_prompt_file(CORE_INSTRUCTIONS_FILE)
        institution_prompt_file = PROMPT_FILES.get(institution_name)

        if not institution_prompt_file:
            raise LLMError(
                message=f"No prompt file configured for institution: {institution_name}",
                provider="pydantic-ai"
            )
        institution_instructions = _load_prompt_file(institution_prompt_file)

    except (FileNotFoundError, IOError) as e:
        # Logged in _load_prompt_file, re-raise specific error type
        raise e
    except LLMError as e:
         # Logged before raising
         raise e


    # 3. Construct System Prompt for PydanticAI
    # Combine instructions. The result_type handles the schema part.
    system_prompt = (
        f"{core_instructions}\n\n"
        f"Institution Specific Instructions ({institution_name}):\n"
        f"{institution_instructions}\n\n"
        "**Task:** Analyze the user-provided bank statement markdown content. "
        "Extract all relevant information according to the defined structure. "
        "Ensure all fields in the structure are populated accurately based on the content."
    )

    # 4. Configure PydanticAI Agent
    # Use a Gemini model suitable for structured output, ideally one supporting function calling/tools
    # Default to 1.5 Flash via Config, ensure it's prefixed correctly for PydanticAI
    llm_model_name = Config.DEFAULT_LLM_MODEL or "gemini-1.5-flash-001" # Example, adjust if needed
    # PydanticAI expects 'google-gla:' prefix for Gemini via Generative Language API
    # Or 'google-vertex:' if using Vertex AI
    # Assuming Generative Language API based on previous extractor
    pydantic_ai_model_name = f"google-gla:{llm_model_name}"

    # Ensure API key is set (PydanticAI reads GEMINI_API_KEY from env by default)
    if not Config.GEMINI_API_KEY:
        raise LLMError("GEMINI_API_KEY environment variable not set.", provider="pydantic-ai")

    try:
        # Timeout can be implicitly handled by the underlying HTTP client PydanticAI uses,
        # or configured if using a custom provider/client. Default should be reasonable.
        agent = Agent(
            pydantic_ai_model_name,
            system_prompt=system_prompt,
            result_type=StatementData # Crucial: Tell PydanticAI the target structure
        )
        logger.info(f"Initialized PydanticAI Agent with model: {pydantic_ai_model_name}")

    except Exception as e:
        logger.error(f"Failed to initialize PydanticAI Agent: {str(e)}", exc_info=True)
        raise LLMError(f"Failed to initialize PydanticAI Agent: {str(e)}", provider="pydantic-ai")

    # 5. Run Extraction
    try:
        logger.info(f"Sending extraction request for {institution_name} via PydanticAI...")
        # The markdown content goes as the user message/query
        result = agent.run_sync(markdown_content)
        extracted_data: StatementData = result.data # Access the validated Pydantic model

        logger.info(f"Successfully extracted and validated data for {institution_name} using PydanticAI.")

        # 6. Save to Cache
        _save_extraction_result(extraction_path, extracted_data)

        return extracted_data

    except PydanticAIError as e:
        # Handles errors from the PydanticAI library specifically
        # This could include API errors, validation errors during generation, etc.
        logger.error(f"PydanticAI extraction failed: {str(e)}", exc_info=True)
        # Check if the error contains more details, e.g., from the LLM response
        error_details = getattr(e, 'message', str(e)) # Basic example
        raise LLMError(
            message=f"PydanticAI extraction failed: {error_details}",
            provider="pydantic-ai",
            original_exception=e
        )
    except ValidationError as e:
         # This might occur if the LLM output doesn't strictly match the Pydantic model
         # *after* the run_sync call, although PydanticAI aims to handle this internally.
         # Catching it here provides an extra layer of safety.
         logger.error(f"Final validation failed for PydanticAI output: {str(e)}", exc_info=True)
         raise LLMError(
             message=f"LLM output failed final validation against StatementData model: {str(e)}",
             provider="pydantic-ai",
             original_exception=e
         )
    except Exception as e:
        # Catch any other unexpected errors during the run
        logger.error(f"Unexpected error during PydanticAI extraction: {str(e)}", exc_info=True)
        raise LLMError(
            message=f"Unexpected error during PydanticAI extraction: {str(e)}",
            provider="pydantic-ai",
            original_exception=e
        )

# Example Usage (Optional, for testing)
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    # This requires prompts and models setup to run directly
    # Create dummy markdown and select an institution with a prompt file
    dummy_markdown = """
    JPMorgan Chase Bank Statement
    Account Number: ****1234
    Statement Period: 01/01/2024 - 01/31/2024
    Summary:
    Beginning Balance: $1000.00
    Total Deposits: $500.00
    Total Withdrawals: $200.00
    Ending Balance: $1300.00
    Transactions:
    01/15/2024 Deposit Check #123 $500.00
    01/20/2024 Withdrawal ATM $200.00
    """
    institution = 'JPMorgan Chase'

    # Make sure GEMINI_API_KEY is set in your environment for this test
    if not os.getenv('GEMINI_API_KEY'):
        print("Please set the GEMINI_API_KEY environment variable to run this example.")
    else:
        try:
            extracted = extract_structured_data_with_pydanticai(dummy_markdown, institution)
            print("\n--- Extracted Data ---")
            print(extracted.model_dump_json(indent=2))
            print("\nExtraction Successful!")
        except (LLMError, FileNotFoundError, IOError, KeyError) as e:
            print(f"\n--- Extraction Failed ---")
            print(f"Error: {e}")
        except Exception as e:
            print(f"\n--- An Unexpected Error Occurred ---")
            print(f"Error: {e}") 