"""
Verification Engine module for verifying FDD headers against PDF content.
Refactored to remove redundancies and improve maintainability.
"""

import os
from typing import Dict, List, Optional, Tuple, Any

# Import utility modules
from fdd_verification.utils.text_utils import (
    clean_header_text,
    extract_item_number,
    create_header_pattern,
    get_standard_header_pattern,
    find_pattern_in_text,
    convert_to_one_based_page,
    ensure_one_based_pages,
    calculate_text_similarity,
)
from fdd_verification.utils.confidence_utils import (
    calculate_confidence_score,
    determine_verification_status,
    format_verification_result,
    standardize_result_schema,
)


class VerificationEngine:
    """
    Engine for verifying FDD headers against PDF content.
    """

    def __init__(self, pdf_processor, json_processor):
        """
        Initialize the verification engine.

        Args:
            pdf_processor: PDF processor instance
            json_processor: JSON processor instance
        """
        self.pdf_processor = pdf_processor
        self.json_processor = json_processor
        self.verification_results = {}

    def verify_all_headers(self):
        """
        Verify all headers in the JSON against the PDF.

        Returns:
            dict: Verification results for all headers
        """
        headers = self.json_processor.get_all_headers()

        for header in headers:
            item_number = header.get("item_number")
            header_text = header.get("text")
            expected_page = header.get("page_number")

            # Ensure expected_page is 1-based
            expected_page = convert_to_one_based_page(expected_page)

            result = self.verify_header(item_number, header_text, expected_page)
            self.verification_results[item_number] = result

        return self.verification_results

    def verify_header(self, item_number, header_text, expected_page):
        """
        Verify a single header against the PDF.

        Args:
            item_number (int): Item number
            header_text (str): Header text
            expected_page (int): Expected page number (1-based)

        Returns:
            dict: Verification result
        """
        # Clean the header text
        header_text = clean_header_text(header_text)

        # Ensure expected_page is 1-based
        expected_page = convert_to_one_based_page(expected_page)

        # Create a pattern for the header
        pattern = get_standard_header_pattern(item_number)
        if not pattern:
            pattern = create_header_pattern(
                item_number,
                header_text.split("ITEM")[1].strip() if "ITEM" in header_text else None,
            )

        # Find the pattern in the PDF
        found_pages = {}

        # First check the expected page and nearby pages
        window_size = 5
        if expected_page is not None:
            start = max(1, expected_page - window_size)
            end = min(self.pdf_processor.total_pages, expected_page + window_size)
            # Search in the window around expected page
            window_matches = self.pdf_processor.find_pattern_in_pdf(pattern, start, end)
            found_pages.update(window_matches)
        else:
            # If expected page is None, start search from the beginning
            start = 1
            end = self.pdf_processor.total_pages # Search whole document if page unknown
            # No initial window search if page is unknown
            window_matches = {}

        # If no pages found in the window OR if expected_page was None initially, search in the entire PDF
        # (Avoid redundant full search if window search already covered everything)
        if not found_pages and (start != 1 or end != self.pdf_processor.total_pages):
            full_matches = self.pdf_processor.find_pattern_in_pdf(pattern)
            found_pages.update(full_matches)

        # Process the results
        result = self._process_verification_results(
            item_number, header_text, expected_page, found_pages
        )

        # Ensure result follows standardized schema
        return standardize_result_schema(result)

    def should_auto_copy_to_corrected(self) -> bool:
        """
        Check if all verified headers have a 'verified' status.

        Returns:
            bool: True if all headers are verified, False otherwise.
        """
        if not self.verification_results:
            print("Debug: No verification results found for auto-copy check.")
            return False  # No results to check

        all_verified = True
        print(
            f"Debug: Checking {len(self.verification_results)} results for auto-copy."
        )
        for item_number, result in self.verification_results.items():
            status = result.get("status")
            # Assuming 'verified' is the status for a successfully confirmed header
            # Add print for debugging status
            print(f"Debug: Item {item_number} status: {status}")
            if status != "verified":
                print(f"Debug: Item {item_number} is not 'verified', returning False.")
                all_verified = False

        print(f"Debug: Final auto-copy check result: {all_verified}")
        return all_verified

    def auto_copy_to_corrected_json(self, output_dir: str) -> Optional[str]:
        """
        Saves the current state of the JSON data (assumed verified)
        to the corrected output directory.

        Args:
            output_dir (str): The directory to save the corrected JSON file.

        Returns:
            Optional[str]: The path to the saved file, or None if saving failed.
        """
        if not self.json_processor or not self.json_processor.json_path:
            print("Error: JSON processor or path not available for saving.")
            return None

        try:
            original_basename = os.path.basename(self.json_processor.json_path)
            # Ensure suffix is added correctly
            base, ext = os.path.splitext(original_basename)
            if base.endswith("_origin"): # Handle common case
                base = base[:-len("_origin")]
            suggested_filename = f"{base}_corrected.json"

            output_path = os.path.join(output_dir, suggested_filename)

            # The json_processor holds the current state (potentially modified by UI)
            # If auto-copy is called, it implies the state is verified.
            saved_path = self.json_processor.save_json(output_path)
            return saved_path
        except Exception as e:
            print(f"Error during auto-copy save: {e}")
            return None

    def _process_verification_results(
        self, item_number, header_text, expected_page, found_pages
    ):
        """
        Process verification results to determine status and confidence.
        Prioritizes pattern matches found in logical page sequence.

        Args:
            item_number (int): Item number
            header_text (str): Header text
            expected_page (int): Expected page number (1-based)
            found_pages (dict): Dictionary of found pages with match details

        Returns:
            dict: Processed verification result
        """
        if not found_pages:
            # No pattern match found anywhere
            return format_verification_result(
                item_number=item_number,
                header_text=header_text,
                expected_page=expected_page,
                found_pages={},
                best_match_page=None,
                confidence=0,
                status="not_found",
                method="pattern_matching",
            )

        # --- Matches were found, process them ---

        processed_pages = {}
        for page_num, matches in found_pages.items():
            page_num = convert_to_one_based_page(page_num)  # Ensure 1-based
            if page_num is None:
                continue  # Skip if conversion failed

            best_match = max(matches, key=lambda m: len(m[0]))
            matched_text = best_match[0]
            similarity = calculate_text_similarity(header_text, matched_text)
            is_toc_match = page_num == self.pdf_processor.toc_page

            # Calculate original confidence for ranking/fallback
            # Ensure both page numbers are valid before calculating distance
            distance = (
                abs(page_num - expected_page)
                if expected_page is not None and page_num is not None
                else None
            )
            original_confidence = calculate_confidence_score(
                similarity=similarity,
                distance_from_expected=distance,
                is_toc_match=is_toc_match,
            )

            processed_pages[page_num] = {
                "confidence": original_confidence,  # Store original confidence for comparison
                "matched_text": matched_text,
                "distance_from_expected": distance,  # Use the calculated distance
                "is_toc_match": is_toc_match,
            }

        # --- Check page sequence logic ---
        all_headers = self.json_processor.get_all_headers()
        # Sort headers by item number just in case they aren't already
        all_headers.sort(key=lambda h: h.get("item_number", float("inf")))

        current_index = -1
        for i, header in enumerate(all_headers):
            if header.get("item_number") == item_number:
                current_index = i
                break

        # Determine expected page range (handle missing pages gracefully)
        prev_expected_page = (
            -1
        )  # Use -1 to indicate no lower bound if first item or prev missing page
        if current_index > 0:
            prev_header = all_headers[current_index - 1]
            prev_page = prev_header.get("page_number")
            if prev_page is not None:
                prev_expected_page = (
                    convert_to_one_based_page(prev_page) or -1
                )  # Use -1 if conversion fails

        next_expected_page = float(
            "inf"
        )  # Use infinity to indicate no upper bound if last item or next missing page
        if current_index != -1 and current_index < len(all_headers) - 1:
            next_header = all_headers[current_index + 1]
            next_page = next_header.get("page_number")
            if next_page is not None:
                next_expected_page = convert_to_one_based_page(next_page) or float(
                    "inf"
                )  # Use inf if conversion fails

        # Find candidate pages within the logical sequence
        logical_candidates = {}
        for page_num, details in processed_pages.items():
            # Check if page_num is within the logical bounds
            # Allows page_num == prev_expected_page
            # Allows page_num == next_expected_page
            page_num_int = int(page_num)  # Ensure comparison is int vs int/float
            if (prev_expected_page == -1 or page_num_int >= prev_expected_page) and (
                next_expected_page == float("inf") or page_num_int <= next_expected_page
            ):
                logical_candidates[page_num] = details

        best_match_page = None
        confidence = 0.0
        status = "needs_review"  # Default if matches found but logic fails
        matched_text = ""

        if logical_candidates:
            # Found matches within the logical page sequence
            # Select the best one (closest to original expected page, then highest original confidence)
            best_logical_page = min(
                logical_candidates.items(),
                key=lambda x: (
                    (
                        x[1]["distance_from_expected"]
                        if x[1]["distance_from_expected"] is not None
                        else float("inf")
                    ),
                    -x[1]["confidence"],
                ),
            )

            best_match_page = best_logical_page[0]
            confidence = 1.0  # Set confidence to 100%
            status = "verified"  # Set status to verified
            matched_text = best_logical_page[1]["matched_text"]
        else:
            # Matches found, but NONE are in the logical sequence
            # Fallback to highest original confidence match among all found pages
            best_fallback_page = max(
                processed_pages.items(), key=lambda x: x[1]["confidence"]
            )

            best_match_page = best_fallback_page[0]
            confidence = best_fallback_page[1]["confidence"]  # Use original confidence
            status = "needs_review"  # Keep status as needs review
            matched_text = best_fallback_page[1]["matched_text"]

        # Determine which details to include in the final output's found_pages
        final_found_pages = {}
        if best_match_page is not None and best_match_page in processed_pages:
            final_found_pages = {best_match_page: processed_pages[best_match_page]}
        elif status == "not_found":
            # If not found, found_pages should be empty
            final_found_pages = {}
        # else: If status is needs_review due to no logical candidates,
        # best_match_page would be the fallback, so the first condition handles it.

        return format_verification_result(
            item_number=item_number,
            header_text=header_text,
            expected_page=expected_page,
            found_pages=final_found_pages,  # Pass only the best match details
            best_match_page=best_match_page,
            confidence=confidence,
            status=status,
            method="pattern_matching",
            additional_info={"matched_text": matched_text},
        )

    def get_verification_summary(self):
        """
        Get a summary of the verification results.

        Returns:
            dict: Summary of verification results
        """
        if not self.verification_results:
            self.verify_all_headers()

        summary = {
            "total": len(self.verification_results),
            "verified": 0,
            "likely_correct": 0,
            "needs_review": 0,
            "likely_incorrect": 0,
            "not_found": 0,
        }

        for result in self.verification_results.values():
            status = result.get("status")
            if status in summary:
                summary[status] += 1

        return summary

    def get_headers_by_status(self, status):
        """
        Get headers with a specific verification status.

        Args:
            status (str): Verification status

        Returns:
            list: Headers with the specified status
        """
        if not self.verification_results:
            self.verify_all_headers()

        return [
            result
            for result in self.verification_results.values()
            if result.get("status") == status
        ]

    def get_all_results(self):
        """
        Get all verification results.

        Returns:
            dict: All verification results
        """
        if not self.verification_results:
            self.verify_all_headers()

        return self.verification_results


# Example usage
if __name__ == "__main__":
    from fdd_verification.core.pdf_processor import PDFProcessor, JSONProcessor

    # This is just for testing the module directly
    pdf_path = "/path/to/pdf"
    json_path = "/path/to/json"

    if os.path.exists(pdf_path) and os.path.exists(json_path):
        pdf_processor = PDFProcessor(pdf_path)
        json_processor = JSONProcessor(json_path)

        engine = VerificationEngine(pdf_processor, json_processor)
        results = engine.verify_all_headers()

        print("Verification Summary:")
        print(engine.get_verification_summary())

        print("\nHeaders that need review:")
        for header in engine.get_headers_by_status("needs_review"):
            print(f"Item {header['item_number']}: {header['header_text']}")
            print(f"  Expected page: {header['expected_page']}")
            print(f"  Best match page: {header['best_match_page']}")
            print(f"  Confidence: {header['confidence']:.2f}")
