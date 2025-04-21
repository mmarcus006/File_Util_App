"""
Error handling module for Bank Statement Analyzer.

This module provides custom exception classes and error handling utilities.
"""

import logging
import traceback
from typing import Optional, Dict, Any, Union, Type

# Configure logging
logger = logging.getLogger(__name__)

class BankStatementError(Exception):
    """Base exception class for all Bank Statement Analyzer errors."""
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize the exception.
        
        Args:
            message: Error message
            error_code: Optional error code for categorization
            details: Optional dictionary with additional error details
        """
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(message)


class FileError(BankStatementError):
    """Exception raised for file-related errors."""
    
    def __init__(
        self, 
        message: str, 
        file_path: Optional[str] = None,
        **kwargs
    ):
        """Initialize file error.
        
        Args:
            message: Error message
            file_path: Path to the file that caused the error
            **kwargs: Additional arguments passed to parent
        """
        details = kwargs.pop('details', {})
        if file_path:
            details['file_path'] = file_path
        
        super().__init__(
            message=message,
            error_code='FILE_ERROR',
            details=details,
            **kwargs
        )


class PDFProcessingError(BankStatementError):
    """Exception raised for PDF processing errors."""
    
    def __init__(
        self, 
        message: str, 
        pdf_source: Optional[str] = None,
        **kwargs
    ):
        """Initialize PDF processing error.
        
        Args:
            message: Error message
            pdf_source: Source of the PDF that caused the error
            **kwargs: Additional arguments passed to parent
        """
        details = kwargs.pop('details', {})
        if pdf_source:
            details['pdf_source'] = pdf_source
        
        super().__init__(
            message=message,
            error_code='PDF_PROCESSING_ERROR',
            details=details,
            **kwargs
        )


class InstitutionIdentificationError(BankStatementError):
    """Exception raised when institution identification fails."""
    
    def __init__(
        self, 
        message: str = "Failed to identify financial institution",
        **kwargs
    ):
        """Initialize institution identification error.
        
        Args:
            message: Error message
            **kwargs: Additional arguments passed to parent
        """
        super().__init__(
            message=message,
            error_code='INSTITUTION_IDENTIFICATION_ERROR',
            **kwargs
        )


class LLMError(BankStatementError):
    """Exception raised for LLM-related errors."""
    
    def __init__(
        self, 
        message: str,
        provider: Optional[str] = None,
        **kwargs
    ):
        """Initialize LLM error.
        
        Args:
            message: Error message
            provider: LLM provider name
            **kwargs: Additional arguments passed to parent
        """
        details = kwargs.pop('details', {})
        if provider:
            details['provider'] = provider
        
        super().__init__(
            message=message,
            error_code='LLM_ERROR',
            details=details,
            **kwargs
        )


class ErrorHandler:
    """Utility class for handling and logging errors."""
    
    @staticmethod
    def log_exception(
        exception: Exception,
        log_level: int = logging.ERROR,
        include_traceback: bool = True
    ) -> None:
        """Log an exception with optional traceback.
        
        Args:
            exception: The exception to log
            log_level: Logging level
            include_traceback: Whether to include traceback
        """
        message = str(exception)
        
        if isinstance(exception, BankStatementError):
            error_info = f"{exception.error_code}: {message}" if exception.error_code else message
            
            if exception.details:
                details_str = ", ".join(f"{k}={v}" for k, v in exception.details.items())
                error_info = f"{error_info} - Details: {details_str}"
        else:
            error_info = f"{type(exception).__name__}: {message}"
        
        if include_traceback:
            logger.log(log_level, error_info, exc_info=True)
        else:
            logger.log(log_level, error_info)
    
    @staticmethod
    def format_exception_for_ui(exception: Exception) -> Dict[str, Any]:
        """Format an exception for display in the UI.
        
        Args:
            exception: The exception to format
            
        Returns:
            Dictionary with formatted error information
        """
        if isinstance(exception, BankStatementError):
            result = {
                'error': True,
                'error_type': type(exception).__name__,
                'message': exception.message,
            }
            
            if exception.error_code:
                result['error_code'] = exception.error_code
                
            if exception.details:
                result['details'] = exception.details
        else:
            result = {
                'error': True,
                'error_type': type(exception).__name__,
                'message': str(exception),
            }
            
        return result 