"""
Enhanced Verification Engine module for FDD header verification.
Main module that coordinates different verification methods.
"""

import os
import re
import numpy as np
from typing import Dict, List, Optional, Tuple, Any

# Import utility modules
from fdd_verification.utils.text_utils import (
    clean_header_text, 
    extract_item_number, 
    get_standard_header_pattern,
    convert_to_one_based_page,
    ensure_one_based_pages
)
from fdd_verification.utils.confidence_utils import (
    format_verification_result, 
    merge_verification_results,
    standardize_result_schema
)

# Import verification components
from fdd_verification.core.verification_engine import VerificationEngine
from fdd_verification.core.transformer_verification import TransformerVerifier
from fdd_verification.core.llm_verification import LLMVerifier
from fdd_verification.core.header_database import HeaderDatabase

class EnhancedVerificationEngine:
    """
    Enhanced engine for verifying FDD headers using multiple methods
    """
    
    def __init__(self, pdf_processor, json_processor, use_transformer=True, use_llm=True):
        """
        Initialize the enhanced verification engine
        
        Args:
            pdf_processor: PDF processor instance
            json_processor: JSON processor instance
            use_transformer: Whether to use transformer-based verification
            use_llm: Whether to use LLM-based verification
        """
        self.pdf_processor = pdf_processor
        self.json_processor = json_processor
        self.use_transformer = use_transformer
        self.use_llm = use_llm
        
        # Initialize verification components
        self.pattern_verifier = VerificationEngine(pdf_processor, json_processor)
        self.header_db = HeaderDatabase()
        
        # Initialize transformer verifier if enabled
        self.transformer_verifier = None
        if use_transformer:
            try:
                self.transformer_verifier = TransformerVerifier(pdf_processor, self.header_db.get_all_embeddings())
            except Exception as e:
                print(f"Error initializing transformer verifier: {str(e)}")
                self.use_transformer = False
        
        # Initialize LLM verifier if enabled
        self.llm_verifier = None
        if use_llm:
            try:
                self.llm_verifier = LLMVerifier()
            except Exception as e:
                print(f"Error initializing LLM verifier: {str(e)}")
                self.use_llm = False
        
        # Store verification results
        self.verification_results = {}
    
    def verify_all_headers(self):
        """
        Verify all headers using a progressive enhancement strategy
        
        Returns:
            dict: Verification results for all headers
        """
        headers = self.json_processor.get_all_headers()
        
        # First pass: verify all headers with pattern matching
        print("Verifying headers with pattern matching...")
        pattern_results = self.pattern_verifier.verify_all_headers()
        
        # Store initial results
        self.verification_results = pattern_results.copy()
        
        # Second pass: use transformer for headers that need additional verification
        if self.use_transformer and self.transformer_verifier:
            print("Verifying uncertain headers with transformer...")
            headers_for_transformer = self._get_headers_needing_verification(pattern_results, threshold=0.8)
            
            for header in headers_for_transformer:
                item_number = header['item_number']
                header_text = header['header_text']
                expected_page = header['expected_page']
                
                # Ensure expected_page is 1-based
                expected_page = convert_to_one_based_page(expected_page)
                
                transformer_result = self.transformer_verifier.verify_header(item_number, header_text, expected_page)
                
                # Ensure result follows standardized schema
                transformer_result = standardize_result_schema(transformer_result)
                
                # Merge results, giving more weight to transformer for uncertain cases
                if transformer_result['confidence'] > pattern_results[item_number]['confidence']:
                    self.verification_results[item_number] = transformer_result
                else:
                    # Merge the results with appropriate weights
                    merged_result = merge_verification_results(
                        [pattern_results[item_number], transformer_result],
                        weights=[0.4, 0.6]  # Give more weight to transformer
                    )
                    self.verification_results[item_number] = merged_result
        
        # Third pass: use LLM for headers that still need verification
        if self.use_llm and self.llm_verifier:
            print("Verifying difficult headers with LLM...")
            headers_for_llm = self._get_headers_needing_verification(self.verification_results, threshold=0.7)
            
            # Process headers in batches by page to minimize API calls
            headers_by_page = {}
            for header in headers_for_llm:
                page = header['expected_page']
                if page not in headers_by_page:
                    headers_by_page[page] = []
                headers_by_page[page].append(header)
            
            # Process each page batch
            for page_num, page_headers in headers_by_page.items():
                # Ensure page_num is 1-based
                page_num = convert_to_one_based_page(page_num)
                
                # Get page text
                page_text = self.pdf_processor.get_page_text(page_num)
                
                # Process each header on this page
                for header in page_headers:
                    item_number = header['item_number']
                    header_text = header['header_text']
                    
                    # Verify with LLM
                    llm_result = self.llm_verifier.verify_header(
                        item_number, 
                        header_text, 
                        page_num, 
                        page_text
                    )
                    
                    # Format the result
                    found_pages = {}
                    if llm_result.get('verified', False) and llm_result.get('page_number'):
                        found_page = convert_to_one_based_page(llm_result.get('page_number'))
                        found_pages[found_page] = {
                            'confidence': llm_result.get('confidence', 0),
                            'explanation': llm_result.get('explanation', ''),
                            'distance_from_expected': abs(found_page - page_num) if page_num else None
                        }
                    
                    formatted_result = format_verification_result(
                        item_number=item_number,
                        header_text=header_text,
                        expected_page=page_num,
                        found_pages=found_pages,
                        best_match_page=convert_to_one_based_page(llm_result.get('page_number')),
                        confidence=llm_result.get('confidence', 0),
                        status="verified" if llm_result.get('verified', False) else "not_found",
                        method="llm",
                        additional_info={"explanation": llm_result.get('explanation', '')}
                    )
                    
                    # Ensure result follows standardized schema
                    formatted_result = standardize_result_schema(formatted_result)
                    
                    # Merge with existing results, giving more weight to LLM for difficult cases
                    if formatted_result['confidence'] > self.verification_results[item_number]['confidence']:
                        self.verification_results[item_number] = formatted_result
                    else:
                        # Merge the results with appropriate weights
                        merged_result = merge_verification_results(
                            [self.verification_results[item_number], formatted_result],
                            weights=[0.3, 0.7]  # Give more weight to LLM
                        )
                        self.verification_results[item_number] = merged_result
        
        # Final pass: ensure all results follow the standardized schema
        for item_number in self.verification_results:
            self.verification_results[item_number] = standardize_result_schema(
                self.verification_results[item_number]
            )
            
            # Ensure all page numbers are 1-based
            self.verification_results[item_number] = ensure_one_based_pages(
                self.verification_results[item_number]
            )
        
        return self.verification_results
    
    def _get_headers_needing_verification(self, results, threshold=0.8):
        """
        Get headers that need additional verification based on confidence threshold
        
        Args:
            results: Current verification results
            threshold: Confidence threshold
            
        Returns:
            list: Headers that need additional verification
        """
        headers_needing_verification = []
        
        for item_number, result in results.items():
            # Headers with low confidence or uncertain status need additional verification
            if (result['confidence'] < threshold or 
                result['status'] in ['needs_review', 'likely_incorrect', 'not_found']):
                
                # Get the original header data
                header = self.json_processor.get_header_by_item_number(item_number)
                
                if header:
                    # Create a new header object with standardized fields
                    verification_header = {
                        'item_number': item_number,
                        'header_text': result['header_text'],
                        'expected_page': convert_to_one_based_page(result['expected_page']),
                        'best_match_page': convert_to_one_based_page(result['best_match_page']),
                        'current_confidence': result['confidence']
                    }
                    headers_needing_verification.append(verification_header)
        
        # Sort by confidence (lowest first)
        headers_needing_verification.sort(key=lambda x: x.get('current_confidence', 0))
        
        return headers_needing_verification
    
    def verify_header(self, item_number, header_text, expected_page):
        """
        Verify a single header using the progressive enhancement strategy
        
        Args:
            item_number (int): Item number
            header_text (str): Header text
            expected_page (int): Expected page number
            
        Returns:
            dict: Verification result
        """
        # Clean the header text
        header_text = clean_header_text(header_text)
        
        # Ensure expected_page is 1-based
        expected_page = convert_to_one_based_page(expected_page)
        
        # First try pattern matching
        pattern_result = self.pattern_verifier.verify_header(item_number, header_text, expected_page)
        
        # Ensure result follows standardized schema
        pattern_result = standardize_result_schema(pattern_result)
        
        # If high confidence, return the result
        if pattern_result['confidence'] > 0.8:
            self.verification_results[item_number] = pattern_result
            return pattern_result
        
        # Try transformer if available
        transformer_result = None
        if self.use_transformer and self.transformer_verifier:
            transformer_result = self.transformer_verifier.verify_header(item_number, header_text, expected_page)
            
            # Ensure result follows standardized schema
            transformer_result = standardize_result_schema(transformer_result)
            
            # If transformer gives high confidence, use it
            if transformer_result['confidence'] > pattern_result['confidence']:
                self.verification_results[item_number] = transformer_result
                return transformer_result
        
        # Try LLM for difficult cases
        if self.use_llm and self.llm_verifier and pattern_result['confidence'] < 0.7:
            # Get page text
            page_text = self.pdf_processor.get_page_text(expected_page)
            
            # Verify with LLM
            llm_result = self.llm_verifier.verify_header(
                item_number, 
                header_text, 
                expected_page, 
                page_text
            )
            
            # Format the result
            found_pages = {}
            if llm_result.get('verified', False) and llm_result.get('page_number'):
                found_page = convert_to_one_based_page(llm_result.get('page_number'))
                found_pages[found_page] = {
                    'confidence': llm_result.get('confidence', 0),
                    'explanation': llm_result.get('explanation', ''),
                    'distance_from_expected': abs(found_page - expected_page) if expected_page else None
                }
            
            formatted_result = format_verification_result(
                item_number=item_number,
                header_text=header_text,
                expected_page=expected_page,
                found_pages=found_pages,
                best_match_page=convert_to_one_based_page(llm_result.get('page_number')),
                confidence=llm_result.get('confidence', 0),
                status="verified" if llm_result.get('verified', False) else "not_found",
                method="llm",
                additional_info={"explanation": llm_result.get('explanation', '')}
            )
            
            # Ensure result follows standardized schema
            formatted_result = standardize_result_schema(formatted_result)
            
            # If LLM gives high confidence, use it
            if formatted_result['confidence'] > max(
                pattern_result['confidence'], 
                transformer_result['confidence'] if transformer_result else 0
            ):
                self.verification_results[item_number] = formatted_result
                return formatted_result
        
        # Merge results if we have multiple methods
        results_to_merge = [pattern_result]
        weights = [0.4]
        
        if transformer_result:
            results_to_merge.append(transformer_result)
            weights.append(0.6)
        
        merged_result = merge_verification_results(results_to_merge, weights)
        
        # Ensure result follows standardized schema
        merged_result = standardize_result_schema(merged_result)
        
        # Ensure all page numbers are 1-based
        merged_result = ensure_one_based_pages(merged_result)
        
        self.verification_results[item_number] = merged_result
        
        return merged_result
    
    def get_verification_summary(self):
        """
        Get a summary of the verification results
        
        Returns:
            dict: Summary of verification results
        """
        if not self.verification_results:
            self.verify_all_headers()
        
        summary = {
            'total': len(self.verification_results),
            'verified': 0,
            'likely_correct': 0,
            'needs_review': 0,
            'likely_incorrect': 0,
            'not_found': 0,
            'by_method': {
                'pattern_matching': 0,
                'transformer': 0,
                'llm': 0
            }
        }
        
        for result in self.verification_results.values():
            status = result.get('status')
            method = result.get('method')
            
            if status in summary:
                summary[status] += 1
            
            # Count methods (may include multiple methods)
            if 'pattern' in method:
                summary['by_method']['pattern_matching'] += 1
            if 'transformer' in method:
                summary['by_method']['transformer'] += 1
            if 'llm' in method:
                summary['by_method']['llm'] += 1
        
        return summary
    
    def get_headers_by_status(self, status):
        """
        Get headers with a specific verification status
        
        Args:
            status (str): Verification status
            
        Returns:
            list: Headers with the specified status
        """
        if not self.verification_results:
            self.verify_all_headers()
        
        return [result for result in self.verification_results.values() if result.get('status') == status]
    
    def get_all_results(self):
        """
        Get all verification results
        
        Returns:
            dict: All verification results
        """
        if not self.verification_results:
            self.verify_all_headers()
        
        return self.verification_results
    
    def update_header_verification(self, item_number, new_page_number, approved=True):
        """
        Update the verification result for a header and store the correction
        
        Args:
            item_number (int): Item number
            new_page_number (int): New page number
            approved (bool): Whether the verification is approved
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        if item_number not in self.verification_results:
            return False
        
        # Ensure new_page_number is 1-based
        new_page_number = convert_to_one_based_page(new_page_number)
        
        result = self.verification_results[item_number]
        original_page = result.get('expected_page')
        header_text = result.get('header_text')
        
        # Update the result
        result['expected_page'] = new_page_number
        
        if approved:
            result['status'] = "verified"
            result['confidence'] = 1.0
            result['best_match_page'] = new_page_number
        
        # Update the JSON processor
        self.json_processor.update_header_page_number(item_number, new_page_number)
        
        # Store the correction in the header database
        self.header_db.add_header_correction(
            item_number=item_number,
            header_text=header_text,
            original_page=original_page,
            corrected_page=new_page_number
        )
        
        return True
