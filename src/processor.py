import os
import json
import time
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Union, Optional, Tuple, List
import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from pydantic import ValidationError

# Assuming the models are defined in models.py within the same directory
from db.models import FDDAnalysisResult

# --- Constants ---
# Use Path for better cross-platform compatibility
PROMPT_FILE_PATH = Path(__file__).parent.parent.parent / "prompts" / "optimized_section_prompt.txt"
DEFAULT_GEMINI_MODEL = "gemini-2.0-flash"
API_KEY_ENV_VAR = "GEMINI_API_KEY"
FALLBACK_API_KEY = "AIzaSyB9EuxdpvGxH5r-V_2crM_NAU7ZJmXOlgI"

# File tracking constants
TRACKING_CSV_PATH = Path(__file__).parent.parent.parent / "data" / "processed_files.csv"
OUTPUT_DIR = Path(__file__).parent.parent.parent / "data" / "processed_outputs"

# --- File Tracking System ---
class FileTracker:
    """Tracks processed files to avoid duplicate processing."""
    
    @classmethod
    def ensure_dirs_exist(cls) -> None:
        """Ensure tracking CSV and output directories exist."""
        # Make sure the parent directories exist
        TRACKING_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        # Create tracking CSV if it doesn't exist
        if not TRACKING_CSV_PATH.exists():
            with open(TRACKING_CSV_PATH, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['filename', 'original_path', 'output_path'])
    
    @classmethod
    def get_processed_files(cls) -> Dict[str, Dict[str, str]]:
        """
        Get a dictionary of processed files.
        
        Returns:
            Dict with filenames as keys and dict of original_path/output_path as values
        """
        cls.ensure_dirs_exist()
        processed_files = {}
        
        try:
            with open(TRACKING_CSV_PATH, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if 'filename' in row and row['filename']:
                        processed_files[row['filename']] = {
                            'original_path': row.get('original_path', ''),
                            'output_path': row.get('output_path', '')
                        }
        except Exception as e:
            print(f"Warning: Error reading tracking CSV: {e}")
            
        return processed_files
    
    @classmethod
    def add_processed_file(cls, original_path: Union[str, Path], output_path: Union[str, Path]) -> None:
        """
        Add a processed file to the tracking CSV.
        
        Args:
            original_path: Full path to the original JSON file
            output_path: Path where the output JSON was saved
        """
        cls.ensure_dirs_exist()
        
        # Convert paths to Path objects for consistency
        orig_path = Path(original_path)
        out_path = Path(output_path)
        
        # Extract just the filename
        filename = orig_path.name
        
        # Get existing processed files to avoid duplicates
        processed_files = cls.get_processed_files()
        
        # Update or add the entry
        processed_files[filename] = {
            'original_path': str(orig_path),
            'output_path': str(out_path)
        }
        
        # Write back to CSV
        with open(TRACKING_CSV_PATH, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['filename', 'original_path', 'output_path'])
            writer.writeheader()
            for fname, paths in processed_files.items():
                writer.writerow({
                    'filename': fname,
                    'original_path': paths['original_path'],
                    'output_path': paths['output_path']
                })
    
    @classmethod
    def is_file_processed(cls, file_path: Union[str, Path]) -> bool:
        """
        Check if a file has already been processed.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if the file has been processed, False otherwise
        """
        filename = Path(file_path).name
        return filename in cls.get_processed_files()
    
    @classmethod
    def get_output_path(cls, file_path: Union[str, Path]) -> Path:
        """
        Generate an output path for the processed result.
        
        Args:
            file_path: Path to the original file
            
        Returns:
            Path where the output should be saved
        """
        filename = Path(file_path).name
        base_name = filename.split('_content_list.json')[0]
        output_filename = f"{base_name}_analysis_result.json"
        return OUTPUT_DIR / output_filename


# --- Rate Limiting ---
class RateLimiter:
    """Basic rate limiter for Gemini API."""
    # Limits
    MAX_TOKENS_PER_MINUTE = 1_000_000
    MAX_REQUESTS_PER_MINUTE = 15
    MAX_REQUESTS_PER_DAY = 1_500
    
    # Counters
    tokens_this_minute = 0
    requests_this_minute = 0
    requests_today = 0
    
    # Timestamp of last reset
    last_minute_reset = time.time()
    
    @classmethod
    def check_and_reset_minute_counters(cls) -> None:
        """Reset minute-based counters if a minute has passed."""
        current_time = time.time()
        if current_time - cls.last_minute_reset >= 60:
            cls.tokens_this_minute = 0
            cls.requests_this_minute = 0
            cls.last_minute_reset = current_time
    
    @classmethod
    def check_limits(cls) -> Tuple[bool, str]:
        """
        Check if we're within rate limits.
        
        Returns:
            (is_within_limits, reason_if_exceeded)
        """
        cls.check_and_reset_minute_counters()
        
        if cls.tokens_this_minute >= cls.MAX_TOKENS_PER_MINUTE:
            return False, f"Token limit exceeded: {cls.tokens_this_minute}/{cls.MAX_TOKENS_PER_MINUTE} tokens this minute"
        
        if cls.requests_this_minute >= cls.MAX_REQUESTS_PER_MINUTE:
            return False, f"Request limit exceeded: {cls.requests_this_minute}/{cls.MAX_REQUESTS_PER_MINUTE} requests this minute"
        
        if cls.requests_today >= cls.MAX_REQUESTS_PER_DAY:
            return False, f"Daily request limit exceeded: {cls.requests_today}/{cls.MAX_REQUESTS_PER_DAY} requests today"
        
        return True, ""
    
    @classmethod
    def track_request(cls, token_count: int = 0) -> None:
        """Record a request with its token usage."""
        cls.check_and_reset_minute_counters()
        cls.tokens_this_minute += token_count
        cls.requests_this_minute += 1
        cls.requests_today += 1
    
    @classmethod
    def get_usage_stats(cls) -> Dict[str, Any]:
        """Return current usage statistics."""
        cls.check_and_reset_minute_counters()
        return {
            "tokens_this_minute": cls.tokens_this_minute,
            "requests_this_minute": cls.requests_this_minute,
            "requests_today": cls.requests_today,
            "tokens_per_minute_limit": cls.MAX_TOKENS_PER_MINUTE,
            "requests_per_minute_limit": cls.MAX_REQUESTS_PER_MINUTE,
            "requests_per_day_limit": cls.MAX_REQUESTS_PER_DAY
        }


# --- Helper Functions ---

def _load_text_file(file_path: Union[str, Path]) -> str:
    """Loads the content of a text file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Error: File not found at {file_path}")
    except Exception as e:
        raise RuntimeError(f"Error reading file {file_path}: {e}")

def _load_json_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Loads the content of a JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Error: JSON file not found at {file_path}")
    except json.JSONDecodeError:
        raise ValueError(f"Error: Invalid JSON format in file {file_path}")
    except Exception as e:
        raise RuntimeError(f"Error reading JSON file {file_path}: {e}")

def _extract_token_count(response) -> int:
    """Extract token count from Gemini API response if available."""
    try:
        if hasattr(response, 'usage_metadata') and response.usage_metadata:
            return response.usage_metadata.total_token_count
    except:
        pass
    return 0  # Return 0 if token count can't be determined

def _save_analysis_result(result: FDDAnalysisResult, output_path: Union[str, Path]) -> None:
    """
    Save analysis result to a JSON file.
    
    Args:
        result: The validated analysis result to save
        output_path: Where to save the result
    """
    # Convert Path to string if needed
    output_path_str = str(output_path)
    
    # Ensure the directory exists
    Path(output_path_str).parent.mkdir(parents=True, exist_ok=True)
    
    # Save the result
    with open(output_path_str, 'w', encoding='utf-8') as f:
        f.write(result.model_dump_json(indent=2))


# --- Core Processing Function ---

def analyze_fdd_json(
    fdd_json_path: Union[str, Path],
    prompt_path: Union[str, Path] = PROMPT_FILE_PATH,
    model_name: str = DEFAULT_GEMINI_MODEL,
    api_key: str | None = None,
    fallback_api_key: str | None = FALLBACK_API_KEY,
    force_reprocess: bool = False
) -> Tuple[FDDAnalysisResult, str]:
    """
    Analyzes an FDD JSON file using the Gemini API to extract structured information.

    Args:
        fdd_json_path: Path to the FDD content JSON file.
        prompt_path: Path to the prompt text file. Defaults to PROMPT_FILE_PATH.
        model_name: The Gemini model to use. Defaults to DEFAULT_GEMINI_MODEL.
        api_key: Google Gemini API key. If None, attempts to read from API_KEY_ENV_VAR.
        fallback_api_key: Alternative API key to try if the primary fails.
        force_reprocess: Whether to reprocess files that have already been processed.

    Returns:
        A tuple of (FDDAnalysisResult, output_path) containing the validated data and output path.

    Raises:
        ValueError: If API key is not found or if the API response is invalid JSON
                    or doesn't match the Pydantic model.
        FileNotFoundError: If the prompt or FDD JSON file is not found.
        RuntimeError: For other API or file reading errors.
    """
    # Convert to Path for consistency
    fdd_json_path = Path(fdd_json_path)
    
    # 0. Check if already processed
    if not force_reprocess and FileTracker.is_file_processed(fdd_json_path):
        output_path = FileTracker.get_processed_files()[fdd_json_path.name]['output_path']
        print(f"File {fdd_json_path.name} already processed. Loading from {output_path}")
        
        # Load and return the previously processed result
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return FDDAnalysisResult.model_validate(data), output_path
    
    # 1. Check rate limits
    within_limits, limit_reason = RateLimiter.check_limits()
    if not within_limits:
        raise RuntimeError(f"Rate limit exceeded: {limit_reason}")
    
    # 2. Get API Key
    resolved_api_key = api_key or os.getenv(API_KEY_ENV_VAR)
    if not resolved_api_key:
        raise ValueError(f"Gemini API key not provided and not found in environment variable '{API_KEY_ENV_VAR}'")

    # 3. Load Prompt and FDD Data
    prompt_text = _load_text_file(prompt_path)
    # Load the FDD JSON data as a string to append to the prompt
    fdd_json_content_str = json.dumps(_load_json_file(fdd_json_path)) # Read as dict, dump back to string

    # 4. Combine Prompt and Data for API Call
    full_prompt = f"""{prompt_text}

**Input Data:**
```json
{fdd_json_content_str}
```"""

    # 5. Call Gemini API (with fallback)
    response = None
    response_text = None
    current_api_key = resolved_api_key
    
    # Try primary key, then fallback if needed
    for attempt, key in enumerate([current_api_key, fallback_api_key]):
        if attempt > 0 and not key:
            break  # Skip fallback if no fallback key
            
        try:
            # Configure Gemini Client
            genai.configure(api_key=key) #type: ignore
            model = genai.GenerativeModel(model_name) #type: ignore
            
            # Configure for deterministic output and expect JSON
            generation_config = GenerationConfig(
                temperature=0.0,
                response_mime_type="application/json",
            )
            
            # Make the API call
            response = model.generate_content(
                contents=full_prompt,
                generation_config=generation_config
            )
            
            # Extract token usage and track the request
            token_count = _extract_token_count(response)
            RateLimiter.track_request(token_count)
            
            # Ensure we access the text part correctly
            response_text = getattr(response, 'text', None)
            if response_text is None:
                # Look for text within parts if structured differently
                if hasattr(response, 'parts') and response.parts:
                    response_text = ''.join(part.text for part in response.parts if hasattr(part, 'text'))
                    
            # If we got a valid response, break the loop
            if response_text:
                break
                
        except Exception as e:
            if attempt == 0 and fallback_api_key:
                print(f"Primary API key failed: {e}. Trying fallback key...")
                current_api_key = fallback_api_key
            else:
                raise RuntimeError(f"Gemini API call failed with all keys: {e}")
    
    if not response_text:
        raise ValueError("Failed to extract text from Gemini response")

    # 6. Parse and Validate Response
    try:
        # The prompt explicitly asks for ONLY JSON, so the response text should be parseable
        extracted_data = json.loads(response_text.strip())
    except json.JSONDecodeError:
        raise ValueError(f"Gemini response was not valid JSON.\nRaw Response:\n{response_text}")

    try:
        validated_result = FDDAnalysisResult.model_validate(extracted_data)
    except ValidationError as e:
        raise ValueError(f"Gemini response JSON did not match expected schema.\nValidation Errors:\n{e}\nRaw JSON Data:\n{json.dumps(extracted_data, indent=2)}")

    # 7. Save the result and track the processed file
    output_path = FileTracker.get_output_path(fdd_json_path)
    _save_analysis_result(validated_result, output_path)
    FileTracker.add_processed_file(fdd_json_path, output_path)
    
    # 8. Return the structured data and output path
    return validated_result, str(output_path)


def get_api_usage() -> Dict[str, Any]:
    """Return current API usage statistics."""
    return RateLimiter.get_usage_stats()


def get_unprocessed_files(directory_path: Union[str, Path], content_list_suffix: str = "_content_list.json") -> List[Path]:
    """
    Find all FDD JSON files in a directory that haven't been processed yet.
    
    Args:
        directory_path: Directory to scan for JSON files
        content_list_suffix: Suffix to identify content list files
        
    Returns:
        List of paths to unprocessed files
    """
    directory = Path(directory_path)
    all_files = list(directory.glob(f"**/*{content_list_suffix}"))
    processed_files = FileTracker.get_processed_files()
    
    # Filter out files that have already been processed
    unprocessed = [f for f in all_files if f.name not in processed_files]
    return unprocessed


if __name__ == "__main__":
    # Specify a directory to process or a single file
    #sample_fdd_json = r"C:\Projects\File_Util_App\9Round_Franchising_LLC_FDD_2024_ID636440.pdf-a8429847-13bc-4dc6-95a6-d41569e2eb3f\bbd94cce-d087-49e0-a7b7-ba787df47de7_content_list.json"
    
    directory = "C:/Users/mille/MinerU"

    # Ask whether to process a single file or a directory
    choice = input("Process a (s)ingle file or (d)irectory? [s/d]: ").lower()
    
    if choice == 'd':
        unprocessed = get_unprocessed_files(directory)
        
        if not unprocessed:
            print(f"No unprocessed files found in {directory}")
        else:
            print(f"Found {len(unprocessed)} unprocessed files")
            process_count = len(unprocessed) # Process up to 5 files
            
            for i, file_path in enumerate(unprocessed[:process_count]):
                print(f"\nProcessing file {i+1}/{process_count}: {file_path.name}")
                
                try:
                    result, output_path = analyze_fdd_json(file_path)
                    print(f"Successfully processed. Output saved to: {output_path}")
                    
                    # Display API usage statistics
                    usage = get_api_usage()
                    print(f"API Usage - Tokens: {usage['tokens_this_minute']:,}/{usage['tokens_per_minute_limit']:,}, " +
                          f"Requests: {usage['requests_this_minute']}/{usage['requests_per_minute_limit']}")
                          
                    # If we're close to rate limits, wait a bit
                    if usage['tokens_this_minute'] > usage['tokens_per_minute_limit'] * 0.8 or \
                       usage['requests_this_minute'] > usage['requests_per_minute_limit'] * 0.8:
                        wait_time = 65 - (time.time() - RateLimiter.last_minute_reset)
                        if wait_time > 0:
                            print(f"Approaching rate limits. Waiting {wait_time:.1f} seconds...")
                            time.sleep(wait_time)
                            
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
    else:
        # Process a single file
        if not os.path.exists(sample_fdd_json):
            sample_fdd_json = input("Enter the full path to the FDD JSON content file: ")
            
        if not os.path.exists(sample_fdd_json):
            print(f"Error: Sample FDD JSON file not found at: {sample_fdd_json}")
        else:
            print(f"Analyzing FDD JSON: {sample_fdd_json}")
            print(f"Using prompt: {PROMPT_FILE_PATH}")
            print(f"Using model: {DEFAULT_GEMINI_MODEL}")

            # Ensure API key is set as an environment variable named 'GEMINI_API_KEY'
            if not os.getenv(API_KEY_ENV_VAR):
                print(f"Warning: Environment variable '{API_KEY_ENV_VAR}' is not set. Will try fallback key if provided.")
                
            try:
                result, output_path = analyze_fdd_json(fdd_json_path=sample_fdd_json)
                print("\n--- Analysis Result ---")
                # Print first few fields for verification
                print(f"Franchise: {result.franchise_name}")
                print(f"Issuance Date: {result.issuance_date}")
                print(f"Output saved to: {output_path}")
                
                # Display API usage statistics
                usage = get_api_usage()
                print("\n--- API Usage ---")
                print(f"Tokens used this minute: {usage['tokens_this_minute']:,}/{usage['tokens_per_minute_limit']:,}")
                print(f"Requests this minute: {usage['requests_this_minute']}/{usage['requests_per_minute_limit']}")
                print(f"Requests today: {usage['requests_today']}/{usage['requests_per_day_limit']}")
                
                print("\nAnalysis complete.")
            except (ValueError, FileNotFoundError, RuntimeError) as e:
                print(f"\n--- Error during analysis ---")
                print(e)

