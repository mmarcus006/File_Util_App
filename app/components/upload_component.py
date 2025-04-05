"""
Streamlit UI components for file upload and processing.
"""

import streamlit as st
import tempfile
import logging
from typing import Tuple, Optional, Dict, Any

# Configure logging
logger = logging.getLogger(__name__)

def upload_file_component() -> Tuple[bool, Optional[bytes], Optional[str]]:
    """
    Create a file upload component for Streamlit.
    
    Returns:
        Tuple containing:
        - Success flag (True if file was uploaded, False otherwise)
        - Uploaded file bytes (or None if no file was uploaded)
        - Filename (or None if no file was uploaded)
    """
    st.write("### Upload Bank Statement")
    st.write("Please upload a PDF bank statement from JPMorgan Chase, Morgan Stanley, or Goldman Sachs.")
    
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
    
    if uploaded_file is not None:
        file_size_mb = uploaded_file.size / (1024 * 1024)
        st.success(f"File '{uploaded_file.name}' uploaded successfully ({file_size_mb:.2f} MB)")
        return True, uploaded_file.getvalue(), uploaded_file.name
    
    return False, None, None

def processing_status_component(status: str, progress: float = 0.0, error: Optional[str] = None):
    """
    Display processing status and progress.
    
    Args:
        status: Status message to display
        progress: Progress value (0.0 to 1.0)
        error: Error message to display (if any)
    """
    st.write("### Processing Status")
    
    # Display progress bar
    progress_bar = st.progress(progress)
    
    # Display status message
    st.info(status)
    
    # Display error if any
    if error:
        st.error(f"Error: {error}")

def results_component(results: Dict[str, Any]):
    """
    Display processing results.
    
    Args:
        results: Dictionary containing processing results
    """
    st.write("### Results")
    
    # Display institution
    if results.get("institution"):
        st.write(f"**Institution:** {results['institution']}")
    
    # Display statement period
    if results.get("statement_period"):
        start_date = results["statement_period"].get("statement_period_start_date")
        end_date = results["statement_period"].get("statement_period_end_date")
        if start_date and end_date:
            st.write(f"**Statement Period:** {start_date} to {end_date}")
    
    # Display account info
    if results.get("account_info"):
        account_number = results["account_info"].get("account_number")
        account_holder = results["account_info"].get("account_holder_name")
        if account_number and account_holder:
            st.write(f"**Account:** {account_holder} (#{account_number})")
    
    # Display summary
    if results.get("summary"):
        st.write("**Summary:**")
        for key, value in results["summary"].items():
            st.write(f"- {key}: {value}")
    
    # Display success message
    if results.get("success"):
        st.success("Data successfully extracted and stored in the database.")
    elif results.get("success") is False:
        st.error("Failed to extract or store data. See error details below.")
        if results.get("error"):
            st.code(results["error"])
    
    # Add a button to view details (placeholder)
    if st.button("View Detailed Results"):
        st.info("Detailed results view not yet implemented.") 