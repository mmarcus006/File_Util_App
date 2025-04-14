"""
PDF Processor module for extracting and processing PDF content.
"""

import os
import re
import json
import fitz  # PyMuPDF
from typing import Dict, List, Optional, Tuple, Any

from fdd_verification.utils.text_utils import (
    clean_header_text,
    find_pattern_in_text,
    convert_to_one_based_page,
    ensure_one_based_pages,
)


class PDFProcessor:
    """
    Class for processing PDF files and extracting text content.
    """

    def __init__(self, pdf_path):
        """
        Initialize the PDF processor.

        Args:
            pdf_path: Path to the PDF file
        """
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)
        self.total_pages = len(self.doc)
        self.page_texts = {}
        self.toc_page = self._find_toc_page()

    def _find_toc_page(self) -> Optional[int]:
        """
        Find the Table of Contents page in the PDF based on relaxed criteria:
        - Page number must be less than or equal to 15.
        - Page must contain "TABLE OF CONTENTS" (case-insensitive).
        - Page must contain at least 5 occurrences of "ITEM X" (e.g., "ITEM 1", "ITEM 10").

        Returns:
            Page number (1-based) of the TOC, or None if not found
        """
        toc_title_pattern = r"TABLE\s+OF\s+CONTENTS"
        item_header_pattern = r"\bITEM\s+\d+\b"  # Pattern to find "ITEM X"
        min_item_occurrences = 2

        # Check first 15 pages for TOC
        for page_num_zero_based in range(min(15, self.total_pages)):
            page_num_one_based = page_num_zero_based + 1
            page_text = self.get_page_text(page_num_one_based)

            # Condition 1: Check for "TABLE OF CONTENTS"
            if re.search(toc_title_pattern, page_text, re.IGNORECASE):
                # Condition 2: Check for at least min_item_occurrences item headers
                item_matches = re.findall(item_header_pattern, page_text, re.IGNORECASE)

                if len(item_matches) >= min_item_occurrences:
                    # All conditions met
                    # Optional: Log which page was identified as TOC
                    print(f"Identified Page {page_num_one_based} as Table of Contents.")
                    return page_num_one_based

        # No page met all criteria
        # Optional: Log if TOC was not found
        print("Table of Contents page not found based on criteria.")
        return None

    def get_page_text(self, page_num: int) -> str:
        """
        Get the text content of a specific page.

        Args:
            page_num: 1-based page number

        Returns:
            Text content of the page
        """
        # Convert to 0-based for PyMuPDF
        zero_based_page = page_num - 1

        if zero_based_page < 0 or zero_based_page >= self.total_pages:
            return ""

        if zero_based_page not in self.page_texts:
            try:
                page = self.doc[zero_based_page]
                self.page_texts[zero_based_page] = page.get_text() #type: ignore
            except Exception as e:
                print(f"Error extracting text from page {page_num}: {str(e)}")
                self.page_texts[zero_based_page] = ""

        return self.page_texts[zero_based_page]

    def find_pattern_in_pdf(
        self, pattern: str, start_page: int = 1, end_page: Optional[int] = None
    ) -> Dict[int, List[Tuple[str, int, int]]]:
        """
        Find all occurrences of a pattern in the PDF.

        Args:
            pattern: Regex pattern to search for
            start_page: 1-based page number to start search from
            end_page: 1-based page number to end search at (inclusive)

        Returns:
            Dictionary mapping page numbers to lists of matches (matched_text, start_pos, end_pos)
        """
        if end_page is None:
            end_page = self.total_pages

        # Ensure page numbers are within valid range and 1-based
        start_page = max(1, min(start_page, self.total_pages))
        end_page = max(1, min(end_page, self.total_pages))

        results = {}

        for page_num in range(start_page, end_page + 1):
            page_text = self.get_page_text(page_num)
            matches = find_pattern_in_text(pattern, page_text)

            if matches:
                results[page_num] = matches

        return results

    def extract_all_text(self) -> str:
        """
        Extract text from the entire PDF.

        Returns:
            Full text content of the PDF
        """
        full_text = ""
        for page_num in range(1, self.total_pages + 1):
            full_text += self.get_page_text(page_num) + "\n\n"

        return full_text

    def close(self):
        """Close the PDF document."""
        if self.doc:
            self.doc.close()


