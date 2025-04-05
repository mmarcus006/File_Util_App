"""
Configuration file for Supabase database credentials.
"""
import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase Configuration
SUPABASE_CONFIG: Dict[str, Any] = {
    "url": os.getenv("SUPABASE_URL"),
    "anon_key": os.getenv("SUPABASE_ANON_KEY"),
    "service_role_key": os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
    "jwt_secret": os.getenv("SUPABASE_JWT_SECRET"),
    "access_token": os.getenv("SUPABASE_ACCESS_TOKEN")
}

# Database schema configuration
DB_SCHEMA = os.getenv("SUPABASE_DB_SCHEMA", "public")  # The default schema in Supabase

# Other configuration settings
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "t") 