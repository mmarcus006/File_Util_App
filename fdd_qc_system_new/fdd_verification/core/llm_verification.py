"""
LLM-based verification module for enhanced header verification.
Part of the refactored enhanced verification system.
"""

import os
import json
import re
import requests
from typing import Dict, List, Optional, Tuple, Any
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

from fdd_verification.utils.text_utils import (
    clean_header_text,
    convert_to_one_based_page,
    ensure_one_based_pages,
)
from fdd_verification.utils.confidence_utils import (
    determine_verification_status,
    format_verification_result,
    standardize_result_schema,
)

# Ensure NLTK data is downloaded
import nltk

nltk.download("punkt", quiet=True)
nltk.download("stopwords", quiet=True)


class LLMVerifier:
    """
    Class for verifying headers using LLM API calls (for difficult cases only)
    """

    def __init__(self, api_key=None, api_url=None):
        """
        Initialize the LLM verifier

        Args:
            api_key (str): API key for the LLM service
            api_url (str): URL for the LLM API endpoint
        """
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.api_url = (
            api_url
            or "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
        )
        self.call_count = 0
        self.max_calls_per_session = 10  # Limit API calls for cost efficiency
        self.cache = {}  # Simple cache to avoid duplicate API calls

    def verify_header(self, item_number, header_text, expected_page, page_text):
        """
        Verify a header using the LLM API

        Args:
            item_number (int): Item number
            header_text (str): Header text to verify
            expected_page (int): Expected page number (1-based)
            page_text (str): Text content of the page

        Returns:
            dict: Verification result with confidence score and explanation
        """
        # Clean the header text
        header_text = clean_header_text(header_text)

        # Ensure expected_page is 1-based
        expected_page = convert_to_one_based_page(expected_page)

        # Create a cache key
        cache_key = f"{item_number}_{expected_page}_{hash(header_text[:100])}"

        # Check cache first
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Check if we've exceeded the maximum number of API calls
        if self.call_count >= self.max_calls_per_session:
            result = {
                "verified": False,
                "confidence": 0.0,
                "explanation": "Maximum number of LLM API calls exceeded",
                "page_number": None,
            }
            self.cache[cache_key] = result
            return result

        # Increment call count
        self.call_count += 1

        # Prepare the prompt
        prompt = f"""
        Task: Verify if the following FDD (Franchise Disclosure Document) header appears on the provided page text.
        
        Header: {header_text}
        Item Number: {item_number}
        Expected Page Number: {expected_page}
        
        Page Text (first 1000 characters):
        {page_text[:1000]}
        
        Please analyze if this header appears on this page. Respond in JSON format with the following fields:
        - verified: true/false
        - confidence: a number between 0 and 1
        - explanation: brief explanation of your decision
        - page_number: the page number where you think this header appears, or null if not found
        """

        # If no API key is available, use a mock response
        if not self.api_key:
            print("No API key available, using mock LLM response")
            result = self._mock_llm_response(header_text, page_text, expected_page)
            self.cache[cache_key] = result
            return result

        try:
            # Make the API call
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": self.api_key,
            }

            data = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.1, "topP": 0.8, "topK": 40},
            }

            response = requests.post(
                f"{self.api_url}?key={self.api_key}", headers=headers, json=data
            )

            if response.status_code != 200:
                print(f"LLM API error: {response.status_code} - {response.text}")
                result = {
                    "verified": False,
                    "confidence": 0.0,
                    "explanation": f"API error: {response.status_code}",
                    "page_number": None,
                }
                self.cache[cache_key] = result
                return result

            # Parse the response
            response_data = response.json()
            response_text = (
                response_data.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
            )

            # Extract JSON from response
            try:
                # Find JSON in the response
                json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
                if json_match:
                    llm_result = json.loads(json_match.group(0))
                else:
                    # Fallback to parsing the entire response
                    llm_result = json.loads(response_text)

                # Ensure page_number is 1-based
                if llm_result.get("page_number") is not None:
                    llm_result["page_number"] = convert_to_one_based_page(
                        llm_result["page_number"]
                    )

                result = {
                    "verified": llm_result.get("verified", False),
                    "confidence": llm_result.get("confidence", 0.0),
                    "explanation": llm_result.get(
                        "explanation", "No explanation provided"
                    ),
                    "page_number": llm_result.get("page_number"),
                }
                self.cache[cache_key] = result
                return result
            except json.JSONDecodeError:
                print(f"Failed to parse LLM response as JSON: {response_text}")
                result = {
                    "verified": False,
                    "confidence": 0.0,
                    "explanation": "Failed to parse LLM response",
                    "page_number": None,
                }
                self.cache[cache_key] = result
                return result

        except Exception as e:
            print(f"Error calling LLM API: {str(e)}")
            result = {
                "verified": False,
                "confidence": 0.0,
                "explanation": f"Error: {str(e)}",
                "page_number": None,
            }
            self.cache[cache_key] = result
            return result

    def _mock_llm_response(self, header_text, page_text, expected_page):
        """
        Generate a mock LLM response for testing without API calls

        Args:
            header_text (str): Header text to verify
            page_text (str): Text content of the page
            expected_page (int): Expected page number (1-based)

        Returns:
            dict: Mock verification result
        """
        # Simple heuristic: check if the header text appears in the page text
        if header_text.lower() in page_text.lower():
            return {
                "verified": True,
                "confidence": 0.95,
                "explanation": "Header text found in page content",
                "page_number": expected_page,
            }
        else:
            # Check if parts of the header appear
            stop_words = set(stopwords.words("english"))
            header_words = set(word_tokenize(header_text.lower()))
            header_words = {
                word
                for word in header_words
                if word.isalnum() and word not in stop_words
            }

            page_words = set(word_tokenize(page_text.lower()))
            page_words = {word for word in page_words if word.isalnum()}

            common_words = header_words.intersection(page_words)

            if len(common_words) / len(header_words) > 0.7:
                return {
                    "verified": True,
                    "confidence": 0.8,
                    "explanation": "Most header words found in page content",
                    "page_number": expected_page,
                }
            else:
                return {
                    "verified": False,
                    "confidence": 0.2,
                    "explanation": "Header text not found in page content",
                    "page_number": None,
                }

    def batch_verify_headers(self, headers_data, pdf_text_by_page):
        """
        Batch verify multiple headers at once to reduce API calls

        Args:
            headers_data: List of header data dictionaries with item_number, header_text, expected_page
            pdf_text_by_page: Dictionary mapping page numbers to page text

        Returns:
            List of verification results
        """
        # Group headers by expected page to minimize API calls
        headers_by_page = {}
        for header in headers_data:
            page = convert_to_one_based_page(header.get("expected_page"))
            if page not in headers_by_page:
                headers_by_page[page] = []
            headers_by_page[page].append(header)

        results = []

        # Process each page with its headers
        for page_num, page_headers in headers_by_page.items():
            # Skip if we've exceeded the maximum number of API calls
            if self.call_count >= self.max_calls_per_session:
                for header in page_headers:
                    result = format_verification_result(
                        item_number=header.get("item_number"),
                        header_text=header.get("header_text", ""),
                        expected_page=page_num,
                        found_pages={},
                        best_match_page=None,
                        confidence=0.0,
                        status="not_found",
                        method="llm_batch",
                        additional_info={
                            "explanation": "Maximum number of LLM API calls exceeded"
                        },
                    )
                    results.append(standardize_result_schema(result))
                continue

            # Get page text
            page_text = pdf_text_by_page.get(page_num, "")
            if not page_text:
                for header in page_headers:
                    result = format_verification_result(
                        item_number=header.get("item_number"),
                        header_text=header.get("header_text", ""),
                        expected_page=page_num,
                        found_pages={},
                        best_match_page=None,
                        confidence=0.0,
                        status="not_found",
                        method="llm_batch",
                        additional_info={"explanation": "Page text not available"},
                    )
                    results.append(standardize_result_schema(result))
                continue

            # Create a batch prompt for all headers on this page
            batch_result = self._verify_headers_batch(page_headers, page_text, page_num)

            # Format the results
            for item in batch_result:
                item_number = item.get("item_number")
                header = next(
                    (h for h in page_headers if h.get("item_number") == item_number),
                    None,
                )

                if header:
                    found_pages = {}
                    if item.get("verified", False) and item.get("page_number"):
                        found_page = convert_to_one_based_page(item.get("page_number"))
                        found_pages[found_page] = {
                            "confidence": item.get("confidence", 0.0),
                            "explanation": item.get("explanation", ""),
                            "distance_from_expected": (
                                abs(found_page - page_num) if page_num else None
                            ),
                        }

                    confidence = item.get("confidence", 0.0)
                    status = determine_verification_status(
                        confidence=confidence,
                        expected_page=page_num,
                        found_page=item.get("page_number"),
                    )

                    result = format_verification_result(
                        item_number=item_number,
                        header_text=header.get("header_text", ""),
                        expected_page=page_num,
                        found_pages=found_pages,
                        best_match_page=convert_to_one_based_page(
                            item.get("page_number")
                        ),
                        confidence=confidence,
                        status=status,
                        method="llm_batch",
                        additional_info={"explanation": item.get("explanation", "")},
                    )
                    results.append(standardize_result_schema(result))

        return results

    def _verify_headers_batch(self, headers, page_text, page_num):
        """
        Verify multiple headers on the same page with a single API call

        Args:
            headers: List of header data dictionaries
            page_text: Text content of the page
            page_num: Page number (1-based)

        Returns:
            List of verification results
        """
        # Create a cache key based on headers and page
        cache_key = (
            f"batch_{page_num}_{','.join([str(h.get('item_number')) for h in headers])}"
        )

        # Check cache first
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Increment call count
        self.call_count += 1

        # Prepare the prompt
        headers_json = json.dumps(
            [
                {
                    "item_number": h.get("item_number"),
                    "header_text": h.get("header_text"),
                }
                for h in headers
            ]
        )

        prompt = f"""
        Task: Verify if the following FDD (Franchise Disclosure Document) headers appear on the provided page text.
        
        Headers: {headers_json}
        Page Number: {page_num}
        
        Page Text (first 2000 characters):
        {page_text[:2000]}
        
        For each header, analyze if it appears on this page. Respond in JSON format with an array of results, each with the following fields:
        - item_number: the item number from the input
        - verified: true/false
        - confidence: a number between 0 and 1
        - explanation: brief explanation of your decision
        - page_number: the page number where you think this header appears, or null if not found
        """

        # If no API key is available, use mock responses
        if not self.api_key:
            print("No API key available, using mock LLM responses")
            results = []
            for header in headers:
                mock_result = self._mock_llm_response(
                    header.get("header_text", ""), page_text, page_num
                )
                mock_result["item_number"] = header.get("item_number")
                results.append(mock_result)

            self.cache[cache_key] = results
            return results

        try:
            # Make the API call
            headers_dict = {
                "Content-Type": "application/json",
                "x-goog-api-key": self.api_key,
            }

            data = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.1, "topP": 0.8, "topK": 40},
            }

            response = requests.post(
                f"{self.api_url}?key={self.api_key}", headers=headers_dict, json=data
            )

            if response.status_code != 200:
                print(f"LLM API error: {response.status_code} - {response.text}")
                # Fall back to individual mock responses
                results = []
                for header in headers:
                    mock_result = self._mock_llm_response(
                        header.get("header_text", ""), page_text, page_num
                    )
                    mock_result["item_number"] = header.get("item_number")
                    results.append(mock_result)

                self.cache[cache_key] = results
                return results

            # Parse the response
            response_data = response.json()
            response_text = (
                response_data.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
            )

            # Extract JSON from response
            try:
                # Find JSON array in the response
                json_match = re.search(r"\[\s*\{.*\}\s*\]", response_text, re.DOTALL)
                if json_match:
                    results = json.loads(json_match.group(0))
                else:
                    # Try to find a single JSON object and wrap it in an array
                    json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
                    if json_match:
                        results = [json.loads(json_match.group(0))]
                    else:
                        raise json.JSONDecodeError(
                            "No JSON found in response", response_text, 0
                        )

                # Ensure all page numbers are 1-based
                for result in results:
                    if result.get("page_number") is not None:
                        result["page_number"] = convert_to_one_based_page(
                            result["page_number"]
                        )

                self.cache[cache_key] = results
                return results

            except json.JSONDecodeError:
                print(f"Failed to parse LLM batch response as JSON: {response_text}")
                # Fall back to individual mock responses
                results = []
                for header in headers:
                    mock_result = self._mock_llm_response(
                        header.get("header_text", ""), page_text, page_num
                    )
                    mock_result["item_number"] = header.get("item_number")
                    results.append(mock_result)

                self.cache[cache_key] = results
                return results

        except Exception as e:
            print(f"Error in batch verification: {str(e)}")
            # Fall back to individual mock responses
            results = []
            for header in headers:
                mock_result = self._mock_llm_response(
                    header.get("header_text", ""), page_text, page_num
                )
                mock_result["item_number"] = header.get("item_number")
                results.append(mock_result)

            self.cache[cache_key] = results
            return results
