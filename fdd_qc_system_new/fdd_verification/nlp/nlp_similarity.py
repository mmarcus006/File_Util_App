"""
NLP Similarity module for computing text similarity using various methods.
Part of the refactored advanced NLP system.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from difflib import SequenceMatcher
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from nlp_core import NLPCore

class NLPSimilarity:
    """
    Class for computing text similarity using various methods
    """
    
    def __init__(self):
        """Initialize the NLP similarity processor"""
        self.nlp_core = NLPCore()
    
    def compute_text_similarity(self, text1: str, text2: str, method: str = 'tfidf') -> float:
        """
        Compute similarity between two texts using various methods
        
        Args:
            text1: First text
            text2: Second text
            method: Similarity method ('tfidf', 'spacy', 'levenshtein', 'ensemble')
            
        Returns:
            Similarity score (0-1)
        """
        if method == 'tfidf':
            return self._tfidf_similarity(text1, text2)
        elif method == 'spacy':
            return self._spacy_similarity(text1, text2)
        elif method == 'levenshtein':
            return self._levenshtein_similarity(text1, text2)
        elif method == 'ensemble':
            # Use an ensemble of methods for more robust similarity
            tfidf_sim = self._tfidf_similarity(text1, text2)
            spacy_sim = self._spacy_similarity(text1, text2)
            levenshtein_sim = self._levenshtein_similarity(text1, text2)
            
            # Weight the methods (can be adjusted based on performance)
            weights = [0.4, 0.4, 0.2]  # tfidf, spacy, levenshtein
            return (tfidf_sim * weights[0] + 
                    spacy_sim * weights[1] + 
                    levenshtein_sim * weights[2])
        else:
            # Default to TF-IDF
            return self._tfidf_similarity(text1, text2)
    
    def _tfidf_similarity(self, text1: str, text2: str) -> float:
        """
        Compute TF-IDF cosine similarity between two texts
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score (0-1)
        """
        # Preprocess texts
        text1_processed = self.nlp_core.preprocess_text(text1)
        text2_processed = self.nlp_core.preprocess_text(text2)
        
        # Create TF-IDF vectorizer
        vectorizer = TfidfVectorizer()
        
        try:
            # Transform texts to TF-IDF vectors
            tfidf_matrix = vectorizer.fit_transform([text1_processed, text2_processed])
            
            # Compute cosine similarity
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            
            return float(similarity)
        except Exception as e:
            print(f"Error computing TF-IDF similarity: {str(e)}")
            # Fall back to Levenshtein similarity
            return self._levenshtein_similarity(text1, text2)
    
    def _spacy_similarity(self, text1: str, text2: str) -> float:
        """
        Compute spaCy similarity between two texts
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score (0-1)
        """
        if not self.nlp_core.nlp:
            # Fall back to Levenshtein if spaCy is not available
            return self._levenshtein_similarity(text1, text2)
        
        try:
            # Process texts with spaCy
            doc1 = self.nlp_core.nlp(text1)
            doc2 = self.nlp_core.nlp(text2)
            
            # Compute similarity
            similarity = doc1.similarity(doc2)
            
            return float(similarity)
        except Exception as e:
            print(f"Error computing spaCy similarity: {str(e)}")
            # Fall back to Levenshtein similarity
            return self._levenshtein_similarity(text1, text2)
    
    def _levenshtein_similarity(self, text1: str, text2: str) -> float:
        """
        Compute Levenshtein (sequence) similarity between two texts
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score (0-1)
        """
        return SequenceMatcher(None, text1, text2).ratio()