class JSONProcessor:
    """
    Class for processing JSON files containing header information.
    """

    def __init__(self, json_path):
        """
        Initialize the JSON processor.

        Args:
            json_path: Path to the JSON file
        """
        self.json_path = json_path
        self.data = self._load_json()

    def _load_json(self) -> Dict:
        """
        Load the JSON file.

        Returns:
            Loaded JSON data
        """
        try:
            with open(self.json_path, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading JSON file: {str(e)}")
            return {}

    def get_all_headers(self) -> List[Dict]:
        """
        Get all headers from the JSON data.

        Returns:
            List of header dictionaries
        """
        headers = []

        # Handle case where the root object is a list of headers
        if isinstance(self.data, list):
            for header in self.data:
                if isinstance(header, dict):
                    # Ensure page numbers are 1-based (if applicable)
                    if "page_number" in header and header["page_number"] is not None:
                        header["page_number"] = convert_to_one_based_page(
                            header["page_number"]
                        )
                    if "start_page" in header and header["start_page"] is not None:
                        header["start_page"] = convert_to_one_based_page(
                            header["start_page"]
                        )
                    if "end_page" in header and header["end_page"] is not None:
                        header["end_page"] = convert_to_one_based_page(
                            header["end_page"]
                        )
                    headers.append(header)
            return headers  # Return early if it's a list

        # --- Existing logic for dictionary-based structures ---

        # Extract headers based on the JSON structure
        if "headers" in self.data:
            # Direct headers list
            for header in self.data["headers"]:
                # Ensure page numbers are 1-based
                if "page_number" in header and header["page_number"] is not None:
                    header["page_number"] = convert_to_one_based_page(
                        header["page_number"]
                    )
                headers.append(header)
        elif "items" in self.data:
            # Items structure
            for item in self.data["items"]:
                header = {
                    "item_number": item.get("item_number"),
                    "text": item.get("header_text", ""),
                    "page_number": convert_to_one_based_page(item.get("page_number")),
                }
                headers.append(header)
        else:
            # Try to extract from flat structure
            for key, value in self.data.items():
                if (
                    isinstance(value, dict)
                    and "header_text" in value
                    and "page_number" in value
                ):
                    try:
                        item_number = int(key)
                        header = {
                            "item_number": item_number,
                            "text": value.get("header_text", ""),
                            "page_number": convert_to_one_based_page(
                                value.get("page_number")
                            ),
                        }
                        headers.append(header)
                    except ValueError:
                        pass

        return headers

    def get_header_by_item_number(self, item_number: int) -> Optional[Dict]:
        """
        Get a specific header by item number.

        Args:
            item_number: Item number to look for

        Returns:
            Header dictionary, or None if not found
        """
        headers = self.get_all_headers()

        for header in headers:
            if header.get("item_number") == item_number:
                return header

        return None

    def update_header_page_number(self, item_number: int, new_page_number: int) -> bool:
        """
        Update the page number for a specific header.

        Args:
            item_number: Item number to update
            new_page_number: New 1-based page number

        Returns:
            True if update was successful, False otherwise
        """
        updated = False
        # Validate the new page number first
        new_page_number_1based = convert_to_one_based_page(new_page_number)
        if new_page_number_1based is None:
            print(
                f"Warning: Invalid new page number (None) provided for item {item_number}."
            )
            return False

        # Update based on JSON structure
        if "headers" in self.data:
            for header in self.data["headers"]:
                if header.get("item_number") == item_number:
                    header["page_number"] = (
                        new_page_number_1based  # Use validated number
                    )
                    updated = True
                    break
        elif "items" in self.data:
            for item in self.data["items"]:
                if item.get("item_number") == item_number:
                    item["page_number"] = new_page_number_1based  # Use validated number
                    updated = True
                    break
        else:
            # Try to update in flat structure
            key = str(item_number)
            if key in self.data:
                self.data[key][
                    "page_number"
                ] = new_page_number_1based  # Use validated number
                updated = True

        if not updated:
            print(f"Warning: Item {item_number} not found in JSON data.")

        return updated

    def save_json(self, output_path: Optional[str] = None) -> str:
        """
        Save the JSON data to a file.

        Args:
            output_path: Path to save the JSON file (defaults to original path)

        Returns:
            Path to the saved file
        """
        save_path = output_path or self.json_path

        try:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, "w") as f:
                json.dump(self.data, f, indent=2)
            return save_path
        except Exception as e:
            print(f"Error saving JSON file: {str(e)}")
            return ""
