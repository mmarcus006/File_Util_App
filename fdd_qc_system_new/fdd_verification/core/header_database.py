"""
Header Database module for storing and retrieving header information.
Part of the refactored enhanced verification system.
"""

import os
import json
import numpy as np
from typing import Dict, List, Optional, Tuple, Any

from fdd_verification.utils.text_utils import clean_header_text, convert_to_one_based_page

class HeaderDatabase:
    """
    Class for storing and retrieving header information and embeddings
    """
    
    def __init__(self, db_path=None):
        """
        Initialize the header database
        
        Args:
            db_path (str): Path to the database file (optional)
        """
        self.db_path = db_path or os.path.join(os.path.dirname(__file__), "data", "header_database.json")
        self.headers = {}
        self.embeddings = {}
        self.corrections = {}
        self._load_database()
    
    def _load_database(self):
        """Load the header database from file"""
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'r') as f:
                    data = json.load(f)
                    self.headers = data.get('headers', {})
                    self.corrections = data.get('corrections', {})
                    
                    # Convert embeddings from list to numpy arrays
                    embeddings_data = data.get('embeddings', {})
                    for key, value in embeddings_data.items():
                        if value:
                            self.embeddings[key] = np.array(value)
            except Exception as e:
                print(f"Error loading header database: {str(e)}")
    
    def _save_database(self):
        """Save the header database to file"""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            # Convert numpy arrays to lists for JSON serialization
            embeddings_data = {}
            for key, value in self.embeddings.items():
                if isinstance(value, np.ndarray):
                    embeddings_data[key] = value.tolist()
                else:
                    embeddings_data[key] = value
            
            data = {
                'headers': self.headers,
                'embeddings': embeddings_data,
                'corrections': self.corrections
            }
            
            with open(self.db_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving header database: {str(e)}")
    
    def add_header(self, item_number: int, header_text: str, page_number: int, embedding=None):
        """
        Add a header to the database
        
        Args:
            item_number (int): Item number
            header_text (str): Header text
            page_number (int): Page number (1-based)
            embedding: Optional embedding vector
        """
        # Ensure page_number is 1-based
        page_number_1based = convert_to_one_based_page(page_number)
        if page_number_1based is None:
            raise ValueError("Page number cannot be None when adding a header.")

        # Clean the header text
        header_text = clean_header_text(header_text)
        
        # Create a unique key for the header
        key = f"item_{item_number}"
        
        # Store the header information
        self.headers[key] = {
            'item_number': item_number,
            'header_text': header_text,
            'page_number': page_number_1based
        }
        
        # Store the embedding if provided
        if embedding is not None:
            self.embeddings[key] = embedding
        
        # Save the database
        self._save_database()
    
    def get_header(self, item_number: int) -> Optional[Dict]:
        """
        Get a header from the database
        
        Args:
            item_number (int): Item number
            
        Returns:
            dict: Header information, or None if not found
        """
        key = f"item_{item_number}"
        return self.headers.get(key)
    
    def get_embedding(self, item_number: int) -> Optional[np.ndarray]:
        """
        Get an embedding from the database
        
        Args:
            item_number (int): Item number
            
        Returns:
            numpy.ndarray: Embedding vector, or None if not found
        """
        key = f"item_{item_number}"
        return self.embeddings.get(key)
    
    def get_all_headers(self) -> Dict[str, Dict]:
        """
        Get all headers from the database
        
        Returns:
            dict: Dictionary of all headers
        """
        return self.headers
    
    def get_all_embeddings(self) -> Dict[str, np.ndarray]:
        """
        Get all embeddings from the database
        
        Returns:
            dict: Dictionary of all embeddings
        """
        return self.embeddings
    
    def add_header_correction(self, item_number: int, header_text: str, original_page: int, corrected_page: int):
        """
        Add a header correction to the database
        
        Args:
            item_number (int): Item number
            header_text (str): Header text
            original_page (int): Original page number (1-based)
            corrected_page (int): Corrected page number (1-based)
        """
        # Ensure page numbers are 1-based
        original_page_1based = convert_to_one_based_page(original_page)
        corrected_page_1based = convert_to_one_based_page(corrected_page)

        if original_page_1based is None or corrected_page_1based is None:
            raise ValueError("Page numbers cannot be None when adding a correction.")

        # Clean the header text
        header_text = clean_header_text(header_text)
        
        # Create a unique key for the correction
        key = f"item_{item_number}"
        
        # Store the correction
        if key not in self.corrections:
            self.corrections[key] = []
        
        self.corrections[key].append({
            'header_text': header_text,
            'original_page': original_page_1based,
            'corrected_page': corrected_page_1based,
            'timestamp': import_time()
        })
        
        # Update the header in the database
        if key in self.headers:
            self.headers[key]['page_number'] = corrected_page_1based
        else:
            self.add_header(item_number, header_text, corrected_page_1based)
        
        # Save the database
        self._save_database()
    
    def get_header_corrections(self, item_number: int) -> List[Dict]:
        """
        Get all corrections for a header
        
        Args:
            item_number (int): Item number
            
        Returns:
            list: List of correction dictionaries
        """
        key = f"item_{item_number}"
        return self.corrections.get(key, [])

def import_time():
    """Import time module and return current time as string"""
    from datetime import datetime
    return datetime.now().isoformat()
