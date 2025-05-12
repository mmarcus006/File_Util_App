"""
Bank Statement Analyzer - Main Application Entry Point

This module serves as the entry point for the Streamlit application.
It initializes the UI and orchestrates the workflow.
"""

import streamlit as st
import tempfile
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

from app.components.upload_component import (
    upload_file_component,
    processing_status_component,
    results_component
)
from app.services.database import create_db_if_not_exists
from app.config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize database
create_db_if_not_exists()

# Set page config
st.set_page_config(
    page_title="Bank Statement Analyzer",
    page_icon="💰",
    layout="wide",
)

def main():
    """Main function to run the Streamlit application."""
    
    st.title("Bank Statement Analyzer")
    st.write("Upload a bank statement (JPMorgan Chase, Morgan Stanley, or Goldman Sachs) to extract and store financial data.")
    
    # File upload
    file_uploaded, file_bytes, file_name = upload_file_component()
    
    if file_uploaded:
        # Check if the process button is clicked
        if st.button("Process Statement"):
            # Display processing status
            processing_status_component("Initializing...", 0.1)
            
            # TODO: Implement the following workflow:
            # 1. Identify the institution
            processing_status_component("Identifying institution...", 0.2)
            
            # 2. Convert PDF to markdown
            processing_status_component("Converting to markdown...", 0.4)
            
            # 3. Extract data using LLM
            processing_status_component("Extracting data using AI...", 0.6)
            
            # 4. Validate and structure data
            processing_status_component("Validating extracted data...", 0.8)
            
            # 5. Store in database
            processing_status_component("Storing data in database...", 0.9)
            
            # Display mock results for now
            processing_status_component("Processing complete", 1.0)
            
            # Show mock results
            mock_results = {
                "success": True,
                "institution": "JPMorgan Chase",
                "account_info": {
                    "account_number": "12345",
                    "account_holder_name": "John Doe"
                },
                "statement_period": {
                    "statement_period_start_date": "2023-01-01",
                    "statement_period_end_date": "2023-01-31"
                },
                "summary": {
                    "Beginning Market Value": "$100,000.00",
                    "Ending Market Value": "$105,000.00",
                    "Change in Market Value": "$5,000.00"
                }
            }
            
            results_component(mock_results)

if __name__ == "__main__":
    main() 