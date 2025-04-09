#!/usr/bin/env python3
"""
Bank Statement Batch Processor

This script processes all PDF bank statements found in the 'samples' directory.
It bypasses the Streamlit UI and directly uses the underlying services to:
1. Identify the financial institution
2. Convert the PDF to markdown
3. Extract structured data using LLM
4. Validate and save the data to CSV files

Usage:
    python process_statements.py
"""

import os
import logging
import time
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

# Application imports
from app.services.pdf_processor import PDFProcessor
from app.services.docling_service import DoclingService
from app.services.llm_extractor_v2 import LLMExtractor
from app.services.data_parser import DataParser
from app.utils.error_handler import ErrorHandler, BankStatementError
from app.config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO if not Config.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("statement_processing.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BankStatementProcessor:
    """Main class for batch processing bank statements."""
    
    def __init__(self, samples_dir: str = "New_Samples"):
        """Initialize the bank statement processor.
        
        Args:
            samples_dir: Directory containing the PDF statements to process
        """
        self.samples_dir = Path(samples_dir)
        self.pdf_processor = PDFProcessor()
        self.docling_service = DoclingService()
        self.llm_extractor = LLMExtractor()
        self.data_parser = DataParser()
        
        logger.info(f"Bank Statement Processor initialized. Using samples dir: {self.samples_dir}")
    
    def get_pdf_files(self) -> List[Path]:
        """Get all PDF files in the samples directory.
        
        Returns:
            List of Path objects for all PDF files found
        """
        if not self.samples_dir.exists():
            logger.error(f"Samples directory '{self.samples_dir}' does not exist")
            return []
        
        pdf_files = list(self.samples_dir.glob("*.pdf"))
        logger.info(f"Found {len(pdf_files)} PDF file(s) in {self.samples_dir}")
        return pdf_files
    
    def check_existing_markdown(self, pdf_path: Path) -> Optional[str]:
        """Check if markdown version of PDF already exists.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Markdown content if file exists, None otherwise
        """
        markdown_path = pdf_path.with_suffix('.md')
        if markdown_path.exists():
            logger.info(f"Found existing markdown file: {markdown_path}")
            try:
                with open(markdown_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                logger.warning(f"Error reading existing markdown file: {str(e)}")
        
        return None
    
    def process_pdf(self, pdf_path: Path) -> Dict[str, Any]:
        """Process a single PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary with processing results
        """
        result = {
            "file": pdf_path.name,
            "success": False,
            "institution": None,
            "error": None,
            "output_path": None
        }
        
        start_time = time.time()
        logger.info(f"Processing: {pdf_path.name}")
        
        try:
            # Step 1: Identify the institution
            logger.info("Step 1: Identifying institution...")
            institution = self.pdf_processor.identify_institution(str(pdf_path))
            result["institution"] = institution
            
            if not institution:
                raise BankStatementError(
                    message="Could not identify financial institution",
                    error_code="INSTITUTION_IDENTIFICATION_ERROR"
                )
            
            # Step 2: Convert PDF to markdown (or use existing)
            logger.info("Step 2: Converting PDF to markdown...")
            
            # Check for existing markdown file first (this also happens in DoclingService, 
            # but we'll check here to avoid duplicate log messages)
            markdown_content = self.check_existing_markdown(pdf_path)
            
            if not markdown_content:
                # No existing markdown file, convert the PDF
                markdown_content = self.docling_service.convert_pdf_to_markdown(pdf_path)
            
            if not markdown_content:
                raise BankStatementError(
                    message="Failed to convert PDF to markdown",
                    error_code="MARKDOWN_CONVERSION_ERROR"
                )
            
            # Step 3: Extract data using LLM (or use existing extraction)
            logger.info("Step 3: Extracting data using LLM...")
            
            # We don't need to check for existing extraction files here anymore
            # as the LLM extractor now handles that internally
            extracted_data = self.llm_extractor.extract_data(markdown_content, institution)
            
            if not extracted_data:
                raise BankStatementError(
                    message="Failed to extract data from markdown",
                    error_code="DATA_EXTRACTION_ERROR"
                )
            
            # Step 4: Validate and save data to CSV
            logger.info("Step 4: Validating and saving data to CSV...")
            
            # Parse and validate the extracted dictionary directly
            validated_data = DataParser.parse_and_validate_dict(extracted_data)

            # Save the validated data to CSV files using the static method
            # Pass the original PDF path to determine the output directory
            output_dir = DataParser.save_data_to_csv(validated_data, str(pdf_path))
            
            # Success
            result["success"] = True
            result["output_path"] = output_dir
            logger.info(f"Successfully processed {pdf_path.name}")
            
        except BankStatementError as e:
            result["error"] = str(e)
            ErrorHandler.log_exception(e)
        except Exception as e:
            result["error"] = str(e)
            ErrorHandler.log_exception(e)
        
        processing_time = time.time() - start_time
        logger.info(f"Processing completed in {processing_time:.2f} seconds")
        
        return result
    
    def process_all_pdfs(self) -> List[Dict[str, Any]]:
        """Process all PDF files in the samples directory.
        
        Returns:
            List of results for each processed PDF
        """
        pdf_files = self.get_pdf_files()
        
        if not pdf_files:
            logger.warning("No PDF files found to process")
            return []
        
        results = []
        for pdf_path in pdf_files:
            result = self.process_pdf(pdf_path)
            results.append(result)
        
        # Log summary
        success_count = sum(1 for r in results if r["success"])
        logger.info(f"Processed {len(results)} file(s): {success_count} succeeded, {len(results) - success_count} failed")
        
        return results

def main():
    """Main entry point for the bank statement processor."""
    logger.info("Starting bank statement batch processor")
    
    try:
        processor = BankStatementProcessor()
        results = processor.process_all_pdfs()
        
        # Print results summary
        print("\n--- Processing Results ---")
        for result in results:
            status = "SUCCESS" if result["success"] else "FAILED"
            institution = result["institution"] or "Unknown"
            output_info = f"-> {result['output_path']}" if result['output_path'] else ""
            error = f": {result['error']}" if result["error"] else ""
            print(f"{result['file']} - {status} - {institution}{output_info}{error}")
        
        # Print overall status
        success_count = sum(1 for r in results if r["success"])
        print(f"\nProcessed {len(results)} file(s): {success_count} succeeded, {len(results) - success_count} failed")
        print("See statement_processing.log for details")
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        print(f"Error: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code) 