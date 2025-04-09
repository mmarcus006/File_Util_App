"""
PDF processor for Bank Statement Analyzer.

This module provides functionality for extracting text from PDF files
and identifying the financial institution based on the content.
"""

import logging
import re
from pathlib import Path
from typing import Optional, Dict, Tuple, List, BinaryIO, Union, cast, Any
import fitz  # PyMuPDF

# Configure logging
logger = logging.getLogger(__name__)

class InstitutionIdentifier:
    """Class for identifying financial institutions from PDF content."""
    
    # Regex patterns for institution identification
    INSTITUTION_PATTERNS: Dict[str, re.Pattern] = {
        'JPMorgan Chase': re.compile(r'(?i)j\.?p\.?\s*morgan|chase|jpmc'),
        'Morgan Stanley': re.compile(r'(?i)morgan\s*stanley|ms\s+account'),
        'Goldman Sachs': re.compile(r'(?i)goldman\s*sachs|gs\s+account')
    }
    
    @classmethod
    def identify_institution(cls, text: str) -> Optional[str]:
        """Identify the financial institution from text content.
        
        Args:
            text: Text content extracted from PDF
            
        Returns:
            Institution name if identified, None otherwise
        """
        for institution, pattern in cls.INSTITUTION_PATTERNS.items():
            if pattern.search(text):
                logger.info(f"Identified institution: {institution}")
                return institution
        
        logger.warning("Failed to identify institution from document")
        return None


class PDFProcessor:
    """Main class for processing PDF bank statements."""
    
    def __init__(self, max_pages_for_identification: int = 2):
        """Initialize PDF processor.
        
        Args:
            max_pages_for_identification: Maximum number of pages to scan for identification
        """
        self.max_pages_for_identification = max_pages_for_identification
    
    def extract_text(
        self, 
        pdf_source: Union[str, Path, BinaryIO],
        start_page: int = 0, 
        end_page: Optional[int] = None
    ) -> str:
        """Extract text from PDF document.
        
        Args:
            pdf_source: PDF file path or file-like object
            start_page: First page to extract (0-indexed)
            end_page: Last page to extract (exclusive) or None for all
            
        Returns:
            Extracted text content
            
        Raises:
            ValueError: If PDF cannot be opened or processed
        """
        try:
            document = fitz.open(pdf_source)
            
            # Determine end page
            if end_page is None:
                end_page = len(document)
            else:
                end_page = min(end_page, len(document))
            
            # Extract text from specified pages
            text_content = []
            for page_num in range(start_page, end_page):
                page = document[page_num]
                # Use an Any type for get_text to avoid the type error
                text = cast(Any, page).get_text()
                text_content.append(text)
            
            document.close()
            return "\n".join(text_content)
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            raise ValueError(f"Failed to process PDF: {str(e)}")
    
    def identify_institution(
        self, 
        pdf_source: Union[str, Path, BinaryIO]
    ) -> Optional[str]:
        """Identify the financial institution from a PDF statement.
        
        Args:
            pdf_source: PDF file path or file-like object
            
        Returns:
            Institution name if identified, None otherwise
        """
        try:
            # Extract text from first few pages
            text = self.extract_text(
                pdf_source, 
                start_page=0, 
                end_page=self.max_pages_for_identification
            )
            
            # Identify institution from the extracted text
            return InstitutionIdentifier.identify_institution(text)
            
        except Exception as e:
            logger.error(f"Error identifying institution: {str(e)}")
            return None
    
    def extract_full_text(
        self, 
        pdf_source: Union[str, Path, BinaryIO]
    ) -> Optional[str]:
        """Extract full text content from PDF.
        
        Args:
            pdf_source: PDF file path or file-like object
            
        Returns:
            Full text content if successful, None otherwise
        """
        try:
            return self.extract_text(pdf_source)
        except Exception as e:
            logger.error(f"Error extracting full text: {str(e)}")
            return None 