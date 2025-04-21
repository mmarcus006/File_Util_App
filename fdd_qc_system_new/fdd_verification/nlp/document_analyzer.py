"""
Document Analysis module for analyzing document structure and predicting header locations.
Part of the refactored advanced NLP system.
"""

import re
from typing import Dict, List, Optional, Tuple, Any

from nlp_core import NLPCore

class DocumentAnalyzer:
    """
    Class for analyzing document structure and predicting header locations
    """
    
    def __init__(self):
        """Initialize the document analyzer"""
        self.nlp_core = NLPCore()
    
    def analyze_document_structure(self, pdf_text_by_page: Dict[int, str]) -> Dict[str, Any]:
        """
        Analyze the structure of the document to identify patterns in header placement
        
        Args:
            pdf_text_by_page: Dictionary mapping page numbers to page text
            
        Returns:
            Dictionary with document structure analysis
        """
        structure = {
            'header_pages': {},
            'avg_pages_between_headers': 0,
            'header_positions': {},
            'toc_page': None
        }
        
        all_headers = []
        
        # Extract headers from each page
        for page_num, page_text in pdf_text_by_page.items():
            headers = self.nlp_core.extract_structured_headers(page_text)
            
            for header in headers:
                header['page'] = page_num
                all_headers.append(header)
                
                item_num = header['item_number']
                structure['header_pages'][item_num] = page_num
        
        # Sort headers by item number
        all_headers.sort(key=lambda x: x['item_number'])
        
        # Calculate average pages between headers
        if len(all_headers) > 1:
            page_diffs = []
            for i in range(1, len(all_headers)):
                prev_page = all_headers[i-1]['page']
                curr_page = all_headers[i]['page']
                page_diffs.append(curr_page - prev_page)
            
            if page_diffs:
                structure['avg_pages_between_headers'] = sum(page_diffs) / len(page_diffs)
        
        # Analyze header positions on page
        for header in all_headers:
            item_num = header['item_number']
            position = header['position']
            page_text = pdf_text_by_page[header['page']]
            
            # Calculate relative position in the page (0-1)
            relative_position = position / len(page_text) if page_text else 0
            structure['header_positions'][item_num] = relative_position
        
        # Try to identify table of contents page
        for page_num, page_text in pdf_text_by_page.items():
            if re.search(r'(TABLE\s+OF\s+CONTENTS|CONTENTS)', page_text, re.IGNORECASE):
                structure['toc_page'] = page_num
                break
        
        return structure
    
    def predict_header_page(self, item_number: int, document_structure: Dict[str, Any]) -> Optional[int]:
        """
        Predict the page number for a header based on document structure analysis
        
        Args:
            item_number: Item number to predict
            document_structure: Document structure analysis
            
        Returns:
            Predicted page number or None
        """
        header_pages = document_structure.get('header_pages', {})
        
        # If we already have this header, return its page
        if item_number in header_pages:
            return header_pages[item_number]
        
        # If we have headers before and after, interpolate
        prev_item = None
        next_item = None
        
        for i in sorted(header_pages.keys()):
            if i < item_number:
                prev_item = i
            elif i > item_number:
                next_item = i
                break
        
        if prev_item and next_item:
            prev_page = header_pages[prev_item]
            next_page = header_pages[next_item]
            
            # Simple linear interpolation
            items_between = next_item - prev_item
            pages_between = next_page - prev_page
            
            if items_between > 0:
                relative_position = (item_number - prev_item) / items_between
                predicted_page = prev_page + int(relative_position * pages_between)
                return predicted_page
        
        # If we only have headers before or after, use average pages between headers
        avg_pages = document_structure.get('avg_pages_between_headers', 0)
        
        if prev_item:
            return header_pages[prev_item] + int((item_number - prev_item) * avg_pages)
        elif next_item:
            return header_pages[next_item] - int((next_item - item_number) * avg_pages)
        
        return None
