"""
Unit tests for PDF processor functionality.

This module contains tests for PDF text extraction and institution identification.
"""

import unittest
import io
from unittest.mock import patch, Mock

from app.utils.pdf_processor import PDFProcessor, InstitutionIdentifier

class TestInstitutionIdentifier(unittest.TestCase):
    """Test institution identification functionality."""
    
    def test_identify_jpmorgan(self):
        """Test identifying JPMorgan Chase."""
        test_text = "Welcome to your J.P. Morgan Chase Bank statement"
        result = InstitutionIdentifier.identify_institution(test_text)
        self.assertEqual(result, "JPMorgan Chase")
    
    def test_identify_morgan_stanley(self):
        """Test identifying Morgan Stanley."""
        test_text = "MORGAN STANLEY WEALTH MANAGEMENT\nAccount Statement"
        result = InstitutionIdentifier.identify_institution(test_text)
        self.assertEqual(result, "Morgan Stanley")
    
    def test_identify_goldman_sachs(self):
        """Test identifying Goldman Sachs."""
        test_text = "Goldman Sachs Bank USA\nAccount Summary"
        result = InstitutionIdentifier.identify_institution(test_text)
        self.assertEqual(result, "Goldman Sachs")
    
    def test_unknown_institution(self):
        """Test when institution cannot be identified."""
        test_text = "Generic Bank Statement\nAccount Summary"
        result = InstitutionIdentifier.identify_institution(test_text)
        self.assertIsNone(result)


class TestPDFProcessor(unittest.TestCase):
    """Test PDF processor functionality."""
    
    @patch('fitz.open')
    def test_extract_text(self, mock_open):
        """Test extracting text from PDF."""
        # Mock PyMuPDF document and page
        mock_page1 = Mock()
        mock_page1.get_text.return_value = "Page 1 Content"
        
        mock_page2 = Mock()
        mock_page2.get_text.return_value = "Page 2 Content"
        
        mock_doc = Mock()
        mock_doc.__len__.return_value = 2
        mock_doc.__getitem__.side_effect = [mock_page1, mock_page2]
        mock_doc.close.return_value = None
        
        mock_open.return_value = mock_doc
        
        # Test extracting text
        processor = PDFProcessor()
        result = processor.extract_text("dummy.pdf")
        
        # Verify results
        self.assertEqual(result, "Page 1 Content\nPage 2 Content")
        mock_open.assert_called_once_with("dummy.pdf")
        mock_doc.close.assert_called_once()
    
    @patch('app.utils.pdf_processor.PDFProcessor.extract_text')
    def test_identify_institution(self, mock_extract_text):
        """Test identifying institution from PDF."""
        # Mock extract_text to return sample content
        mock_extract_text.return_value = "Welcome to your J.P. Morgan Chase Bank statement"
        
        # Test institution identification
        processor = PDFProcessor()
        result = processor.identify_institution("dummy.pdf")
        
        # Verify results
        self.assertEqual(result, "JPMorgan Chase")
        mock_extract_text.assert_called_once_with(
            "dummy.pdf",
            start_page=0,
            end_page=2
        )
    
    @patch('app.utils.pdf_processor.PDFProcessor.extract_text')
    def test_extract_full_text(self, mock_extract_text):
        """Test extracting full text content from PDF."""
        # Mock extract_text to return sample content
        mock_extract_text.return_value = "Full PDF Content"
        
        # Test full text extraction
        processor = PDFProcessor()
        result = processor.extract_full_text("dummy.pdf")
        
        # Verify results
        self.assertEqual(result, "Full PDF Content")
        mock_extract_text.assert_called_once_with("dummy.pdf")


if __name__ == "__main__":
    unittest.main() 