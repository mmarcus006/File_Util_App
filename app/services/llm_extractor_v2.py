"""
LLM extractor service for Bank Statement Analyzer.

This module provides functionality for extracting structured data from bank statements
using the native Google Generative AI Python library.
"""

import logging
import json
import os
from typing import Dict, Any, Optional, List, Union, cast
from pathlib import Path
import base64

# Use native Google Generative AI library
import google.generativeai as genai
from google.generativeai.types import GenerationConfig

from app.config import Config
from app.utils.error_handler import LLMError, BankStatementError
# Import the schema from models
from app.models.models import StatementData

# Configure logging
logger = logging.getLogger(__name__)

class LLMExtractor:
    """LLM extractor for interacting with the native Gemini API."""
    
    # Prompt file paths
    PROMPT_FILES: Dict[str, str] = {
        'JPMorgan Chase': 'prompts/jpmorgan_chase.txt',
        'Morgan Stanley': 'prompts/morgan_stanley.txt',
        'Goldman Sachs': 'prompts/goldman_sachs.txt'
    }
    
    # Core instructions file
    CORE_INSTRUCTIONS_FILE = 'prompts/core_instructions.txt'
    
    def __init__(self) -> None:
        """Initialize LLM extractor."""
        # Model name for Gemini
        # Use a model compatible with JSON mode, e.g., gemini-1.5-flash-001 or gemini-1.5-pro-001
        self.model_name = Config.DEFAULT_LLM_MODEL or "gemini-2.0-flash" 
        self.timeout = float(Config.LLM_TIMEOUT) # Timeout is handled differently, but keep for reference if needed
        
        # Get Gemini API Key
        gemini_api_key = Config.GEMINI_API_KEY
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY is not set in the environment variables.")

        # Configure the Gemini API
        try:
            # Configure the API key - using proper API from latest package version
            genai.configure(api_key=gemini_api_key) #type: ignore
            # Create the generative model - using proper API from latest package version
            self.model = genai.GenerativeModel(model_name=self.model_name) #type: ignore
            logger.info(f"Successfully initialized Gemini model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to configure Google Generative AI client: {str(e)}")
            raise LLMError(
                message=f"Failed to configure Google Generative AI client: {str(e)}",
                provider="google-genai"
            )
        
        # Load core instructions
        self.core_instructions = self._load_prompt_file(self.CORE_INSTRUCTIONS_FILE)
        
        logger.info(f"LLM Extractor initialized with native model: {self.model_name}")
    
    def _load_prompt_file(self, file_path: str) -> str:
        """Load prompt template from file."""
        try:
            # Use Pathlib for robust path handling
            base_path = Path(__file__).resolve().parent.parent.parent 
            full_path = base_path / file_path
            logger.debug(f"Attempting to load prompt file from: {full_path}")
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except FileNotFoundError:
            logger.error(f"Prompt file not found: {full_path}")
            raise FileNotFoundError(f"Prompt file not found: {full_path}")
        except Exception as e:
            logger.error(f"Error loading prompt file {file_path}: {str(e)}")
            raise
            
    def _get_cached_extraction_path(self, markdown_content: str, institution_name: str) -> Path:
        """Get the path for cached extraction result.
        
        Args:
            markdown_content: Markdown content to create a unique identifier from
            institution_name: Name of the institution
            
        Returns:
            Path object for the extraction cache file
        """
        # Create a safe, unique filename based on the first 100 chars of content
        # and institution name to identify this specific extraction
        content_hash = str(hash(markdown_content[:100]))
        extraction_filename = f"extraction_{institution_name.lower().replace(' ', '_')}_{content_hash}.json"
        
        # Save to a dedicated cache directory in the application root
        base_path = Path(__file__).resolve().parent.parent.parent
        cache_dir = base_path / "cache" / "extractions"
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        return cache_dir / extraction_filename
    
    def _save_extraction_result(self, extraction_path: Path, extraction_data: Dict[str, Any]) -> None:
        """Save extraction result to a JSON file.
        
        Args:
            extraction_path: Path to save the extraction result
            extraction_data: Extracted data to save
        """
        try:
            with open(extraction_path, 'w', encoding='utf-8') as f:
                json.dump(extraction_data, f, indent=2)
            logger.info(f"Saved extraction result to {extraction_path}")
        except Exception as e:
            logger.error(f"Failed to save extraction result to {extraction_path}: {str(e)}")
            # Don't raise an exception here, as this is a non-critical operation
    
    def _load_extraction_result(self, extraction_path: Path) -> Optional[Dict[str, Any]]:
        """Load extraction result from a JSON file.
        
        Args:
            extraction_path: Path to the extraction result file
            
        Returns:
            Extracted data if file exists and is valid, None otherwise
        """
        try:
            if extraction_path.exists():
                with open(extraction_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logger.info(f"Loaded extraction result from {extraction_path}")
                return data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse extraction result from {extraction_path}: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to load extraction result from {extraction_path}: {str(e)}")
        
        return None
    
    def extract_data(
        self, 
        markdown_content: str, 
        institution_name: str
    ) -> Dict[str, Any]:
        """Extract structured data from markdown content using the native Gemini API.
        
        Args:
            markdown_content: Markdown content of bank statement
            institution_name: Name of financial institution
            
        Returns:
            Extracted structured data as dictionary
            
        Raises:
            LLMError: If LLM API call fails or parsing fails.
        """
        # First check if we have a cached extraction
        extraction_path = self._get_cached_extraction_path(markdown_content, institution_name)
        
        # Try to load cached extraction
        cached_data = self._load_extraction_result(extraction_path)
        if cached_data:
            logger.info(f"Using cached extraction result for {institution_name}")
            return cached_data
        
        try:
            # Get prompt file for institution
            prompt_file = self.PROMPT_FILES.get(institution_name)
            if not prompt_file:
                raise LLMError(
                    message=f"No prompt file found for institution: {institution_name}",
                    provider="google-genai"
                )
            
            # Load institution-specific instructions
            institution_instructions = self._load_prompt_file(prompt_file)
            
            # Combine core instructions and institution-specific instructions
            # Prepare the full prompt content. Ensure no JSON examples are in the prompt itself.
            # Add a clear instruction to provide output matching the schema.
            prompt = (
                f"{self.core_instructions}\n\n"
                f"{institution_instructions}\n\n"
                "**Instructions:** Extract the relevant information from the following markdown "
                "content and structure it according to the provided JSON schema. "
                "Only output the JSON object.\n\n"
                f"**Markdown Content:**\n\n{markdown_content}"
            )
            
            # Log request info
            logger.info(f"Sending extraction request to {self.model_name} using native client")
            logger.debug(f"Prompt length: {len(prompt)} chars")
            
            # Create generation config - use proper GenerationConfig object
            generation_config = GenerationConfig(
                temperature=0.1,
                max_output_tokens=8000,
                response_mime_type="application/json"
            )
            
            # Call the Gemini API
            response = self.model.generate_content(
                contents=prompt,
                generation_config=generation_config
            )

            if hasattr(response, 'text') and response.text:
                try:
                    # Parse the JSON string from the response text
                    extracted_json = json.loads(response.text)
                    
                    # Save the extraction result
                    self._save_extraction_result(extraction_path, extracted_json)
                    
                    return extracted_json
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode JSON from LLM response: {str(e)}")
                    logger.debug(f"Raw LLM response text: {response.text}")
                    raise LLMError(
                        message=f"Failed to decode JSON from LLM response: {str(e)}",
                        provider="google-genai"
                    )
                except Exception as e:
                    logger.error(f"Failed to process LLM JSON response: {str(e)}")
                    logger.debug(f"Raw LLM response text: {response.text}")
                    raise LLMError(
                        message=f"Failed to process LLM response: {str(e)}",
                        provider="google-genai"
                    )
            else:
                # Handle cases where the response might be blocked or empty
                # Check prompt_feedback for block reasons
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

        # Specific Google GenAI errors (add more as needed based on library specifics)
        except Exception as e: # Catch-all for other potential API or library errors
            logger.error(f"Unexpected error during extraction: {str(e)}", exc_info=True)
            # You might want to check for specific exception types from google.api_core.exceptions
            raise LLMError(
                message=f"Unexpected error calling Google GenAI API: {str(e)}",
                provider="google-genai"
            )