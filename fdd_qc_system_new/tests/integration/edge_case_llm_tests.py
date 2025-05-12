"""
Edge Case Tests for LLM Verification module for testing LLM-based verification.
Part of the refactored edge case testing system.
"""

import unittest
import os
import sys
import json
from typing import Dict, List, Optional, Any

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from edge_case_test_base import EdgeCaseTestBase
from llm_verification import LLMVerifier

class MockLLMVerifier(LLMVerifier):
    """Mock LLM verifier for testing"""
    
    def __init__(self):
        """Initialize the mock LLM verifier"""
        super().__init__(api_key=None, api_url=None)
        self.mock_responses = {}
    
    def set_mock_response(self, header_text, page_text, response):
        """
        Set a mock response for a specific header and page text
        
        Args:
            header_text: Header text
            page_text: Page text
            response: Mock response to return
        """
        key = f"{hash(header_text)}_{hash(page_text)}"
        self.mock_responses[key] = response
    
    def _mock_llm_response(self, header_text, page_text, expected_page):
        """
        Generate a mock LLM response based on predefined responses or default behavior
        
        Args:
            header_text: Header text to verify
            page_text: Text content of the page
            expected_page: Expected page number
            
        Returns:
            dict: Mock verification result
        """
        key = f"{hash(header_text)}_{hash(page_text)}"
        if key in self.mock_responses:
            return self.mock_responses[key]
        
        # Default behavior from parent class
        return super()._mock_llm_response(header_text, page_text, expected_page)

