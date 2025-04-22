"""Handles direct text extraction from PDF files."""

import logging
import PyPDF2
from PyPDF2 import PdfReader
from PyPDF2.errors import PdfReadError
from typing import Optional

def get_pdf_page_count(pdf_path: str) -> int:
    """Gets the total number of pages in a PDF file.

    Args:
        pdf_path: The file path to the PDF document.

    Returns:
        The number of pages in the PDF, or 0 if an error occurs.
    """
    try:
        with open(pdf_path, 'rb') as file:
            reader = PdfReader(file)
            return len(reader.pages)
    except FileNotFoundError:
        logging.error(f"PDF file not found: {pdf_path}")
        return 0
    except PdfReadError as e:
        logging.error(f"Error reading PDF file {pdf_path}: {e}")
        return 0
    except Exception as e:
        logging.error(f"An unexpected error occurred while getting page count for {pdf_path}: {e}")
        return 0

def extract_text_from_page(pdf_reader: PdfReader, page_num: int) -> Optional[str]:
    """Extracts text directly from a specific page of an opened PDF.

    Args:
        pdf_reader: An initialized PyPDF2 PdfReader object.
        page_num: The 0-based index of the page to extract text from.

    Returns:
        The extracted text as a string, or None if extraction fails,
        the page number is invalid, or the extracted text is empty/whitespace.
    """
    try:
        page = pdf_reader.pages[page_num]
        text = page.extract_text()
        if text and text.strip():
            logging.debug(f"Successfully extracted text from page {page_num + 1}")
            return text
        else:
            logging.warning(f"No text or only whitespace found on page {page_num + 1} via direct extraction.")
            return None
    except IndexError:
        logging.error(f"Invalid page number {page_num} requested.")
        return None
    except Exception as e:
        # Catch other potential errors during text extraction
        logging.error(f"Error extracting text from page {page_num + 1}: {e}")
        return None 