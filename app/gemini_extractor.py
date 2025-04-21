"""
Generic LLM Extractor with Gemini API

A modular script for generating structured outputs using Pydantic models and the Gemini LLM API.
Uses functional programming approach with simple, single-purpose functions.
"""

import os
import json
import logging
import hashlib
from typing import Dict, Any, Optional, List, Union, Type, TypeVar, Callable
from pathlib import Path

# Third-party imports
import google.generativeai as genai
from google.genai import types
from dotenv import load_dotenv
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Custom exceptions
class LLMError(Exception):
    """Exception raised for errors in the LLM API."""
    
    def __init__(self, message: str, provider: str = "unknown"):
        self.message = message
        self.provider = provider
        super().__init__(self.message)


class ConfigError(Exception):
    """Exception raised for errors in configuration."""
    
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class PromptError(Exception):
    """Exception raised for errors in prompt templates."""
    
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


# Configuration functions
def load_config_from_env() -> Dict[str, Any]:
    """Load configuration from environment variables.
    
    Returns:
        Dict[str, Any]: Configuration dictionary with all settings
        
    Raises:
        ConfigError: If required configuration is missing
    """
    # Load .env file if it exists
    load_dotenv()
    
    config = {
        "api_key": os.getenv("GEMINI_API_KEY"),
        "model_name": os.getenv("LLM_MODEL", "gemini-1.5-flash"),
        "temperature": float(os.getenv("LLM_TEMPERATURE", "0.1")),
        "cache_dir": os.getenv("CACHE_DIR", "cache"),
        "use_cache": os.getenv("USE_CACHE", "true").lower() == "true"
    }
    
    # Validate essential configuration
    if not config["api_key"]:
        raise ConfigError("GEMINI_API_KEY is not set in environment variables.")
    
    return config


