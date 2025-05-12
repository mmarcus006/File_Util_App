"""
Utility functions for text processing and pattern matching.
"""

import re
import string
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from difflib import SequenceMatcher

def clean_header_text(text: str) -> str:
    """
    Clean and normalize header text.
    
    Args:
        text: Raw header text
        
    Returns:
        Cleaned header text
    """
    if not text:
        return ""
    
    # Convert to uppercase for consistency
    text = text.upper()
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Remove punctuation except for periods in item numbers
    text = re.sub(r'[^\w\s\.]', '', text)
    
    return text

def extract_item_number(text: str) -> Optional[int]:
    """
    Extract item number from header text.
    
    Args:
        text: Header text
        
    Returns:
        Item number as integer, or None if not found
    """
    if not text:
        return None
    
    # Look for "ITEM X" pattern
    match = re.search(r'ITEM\s+(\d+)', text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    
    return None

def create_header_pattern(item_number: int, header_text: Optional[str] = None) -> str:
    """
    Create a regex pattern for finding a header in text.
    
    Args:
        item_number: Item number
        header_text: Optional header text to include in pattern
        
    Returns:
        Regex pattern string
    """
    if header_text:
        # Create a pattern that includes both item number and some words from header
        words = re.findall(r'\b\w+\b', header_text)
        if len(words) > 3:
            # Use first few significant words
            significant_words = [w for w in words if len(w) > 3][:3]
            word_pattern = '|'.join(significant_words)
            return rf'ITEM\s+{item_number}[\.:]?\s+(?:.*?(?:{word_pattern}).*?)'
    
    # Default pattern just matching the item number
    return rf'ITEM\s+{item_number}[\.:]?'

def get_standard_header_pattern(item_number: int) -> Optional[str]:
    """
    Get a standard pattern for common FDD headers.
    
    Args:
        item_number: Item number
        
    Returns:
        Regex pattern string, or None if no standard pattern exists
    """
    # Define patterns as individual variables to avoid dictionary syntax issues
    pattern_1 = r'ITEM\s+1\.?\s+(?:THE\s+)?FRANCHISOR(?:,|\.|\s+AND|\s+ITS\s+|$)'
    pattern_2 = r'ITEM\s+2\.?\s+(?:BUSINESS\s+)?EXPERIENCE'
    pattern_3 = r'ITEM\s+3\.?\s+(?:LITIGATION|LEGAL\s+PROCEEDINGS)'
    pattern_4 = r'ITEM\s+4\.?\s+(?:BANKRUPTCY)'
    pattern_5 = r'ITEM\s+5\.?\s+(?:INITIAL\s+)?(?:FRANCHISE\s+)?(?:FEE|FEES)'
    pattern_6 = r'ITEM\s+6\.?\s+(?:OTHER\s+)?(?:FEES|FEE)'
    pattern_7 = r'ITEM\s+7\.?\s+(?:ESTIMATED\s+)?INITIAL\s+INVESTMENT'
    pattern_8 = r'ITEM\s+8\.?\s+(?:RESTRICTIONS\s+ON\s+)?(?:SOURCES\s+OF\s+)?PRODUCTS?\s+AND\s+SERVICES'
    pattern_9 = r'ITEM\s+9\.?\s+(?:FRANCHISEE\'S\s+)?OBLIGATIONS'
    pattern_10 = r'ITEM\s+10\.?\s+FINANCING'
    pattern_11 = r'ITEM\s+11\.?\s+FRANCHISOR\'S\s+(?:ASSISTANCE|OBLIGATIONS)'
    pattern_12 = r'ITEM\s+12\.?\s+TERRITORY'
    pattern_13 = r'ITEM\s+13\.?\s+TRADEMARKS'
    pattern_14 = r'ITEM\s+14\.?\s+PATENTS,\s+(?:COPYRIGHTS,\s+)?(?:AND\s+)?PROPRIETARY\s+INFORMATION'
    pattern_15 = r'ITEM\s+15\.?\s+OBLIGATION\s+TO\s+(?:PARTICIPATE|OPERATE)'
    pattern_16 = r'ITEM\s+16\.?\s+RESTRICTIONS\s+ON\s+WHAT\s+(?:THE\s+)?FRANCHISEE\s+MAY\s+SELL'
    pattern_17 = r'ITEM\s+17\.?\s+(?:RENEWAL,\s+)?TERMINATION'
    pattern_18 = r'ITEM\s+18\.?\s+PUBLIC\s+FIGURES'
    pattern_19 = r'ITEM\s+19\.?\s+(?:FINANCIAL\s+)?PERFORMANCE\s+REPRESENTATIONS'
    pattern_20 = r'ITEM\s+20\.?\s+(?:OUTLETS\s+AND\s+)?FRANCHISEE\s+INFORMATION'
    pattern_21 = r'ITEM\s+21\.?\s+FINANCIAL\s+STATEMENTS'
    pattern_22 = r'ITEM\s+22\.?\s+CONTRACTS?'
    pattern_23 = r'ITEM\s+23\.?\s+RECEIPTS?'
    
    # Create dictionary with patterns
    standard_patterns = {
        1: pattern_1,
        2: pattern_2,
        3: pattern_3,
        4: pattern_4,
        5: pattern_5,
        6: pattern_6,
        7: pattern_7,
        8: pattern_8,
        9: pattern_9,
        10: pattern_10,
        11: pattern_11,
        12: pattern_12,
        13: pattern_13,
        14: pattern_14,
        15: pattern_15,
        16: pattern_16,
        17: pattern_17,
        18: pattern_18,
        19: pattern_19,
        20: pattern_20,
        21: pattern_21,
        22: pattern_22,
        23: pattern_23
    }
    
    return standard_patterns.get(item_number)

def find_pattern_in_text(pattern: str, text: str) -> List[Tuple[str, int, int]]:
    """
    Find all occurrences of a pattern in text.
    
    Args:
        pattern: Regex pattern to search for
        text: Text to search in
        
    Returns:
        List of tuples (matched_text, start_pos, end_pos)
    """
    matches = []
    for match in re.finditer(pattern, text, re.IGNORECASE | re.DOTALL):
        matched_text = match.group(0)
        start_pos = match.start()
        end_pos = match.end()
        matches.append((matched_text, start_pos, end_pos))
    
    return matches

def calculate_text_similarity(text1: str, text2: str) -> float:
    """
    Calculate similarity between two text strings.
    
    Args:
        text1: First text string
        text2: Second text string
        
    Returns:
        Similarity score (0-1)
    """
    if not text1 or not text2:
        return 0.0
    
    # Clean and normalize texts
    text1 = clean_header_text(text1)
    text2 = clean_header_text(text2)
    
    # Use SequenceMatcher for similarity
    return SequenceMatcher(None, text1, text2).ratio()

def convert_to_one_based_page(page_number: Optional[int]) -> Optional[int]:
    """
    Convert a page number to 1-based indexing.
    
    Args:
        page_number: Page number (0-based or None)
        
    Returns:
        1-based page number or None
    """
    if page_number is None:
        return None
    
    # Ensure page number is at least 1
    return max(1, page_number)

def ensure_one_based_pages(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure all page numbers in a verification result use 1-based indexing.
    
    Args:
        result: Verification result dictionary
        
    Returns:
        Updated verification result with 1-based page numbers
    """
    # Create a copy to avoid modifying the original
    updated_result = result.copy()
    
    # Convert expected_page
    if 'expected_page' in updated_result and updated_result['expected_page'] is not None:
        updated_result['expected_page'] = convert_to_one_based_page(updated_result['expected_page'])
    
    # Convert best_match_page
    if 'best_match_page' in updated_result and updated_result['best_match_page'] is not None:
        updated_result['best_match_page'] = convert_to_one_based_page(updated_result['best_match_page'])
    
    # Convert found_pages keys and any page numbers in their values
    if 'found_pages' in updated_result and updated_result['found_pages']:
        found_pages = updated_result['found_pages']
        updated_found_pages = {}
        
        for page_num, page_info in found_pages.items():
            # Convert the page number key
            new_page_num = convert_to_one_based_page(page_num)
            
            # Copy the page info
            updated_page_info = page_info.copy()
            
            # Update any page numbers in the page info
            if 'page_number' in updated_page_info:
                updated_page_info['page_number'] = convert_to_one_based_page(updated_page_info['page_number'])
            
            updated_found_pages[new_page_num] = updated_page_info
        
        updated_result['found_pages'] = updated_found_pages
    
    return updated_result
