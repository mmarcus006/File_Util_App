"""
Advanced NLP Core module for text processing and analysis.
Part of the refactored advanced NLP system.
"""

import os
import re
import nltk
import spacy
from typing import Dict, List, Optional, Tuple, Any
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# Download necessary NLTK data
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)

class NLPCore:
    """
    Core NLP functionality for text processing and analysis
    """
    
    def __init__(self):
        """Initialize the NLP core processor"""
        self.nlp = None
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        self.load_spacy_model()
    
    def load_spacy_model(self):
        """Load the spaCy model for NLP processing"""
        try:
            # Try to load a larger model first
            self.nlp = spacy.load("en_core_web_md")
        except OSError:
            try:
                # Fall back to the small model if the medium one isn't available
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                # If no model is installed, download the small one
                os.system("python -m spacy download en_core_web_sm")
                try:
                    self.nlp = spacy.load("en_core_web_sm")
                except Exception as e:
                    print(f"Error loading spaCy model: {str(e)}")
                    self.nlp = None
    
    def preprocess_text(self, text: str) -> str:
        """
        Preprocess text for NLP analysis
        
        Args:
            text: Input text
            
        Returns:
            Preprocessed text
        """
        # Convert to lowercase
        text = text.lower()
        
        # Tokenize
        tokens = word_tokenize(text)
        
        # Remove stopwords and punctuation
        tokens = [token for token in tokens if token.isalnum() and token not in self.stop_words]
        
        # Lemmatize
        tokens = [self.lemmatizer.lemmatize(token) for token in tokens]
        
        # Join back into text
        return ' '.join(tokens)
    
    def extract_header_candidates(self, page_text: str) -> List[str]:
        """
        Extract potential header candidates from page text
        
        Args:
            page_text: Text content of the page
            
        Returns:
            List of potential header candidates
        """
        candidates = []
        
        # Look for lines starting with "ITEM"
        item_pattern = re.compile(r'^(ITEM\s+\d+\.?.*?)$', re.MULTILINE | re.IGNORECASE)
        item_matches = item_pattern.findall(page_text)
        candidates.extend(item_matches)
        
        # Look for lines with all caps (potential headers)
        lines = page_text.split('\n')
        for line in lines:
            line = line.strip()
            if line and line.isupper() and len(line) > 10:
                candidates.append(line)
        
        # Use spaCy for more sophisticated extraction if available
        if self.nlp:
            doc = self.nlp(page_text)
            
            # Extract sentences that might be headers based on their structure
            for sent in doc.sents:
                sent_text = sent.text.strip()
                # Check if sentence is short and starts with a number or "ITEM"
                if (len(sent_text) < 100 and 
                    (sent_text.startswith("ITEM") or 
                     any(token.is_digit for token in sent[:2]))):
                    candidates.append(sent_text)
        
        # Remove duplicates while preserving order
        unique_candidates = []
        for candidate in candidates:
            if candidate not in unique_candidates:
                unique_candidates.append(candidate)
        
        return unique_candidates
    
    def extract_structured_headers(self, page_text: str) -> List[Dict[str, Any]]:
        """
        Extract structured header information from page text
        
        Args:
            page_text: Text content of the page
            
        Returns:
            List of structured header dictionaries
        """
        structured_headers = []
        
        # Regular expression to match FDD headers
        header_pattern = re.compile(
            r'(ITEM\s+(\d+)\.?\s+([A-Z][A-Z\s\.,\-&\']+))',
            re.IGNORECASE
        )
        
        matches = header_pattern.finditer(page_text)
        
        for match in matches:
            full_match = match.group(1)
            item_number = int(match.group(2))
            header_text = match.group(3).strip()
            
            structured_headers.append({
                'full_text': full_match,
                'item_number': item_number,
                'header_text': header_text,
                'position': match.start()
            })
        
        # Use spaCy for more sophisticated extraction if available
        if self.nlp and not structured_headers:
            doc = self.nlp(page_text)
            
            # Look for patterns like "ITEM X" followed by uppercase text
            for i, token in enumerate(doc):
                if token.text.lower() == "item" and i + 1 < len(doc) and doc[i+1].is_digit:
                    item_number = int(doc[i+1].text)
                    
                    # Extract the header text (next few tokens that are uppercase)
                    header_text = ""
                    j = i + 2
                    while j < len(doc) and (doc[j].is_upper or doc[j].is_punct or doc[j].is_space):
                        header_text += doc[j].text_with_ws
                        j += 1
                    
                    if header_text:
                        structured_headers.append({
                            'full_text': f"ITEM {item_number} {header_text}".strip(),
                            'item_number': item_number,
                            'header_text': header_text.strip(),
                            'position': token.idx
                        })
        
        return structured_headers
    
    def extract_keywords_from_header(self, header_text: str) -> List[str]:
        """
        Extract important keywords from a header text
        
        Args:
            header_text: Header text
            
        Returns:
            List of keywords
        """
        # Remove "ITEM X" prefix if present
        header_text = re.sub(r'^ITEM\s+\d+\.?\s+', '', header_text, flags=re.IGNORECASE)
        
        # Tokenize and remove stopwords
        tokens = word_tokenize(header_text.lower())
        keywords = [token for token in tokens if token.isalnum() and token not in self.stop_words]
        
        return keywords
    
    def find_header_by_keywords(self, keywords: List[str], page_text: str) -> Dict[str, Any]:
        """
        Find a header in page text based on keywords
        
        Args:
            keywords: List of keywords to search for
            page_text: Text content of the page
            
        Returns:
            Dictionary with match information
        """
        # Preprocess page text
        page_text_lower = page_text.lower()
        page_tokens = word_tokenize(page_text_lower)
        page_tokens = [token for token in page_tokens if token.isalnum()]
        
        # Count keyword matches
        matches = sum(1 for keyword in keywords if keyword in page_tokens)
        match_ratio = matches / len(keywords) if keywords else 0
        
        # Find the best matching sentence
        best_sentence = None
        best_score = 0
        
        sentences = sent_tokenize(page_text)
        for sentence in sentences:
            sentence_lower = sentence.lower()
            keyword_count = sum(1 for keyword in keywords if keyword in sentence_lower)
            score = keyword_count / len(keywords) if keywords else 0
            
            if score > best_score:
                best_score = score
                best_sentence = sentence
        
        return {
            'match_ratio': match_ratio,
            'best_sentence': best_sentence,
            'best_score': best_score
        }
