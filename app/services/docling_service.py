"""
Docling service for Bank Statement Analyzer.

This module provides functionality for converting PDF documents to Markdown format
using the Docling library.
"""

import logging
import os
import json
import time
from typing import Optional, Dict, Any, Union, BinaryIO
from pathlib import Path
from tempfile import NamedTemporaryFile

from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
from docling.datamodel.base_models import InputFormat
from docling_core.types.io import DocumentStream
from docling.datamodel.pipeline_options import (
    AcceleratorDevice,
    AcceleratorOptions,
    PdfPipelineOptions,
)
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.models.tesseract_ocr_cli_model import TesseractCliOcrOptions
import pytesseract
from PIL import Image
from app.config import Config
from app.utils.error_handler import BankStatementError

# Configure logging
logger = logging.getLogger(__name__)

class DoclingService:
    """Service for converting PDFs to Markdown using Docling."""
    
    def __init__(self):
        """Initialize the Docling service."""
        # Set default timeout
        self.timeout = 120  # 2 minutes timeout for PDF conversion
        
        # Configure OCR settings
        self.do_ocr = Config.DOCLING_DO_OCR
        self.ocr_languages = Config.DOCLING_OCR_LANGUAGES
        
        # Set up accelerator options
        self.num_threads = Config.DOCLING_NUM_THREADS
        self.accelerator_device = self._get_accelerator_device()
        
        logger.info(f"Docling service initialized with OCR={self.do_ocr}, "
                   f"threads={self.num_threads}, device={self.accelerator_device}")
    
    def _get_accelerator_device(self) -> str:
        """Determine the accelerator device to use.
        
        Returns:
            String representation of the accelerator device
        """
        device_setting = Config.DOCLING_ACCELERATOR_DEVICE.upper()
        
        if device_setting == "AUTO":
            return AcceleratorDevice.AUTO
        elif device_setting == "CPU":
            return AcceleratorDevice.CPU
        elif device_setting == "CUDA" and self._is_cuda_available():
            return AcceleratorDevice.CUDA
        elif device_setting == "MPS" and self._is_mps_available():
            return AcceleratorDevice.MPS
        else:
            # Default to CPU if specified device is not available
            logger.warning(f"Requested accelerator device {device_setting} is not available. Falling back to CPU.")
            return AcceleratorDevice.CPU
    
    def _is_cuda_available(self) -> bool:
        """Check if CUDA is available.
        
        Returns:
            True if CUDA is available, False otherwise
        """
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
    
    def _is_mps_available(self) -> bool:
        """Check if MPS (Metal Performance Shaders) is available.
        
        Returns:
            True if MPS is available, False otherwise
        """
        try:
            import torch
            return hasattr(torch.backends, "mps") and torch.backends.mps.is_available()
        except ImportError:
            return False
        
    def _create_docling_converter(self) -> DocumentConverter:
        """Create a configured DocumentConverter instance.
        
        Returns:
            Configured DocumentConverter instance
        """
        # Configure PDF pipeline options
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = self.do_ocr
        pipeline_options.do_table_structure = True
        pipeline_options.table_structure_options.do_cell_matching = True
        pipeline_options.ocr_options = TesseractCliOcrOptions()
        
        # Set OCR languages if OCR is enabled
        if self.do_ocr and self.ocr_languages:
            pipeline_options.ocr_options.lang = self.ocr_languages
            
            # Don't try to set the OCR engine - use default
            if Config.DOCLING_TESSERACT_PATH:
                os.environ["TESSERACT_PATH"] = Config.DOCLING_TESSERACT_PATH
        
        # Set accelerator options
        pipeline_options.accelerator_options = AcceleratorOptions(
            num_threads=self.num_threads,
            device=self.accelerator_device
        )
        
        # Create and return DocumentConverter with configured options
        return DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=pipeline_options,
                    backend=PyPdfiumDocumentBackend
                )
            }
        )
    
    def convert_pdf_to_markdown(
        self,
        pdf_source: Union[str, Path, BinaryIO],
        max_retries: int = 3,
        retry_delay: int = 5
    ) -> str:
        """Convert PDF document to Markdown format using Docling.
        
        Args:
            pdf_source: PDF file path, Path object, or file-like object
            max_retries: Maximum number of retries on failure
            retry_delay: Delay between retries in seconds
            
        Returns:
            Markdown content as string
            
        Raises:
            BankStatementError: If conversion fails
        """
        temp_file = None
        retries = 0
        
        try:
            # Handle different types of pdf_source
            if isinstance(pdf_source, (str, Path)):
                # Path or string path - use directly
                input_path = Path(pdf_source)
                filename = input_path.name
                
                # Check if a markdown file already exists
                markdown_path = input_path.with_suffix('.md')
                if markdown_path.exists():
                    logger.info(f"Found existing markdown file: {markdown_path}")
                    try:
                        with open(markdown_path, 'r', encoding='utf-8') as f:
                            markdown_content = f.read()
                        return markdown_content
                    except Exception as e:
                        logger.warning(f"Error reading existing markdown file: {str(e)}. Will regenerate.")
            else:
                # File-like object - need to save to temp file
                temp_file = NamedTemporaryFile(delete=False, suffix=".pdf")
                temp_file.write(pdf_source.read())
                temp_file.close()
                input_path = Path(temp_file.name)
                filename = getattr(pdf_source, 'name', 'uploaded_file.pdf')
                markdown_path = None
            
            # Create converter
            doc_converter = self._create_docling_converter()
            
            while retries < max_retries:
                try:
                    logger.info(f"Converting PDF to Markdown: {filename}")
                    start_time = time.time()
                    
                    # Perform the conversion
                    conversion_result = doc_converter.convert(input_path)
                    
                    # Export to markdown
                    markdown_content = conversion_result.document.export_to_markdown()
                    
                    end_time = time.time()
                    logger.info(f"Successfully converted PDF to Markdown in {end_time - start_time:.2f} seconds "
                               f"({len(markdown_content)} chars)")
                    
                    # Save markdown content to file if input was a file path
                    if markdown_path:
                        try:
                            with open(markdown_path, 'w', encoding='utf-8') as f:
                                f.write(markdown_content)
                            logger.info(f"Saved markdown content to: {markdown_path}")
                        except Exception as e:
                            logger.warning(f"Failed to save markdown content to file: {str(e)}")
                    
                    return markdown_content
                
                except Exception as e:
                    logger.error(f"Error during conversion attempt {retries + 1}: {str(e)}")
                    retries += 1
                    if retries < max_retries:
                        time.sleep(retry_delay)
            
            # If we've exhausted all retries
            raise BankStatementError(
                message="Failed to convert PDF to Markdown after multiple attempts",
                error_code="MARKDOWN_CONVERSION_FAILED"
            )
            
        except Exception as e:
            error_msg = f"Error converting PDF to Markdown: {str(e)}"
            logger.error(error_msg)
            raise BankStatementError(
                message=error_msg,
                error_code="MARKDOWN_CONVERSION_ERROR"
            )
        finally:
            # Clean up temp file if created
            if temp_file and os.path.exists(temp_file.name):
                try:
                    os.unlink(temp_file.name)
                except Exception as e:
                    logger.warning(f"Failed to delete temporary file {temp_file.name}: {str(e)}")