class LLMVerificationTests(EdgeCaseTestBase):
    """
    Tests for LLM-based verification edge cases
    """
    
    def setUp(self):
        """Set up test environment"""
        super().setUp()
        
        # Create mock LLM verifier
        self.llm_verifier = MockLLMVerifier()
    
    def test_exact_header_match_llm(self):
        """Test exact header match with LLM verification"""
        # Create test data
        pdf_content = {
            1: "ITEM 1. THE FRANCHISOR, AND ANY PARENTS, PREDECESSORS, AND AFFILIATES",
            3: "ITEM 2. BUSINESS EXPERIENCE"
        }
        
        headers = [
            {
                "item_number": 1,
                "text": "ITEM 1. THE FRANCHISOR, AND ANY PARENTS, PREDECESSORS, AND AFFILIATES",
                "page_number": 1
            },
            {
                "item_number": 2,
                "text": "ITEM 2. BUSINESS EXPERIENCE",
                "page_number": 3
            }
        ]
        
        # Set mock responses
        self.llm_verifier.set_mock_response(
            headers[0]["text"],
            pdf_content[1],
            {
                "verified": True,
                "confidence": 0.95,
                "explanation": "Header text found exactly on the page",
                "page_number": 1
            }
        )
        
        self.llm_verifier.set_mock_response(
            headers[1]["text"],
            pdf_content[3],
            {
                "verified": True,
                "confidence": 0.95,
                "explanation": "Header text found exactly on the page",
                "page_number": 3
            }
        )
        
        # Verify headers
        result1 = self.llm_verifier.verify_header(1, headers[0]["text"], 1, pdf_content[1])
        result2 = self.llm_verifier.verify_header(2, headers[1]["text"], 3, pdf_content[3])
        
        # Check results
        self.assertTrue(result1["verified"])
        self.assertTrue(result2["verified"])
        self.assertGreaterEqual(result1["confidence"], 0.9)
        self.assertGreaterEqual(result2["confidence"], 0.9)
        self.assertEqual(result1["page_number"], 1)
        self.assertEqual(result2["page_number"], 3)
    
    def test_semantic_understanding_llm(self):
        """Test semantic understanding with LLM verification"""
        # Create test data with semantically similar but not identical text
        pdf_content = {
            1: "ITEM 1. INFORMATION ABOUT THE FRANCHISOR\nThis section provides details about the franchisor company, its parent organizations, and affiliated entities.",
            3: "ITEM 2. EXPERIENCE OF KEY PERSONNEL\nThis section outlines the business background of the management team."
        }
        
        headers = [
            {
                "item_number": 1,
                "text": "ITEM 1. THE FRANCHISOR, AND ANY PARENTS, PREDECESSORS, AND AFFILIATES",
                "page_number": 1
            },
            {
                "item_number": 2,
                "text": "ITEM 2. BUSINESS EXPERIENCE",
                "page_number": 3
            }
        ]
        
        # Set mock responses
        self.llm_verifier.set_mock_response(
            headers[0]["text"],
            pdf_content[1],
            {
                "verified": True,
                "confidence": 0.9,
                "explanation": "The header content matches semantically, though the wording is different",
                "page_number": 1
            }
        )
        
        self.llm_verifier.set_mock_response(
            headers[1]["text"],
            pdf_content[3],
            {
                "verified": True,
                "confidence": 0.85,
                "explanation": "The header content matches semantically, though the wording is different",
                "page_number": 3
            }
        )
        
        # Verify headers
        result1 = self.llm_verifier.verify_header(1, headers[0]["text"], 1, pdf_content[1])
        result2 = self.llm_verifier.verify_header(2, headers[1]["text"], 3, pdf_content[3])
        
        # Check results
        self.assertTrue(result1["verified"])
        self.assertTrue(result2["verified"])
        self.assertGreaterEqual(result1["confidence"], 0.8)
        self.assertGreaterEqual(result2["confidence"], 0.8)
        self.assertEqual(result1["page_number"], 1)
        self.assertEqual(result2["page_number"], 3)
    
    def test_wrong_page_llm(self):
        """Test header match on wrong page with LLM verification"""
        # Create test data
        pdf_content = {
            1: "Some random content",
            2: "ITEM 1. THE FRANCHISOR, AND ANY PARENTS, PREDECESSORS, AND AFFILIATES",
            3: "More random content",
            4: "ITEM 2. BUSINESS EXPERIENCE"
        }
        
        headers = [
            {
                "item_number": 1,
                "text": "ITEM 1. THE FRANCHISOR, AND ANY PARENTS, PREDECESSORS, AND AFFILIATES",
                "page_number": 1
            },
            {
                "item_number": 2,
                "text": "ITEM 2. BUSINESS EXPERIENCE",
                "page_number": 3
            }
        ]
        
        # Set mock responses for expected pages (not found)
        self.llm_verifier.set_mock_response(
            headers[0]["text"],
            pdf_content[1],
            {
                "verified": False,
                "confidence": 0.1,
                "explanation": "Header text not found on this page",
                "page_number": None
            }
        )
        
        self.llm_verifier.set_mock_response(
            headers[1]["text"],
            pdf_content[3],
            {
                "verified": False,
                "confidence": 0.1,
                "explanation": "Header text not found on this page",
                "page_number": None
            }
        )
        
        # Set mock responses for suggested pages (found)
        self.llm_verifier.set_mock_response(
            headers[0]["text"],
            pdf_content[2],
            {
                "verified": True,
                "confidence": 0.95,
                "explanation": "Header text found exactly on this page",
                "page_number": 2
            }
        )
        
        self.llm_verifier.set_mock_response(
            headers[1]["text"],
            pdf_content[4],
            {
                "verified": True,
                "confidence": 0.95,
                "explanation": "Header text found exactly on this page",
                "page_number": 4
            }
        )
        
        # Verify headers
        result1 = self.llm_verifier.verify_header(1, headers[0]["text"], 1, pdf_content[1])
        result2 = self.llm_verifier.verify_header(2, headers[1]["text"], 3, pdf_content[3])
        
        # Check results
        self.assertFalse(result1["verified"])
        self.assertFalse(result2["verified"])
        self.assertLessEqual(result1["confidence"], 0.2)
        self.assertLessEqual(result2["confidence"], 0.2)
        self.assertIsNone(result1["page_number"])
        self.assertIsNone(result2["page_number"])
    
    def test_no_match_llm(self):
        """Test no header match with LLM verification"""
        # Create test data
        pdf_content = {
            1: "Some random content",
            3: "More random content"
        }
        
        headers = [
            {
                "item_number": 1,
                "text": "ITEM 1. THE FRANCHISOR, AND ANY PARENTS, PREDECESSORS, AND AFFILIATES",
                "page_number": 1
            },
            {
                "item_number": 2,
                "text": "ITEM 2. BUSINESS EXPERIENCE",
                "page_number": 3
            }
        ]
        
        # Set mock responses
        self.llm_verifier.set_mock_response(
            headers[0]["text"],
            pdf_content[1],
            {
                "verified": False,
                "confidence": 0.1,
                "explanation": "Header text not found on this page",
                "page_number": None
            }
        )
        
        self.llm_verifier.set_mock_response(
            headers[1]["text"],
            pdf_content[3],
            {
                "verified": False,
                "confidence": 0.1,
                "explanation": "Header text not found on this page",
                "page_number": None
            }
        )
        
        # Verify headers
        result1 = self.llm_verifier.verify_header(1, headers[0]["text"], 1, pdf_content[1])
        result2 = self.llm_verifier.verify_header(2, headers[1]["text"], 3, pdf_content[3])
        
        # Check results
        self.assertFalse(result1["verified"])
        self.assertFalse(result2["verified"])
        self.assertLessEqual(result1["confidence"], 0.2)
        self.assertLessEqual(result2["confidence"], 0.2)
        self.assertIsNone(result1["page_number"])
        self.assertIsNone(result2["page_number"])
    
    def test_batch_verification(self):
        """Test batch verification with LLM"""
        # Create test data
        pdf_content = {
            1: "ITEM 1. THE FRANCHISOR, AND ANY PARENTS, PREDECESSORS, AND AFFILIATES",
            3: "ITEM 2. BUSINESS EXPERIENCE"
        }
        
        headers = [
            {
                "item_number": 1,
                "text": "ITEM 1. THE FRANCHISOR, AND ANY PARENTS, PREDECESSORS, AND AFFILIATES",
                "page_number": 1,
                "expected_page": 1
            },
            {
                "item_number": 2,
                "text": "ITEM 2. BUSINESS EXPERIENCE",
                "page_number": 3,
                "expected_page": 3
            }
        ]
        
        # Mock the _verify_headers_batch method
        original_method = self.llm_verifier._verify_headers_batch
        self.llm_verifier._verify_headers_batch = lambda h, p, pn: [
            {
                "item_number": 1,
                "verified": True,
                "confidence": 0.95,
                "explanation": "Header text found exactly on the page",
                "page_number": 1
            },
            {
                "item_number": 2,
                "verified": True,
                "confidence": 0.95,
                "explanation": "Header text found exactly on the page",
                "page_number": 3
            }
        ]
        
        # Verify headers in batch
        results = self.llm_verifier.batch_verify_headers(headers, pdf_content)
        
        # Restore original method
        self.llm_verifier._verify_headers_batch = original_method
        
        # Check results
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["item_number"], 1)
        self.assertEqual(results[1]["item_number"], 2)
        self.assertTrue(results[0]["verified"])
        self.assertTrue(results[1]["verified"])
        self.assertGreaterEqual(results[0]["confidence"], 0.9)
        self.assertGreaterEqual(results[1]["confidence"], 0.9)
        self.assertEqual(results[0]["page_number"], 1)
        self.assertEqual(results[1]["page_number"], 3)
