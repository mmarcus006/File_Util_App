"""
Test module for the unit tests of the verification engine.
"""

import unittest
import os
import json
from unittest.mock import MagicMock, patch
import numpy as np

# Import modules to test
from fdd_verification.core.verification_engine import VerificationEngine
from fdd_verification.core.pdf_processor import PDFProcessor, JSONProcessor
from fdd_verification.utils.text_utils import clean_header_text, convert_to_one_based_page, ensure_one_based_pages
from fdd_verification.utils.confidence_utils import calculate_confidence_score, determine_verification_status, standardize_result_schema

class TestVerificationEngine(unittest.TestCase):
    """Test cases for the VerificationEngine class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create mock PDF and JSON processors
        self.pdf_processor = MagicMock(spec=PDFProcessor)
        self.json_processor = MagicMock(spec=JSONProcessor)
        
        # Configure mock behavior
        self.pdf_processor.total_pages = 100
        self.pdf_processor.toc_page = 3
        
        # Sample headers for testing
        self.sample_headers = [
            {'item_number': 1, 'text': 'ITEM 1: THE FRANCHISOR', 'page_number': 10},
            {'item_number': 2, 'text': 'ITEM 2: BUSINESS EXPERIENCE', 'page_number': 15},
            {'item_number': 3, 'text': 'ITEM 3: LITIGATION', 'page_number': 20}
        ]
        
        self.json_processor.get_all_headers.return_value = self.sample_headers
        
        # Create the verification engine
        self.engine = VerificationEngine(self.pdf_processor, self.json_processor)
    
    def test_verify_header_found(self):
        """Test verifying a header that is found on the expected page"""
        # Configure mock behavior for a successful match
        self.pdf_processor.get_page_text.return_value = "This page contains ITEM 1: THE FRANCHISOR and other text"
        self.pdf_processor.find_pattern_in_pdf.return_value = {
            10: [("ITEM 1: THE FRANCHISOR", 10, 30)]
        }
        
        # Verify the header
        result = self.engine.verify_header(1, "ITEM 1: THE FRANCHISOR", 10)
        
        # Check the result
        self.assertEqual(result['item_number'], 1)
        self.assertEqual(result['expected_page'], 10)
        self.assertEqual(result['best_match_page'], 10)
        self.assertEqual(result['status'], "verified")
        self.assertGreater(result['confidence'], 0.9)
        self.assertEqual(result['method'], "pattern_matching")
    
    def test_verify_header_not_found(self):
        """Test verifying a header that is not found"""
        # Configure mock behavior for no match
        self.pdf_processor.find_pattern_in_pdf.return_value = {}
        
        # Verify the header
        result = self.engine.verify_header(1, "ITEM 1: THE FRANCHISOR", 10)
        
        # Check the result
        self.assertEqual(result['item_number'], 1)
        self.assertEqual(result['expected_page'], 10)
        self.assertIsNone(result['best_match_page'])
        self.assertEqual(result['status'], "not_found")
        self.assertEqual(result['confidence'], 0)
        self.assertEqual(result['method'], "pattern_matching")
    
    def test_verify_header_found_on_different_page(self):
        """Test verifying a header that is found on a different page than expected"""
        # Configure mock behavior for a match on a different page
        self.pdf_processor.find_pattern_in_pdf.return_value = {
            12: [("ITEM 1: THE FRANCHISOR", 10, 30)]
        }
        
        # Verify the header
        result = self.engine.verify_header(1, "ITEM 1: THE FRANCHISOR", 10)
        
        # Check the result
        self.assertEqual(result['item_number'], 1)
        self.assertEqual(result['expected_page'], 10)
        self.assertEqual(result['best_match_page'], 12)
        self.assertIn(result['status'], ["likely_correct", "needs_review"])
        self.assertGreater(result['confidence'], 0)
        self.assertEqual(result['method'], "pattern_matching")
    
    def test_verify_all_headers(self):
        """Test verifying all headers"""
        # Configure mock behavior for multiple headers
        self.pdf_processor.find_pattern_in_pdf.side_effect = [
            {10: [("ITEM 1: THE FRANCHISOR", 10, 30)]},
            {15: [("ITEM 2: BUSINESS EXPERIENCE", 10, 35)]},
            {21: [("ITEM 3: LITIGATION", 10, 25)]}
        ]
        
        # Verify all headers
        results = self.engine.verify_all_headers()
        
        # Check the results
        self.assertEqual(len(results), 3)
        self.assertEqual(results[1]['best_match_page'], 10)
        self.assertEqual(results[2]['best_match_page'], 15)
        self.assertEqual(results[3]['best_match_page'], 21)
    
    def test_get_verification_summary(self):
        """Test getting a verification summary"""
        # Configure mock behavior for verification results
        self.engine.verification_results = {
            1: {'status': 'verified', 'confidence': 0.95},
            2: {'status': 'likely_correct', 'confidence': 0.85},
            3: {'status': 'needs_review', 'confidence': 0.65},
            4: {'status': 'likely_incorrect', 'confidence': 0.45},
            5: {'status': 'not_found', 'confidence': 0}
        }
        
        # Get the summary
        summary = self.engine.get_verification_summary()
        
        # Check the summary
        self.assertEqual(summary['total'], 5)
        self.assertEqual(summary['verified'], 1)
        self.assertEqual(summary['likely_correct'], 1)
        self.assertEqual(summary['needs_review'], 1)
        self.assertEqual(summary['likely_incorrect'], 1)
        self.assertEqual(summary['not_found'], 1)
    
    def test_get_headers_by_status(self):
        """Test getting headers by status"""
        # Configure mock behavior for verification results
        self.engine.verification_results = {
            1: {'item_number': 1, 'status': 'verified', 'confidence': 0.95},
            2: {'item_number': 2, 'status': 'likely_correct', 'confidence': 0.85},
            3: {'item_number': 3, 'status': 'needs_review', 'confidence': 0.65},
            4: {'item_number': 4, 'status': 'needs_review', 'confidence': 0.55},
            5: {'item_number': 5, 'status': 'not_found', 'confidence': 0}
        }
        
        # Get headers by status
        needs_review = self.engine.get_headers_by_status('needs_review')
        
        # Check the results
        self.assertEqual(len(needs_review), 2)
        self.assertEqual(needs_review[0]['item_number'], 3)
        self.assertEqual(needs_review[1]['item_number'], 4)


class TestTextUtils(unittest.TestCase):
    """Test cases for text utility functions"""
    
    def test_clean_header_text(self):
        """Test cleaning header text"""
        # Test with various inputs
        self.assertEqual(clean_header_text("ITEM 1: THE FRANCHISOR"), "ITEM 1 THE FRANCHISOR")
        self.assertEqual(clean_header_text("item 2: business experience"), "ITEM 2 BUSINESS EXPERIENCE")
        self.assertEqual(clean_header_text("  ITEM  3:  LITIGATION  "), "ITEM 3 LITIGATION")
        self.assertEqual(clean_header_text("ITEM 4. BANKRUPTCY"), "ITEM 4. BANKRUPTCY")
        self.assertEqual(clean_header_text(None), "")
    
    def test_convert_to_one_based_page(self):
        """Test converting to 1-based page numbers"""
        # Test with various inputs
        self.assertEqual(convert_to_one_based_page(0), 1)
        self.assertEqual(convert_to_one_based_page(1), 1)
        self.assertEqual(convert_to_one_based_page(10), 10)
        self.assertEqual(convert_to_one_based_page(-1), 1)
        self.assertIsNone(convert_to_one_based_page(None))
    
    def test_ensure_one_based_pages(self):
        """Test ensuring all page numbers in a result are 1-based"""
        # Create a test result with various page numbers
        result = {
            'expected_page': 0,
            'best_match_page': 0,
            'found_pages': {
                0: {'confidence': 0.9},
                1: {'confidence': 0.8}
            }
        }
        
        # Ensure 1-based pages
        updated = ensure_one_based_pages(result)
        
        # Check the result
        self.assertEqual(updated['expected_page'], 1)
        self.assertEqual(updated['best_match_page'], 1)
        self.assertIn(1, updated['found_pages'])
        self.assertNotIn(0, updated['found_pages'])


class TestConfidenceUtils(unittest.TestCase):
    """Test cases for confidence utility functions"""
    
    def test_calculate_confidence_score(self):
        """Test calculating confidence scores"""
        # Test with various inputs
        self.assertAlmostEqual(calculate_confidence_score(0.9), 0.9)
        self.assertAlmostEqual(calculate_confidence_score(0.9, distance_from_expected=0), 0.99, places=2)
        self.assertAlmostEqual(calculate_confidence_score(0.9, distance_from_expected=5), 0.65, places=2)
        self.assertAlmostEqual(calculate_confidence_score(0.9, is_toc_match=True), 0.63, places=2)
    
    def test_determine_verification_status(self):
        """Test determining verification status"""
        # Test with various inputs
        self.assertEqual(determine_verification_status(0.95, 10, 10), "verified")
        self.assertEqual(determine_verification_status(0.85, 10, 12), "likely_correct")
        self.assertEqual(determine_verification_status(0.65, 10, 15), "needs_review")
        self.assertEqual(determine_verification_status(0.45, 10, 20), "likely_incorrect")
        self.assertEqual(determine_verification_status(0.95, 10, None), "not_found")
    
    def test_standardize_result_schema(self):
        """Test standardizing result schema"""
        # Create a minimal result
        minimal_result = {
            'item_number': 1,
            'header_text': 'ITEM 1',
            'expected_page': 10,
            'best_match_page': 12,
            'confidence': 0.85,
            'status': 'likely_correct',
            'method': 'pattern_matching'
        }
        
        # Standardize the schema
        standardized = standardize_result_schema(minimal_result)
        
        # Check that all required fields are present
        required_fields = [
            'item_number', 'header_text', 'expected_page', 'found_pages',
            'best_match_page', 'confidence', 'status', 'method',
            'explanation', 'matched_text', 'distance_from_expected'
        ]
        
        for field in required_fields:
            self.assertIn(field, standardized)
        
        # Check that distance_from_expected is calculated correctly
        self.assertEqual(standardized['distance_from_expected'], 2)


if __name__ == '__main__':
    unittest.main()
