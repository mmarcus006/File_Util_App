"""Custom exception hierarchy for extraction workflow."""
import sys
from pathlib import Path

# Add parent directory to path for direct script execution
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

class ExtractionError(RuntimeError):
    """Base-class for all extraction related errors."""

class OpenRouterHTTPError(ExtractionError):
    """Raised when OpenRouter returns a non‑200 status code."""

class OpenRouterParseError(ExtractionError):
    """Raised when the assistant's response cannot be parsed as JSON."""

class ValidationError(ExtractionError):
    """Raised when the response fails Pydantic validation."""

class LLMExtractionError(ExtractionError):
    """Raised when there's an error during LLM extraction process."""

class InvalidLLMJson(ExtractionError):
    """Raised when the LLM returns invalid JSON that cannot be parsed."""