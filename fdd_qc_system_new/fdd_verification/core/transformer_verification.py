"""
Transformer-based verification module for enhanced header verification.
Part of the refactored enhanced verification system.
"""

import os
import numpy as np
import torch
# Remove the general import below
# from transformers import AutoTokenizer, AutoModel
from transformers.models.auto.tokenization_auto import AutoTokenizer
from transformers.models.auto.modeling_auto import AutoModel
from typing import Dict, List, Optional, Tuple, Any

from fdd_verification.utils.text_utils import (
    clean_header_text, 
    convert_to_one_based_page,
    ensure_one_based_pages
)
from fdd_verification.utils.confidence_utils import (
    calculate_confidence_score, 
    determine_verification_status, 
    format_verification_result,
    standardize_result_schema
)

class TransformerEmbedder:
    """
    Class for generating text embeddings using pre-trained transformer models
    """
    
    def __init__(self, model_name="sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize the transformer embedder
        
        Args:
            model_name (str): Name of the pre-trained model to use
        """
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.load_model()
    
    def load_model(self):
        """Load the pre-trained model and tokenizer"""
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModel.from_pretrained(self.model_name).to(self.device)
        except Exception as e:
            print(f"Error loading transformer model: {str(e)}")
            # Fallback to a simpler model if the specified one fails
            try:
                self.model_name = "distilbert-base-uncased"
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                self.model = AutoModel.from_pretrained(self.model_name).to(self.device)
            except Exception as e:
                print(f"Error loading fallback model: {str(e)}")
                raise
    
    def get_embedding(self, text):
        """
        Generate an embedding for the given text
        
        Args:
            text (str): Input text
            
        Returns:
            numpy.ndarray: Vector embedding of the input text
        """
        if not self.tokenizer or not self.model:
            raise ValueError("Model not loaded")
        
        # Tokenize and prepare input
        inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Generate embeddings
        with torch.no_grad():
            outputs = self.model(**inputs)
        
        # Use mean pooling to get a single vector for the entire text
        embeddings = outputs.last_hidden_state.mean(dim=1)
        
        # Convert to numpy array and return
        return embeddings.cpu().numpy()[0]
    
    def compute_similarity(self, text1, text2):
        """
        Compute cosine similarity between two texts
        
        Args:
            text1 (str): First text
            text2 (str): Second text
            
        Returns:
            float: Cosine similarity score (0-1)
        """
        embedding1 = self.get_embedding(text1)
        embedding2 = self.get_embedding(text2)
        
        # Compute cosine similarity
        similarity = np.dot(embedding1, embedding2) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2))
        
        return float(similarity)

class TransformerVerifier:
    """
    Class for verifying headers using transformer embeddings
    """
    
    def __init__(self, pdf_processor, embedding_cache=None):
        """
        Initialize the transformer verifier
        
        Args:
            pdf_processor: PDF processor instance
            embedding_cache: Optional embedding cache
        """
        self.pdf_processor = pdf_processor
        self.transformer = TransformerEmbedder()
        self.embedding_cache = embedding_cache or {}
    
    def verify_header(self, item_number, header_text, expected_page):
        """
        Verify a header using transformer embeddings
        
        Args:
            item_number (int): Item number
            header_text (str): Header text
            expected_page (int): Expected page number (1-based)
            
        Returns:
            dict: Verification result
        """
        import re
        
        # Clean the header text
        header_text = clean_header_text(header_text)
        
        # Ensure expected_page is 1-based - It's already typed as int, conversion might be redundant?
        # Let's assume convert_to_one_based_page handles potential 0 or negative values correctly if they slip through.
        # However, the original function expected int, so we proceed assuming it's valid.
        # If expected_page could truly be None here, the function signature needs update.
        # expected_page_1based = convert_to_one_based_page(expected_page)
        # if expected_page_1based is None:
        #     # Handle error: expected_page cannot be None if function signature is correct
        #     # For now, let's proceed assuming expected_page is a valid int as per signature.
        #     # If errors persist, review where verify_header is called.
        #     raise ValueError("Expected page number cannot be None for verification.")

        # Get embedding for the header
        header_embedding = self._get_cached_embedding(header_text)
        
        # Search for similar text in the PDF
        found_pages = {}
        
        # First, check the expected page and nearby pages
        window_size = 5
        # Add check for expected_page validity before using it in calculations
        if expected_page is None or expected_page < 1:
             # Handle invalid expected_page - perhaps log a warning or return an error state?
             # For now, let's default to a small range if expected_page is invalid.
             print(f"Warning: Invalid expected_page ({expected_page}) for item {item_number}. Defaulting search window.")
             start = 1
             end = min(self.pdf_processor.total_pages, window_size * 2) # Search first 10 pages
        else:
            start = max(1, expected_page - window_size)
            end = min(self.pdf_processor.total_pages, expected_page + window_size)
        
        for page_num in range(start, end + 1):
            page_text = self.pdf_processor.get_page_text(page_num)
            
            # Skip empty pages
            if not page_text:
                continue
            
            # For efficiency, first check if the item number appears in the page
            item_pattern = f"ITEM\\s+{item_number}\\b"
            if not re.search(item_pattern, page_text, re.IGNORECASE):
                continue
            
            # Extract potential header sections (paragraphs starting with "ITEM")
            header_sections = re.findall(r'(ITEM\s+\d+\.?.*?)(?=\n\n|\Z)', page_text, re.IGNORECASE | re.DOTALL)
            
            if not header_sections:
                # If no clear sections, use the first 500 characters
                header_sections = [page_text[:500]]
            
            # Compare each section with the header
            for section in header_sections:
                try:
                    section_embedding = self._get_cached_embedding(section)
                    similarity = np.dot(header_embedding, section_embedding) / (np.linalg.norm(header_embedding) * np.linalg.norm(section_embedding))
                    
                    # Calculate distance only if expected_page is valid
                    distance = abs(page_num - expected_page) if expected_page is not None and expected_page >= 1 else float('inf')

                    if page_num not in found_pages or similarity > found_pages[page_num]['confidence']:
                        found_pages[page_num] = {
                            'confidence': float(similarity),
                            'distance_from_expected': distance, # Use calculated distance
                            'section': section,
                            'is_toc_match': page_num == self.pdf_processor.toc_page
                        }
                except Exception as e:
                    print(f"Error comparing embeddings for page {page_num}: {str(e)}")
        
        # If no pages found in the window, search a wider range
        if not found_pages:
            # Expand search to +/- 10 pages
            # Add check for expected_page validity before using it in calculations
            if expected_page is None or expected_page < 1:
                # If expected_page was invalid before, we might skip the wider search or use a default
                wider_start = 1 # Default to start if expected_page invalid
                wider_end = min(self.pdf_processor.total_pages, 20) # Search first 20 pages
            else:
                wider_start = max(1, expected_page - 10)
                wider_end = min(self.pdf_processor.total_pages, expected_page + 10)
            
            for page_num in range(wider_start, wider_end + 1):
                if page_num in range(start, end + 1):
                    continue  # Skip pages we've already checked
                
                page_text = self.pdf_processor.get_page_text(page_num)
                
                # Skip empty pages
                if not page_text:
                    continue
                
                # For efficiency, first check if the item number appears in the page
                item_pattern = f"ITEM\\s+{item_number}\\b"
                if not re.search(item_pattern, page_text, re.IGNORECASE):
                    continue
                
                # Extract potential header sections
                header_sections = re.findall(r'(ITEM\s+\d+\.?.*?)(?=\n\n|\Z)', page_text, re.IGNORECASE | re.DOTALL)
                
                if not header_sections:
                    # If no clear sections, use the first 500 characters
                    header_sections = [page_text[:500]]
                
                # Compare each section with the header
                for section in header_sections:
                    try:
                        section_embedding = self._get_cached_embedding(section)
                        similarity = np.dot(header_embedding, section_embedding) / (np.linalg.norm(header_embedding) * np.linalg.norm(section_embedding))
                        
                        # Calculate distance only if expected_page is valid
                        distance = abs(page_num - expected_page) if expected_page is not None and expected_page >= 1 else float('inf')

                        if page_num not in found_pages or similarity > found_pages[page_num]['confidence']:
                            found_pages[page_num] = {
                                'confidence': float(similarity),
                                'distance_from_expected': distance, # Use calculated distance
                                'section': section,
                                'is_toc_match': page_num == self.pdf_processor.toc_page
                            }
                    except Exception as e:
                        print(f"Error comparing embeddings for page {page_num}: {str(e)}")
        
        # Process the results
        if not found_pages:
            result = format_verification_result(
                item_number=item_number,
                header_text=header_text,
                expected_page=expected_page,
                found_pages={},
                best_match_page=None,
                confidence=0,
                status="not_found",
                method="transformer"
            )
            return standardize_result_schema(result)
        
        # Find the page with the highest confidence
        best_page = max(found_pages.items(), key=lambda x: x[1]['confidence'])
        page_num = best_page[0]
        confidence = best_page[1]['confidence']
        
        # Adjust confidence based on TOC match
        if best_page[1].get('is_toc_match', False):
            confidence = confidence * 0.7  # Reduce confidence for TOC matches
        
        # Determine status
        status = determine_verification_status(
            confidence=confidence,
            expected_page=expected_page,
            found_page=page_num
        )
        
        result = format_verification_result(
            item_number=item_number,
            header_text=header_text,
            expected_page=expected_page,
            found_pages=found_pages,
            best_match_page=page_num,
            confidence=confidence,
            status=status,
            method="transformer",
            additional_info={"matched_text": best_page[1].get('section', '')}
        )
        
        # Ensure result follows standardized schema and has 1-based page numbers
        return ensure_one_based_pages(standardize_result_schema(result))
    
    def _get_cached_embedding(self, text):
        """
        Get embedding from cache or generate a new one
        
        Args:
            text (str): Text to get embedding for
            
        Returns:
            numpy.ndarray: Embedding vector
        """
        if text in self.embedding_cache:
            return self.embedding_cache[text]
        
        embedding = self.transformer.get_embedding(text)
        self.embedding_cache[text] = embedding
        return embedding
