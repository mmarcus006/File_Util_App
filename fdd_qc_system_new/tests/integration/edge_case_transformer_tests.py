"""
Edge Case Tests for Transformer Verification module for testing transformer-based verification.
Part of the refactored edge case testing system.
"""

import unittest
import os
import sys
import numpy as np
from typing import Dict, List, Optional, Any

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from edge_case_test_base import EdgeCaseTestBase
from transformer_verification import TransformerVerifier

class MockTransformerEmbedder:
    """Mock transformer embedder for testing"""
    
    def __init__(self):
        """Initialize the mock transformer embedder"""
        self.embeddings = {}
    
    def get_embedding(self, text):
        """
        Get a mock embedding for the given text
        
        Args:
            text: Input text
            
        Returns:
            numpy.ndarray: Mock vector embedding
        """
        # Generate a deterministic embedding based on the text
        if text in self.embeddings:
            return self.embeddings[text]
        
        # Create a simple embedding based on character codes
        embedding = np.zeros(10)
        for i, char in enumerate(text[:10]):
            embedding[i % 10] += ord(char) / 1000.0
        
        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        
        self.embeddings[text] = embedding
        return embedding
    
    def compute_similarity(self, text1, text2):
        """
        Compute mock cosine similarity between two texts
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            float: Cosine similarity score
        """
        embedding1 = self.get_embedding(text1)
        embedding2 = self.get_embedding(text2)
        
        # Compute cosine similarity
        similarity = np.dot(embedding1, embedding2) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2))
        
        return float(similarity)

class TransformerVerificationTests(EdgeCaseTestBase):
    """
    Tests for transformer-based verification edge cases
    """
    
    def setUp(self):
        """Set up test environment"""
        super().setUp()
        
        # Create mock transformer embedder
        self.mock_embedder = MockTransformerEmbedder()
        
        # Patch the TransformerVerifier to use our mock embedder
        self._original_transformer = TransformerVerifier.transformer
        TransformerVerifier.transformer = self.mock_embedder
    
    def tearDown(self):
        """Clean up after tests"""
        # Restore original transformer
        TransformerVerifier.transformer = self._original_transformer
        super().tearDown()
    
    def test_exact_header_match_transformer(self):
        """Test exact header match with transformer verification"""
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
        pdf_processor = self._mock_pdf_processor("test_transformer_exact.pdf", pdf_content)
        
        # Create transformer verifier
        verifier = TransformerVerifier(pdf_processor)
        
        # Verify headers
        result1 = verifier.verify_header(1, headers[0]["text"], headers[0]["page_number"])
        result2 = verifier.verify_header(2, headers[1]["text"], headers[1]["page_number"])
        
        # Check results
        self._assert_verification_result(result1, "verified", 0.9)
        self._assert_verification_result(result2, "verified", 0.9)
        self.assertEqual(result1['best_match_page'], 1)
        self.assertEqual(result2['best_match_page'], 3)
    
    def test_semantic_similarity_match(self):
        """Test semantic similarity matching with transformer verification"""
        # Create test data with semantically similar but not identical text
        pdf_content = {
            1: "ITEM 1. THE COMPANY, ITS PARENT ORGANIZATIONS, PREDECESSORS, AND AFFILIATED ENTITIES",
            3: "ITEM 2. PROFESSIONAL BACKGROUND AND EXPERIENCE"
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
        pdf_processor = self._mock_pdf_processor("test_transformer_semantic.pdf", pdf_content)
        
        # Add semantic similarity to mock embedder
        self.mock_embedder.embeddings = {
            headers[0]["text"]: np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]) / np.sqrt(3.85),
            pdf_content[1]: np.array([0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 0.95, 1.05]) / np.sqrt(4.6575),
            headers[1]["text"]: np.array([0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1]) / np.sqrt(5.56),
            pdf_content[3]: np.array([0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 0.95, 1.05, 1.15]) / np.sqrt(6.5625)
        }
        
        # Create transformer verifier
        verifier = TransformerVerifier(pdf_processor)
        
        # Verify headers
        result1 = verifier.verify_header(1, headers[0]["text"], headers[0]["page_number"])
        result2 = verifier.verify_header(2, headers[1]["text"], headers[1]["page_number"])
        
        # Check results
        self._assert_verification_result(result1, "verified", 0.8)
        self._assert_verification_result(result2, "verified", 0.8)
        self.assertEqual(result1['best_match_page'], 1)
        self.assertEqual(result2['best_match_page'], 3)
    
    def test_wrong_page_transformer(self):
        """Test header match on wrong page with transformer verification"""
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
        pdf_processor = self._mock_pdf_processor("test_transformer_wrong_page.pdf", pdf_content)
        
        # Create transformer verifier
        verifier = TransformerVerifier(pdf_processor)
        
        # Verify headers
        result1 = verifier.verify_header(1, headers[0]["text"], headers[0]["page_number"])
        result2 = verifier.verify_header(2, headers[1]["text"], headers[1]["page_number"])
        
        # Check results
        self.assertEqual(result1['best_match_page'], 2)
        self.assertEqual(result2['best_match_page'], 4)
        self._assert_verification_result(result1, "likely_correct", 0.7)
        self._assert_verification_result(result2, "likely_correct", 0.7)
    
    def test_no_match_transformer(self):
        """Test no header match with transformer verification"""
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
        pdf_processor = self._mock_pdf_processor("test_transformer_no_match.pdf", pdf_content)
        
        # Create transformer verifier
        verifier = TransformerVerifier(pdf_processor)
        
        # Verify headers
        result1 = verifier.verify_header(1, headers[0]["text"], headers[0]["page_number"])
        result2 = verifier.verify_header(2, headers[1]["text"], headers[1]["page_number"])
        
        # Check results
        self._assert_verification_result(result1, "not_found", 0.0)
        self._assert_verification_result(result2, "not_found", 0.0)
    
    def test_partial_content_match(self):
        """Test partial content match with transformer verification"""
        # Create test data with partial content
        pdf_content = {
            1: "ITEM 1. THE FRANCHISOR\nThis section describes the franchisor...",
            3: "ITEM 2. BUSINESS\nThis section covers business experience..."
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
        pdf_processor = self._mock_pdf_processor("test_transformer_partial.pdf", pdf_content)
        
        # Add partial match similarity to mock embedder
        self.mock_embedder.embeddings = {
            headers[0]["text"]: np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]) / np.sqrt(3.85),
            "ITEM 1. THE FRANCHISOR": np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.0, 0.0, 0.0, 0.0]) / np.sqrt(0.91),
            headers[1]["text"]: np.array([0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1]) / np.sqrt(5.56),
            "ITEM 2. BUSINESS": np.array([0.2, 0.3, 0.4, 0.5, 0.6, 0.0, 0.0, 0.0, 0.0, 0.0]) / np.sqrt(0.9)
        }
        
        # Create transformer verifier
        verifier = TransformerVerifier(pdf_processor)
        
        # Verify headers
        result1 = verifier.verify_header(1, headers[0]["text"], headers[0]["page_number"])
        result2 = verifier.verify_header(2, headers[1]["text"], headers[1]["page_number"])
        
        # Check results
        self._assert_verification_result(result1, "likely_correct", 0.7)
        self._assert_verification_result(result2, "likely_correct", 0.7)
        self.assertEqual(result1['best_match_page'], 1)
        self.assertEqual(result2['best_match_page'], 3)
