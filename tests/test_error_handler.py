"""
Unit tests for error handling functionality.

This module contains tests for custom exception classes and error handling utilities.
"""

import unittest
import logging
from unittest.mock import patch, MagicMock

from app.utils.error_handler import (
    BankStatementError, FileError, PDFProcessingError,
    InstitutionIdentificationError, LLMError, DatabaseError,
    ErrorHandler
)

class TestExceptionClasses(unittest.TestCase):
    """Test custom exception classes."""
    
    def test_bank_statement_error(self):
        """Test base exception class."""
        error = BankStatementError(
            message="Test error",
            error_code="TEST_ERROR",
            details={"key": "value"}
        )
        
        self.assertEqual(str(error), "Test error")
        self.assertEqual(error.message, "Test error")
        self.assertEqual(error.error_code, "TEST_ERROR")
        self.assertEqual(error.details, {"key": "value"})
    
    def test_file_error(self):
        """Test file error exception."""
        error = FileError(
            message="File not found",
            file_path="/path/to/file.pdf"
        )
        
        self.assertEqual(error.message, "File not found")
        self.assertEqual(error.error_code, "FILE_ERROR")
        self.assertEqual(error.details, {"file_path": "/path/to/file.pdf"})
    
    def test_pdf_processing_error(self):
        """Test PDF processing error exception."""
        error = PDFProcessingError(
            message="Failed to extract text",
            pdf_source="statement.pdf"
        )
        
        self.assertEqual(error.message, "Failed to extract text")
        self.assertEqual(error.error_code, "PDF_PROCESSING_ERROR")
        self.assertEqual(error.details, {"pdf_source": "statement.pdf"})
    
    def test_institution_identification_error(self):
        """Test institution identification error exception."""
        error = InstitutionIdentificationError()
        
        self.assertEqual(error.message, "Failed to identify financial institution")
        self.assertEqual(error.error_code, "INSTITUTION_IDENTIFICATION_ERROR")
    
    def test_llm_error(self):
        """Test LLM error exception."""
        error = LLMError(
            message="API rate limit exceeded",
            provider="gemini"
        )
        
        self.assertEqual(error.message, "API rate limit exceeded")
        self.assertEqual(error.error_code, "LLM_ERROR")
        self.assertEqual(error.details, {"provider": "gemini"})
    
    def test_database_error(self):
        """Test database error exception."""
        original_error = ValueError("Invalid value")
        error = DatabaseError(
            message="Database query failed",
            original_error=original_error
        )
        
        self.assertEqual(error.message, "Database query failed")
        self.assertEqual(error.error_code, "DATABASE_ERROR")
        self.assertEqual(error.details["original_error"], str(original_error))
        self.assertEqual(error.details["error_type"], "ValueError")


class TestErrorHandler(unittest.TestCase):
    """Test error handler utility."""
    
    @patch('app.utils.error_handler.logger')
    def test_log_exception_bank_statement_error(self, mock_logger):
        """Test logging a BankStatementError."""
        error = BankStatementError(
            message="Test error",
            error_code="TEST_ERROR",
            details={"key": "value"}
        )
        
        ErrorHandler.log_exception(error)
        
        mock_logger.log.assert_called_once()
        log_call = mock_logger.log.call_args[0]
        self.assertEqual(log_call[0], logging.ERROR)
        self.assertIn("TEST_ERROR: Test error", log_call[1])
        self.assertIn("key=value", log_call[1])
    
    @patch('app.utils.error_handler.logger')
    def test_log_exception_standard_exception(self, mock_logger):
        """Test logging a standard exception."""
        error = ValueError("Invalid value")
        
        ErrorHandler.log_exception(error)
        
        mock_logger.log.assert_called_once()
        log_call = mock_logger.log.call_args[0]
        self.assertEqual(log_call[0], logging.ERROR)
        self.assertIn("ValueError: Invalid value", log_call[1])
    
    def test_format_exception_for_ui(self):
        """Test formatting exception for UI display."""
        error = BankStatementError(
            message="Processing failed",
            error_code="PROCESS_ERROR",
            details={"source": "PDF extraction"}
        )
        
        result = ErrorHandler.format_exception_for_ui(error)
        
        self.assertTrue(result["error"])
        self.assertEqual(result["error_type"], "BankStatementError")
        self.assertEqual(result["message"], "Processing failed")
        self.assertEqual(result["error_code"], "PROCESS_ERROR")
        self.assertEqual(result["details"], {"source": "PDF extraction"})
    
    def test_format_standard_exception_for_ui(self):
        """Test formatting standard exception for UI display."""
        error = ValueError("Invalid input")
        
        result = ErrorHandler.format_exception_for_ui(error)
        
        self.assertTrue(result["error"])
        self.assertEqual(result["error_type"], "ValueError")
        self.assertEqual(result["message"], "Invalid input")


if __name__ == "__main__":
    unittest.main() 