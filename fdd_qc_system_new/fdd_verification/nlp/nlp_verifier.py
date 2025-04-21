"""
Advanced NLP Verifier module for header verification using NLP techniques.
Part of the refactored advanced NLP system.
"""

from typing import Dict, List, Optional, Tuple, Any
import re

from nlp_core import NLPCore
from nlp_similarity import NLPSimilarity
from document_analyzer import DocumentAnalyzer
from confidence_utils import determine_verification_status, format_verification_result

class NLPVerifier:
    """
    Class for verifying headers using advanced NLP techniques
    """
    
    def __init__(self):
        """Initialize the NLP verifier"""
        self.nlp_core = NLPCore()
        self.similarity = NLPSimilarity()
        self.document_analyzer = DocumentAnalyzer()
    
    def verify_header_with_nlp(self, item_number: int, header_text: str, expected_page: int, pdf_text_by_page: Dict[int, str]) -> Dict[str, Any]:
        """
        Verify a header using advanced NLP techniques
        
        Args:
            header_text: Header text to verify
            expected_page: Expected page number
            pdf_text_by_page: Dictionary mapping page numbers to page text
            
        Returns:
            Dictionary with verification results
        """
        # Extract item number from header text if not provided
        if not item_number:
            item_match = re.search(r'ITEM\s+(\d+)', header_text, re.IGNORECASE)
            item_number = int(item_match.group(1)) if item_match else None
        
        # Extract keywords from header
        keywords = self.nlp_core.extract_keywords_from_header(header_text)
        
        # Check expected page first
        expected_page_text = pdf_text_by_page.get(expected_page, "")
        expected_page_result = self.nlp_core.find_header_by_keywords(keywords, expected_page_text)
        
        # If good match on expected page, return it
        if expected_page_result['match_ratio'] > 0.8:
            return format_verification_result(
                item_number=item_number,
                header_text=header_text,
                expected_page=expected_page,
                found_pages={expected_page: {
                    'confidence': expected_page_result['match_ratio'],
                    'best_match': expected_page_result['best_sentence'],
                    'distance_from_expected': 0
                }},
                best_match_page=expected_page,
                confidence=expected_page_result['match_ratio'],
                status=determine_verification_status(
                    expected_page_result['match_ratio'], 
                    expected_page, 
                    expected_page
                ),
                method='nlp_keywords',
                additional_info={'best_match': expected_page_result['best_sentence']}
            )
        
        # Check nearby pages
        window_size = 5
        start = max(1, expected_page - window_size)
        end = expected_page + window_size
        
        best_page = None
        best_result = None
        best_score = 0
        
        found_pages = {}
        
        for page_num in range(start, end + 1):
            if page_num == expected_page or page_num not in pdf_text_by_page:
                continue
                
            page_text = pdf_text_by_page[page_num]
            result = self.nlp_core.find_header_by_keywords(keywords, page_text)
            
            found_pages[page_num] = {
                'confidence': result['match_ratio'],
                'best_match': result['best_sentence'],
                'distance_from_expected': abs(page_num - expected_page)
            }
            
            if result['match_ratio'] > best_score:
                best_score = result['match_ratio']
                best_result = result
                best_page = page_num
        
        # If we found a good match on another page
        if best_score > 0.7:
            return format_verification_result(
                item_number=item_number,
                header_text=header_text,
                expected_page=expected_page,
                found_pages=found_pages,
                best_match_page=best_page,
                confidence=best_score,
                status=determine_verification_status(best_score, expected_page, best_page),
                method='nlp_keywords',
                additional_info={'best_match': best_result['best_sentence']}
            )
        
        # If no good matches found, try document structure analysis
        document_structure = self.document_analyzer.analyze_document_structure(pdf_text_by_page)
        predicted_page = self.document_analyzer.predict_header_page(item_number, document_structure) if item_number else None
        
        if predicted_page:
            predicted_page_text = pdf_text_by_page.get(predicted_page, "")
            predicted_result = self.nlp_core.find_header_by_keywords(keywords, predicted_page_text)
            
            found_pages[predicted_page] = {
                'confidence': predicted_result['match_ratio'] * 0.9,  # Slightly lower confidence for structure-based prediction
                'best_match': predicted_result['best_sentence'],
                'distance_from_expected': abs(predicted_page - expected_page)
            }
            
            if predicted_result['match_ratio'] > 0.6:
                return format_verification_result(
                    item_number=item_number,
                    header_text=header_text,
                    expected_page=expected_page,
                    found_pages=found_pages,
                    best_match_page=predicted_page,
                    confidence=predicted_result['match_ratio'] * 0.9,
                    status=determine_verification_status(
                        predicted_result['match_ratio'] * 0.9, 
                        expected_page, 
                        predicted_page
                    ),
                    method='document_structure',
                    additional_info={'best_match': predicted_result['best_sentence']}
                )
        
        # If still no good matches, return the best we found
        if best_page:
            return format_verification_result(
                item_number=item_number,
                header_text=header_text,
                expected_page=expected_page,
                found_pages=found_pages,
                best_match_page=best_page,
                confidence=best_score,
                status=determine_verification_status(best_score, expected_page, best_page),
                method='nlp_keywords',
                additional_info={'best_match': best_result['best_sentence']}
            )
        
        # No matches found
        return format_verification_result(
            item_number=item_number,
            header_text=header_text,
            expected_page=expected_page,
            found_pages={},
            best_match_page=None,
            confidence=0,
            status="not_found",
            method='nlp'
        )
