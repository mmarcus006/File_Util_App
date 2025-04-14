"""
Utility modules for FDD header verification.
"""

from fdd_verification.utils.text_utils import (
    clean_header_text,
    extract_item_number,
    create_header_pattern,
    get_standard_header_pattern,
    find_pattern_in_text,
    calculate_text_similarity,
    convert_to_one_based_page,
    ensure_one_based_pages
)

from fdd_verification.utils.confidence_utils import (
    calculate_confidence_score,
    determine_verification_status,
    format_verification_result,
    standardize_result_schema,
    merge_verification_results
)

__all__ = [
    'clean_header_text',
    'extract_item_number',
    'create_header_pattern',
    'get_standard_header_pattern',
    'find_pattern_in_text',
    'calculate_text_similarity',
    'convert_to_one_based_page',
    'ensure_one_based_pages',
    'calculate_confidence_score',
    'determine_verification_status',
    'format_verification_result',
    'standardize_result_schema',
    'merge_verification_results'
]
