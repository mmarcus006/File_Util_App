"""Handles PDF text extraction using OCR (Optical Character Recognition)."""

import logging
import pytesseract
from pdf2image import convert_from_path
from pdf2image.exceptions import (
    PDFInfoNotInstalledError,
    PDFPageCountError,
    PDFSyntaxError
)
from typing import Optional

# Note: Requires poppler and tesseract to be installed system-wide.
# On macOS with Homebrew: brew install poppler tesseract

def extract_text_via_ocr(pdf_path: str, page_num: int) -> Optional[str]:
    """Extracts text from a specific PDF page using OCR.

    Converts the page to an image first, then uses Tesseract OCR.

    Args:
        pdf_path: The file path to the PDF document.
        page_num: The 0-based index of the page to perform OCR on.

    Returns:
        The extracted text as a string, or None if OCR fails,
        dependencies are missing, or the extracted text is empty/whitespace.
    """
    logging.info(f"Attempting OCR for page {page_num + 1} of {pdf_path}")
    try:
        # Convert specific page to an image object (list containing one image)
        # page_num is 0-based, but pdf2image uses 1-based page numbers
        images = convert_from_path(
            pdf_path,
            first_page=page_num + 1,
            last_page=page_num + 1,
            dpi=300 # Higher DPI can improve OCR accuracy
        )

        if not images:
            logging.warning(f"Could not convert page {page_num + 1} of {pdf_path} to image.")
            return None

        # Perform OCR on the image
        text = pytesseract.image_to_string(images[0])

        if text and text.strip():
            logging.info(f"Successfully extracted text via OCR from page {page_num + 1}")
            return text
        else:
            logging.warning(f"OCR found no text or only whitespace on page {page_num + 1}.")
            return None

    except (PDFInfoNotInstalledError, PDFPageCountError, PDFSyntaxError) as e:
        logging.error(f"pdf2image error for page {page_num + 1} of {pdf_path}: {e}. Is poppler installed and in PATH?")
        return None
    except pytesseract.TesseractNotFoundError:
        logging.error("Tesseract is not installed or not in PATH. OCR failed.")
        # Consider raising a more specific error or providing setup instructions.
        return None
    except pytesseract.TesseractError as e:
        logging.error(f"Tesseract error during OCR for page {page_num + 1}: {e}")
        return None
    except FileNotFoundError:
        logging.error(f"PDF file not found for OCR: {pdf_path}")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred during OCR for page {page_num + 1} of {pdf_path}: {e}")
        return None 