def load_config_from_json(config_path: str) -> Dict[str, Any]:
    """Load configuration from a JSON file.
    
    Args:
        config_path: Path to the configuration JSON file
        
    Returns:
        Dict[str, Any]: Configuration dictionary with all settings
        
    Raises:
        ConfigError: If file cannot be loaded or required configuration is missing
    """
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Add default values for missing config items
        defaults = {
            "model_name": "gemini-1.5-flash",
            "temperature": 0.1,
            "cache_dir": "cache",
            "use_cache": True
        }
        
        for key, value in defaults.items():
            if key not in config:
                config[key] = value
        
        # Validate essential configuration
        if "api_key" not in config:
            raise ConfigError("api_key is not set in the config file.")
        
        return config
    except Exception as e:
        raise ConfigError(f"Failed to load configuration file: {str(e)}")


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from environment variables or a config file.
    
    Args:
        config_path: Optional path to a configuration file
        
    Returns:
        Dict[str, Any]: Configuration dictionary
    """
    if config_path and Path(config_path).exists():
        return load_config_from_json(config_path)
    else:
        return load_config_from_env()

def _load_file_content(file_path: Union[str, Path]) -> str:

    try:
        path = Path(file_path)
        if not path.exists() or not path.is_file():
             # Basic check for common extensions if the original path doesn't exist
            base_name = path.stem
            parent_dir = path.parent
            possible_extensions = ['.txt', '.md']
            found = False
            for ext in possible_extensions:
                check_path = parent_dir / f"{base_name}{ext}"
                if check_path.exists() and check_path.is_file():
                    path = check_path
                    found = True
                    break
            if not found:
                 raise PromptError(f"Prompt file not found at '{file_path}' (or with .txt/.md extension)")


        with open(path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception as e:
        if isinstance(e, PromptError):
            raise
        logger.error(f"Error loading file content from {file_path}: {str(e)}", exc_info=True)
        raise PromptError(f"Failed to load file content from {file_path}: {str(e)}")


def create_prompt(
    prompt_file: Union[str, Path],
    instructions_file: Optional[Union[str, Path]] = None,
    context_file: Optional[Union[str, Path]] = None
) -> str:
    """Construct a prompt by combining content from instruction, prompt, and context files.

    Args:
        prompt_file: Path to the main prompt file.
        instructions_file: Optional path to the system instructions file.
        context_file: Optional path to the additional context file.

    Returns:
        str: The complete combined prompt.

    Raises:
        PromptError: If any required file cannot be loaded.
    """
    prompt_parts: List[str] = []

    try:
        # Load instructions if provided
        if instructions_file:
            instructions_content = _load_file_content(instructions_file)
            prompt_parts.append(f"**System Instructions:**\n{instructions_content}")

        # Load main prompt (required)
        prompt_content = _load_file_content(prompt_file)
        prompt_parts.append(f"**Prompt:**\n{prompt_content}")

        # Load context if provided
        if context_file:
            context_content = _load_file_content(context_file)
            prompt_parts.append(f"**Additional Context:**\n{context_content}")

        # Combine parts with separators
        return "\n\n---\n\n".join(prompt_parts)

    except PromptError as e:
        # Re-raise PromptError with more context if needed, or just let it propagate
        logger.error(f"Failed to create prompt due to file loading error: {e}")
        raise # Re-raise the original PromptError
    except Exception as e:
        # Catch any other unexpected errors during prompt construction
        logger.error(f"Unexpected error creating prompt: {str(e)}", exc_info=True)
        raise PromptError(f"Failed unexpectedly during prompt creation: {str(e)}")


# Caching functions
def get_cache_path(cache_dir: str, prompt: str, model_name: str) -> Path:
    """Get cache file path for a specific prompt and model.
    
    Args:
        cache_dir: Directory for cache files
        prompt: The prompt sent to the LLM
        model_name: Name of the LLM model
        
    Returns:
        Path: Path to the cache file
    """
    # Create cache directory if it doesn't exist
    cache_dir_path = Path(cache_dir)
    cache_dir_path.mkdir(parents=True, exist_ok=True)
    
    # Create a deterministic, safe hash from the prompt
    prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
    
    # Create a safe filename
    cache_filename = f"{model_name.replace('-', '_')}_{prompt_hash}.json"
    
    return cache_dir_path / cache_filename


def get_cached_response(cache_dir: str, prompt: str, model_name: str) -> Optional[Dict[str, Any]]:
    """Get cached response if available.
    
    Args:
        cache_dir: Directory for cache files
        prompt: The prompt sent to the LLM
        model_name: Name of the LLM model
        
    Returns:
        Optional[Dict[str, Any]]: Cached response or None if not found
    """
    cache_path = get_cache_path(cache_dir, prompt, model_name)
    
    if cache_path.exists():
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load cache file {cache_path}: {str(e)}")
            return None
    
    return None


def save_response_to_cache(cache_dir: str, prompt: str, model_name: str, response: Dict[str, Any]) -> None:
    """Save response to cache.
    
    Args:
        cache_dir: Directory for cache files
        prompt: The prompt sent to the LLM
        model_name: Name of the LLM model
        response: The response to cache
    """
    cache_path = get_cache_path(cache_dir, prompt, model_name)
    
    try:
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(response, f, indent=2)
    except Exception as e:
        logger.warning(f"Failed to save response to cache {cache_path}: {str(e)}")


# Gemini API functions
def initialize_gemini_client(api_key: str) -> genai.Client:
    """Initialize the Gemini client."""
    try:
        # Initialize the client
        client = genai.Client(api_key=api_key)
        logger.info("Successfully initialized Gemini client.")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize Google Generative AI client: {str(e)}")
        raise LLMError(
            message=f"Failed to initialize Google Generative AI client: {str(e)}",
            provider="google-genai"
        )


def generate_json_with_gemini(
    client: genai.Client,
    model_name: str, 
    prompt: str, 
    temperature: float,
    max_output_tokens: int
) -> Dict[str, Any]:
    """Generate structured JSON response from the Gemini model."""
    try:
        # Create generation config using the imported types
        generation_config = types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            response_mime_type="application/json" # Ensure JSON mode is requested
        )
        
        # Call the Gemini API via the client
        response = client.models.generate_content(
            model=model_name, # Specify model name here
            contents=prompt,
            generation_config=generation_config
        )
        
        if hasattr(response, 'text') and response.text:
            try:
                # Parse the JSON string from the response text
                return json.loads(response.text)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode JSON from LLM response: {str(e)}")
                logger.debug(f"Raw LLM response text: {response.text}")
                raise LLMError(
                    message=f"Failed to decode JSON from LLM response: {str(e)}",
                    provider="google-genai"
                )
        else:
            # Handle cases where the response might be blocked or empty
            block_reason = getattr(response, 'prompt_feedback', None)
            if block_reason:
                logger.error(f"LLM request blocked. Reason: {block_reason}")
                raise LLMError(
                    message=f"LLM request blocked due to safety settings or other reasons: {block_reason}",
                    provider="google-genai"
                )
            else:
                logger.error("LLM response was empty.")
                raise LLMError(
                    message="LLM response was empty",
                    provider="google-genai"
                )
    except Exception as e:
        if isinstance(e, LLMError):
            raise
        
        logger.error(f"Unexpected error during generation: {str(e)}", exc_info=True)
        raise LLMError(
            message=f"Unexpected error calling Google GenAI API: {str(e)}",
            provider="google-genai"
        )


# Main extraction function
def extract_data(
    model_class: Type[T],
    prompt_file: Union[str, Path],
    instructions_file: Optional[Union[str, Path]] = None,
    context_file: Optional[Union[str, Path]] = None,
    config_path: Optional[str] = None
) -> T:
    """Extract structured data using Gemini LLM based on specified prompt files.

    Args:
        model_class: Pydantic model class for the expected output structure.
        prompt_file: Path to the main prompt file.
        instructions_file: Optional path to the system instructions file.
        context_file: Optional path to the additional context file.
        config_path: Optional path to a JSON configuration file.

    Returns:
        T: An instance of the Pydantic model_class populated with extracted data.

    Raises:
        LLMError: If the LLM call or data parsing fails.
        ConfigError: If configuration loading fails or is invalid.
        PromptError: If any prompt file cannot be loaded or constructed.
    """
    # Load configuration
    config = load_config(config_path)

    try:
        # Create prompt from files
        prompt = create_prompt(
            prompt_file=prompt_file,
            instructions_file=instructions_file,
            context_file=context_file
        )

        # Check cache if enabled
        if config["use_cache"]:
            cache_key_info = f"{instructions_file or ''}-{prompt_file}-{context_file or ''}"
            # Use a hash of the combined file info for cache lookup to avoid overly long filenames
            cache_hash_input = f"{prompt}_{config['model_name']}" # Include model name in hash input
            prompt_hash = hashlib.md5(cache_hash_input.encode()).hexdigest()

            cached_response = get_cached_response(
                cache_dir=config["cache_dir"],
                prompt=prompt_hash, # Use hash for cache key
                model_name=config["model_name"] # Model name is still useful for the filename itself
            )
            if cached_response:
                logger.info(f"Using cached response for prompt defined by: {cache_key_info}")
                # Ensure cached data conforms to the model
                try:
                    return model_class.parse_obj(cached_response)
                except Exception as parse_error:
                    logger.warning(f"Cached data validation failed for {cache_key_info}: {parse_error}. Re-generating.")
                    # Invalidate cache entry? For now, just proceed to generate
        
        # Initialize Gemini client
        client = initialize_gemini_client(
            api_key=config["api_key"]
        )
        
        # Call LLM
        extracted_data = generate_json_with_gemini(
            client=client, # Pass the client object
            model_name=config["model_name"], # Pass the model name string
            prompt=prompt,
            temperature=config["temperature"],
            max_output_tokens=config["max_output_tokens"] # Pass max_output_tokens from config
        )
        
        # Save to cache if enabled
        if config["use_cache"]:
             # Use the same hash as used for lookup
            save_response_to_cache(
                cache_dir=config["cache_dir"],
                prompt=prompt_hash, # Use hash for cache key
                model_name=config["model_name"],
                response=extracted_data
            )

        # Parse using Pydantic model
        return model_class.parse_obj(extracted_data)
    except Exception as e:
        if isinstance(e, (LLMError, ConfigError, PromptError)):
            raise
        
        logger.error(f"Failed to extract data: {str(e)}", exc_info=True)
        raise LLMError(
            message=f"Failed to extract data: {str(e)}",
            provider="google-genai"
        )


# Example usage
if __name__ == "__main__":
    from pydantic import BaseModel, Field
    from typing import List, Optional
    
    # Define a directory for prompts and context (adjust as needed)
    PROMPT_DIR = Path("./prompts")
    CONTEXT_DIR = Path("./context")
    PROMPT_DIR.mkdir(exist_ok=True)
    CONTEXT_DIR.mkdir(exist_ok=True)

    # --- Create Dummy Files for Example ---
    # You would replace these with your actual prompt/context files
    example_instructions_file = PROMPT_DIR / "example_instructions.md"
    example_prompt_file = PROMPT_DIR / "example_prompt.txt"
    example_context_file = CONTEXT_DIR / "example_data.txt"

    if not example_instructions_file.exists():
        with open(example_instructions_file, "w") as f:
            f.write("Extract the key information based on the provided context.")

    if not example_prompt_file.exists():
         with open(example_prompt_file, "w") as f:
             f.write("Summarize the document, list keywords, and assign a relevance score.")

    if not example_context_file.exists():
        with open(example_context_file, "w") as f:
            f.write("""
