"""
Test module for the enhanced verification engine.
"""

import unittest
import os
import json
from unittest.mock import MagicMock, patch
import numpy as np
import sys
from pathlib import Path

# Add the parent directory to sys.path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import modules to test
from fdd_verification.core.enhanced_verification import EnhancedVerificationEngine
from fdd_verification.core.verification_engine import VerificationEngine
from fdd_verification.core.transformer_verification import TransformerVerifier
from fdd_verification.core.llm_verification import LLMVerifier
from fdd_verification.core.pdf_processor import PDFProcessor, JSONProcessor
from fdd_verification.utils.text_utils import clean_header_text, convert_to_one_based_page
from fdd_verification.utils.confidence_utils import standardize_result_schema, merge_verification_results

class TestEnhancedVerificationEngine(unittest.TestCase):
    """Test cases for the EnhancedVerificationEngine class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Real file paths for testing
        self.json_file_path = "C:\\Projects\\File_Util_App\\fdd_qc_system_new\\tests\\data\\0a6a4155-b831-4d28-a7bf-f7eb1da5d2ad_origin_huridocs_analysis_extracted_headers.json"
        self.pdf_file_path = "C:\\Projects\\File_Util_App\\fdd_qc_system_new\\tests\\data\\0a6a4155-b831-4d28-a7bf-f7eb1da5d2ad_origin.pdf"
        
        # Load real headers from JSON file for testing
        with open(self.json_file_path, 'r') as f:
            self.real_headers = json.load(f)
        
        # Create mock PDF and JSON processors
        self.pdf_processor = MagicMock(spec=PDFProcessor)
        self.json_processor = MagicMock(spec=JSONProcessor)
        
        # Configure mock behavior based on real data
        self.pdf_processor.total_pages = 256  # Based on JSON data
        self.pdf_processor.toc_page = 3
        
        # Extract sample headers from real headers
        self.sample_headers = self.real_headers[:23]  # All 23 items
        
        self.json_processor.get_all_headers.return_value = self.sample_headers
        self.json_processor.get_header_by_item_number.side_effect = lambda item_number: next(
            (h for h in self.sample_headers if h['item_number'] == item_number), None
        )
        
        # Mock the verification components
        with patch('fdd_verification.core.enhanced_verification.VerificationEngine') as mock_ve, \
             patch('fdd_verification.core.enhanced_verification.TransformerVerifier') as mock_tv, \
             patch('fdd_verification.core.enhanced_verification.LLMVerifier') as mock_lv, \
             patch('fdd_verification.core.enhanced_verification.HeaderDatabase') as mock_hd:
            
            # Create a mock result dictionary for all 23 items
            mock_results = {}
            for header in self.sample_headers:
                item_number = header['item_number']
                page_number = header['page_number']
                text = header['text']
                
                # Set confidence and status based on item number
                if item_number <= 10:
                    confidence = 0.9
                    status = 'verified'
                elif item_number <= 15:
                    confidence = 0.7
                    status = 'needs_review'
                else:
                    confidence = 0.5
                    status = 'likely_incorrect'
                
                mock_results[item_number] = {
                    'item_number': item_number,
                    'header_text': text,
                    'expected_page': page_number,
                    'best_match_page': page_number,
                    'confidence': confidence,
                    'status': status,
                    'method': 'pattern_matching',
                    'found_pages': {page_number: {'confidence': confidence}}
                }
            
            mock_ve.return_value.verify_all_headers.return_value = mock_results
            
            # Configure side effects for verify_header
            mock_ve.return_value.verify_header.side_effect = lambda item_number, header_text, expected_page: {
                'item_number': item_number,
                'header_text': header_text,
                'expected_page': expected_page,
                'best_match_page': expected_page,
                'confidence': 0.9 if item_number <= 10 else 0.7 if item_number <= 15 else 0.5,
                'status': 'verified' if item_number <= 10 else 'needs_review' if item_number <= 15 else 'likely_incorrect',
                'method': 'pattern_matching',
                'found_pages': {expected_page: {'confidence': 0.9 if item_number <= 10 else 0.7 if item_number <= 15 else 0.5}}
            }
            
            # Configure transformer verifier mock
            mock_tv.return_value.verify_header.side_effect = lambda item_number, header_text, expected_page: {
                'item_number': item_number,
                'header_text': header_text,
                'expected_page': expected_page,
                'best_match_page': expected_page,
                'confidence': 0.95 if 10 < item_number <= 15 else 0.8 if 15 < item_number <= 20 else 0.7,
                'status': 'verified' if 10 < item_number <= 15 else 'likely_correct' if 15 < item_number <= 20 else 'needs_review',
                'method': 'transformer',
                'found_pages': {expected_page: {'confidence': 0.95 if 10 < item_number <= 15 else 0.8 if 15 < item_number <= 20 else 0.7}}
            }
            
            # Configure LLM verifier mock
            mock_lv.return_value.verify_header.side_effect = lambda item_number, header_text, expected_page, page_text: {
                'verified': True if item_number > 20 else False,
                'page_number': expected_page if item_number > 20 else None,
                'confidence': 0.98 if item_number > 20 else 0.3,
                'explanation': 'Found the header' if item_number > 20 else 'Could not find the header'
            }
            
            # Create the enhanced verification engine
            self.engine = EnhancedVerificationEngine(self.pdf_processor, self.json_processor)
            
            # Store the mocks for later assertions
            self.mock_ve = mock_ve
            self.mock_tv = mock_tv
            self.mock_lv = mock_lv
            self.mock_hd = mock_hd
    
    def test_verify_all_headers(self):
        """Test verifying all headers with the enhanced engine"""
        # Verify all headers
        results = self.engine.verify_all_headers()
        
        # Check that all verification methods were called
        self.mock_ve.return_value.verify_all_headers.assert_called_once()
        
        # Check the results
        self.assertEqual(len(results), 23)  # 23 items in the JSON
        
        # Check some specific items
        self.assertEqual(results[1]['status'], 'verified')
        self.assertEqual(results[12]['status'], 'verified')
        self.assertEqual(results[20]['status'], 'likely_incorrect')
    
    def test_verify_header(self):
        """Test verifying a single header with the enhanced engine"""
        # Item 1 should use pattern matching only (high confidence)
        result1 = self.engine.verify_header(1, "Item 1", 8)
        
        # Check that pattern matching was called with correct data
        self.mock_ve.return_value.verify_header.assert_called_with(1, "Item 1", 8)
        
        # Check the result
        self.assertEqual(result1['status'], 'verified')
        self.assertEqual(result1['method'], 'pattern_matching')
        
        # Item 12 should use transformer (needs better confidence)
        result12 = self.engine.verify_header(12, "Item 12", 41)
        
        # Check that transformer was called with correct data
        self.mock_tv.return_value.verify_header.assert_called_with(12, "Item 12", 41)
        
        # Check the result
        self.assertEqual(result12['status'], 'verified')
        self.assertEqual(result12['method'], 'transformer')
        
        # Item 23 should use LLM (difficult case)
        result23 = self.engine.verify_header(23, "Item 23", 68)
        
        # Check that LLM was called
        self.mock_lv.return_value.verify_header.assert_called()
        
        # Check the result
        self.assertEqual(result23['status'], 'verified')
        self.assertEqual(result23['method'], 'llm')
    
    def test_get_headers_needing_verification(self):
        """Test getting headers that need additional verification"""
        # Configure mock behavior for verification results based on real data
        results = {}
        
        for header in self.sample_headers[:4]:  # Use first 4 items with varying confidence
            item_number = header['item_number']
            page_number = header['page_number']
            text = header['text']
            
            # Set different confidences for testing
            if item_number == 1:
                confidence = 0.95
                status = 'verified'
                best_match_page = page_number
            elif item_number == 2:
                confidence = 0.75
                status = 'needs_review'
                best_match_page = page_number
            elif item_number == 3:
                confidence = 0.55
                status = 'likely_incorrect'
                best_match_page = page_number + 2  # Mismatch
            else:  # item_number == 4
                confidence = 0
                status = 'not_found'
                best_match_page = None
            
            results[item_number] = {
                'item_number': item_number,
                'header_text': text,
                'expected_page': page_number,
                'best_match_page': best_match_page,
                'confidence': confidence,
                'status': status
            }
        
        # Get headers needing verification
        headers = self.engine._get_headers_needing_verification(results, threshold=0.8)
        
        # Check the results
        self.assertEqual(len(headers), 3)
        self.assertEqual(headers[0]['item_number'], 4)  # Lowest confidence first
        self.assertEqual(headers[1]['item_number'], 3)
        self.assertEqual(headers[2]['item_number'], 2)
    
    def test_get_verification_summary(self):
        """Test getting a verification summary"""
        # Configure mock behavior for verification results
        self.engine.verification_results = {
            1: {'item_number': 1, 'status': 'verified', 'confidence': 0.95, 'method': 'pattern_matching'},
            2: {'item_number': 2, 'status': 'verified', 'confidence': 0.95, 'method': 'pattern_matching'},
            3: {'item_number': 3, 'status': 'verified', 'confidence': 0.95, 'method': 'pattern_matching'},
            4: {'item_number': 4, 'status': 'verified', 'confidence': 0.95, 'method': 'pattern_matching'},
            5: {'item_number': 5, 'status': 'verified', 'confidence': 0.95, 'method': 'pattern_matching'},
            11: {'item_number': 11, 'status': 'likely_correct', 'confidence': 0.85, 'method': 'transformer'},
            12: {'item_number': 12, 'status': 'likely_correct', 'confidence': 0.85, 'method': 'transformer'},
            13: {'item_number': 13, 'status': 'needs_review', 'confidence': 0.65, 'method': 'llm'},
            14: {'item_number': 14, 'status': 'needs_review', 'confidence': 0.65, 'method': 'llm'},
            15: {'item_number': 15, 'status': 'needs_review', 'confidence': 0.65, 'method': 'llm'},
            16: {'item_number': 16, 'status': 'likely_incorrect', 'confidence': 0.45, 'method': 'pattern_matching,transformer'},
            17: {'item_number': 17, 'status': 'likely_incorrect', 'confidence': 0.45, 'method': 'pattern_matching,transformer'},
            18: {'item_number': 18, 'status': 'likely_incorrect', 'confidence': 0.45, 'method': 'pattern_matching,transformer'},
            19: {'item_number': 19, 'status': 'likely_incorrect', 'confidence': 0.45, 'method': 'pattern_matching,transformer'},
            20: {'item_number': 20, 'status': 'likely_incorrect', 'confidence': 0.45, 'method': 'pattern_matching,transformer'},
            21: {'item_number': 21, 'status': 'not_found', 'confidence': 0, 'method': 'pattern_matching,transformer,llm'},
            22: {'item_number': 22, 'status': 'not_found', 'confidence': 0, 'method': 'pattern_matching,transformer,llm'},
            23: {'item_number': 23, 'status': 'not_found', 'confidence': 0, 'method': 'pattern_matching,transformer,llm'}
        }
        
        # Get the summary
        summary = self.engine.get_verification_summary()
        
        # Check the summary
        self.assertEqual(summary['total'], 18)
        self.assertEqual(summary['verified'], 5)
        self.assertEqual(summary['likely_correct'], 2)
        self.assertEqual(summary['needs_review'], 3)
        self.assertEqual(summary['likely_incorrect'], 5)
        self.assertEqual(summary['not_found'], 3)
        
        # Check the method counts
        self.assertEqual(summary['by_method']['pattern_matching'], 13)
        self.assertEqual(summary['by_method']['transformer'], 9)
        self.assertEqual(summary['by_method']['llm'], 6)


if __name__ == '__main__':
    unittest.main()
