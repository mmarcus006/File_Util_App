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
import sys
import platform
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fdd_pipeline.utils.exceptions import LayoutAnalysisError
from fdd_pipeline.config import HURIDOCS_API_URL, HURIDOCS_CONTAINER_NAME

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
        
def is_mac_os() -> bool:
    """Check if the current operating system is macOS."""
    return platform.system() == "Darwin"

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
            "docker", "run", "--rm", "--name", "pdf-document-layout-analysis",
            "-p", "5060:5060",
            "--entrypoint", "./start.sh", "huridocs/pdf-document-layout-analysis:v0.0.23"
        ]
        
        # Add GPU support only for non-Mac systems
        if not is_mac_os():
            cmd.insert(2, "--gpus")
            cmd.insert(3, "all")
        
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
                data["fast"] = "false"
            
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

if __name__ == "__main__":
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Example PDF path
    example_pdf_path = "fdd_pipeline/example_data/example.pdf"
    
    # Check if the file exists
    if not os.path.exists(example_pdf_path):
        logger.error(f"Example PDF not found at {example_pdf_path}")
        sys.exit(1)
    
    # Ensure the container is running
    if not check_container_running():
        logger.info("Starting Huridocs container...")
        if not start_container():
            logger.error("Failed to start container, exiting.")
            sys.exit(1)
    else:
        logger.info("Huridocs container is already running")
    
    # 1. Basic analysis using default (visual) model
    try:
        logger.info("Analyzing PDF with default (visual) model...")
        result = analyze_pdf(example_pdf_path)
        output_path = "fdd_pipeline/example_data/fdd_analysis.json"
        save_layout_json(result, output_path)
        logger.info(f"Analysis saved to {output_path}")
        
        # Print a sample of the first segment for demonstration
        if result.get("segment_boxes") and len(result["segment_boxes"]) > 0:
            logger.info(f"First segment type: {result['segment_boxes'][0]['type']}")
            logger.info(f"First segment text preview: {result['segment_boxes'][0]['text'][:100]}...")
    except LayoutAnalysisError as e:
        logger.error(f"Analysis failed: {str(e)}")
    
    # 2. Analysis with fast mode (LightGBM model)
    try:
        logger.info("Analyzing PDF with fast mode (LightGBM model)...")
        fast_result = analyze_pdf(example_pdf_path, fast_mode=False)
        fast_output_path = "fdd_pipeline/example_data/fdd_analysis_fast.json"
        save_layout_json(fast_result, fast_output_path)
        logger.info(f"Fast analysis saved to {fast_output_path}")
    except LayoutAnalysisError as e:
        logger.error(f"Fast analysis failed: {str(e)}")