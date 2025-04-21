"""
Edge Case Tests for Pattern Matching module for testing pattern matching verification.
Part of the refactored edge case testing system.
"""

import unittest
import os
import sys
import re
from typing import Dict, List, Optional, Any

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from edge_case_test_base import EdgeCaseTestBase
from verification_engine import VerificationEngine

class PatternMatchingTests(EdgeCaseTestBase):
    """
    Tests for pattern matching verification edge cases
    """
    
    def test_exact_header_match(self):
        """Test exact header match with pattern matching"""
        # Create test data
        pdf_content = {
            1: "ITEM 1. THE FRANCHISOR, AND ANY PARENTS, PREDECESSORS, AND AFFILIATES",
            2: "Some other content",
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
        
        # Create mock processors
        pdf_processor = self._mock_pdf_processor("test_exact_match.pdf", pdf_content)
        json_processor = self._mock_json_processor("test_exact_match.json", headers)
        
        # Create verification engine
        engine = VerificationEngine(pdf_processor, json_processor)
        
        # Verify headers
        results = engine.verify_all_headers()
        
        # Check results
        self.assertEqual(len(results), 2)
        self._assert_verification_result(results[1], "verified", 0.9)
        self._assert_verification_result(results[2], "verified", 0.9)
    
    def test_case_insensitive_match(self):
        """Test case insensitive header match with pattern matching"""
        # Create test data
        pdf_content = {
            1: "Item 1. The Franchisor, and Any Parents, Predecessors, and Affiliates",
            3: "item 2. business experience"
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
        
        # Create mock processors
        pdf_processor = self._mock_pdf_processor("test_case_insensitive.pdf", pdf_content)
        json_processor = self._mock_json_processor("test_case_insensitive.json", headers)
        
        # Create verification engine
        engine = VerificationEngine(pdf_processor, json_processor)
        
        # Verify headers
        results = engine.verify_all_headers()
        
        # Check results
        self.assertEqual(len(results), 2)
        self._assert_verification_result(results[1], "verified", 0.8)
        self._assert_verification_result(results[2], "verified", 0.8)
    
    def test_whitespace_variation(self):
        """Test header match with whitespace variations"""
        # Create test data
        pdf_content = {
            1: "ITEM 1.   THE   FRANCHISOR,   AND ANY PARENTS, PREDECESSORS, AND AFFILIATES",
            3: "ITEM  2.  BUSINESS  EXPERIENCE"
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
        
        # Create mock processors
        pdf_processor = self._mock_pdf_processor("test_whitespace.pdf", pdf_content)
        json_processor = self._mock_json_processor("test_whitespace.json", headers)
        
        # Create verification engine
        engine = VerificationEngine(pdf_processor, json_processor)
        
        # Verify headers
        results = engine.verify_all_headers()
        
        # Check results
        self.assertEqual(len(results), 2)
        self._assert_verification_result(results[1], "verified", 0.8)
        self._assert_verification_result(results[2], "verified", 0.8)
    
    def test_partial_header_match(self):
        """Test partial header match with pattern matching"""
        # Create test data
        pdf_content = {
            1: "ITEM 1. THE FRANCHISOR",
            3: "ITEM 2. BUSINESS"
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
        
        # Create mock processors
        pdf_processor = self._mock_pdf_processor("test_partial_match.pdf", pdf_content)
        json_processor = self._mock_json_processor("test_partial_match.json", headers)
        
        # Create verification engine
        engine = VerificationEngine(pdf_processor, json_processor)
        
        # Verify headers
        results = engine.verify_all_headers()
        
        # Check results
        self.assertEqual(len(results), 2)
        self._assert_verification_result(results[1], "likely_correct", 0.7)
        self._assert_verification_result(results[2], "likely_correct", 0.7)
    
    def test_wrong_page_match(self):
        """Test header match on wrong page"""
        # Create test data
        pdf_content = {
            2: "ITEM 1. THE FRANCHISOR, AND ANY PARENTS, PREDECESSORS, AND AFFILIATES",
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
        
        # Create mock processors
        pdf_processor = self._mock_pdf_processor("test_wrong_page.pdf", pdf_content)
        json_processor = self._mock_json_processor("test_wrong_page.json", headers)
        
        # Create verification engine
        engine = VerificationEngine(pdf_processor, json_processor)
        
        # Verify headers
        results = engine.verify_all_headers()
        
        # Check results
        self.assertEqual(len(results), 2)
        self.assertEqual(results[1]['best_match_page'], 2)
        self.assertEqual(results[2]['best_match_page'], 4)
        self._assert_verification_result(results[1], "likely_correct", 0.7)
        self._assert_verification_result(results[2], "likely_correct", 0.7)
    
    def test_no_match(self):
        """Test no header match"""
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
        
        # Create mock processors
        pdf_processor = self._mock_pdf_processor("test_no_match.pdf", pdf_content)
        json_processor = self._mock_json_processor("test_no_match.json", headers)
        
        # Create verification engine
        engine = VerificationEngine(pdf_processor, json_processor)
        
        # Verify headers
        results = engine.verify_all_headers()
        
        # Check results
        self.assertEqual(len(results), 2)
        self._assert_verification_result(results[1], "not_found", 0.0)
        self._assert_verification_result(results[2], "not_found", 0.0)
    
    def test_multiple_matches(self):
        """Test multiple header matches on different pages"""
        # Create test data
        pdf_content = {
            1: "ITEM 1. THE FRANCHISOR, AND ANY PARENTS, PREDECESSORS, AND AFFILIATES",
            2: "Some other content",
            3: "ITEM 1. THE FRANCHISOR, AND ANY PARENTS, PREDECESSORS, AND AFFILIATES",
            4: "ITEM 2. BUSINESS EXPERIENCE",
            5: "ITEM 2. BUSINESS EXPERIENCE"
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
                "page_number": 4
            }
        ]
        
        # Create mock processors
        pdf_processor = self._mock_pdf_processor("test_multiple_matches.pdf", pdf_content)
        json_processor = self._mock_json_processor("test_multiple_matches.json", headers)
        
        # Create verification engine
        engine = VerificationEngine(pdf_processor, json_processor)
        
        # Verify headers
        results = engine.verify_all_headers()
        
        # Check results
        self.assertEqual(len(results), 2)
        self.assertEqual(results[1]['best_match_page'], 1)  # Should prefer the expected page
        self.assertEqual(results[2]['best_match_page'], 4)  # Should prefer the expected page
        self._assert_verification_result(results[1], "verified", 0.9)
        self._assert_verification_result(results[2], "verified", 0.9)
    
    def test_toc_page_match(self):
        """Test header match on table of contents page"""
        # Create test data
        pdf_content = {
            1: "TABLE OF CONTENTS\n\nITEM 1. THE FRANCHISOR, AND ANY PARENTS, PREDECESSORS, AND AFFILIATES...1\nITEM 2. BUSINESS EXPERIENCE...3",
            3: "ITEM 1. THE FRANCHISOR, AND ANY PARENTS, PREDECESSORS, AND AFFILIATES",
            5: "ITEM 2. BUSINESS EXPERIENCE"
        }
        
        headers = [
            {
                "item_number": 1,
                "text": "ITEM 1. THE FRANCHISOR, AND ANY PARENTS, PREDECESSORS, AND AFFILIATES",
                "page_number": 3
            },
            {
                "item_number": 2,
                "text": "ITEM 2. BUSINESS EXPERIENCE",
                "page_number": 5
            }
        ]
        
        # Create mock processors
        pdf_processor = self._mock_pdf_processor("test_toc_match.pdf", pdf_content)
        json_processor = self._mock_json_processor("test_toc_match.json", headers)
        
        # Create verification engine
        engine = VerificationEngine(pdf_processor, json_processor)
        
        # Verify headers
        results = engine.verify_all_headers()
        
        # Check results
        self.assertEqual(len(results), 2)
        self.assertEqual(results[1]['best_match_page'], 3)  # Should prefer the content page over TOC
        self.assertEqual(results[2]['best_match_page'], 5)  # Should prefer the content page over TOC
        self._assert_verification_result(results[1], "verified", 0.9)
        self._assert_verification_result(results[2], "verified", 0.9)