# Sample Document for Context

This is a sample document to demonstrate the LLM extractor using file-based prompts.
It contains text that will be included as context for the LLM.

## Key Points

1. Refactored prompt loading.
2. Uses direct file paths.
3. No more templates.
""")
    # --- End of Dummy File Creation ---

    # Example Pydantic model
    class ExampleOutput(BaseModel):
        title: str
        summary: str
        keywords: List[str]
        score: float = Field(ge=0, le=10)
        metadata: Optional[Dict[str, Any]] = None
    
    # Extract data using file paths
    try:
        # Example 1: Using instruction, prompt, and context files
        print("\n--- Example 1: Using all three files ---")
        result1 = extract_data(
            model_class=ExampleOutput,
            instructions_file=example_instructions_file,
            prompt_file=example_prompt_file,
            context_file=example_context_file
        )
        print(f"Extracted data (Example 1):\n{result1.json(indent=2)}")

        # Example 2: Using only prompt and context files
        print("\n--- Example 2: Using prompt and context files ---")
        result2 = extract_data(
            model_class=ExampleOutput,
            prompt_file=example_prompt_file,
            context_file=example_context_file
            # instructions_file is omitted
        )
        print(f"Extracted data (Example 2):\n{result2.json(indent=2)}")

        # Example 3: Using only the prompt file
        print("\n--- Example 3: Using only prompt file ---")
        # Create a dummy prompt file that contains everything needed
        simple_prompt_file = PROMPT_DIR / "simple_prompt.txt"
        if not simple_prompt_file.exists():
            with open(simple_prompt_file, "w") as f:
                f.write("""
Extract the title, summary, keywords, and score (0-10) from the following text:

# Sample Document for Single Prompt

This is a sample document contained entirely within the prompt file.
Key points: Single file, self-contained, specific task.
""")

        result3 = extract_data(
            model_class=ExampleOutput,
            prompt_file=simple_prompt_file
            # instructions_file and context_file are omitted
        )
        print(f"Extracted data (Example 3):\n{result3.json(indent=2)}")

    except (LLMError, ConfigError, PromptError) as e:
        print(f"\nError during extraction: {type(e).__name__} - {str(e)}")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {str(e)}")
