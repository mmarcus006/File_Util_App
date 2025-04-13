"""
Configuration module for the FDD document management system.
Loads environment variables and provides configuration for the application.
"""

import os
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from pathlib import Path

# Calculate the path to the .env file in the same directory as config.py
dotenv_path = Path(__file__).parent / ".env"

# Load environment variables from the specified .env file
load_dotenv(dotenv_path=dotenv_path)

# Configure logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class Config:
    """Configuration class for the application."""

    # Supabase configuration
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
    SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    # S3 configuration
    S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "your-existing-bucket-name")
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

    @classmethod
    def validate(cls) -> bool:
        """
        Validate that all required configuration variables are set.
        
        Returns:
            bool: True if all required variables are set, False otherwise.
        """
        required_vars = [
            "SUPABASE_URL",
            "SUPABASE_ANON_KEY",
            "S3_BUCKET_NAME",
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
        ]
        
        missing_vars = [var for var in required_vars if not getattr(cls, var)]
        
        if missing_vars:
            logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
            return False
            
        return True

    @classmethod
    def get_supabase_config(cls) -> Dict[str, str | None]:
        """
        Get Supabase configuration.
        
        Returns:
            Dict[str, str | None]: Dictionary with Supabase configuration.
        """
        return {
            "url": cls.SUPABASE_URL,
            "anon_key": cls.SUPABASE_ANON_KEY,
            "service_role_key": cls.SUPABASE_SERVICE_ROLE_KEY,
        }

    @classmethod
    def get_s3_config(cls) -> Dict[str, str | None]:
        """
        Get S3 configuration.
        
        Returns:
            Dict[str, str | None]: Dictionary with S3 configuration.
        """
        return {
            "bucket_name": cls.S3_BUCKET_NAME,
            "aws_access_key_id": cls.AWS_ACCESS_KEY_ID,
            "aws_secret_access_key": cls.AWS_SECRET_ACCESS_KEY,
            "region_name": cls.AWS_REGION,
        }


# Validate configuration on import
if not Config.validate():
    logger.warning("Configuration validation failed. Some features may not work correctly.")
