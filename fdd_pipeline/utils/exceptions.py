"""
Custom exceptions for FDD Pipeline
"""

class FDDPipelineError(Exception):
    """Base exception for FDD Pipeline errors."""
    pass

class LayoutAnalysisError(FDDPipelineError):
    """Raised when layout analysis fails."""
    pass

class HeaderExtractionError(FDDPipelineError):
    """Raised when header extraction fails."""
    pass

class SectioningError(FDDPipelineError):
    """Raised when section extraction fails."""
    pass

class LLMExtractionError(FDDPipelineError):
    """Raised when LLM extraction fails."""
    pass

class ValidationError(FDDPipelineError):
    """Raised when validation fails."""
    pass

class StorageError(FDDPipelineError):
    """Raised when storage operations fail."""
    pass 