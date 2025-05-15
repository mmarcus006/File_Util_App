"""
Layout analysis using Huridocs PDF Document Layout Analysis
"""

import requests
import time
import subprocess
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, Union

from .utils.exceptions import LayoutAnalysisError
from .config import HURIDOCS_API_URL, HURIDOCS_CONTAINER_NAME

logger = logging.getLogger(__name__)

def check_container_running() -> bool:
    """Check if the Huridocs container is running."""
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", f"name={HURIDOCS_CONTAINER_NAME}", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            check=True
        )
        return HURIDOCS_CONTAINER_NAME in result.stdout
    except subprocess.CalledProcessError:
        return False
        
def start_container() -> bool:
    """Start the Docker container for layout analysis."""
    logger.info("Starting Huridocs container...")
    
    try:
        # Check if already running
        if check_container_running():
            logger.info("Container already running")
            return True
            
        # Start container
        cmd = [
            "docker", "run", "-d", "--rm", "--name", HURIDOCS_CONTAINER_NAME,
            "-p", f"5060:5060",
            "--entrypoint", "./start.sh", "huridocs/pdf-document-layout-analysis:v0.0.23"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info("Container started, waiting for API...")
        
        # Wait for API to become available
        for i in range(30):  # Try for 30 seconds
            try:
                response = requests.get(f"{HURIDOCS_API_URL}", timeout=1)
                if response.status_code in [200, 404, 405]:  # API returns 405 for GET
                    logger.info("API is available")
                    return True
            except requests.RequestException:
                time.sleep(1)
                
        logger.error("Timed out waiting for API")
        return False
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Error starting container: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error starting container: {str(e)}")
        return False

def analyze_pdf(pdf_path: str, fast_mode: bool = False) -> Dict[str, Any]:
    """
    Send PDF to layout analysis API and return results.
    
    Args:
        pdf_path: Path to the PDF file
        fast_mode: Whether to use fast mode (less accurate but quicker)
        
    Returns:
        Dictionary with layout analysis results
        
    Raises:
        LayoutAnalysisError: If analysis fails
    """
    if not check_container_running():
        if not start_container():
            raise LayoutAnalysisError("Failed to start Huridocs container")
    
    url = HURIDOCS_API_URL
    
    try:
        logger.info(f"Sending PDF to layout analysis: {pdf_path}")
        with open(pdf_path, "rb") as pdf_file:
            files = {"file": pdf_file}
            data = {}
            
            if fast_mode:
                data["fast"] = "true"
            
            response = requests.post(url, files=files, data=data, timeout=300)  # 5 minute timeout
            
        if response.status_code != 200:
            raise LayoutAnalysisError(f"API returned status {response.status_code}: {response.text}")
            
        return response.json()
    except requests.RequestException as e:
        raise LayoutAnalysisError(f"API request failed: {str(e)}")
    except json.JSONDecodeError:
        raise LayoutAnalysisError("API returned invalid JSON")
        
def save_layout_json(layout_json: Dict[str, Any], output_path: str) -> str:
    """
    Save layout analysis JSON to a file.
    
    Args:
        layout_json: Layout analysis results
        output_path: Path to save the JSON
        
    Returns:
        Path to the saved file
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(layout_json, f, indent=2)
            
        logger.info(f"Saved layout JSON to {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Error saving layout JSON: {str(e)}")
        raise LayoutAnalysisError(f"Failed to save layout JSON: {str(e)}") 