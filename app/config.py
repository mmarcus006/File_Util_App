"""
Configuration module for Bank Statement Analyzer.

This module loads environment variables and provides configuration settings.
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional, List

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class Config:
    """Application configuration class."""
    
    # API Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    MISTRAL_API_KEY: str = os.getenv("MISTRAL_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPEN_ROUTER_API_KEY: str = os.getenv("OPEN_ROUTER_API_KEY", "")
    JINA_API_KEY: str = os.getenv("JINA_API_KEY", "")
    REQUESTY_API_KEY: str = os.getenv("REQUESTY_API_KEY", "")
    
    # LLM Configuration
    DEFAULT_LLM_PROVIDER: str = os.getenv("DEFAULT_LLM_PROVIDER", "gemini")
    DEFAULT_LLM_MODEL: str = os.getenv("DEFAULT_LLM_MODEL", "gemini-2.5-pro")
    LLM_TIMEOUT: int = int(os.getenv("LLM_TIMEOUT", "30"))
    
    # Docling Configuration
    DOCLING_DO_OCR: bool = os.getenv("DOCLING_DO_OCR", "True").lower() == "true"
    DOCLING_OCR_LANGUAGES: List[str] = os.getenv("DOCLING_OCR_LANGUAGES", "eng").split(",")
    DOCLING_NUM_THREADS: int = int(os.getenv("DOCLING_NUM_THREADS", "4"))
    DOCLING_ACCELERATOR_DEVICE: str = os.getenv("DOCLING_ACCELERATOR_DEVICE", "AUTO")
    DOCLING_USE_TESSERACT: bool = os.getenv("DOCLING_USE_TESSERACT", "True").lower() == "true"
    DOCLING_TESSERACT_PATH: Optional[str] = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

    # Application Settings
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate that required configuration is present."""
        is_valid = True
        
        # Validate LLM API keys
        if cls.DEFAULT_LLM_PROVIDER == "gemini" and not cls.GEMINI_API_KEY:
            logger.error("GEMINI_API_KEY is required when using Gemini provider")
            is_valid = False
        
        # Add more validations as needed
        
        return is_valid
    
    @classmethod
    def get_llm_api_key(cls) -> str:
        """Get the API key for the default LLM provider."""
        provider = cls.DEFAULT_LLM_PROVIDER.lower()
        
        if provider == "gemini":
            return cls.GEMINI_API_KEY
        elif provider == "mistral":
            return cls.MISTRAL_API_KEY
        elif provider == "anthropic":
            return cls.ANTHROPIC_API_KEY
        elif provider == "openai":
            return cls.OPENAI_API_KEY
        elif provider == "openrouter":
            return cls.OPEN_ROUTER_API_KEY
        elif provider == "jina":
            return cls.JINA_API_KEY
        elif provider == "requesty":
            return cls.REQUESTY_API_KEY
        else:
            logger.warning(f"Unknown provider: {provider}. Defaulting to Gemini.")
            return cls.GEMINI_API_KEY 