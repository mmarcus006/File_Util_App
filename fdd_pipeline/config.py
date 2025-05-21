"""
Configuration settings for FDD Pipeline
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"

# Create directories if they don't exist
for dir_path in [DATA_DIR, OUTPUT_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# R2 Configuration
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_ENDPOINT_URL = os.getenv("R2_ENDPOINT_URL")

# Specific R2 Buckets for different types of data
R2_BUCKET_PDFS = "pdfs"
R2_BUCKET_LAYOUTJSON = "layoutjson"
R2_BUCKET_HEADERSJSON = "headersjson"
R2_BUCKET_EXTRACTEDDATA = "extracteddata"
R2_BUCKET_COMPANYLOGOS = "companylogos"
R2_BUCKET_BLOG = "blog"

# Baserow Configuration
BASEROW_API_URL = os.getenv("BASEROW_API_URL")
BASEROW_API_TOKEN = os.getenv("BASEROW_API_TOKEN")

# LLM Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4-turbo")

# Huridocs Configuration
HURIDOCS_CONTAINER_NAME = "pdf-document-layout-analysis"
HURIDOCS_API_PORT = 5060
HURIDOCS_API_URL = f"http://localhost:{HURIDOCS_API_PORT}" 

# Docling Configuration
DOCLING_CONTAINER_NAME = "docling-server"
DOCLING_API_PORT = 8000
DOCLING_API_URL = f"http://localhost:{DOCLING_API_PORT}" 