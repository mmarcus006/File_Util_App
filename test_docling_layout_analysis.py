"""
Test script for Docling document layout analysis
"""

import os
import sys
import logging
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fdd_pipeline.layout_analysis_docling import analyze_pdf, save_layout_json

def main():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # Example PDF path
    example_pdf_path = "fdd_pipeline/example_data/example.pdf"
    
    # Check if the file exists
    if not os.path.exists(example_pdf_path):
        logger.error(f"Example PDF not found at {example_pdf_path}")
        sys.exit(1)
    
    # Analyze PDF
    try:
        logger.info("Analyzing PDF with Docling...")
        result = analyze_pdf(example_pdf_path)
        
        # Save the results
        output_path = "fdd_pipeline/example_data/docling_test_output.json"
        save_layout_json(result, output_path)
        logger.info(f"Test analysis complete. Results saved to {output_path}")
        
        # Print some info about the document
        if "texts" in result and len(result["texts"]) > 0:
            logger.info(f"Document contains {len(result['texts'])} text elements")
            logger.info(f"First text element: {result['texts'][0]['text'][:100]}...")
        
        if "tables" in result and len(result["tables"]) > 0:
            logger.info(f"Document contains {len(result['tables'])} tables")
            
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        sys.exit(1)
        
    logger.info("Test completed successfully")

if __name__ == "__main__":
    main()
