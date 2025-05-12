"""
Utility functions for confidence calculation and verification status determination.
"""

from typing import Dict, Optional, Any, Union, List

def calculate_confidence_score(
    similarity: float, 
    distance_from_expected: Optional[int] = None,
    is_toc_match: bool = False
) -> float:
    """
    Calculate a confidence score based on similarity and distance from expected page.
    
    Args:
        similarity: Base similarity score (0-1)
        distance_from_expected: Distance from expected page (if applicable)
        is_toc_match: Whether the match is on a Table of Contents page
        
    Returns:
        Adjusted confidence score (0-1)
    """
    # Start with the base similarity score
    confidence = similarity
    
    # Adjust for distance from expected page if provided
    if distance_from_expected is not None:
        if distance_from_expected == 0:
            # Exact page match, slight boost
            confidence = min(1.0, confidence * 1.1)
        else:
            # Reduce confidence based on distance
            distance_penalty = min(0.5, distance_from_expected * 0.05)
            confidence = max(0.0, confidence - distance_penalty)
    
    # Reduce confidence for TOC matches
    if is_toc_match:
        confidence = confidence * 0.7
    
    return confidence

def determine_verification_status(
    confidence: float, 
    expected_page: Optional[int] = None,
    found_page: Optional[int] = None
) -> str:
    """
    Determine verification status based on confidence score and page match.
    
    Args:
        confidence: Confidence score (0-1)
        expected_page: Expected page number (if applicable)
        found_page: Found page number (if applicable)
        
    Returns:
        Verification status string
    """
    if not found_page:
        return "not_found"
    
    # Perfect match: high confidence and on expected page
    if expected_page and found_page == expected_page and confidence > 0.9:
        return "verified"
    
    # High confidence but not on expected page
    if confidence > 0.8:
        return "likely_correct"
    
    # Medium confidence
    if confidence > 0.6:
        return "needs_review"
    
    # Low confidence
    return "likely_incorrect"

def format_verification_result(
    item_number: int,
    header_text: str,
    expected_page: Optional[int],
    found_pages: Dict[int, Dict[str, Any]],
    best_match_page: Optional[int],
    confidence: float,
    status: str,
    method: str,
    additional_info: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Format a standardized verification result dictionary.
    
    Args:
        item_number: Item number
        header_text: Header text
        expected_page: Expected page number
        found_pages: Dictionary of found pages with match details
        best_match_page: Best matching page number
        confidence: Confidence score
        status: Verification status
        method: Verification method used
        additional_info: Any additional information to include
        
    Returns:
        Formatted verification result dictionary
    """
    # Ensure standardized output schema regardless of verification result
    result = {
        'item_number': item_number,
        'header_text': header_text,
        'expected_page': expected_page,
        'found_pages': found_pages if found_pages else {},
        'best_match_page': best_match_page,  # Can be None if not found
        'confidence': confidence,
        'status': status,
        'method': method,
        'explanation': None,
        'matched_text': None,
        'distance_from_expected': None if best_match_page is None or expected_page is None else abs(best_match_page - expected_page)
    }
    
    # Add any additional information if provided
    if additional_info:
        for key, value in additional_info.items():
            result[key] = value
    
    return result

def merge_verification_results(
    results: List[Dict[str, Any]], 
    weights: Optional[List[float]] = None
) -> Dict[str, Any]:
    """
    Merge multiple verification results, prioritizing higher confidence results
    while preserving individual method findings.
    
    Args:
        results: List of verification result dictionaries
        weights: Optional weights for each result (defaults to equal weights)
        
    Returns:
        Merged verification result
    """
    if not results:
        return {}
    
    if len(results) == 1:
        return results[0]
    
    # Use equal weights if not provided
    if not weights:
        weights = [1.0] * len(results)
    
    # Normalize weights
    total_weight = sum(weights)
    if total_weight > 0:
        weights = [w / total_weight for w in weights]
    else:
        weights = [1.0 / len(results)] * len(results)
    
    # Calculate weighted confidence
    weighted_confidence = sum(r['confidence'] * w for r, w in zip(results, weights))
    
    # Find the result with highest confidence
    best_result_index = max(range(len(results)), key=lambda i: results[i]['confidence'])
    best_result = results[best_result_index]
    
    # Get common fields from the best result
    item_number = best_result['item_number']
    header_text = best_result['header_text']
    expected_page = best_result['expected_page']
    
    # Merge found_pages from all results
    merged_found_pages = {}
    for result in results:
        for page_num, page_info in result.get('found_pages', {}).items():
            if page_num not in merged_found_pages or page_info['confidence'] > merged_found_pages[page_num]['confidence']:
                merged_found_pages[page_num] = page_info
    
    # Determine best_match_page based on highest confidence in merged found_pages
    best_match_page = None
    best_match_confidence = 0
    
    for page_num, page_info in merged_found_pages.items():
        if page_info['confidence'] > best_match_confidence:
            best_match_confidence = page_info['confidence']
            best_match_page = page_num
    
    # Recalculate status based on merged confidence and best_match_page
    status = determine_verification_status(
        weighted_confidence, 
        expected_page, 
        best_match_page
    )
    
    # Add information about merged methods
    method = '+'.join(r['method'] for r in results)
    
    # Create merged result with standardized schema
    merged = format_verification_result(
        item_number=item_number,
        header_text=header_text,
        expected_page=expected_page,
        found_pages=merged_found_pages,
        best_match_page=best_match_page,
        confidence=weighted_confidence,
        status=status,
        method=method
    )
    
    # Add any additional information from the best result
    for key, value in best_result.items():
        if key not in merged and key not in ['item_number', 'header_text', 'expected_page', 
                                            'found_pages', 'best_match_page', 'confidence', 
                                            'status', 'method']:
            merged[key] = value
    
    return merged

def standardize_result_schema(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure all verification results follow the same schema regardless of verification method.
    
    Args:
        result: Verification result dictionary
        
    Returns:
        Standardized verification result dictionary
    """
    # Define the standard schema with default values
    standard_schema = {
        'item_number': result.get('item_number'),
        'header_text': result.get('header_text', ''),
        'expected_page': result.get('expected_page'),
        'found_pages': result.get('found_pages', {}),
        'best_match_page': result.get('best_match_page'),
        'confidence': result.get('confidence', 0.0),
        'status': result.get('status', 'not_found'),
        'method': result.get('method', 'unknown'),
        'explanation': result.get('explanation'),
        'matched_text': result.get('matched_text'),
        'distance_from_expected': None
    }
    
    # Calculate distance if both expected and best match pages are available
    if standard_schema['expected_page'] is not None and standard_schema['best_match_page'] is not None:
        standard_schema['distance_from_expected'] = abs(standard_schema['best_match_page'] - standard_schema['expected_page'])
    
    # Copy any additional fields from the original result
    for key, value in result.items():
        if key not in standard_schema:
            standard_schema[key] = value
    
    return standard_schema
