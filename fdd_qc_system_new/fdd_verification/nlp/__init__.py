"""
NLP modules for FDD header verification.
"""

from fdd_verification.nlp.nlp_core import (
    preprocess_text,
    extract_keywords,
    tokenize_text,
    remove_stopwords
)

from fdd_verification.nlp.nlp_similarity import (
    compute_similarity,
    compute_embedding_similarity,
    compute_jaccard_similarity,
    compute_cosine_similarity
)

from fdd_verification.nlp.nlp_verifier import (
    NLPVerifier,
    verify_header_with_nlp
)

from fdd_verification.nlp.document_analyzer import (
    analyze_document_structure,
    extract_document_sections,
    identify_headers
)

__all__ = [
    'preprocess_text',
    'extract_keywords',
    'tokenize_text',
    'remove_stopwords',
    'compute_similarity',
    'compute_embedding_similarity',
    'compute_jaccard_similarity',
    'compute_cosine_similarity',
    'NLPVerifier',
    'verify_header_with_nlp',
    'analyze_document_structure',
    'extract_document_sections',
    'identify_headers'
]
