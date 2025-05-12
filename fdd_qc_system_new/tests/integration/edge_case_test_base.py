"""
Edge Case Test Base module for testing FDD header verification edge cases.
Part of the refactored edge case testing system.
"""

import unittest
import os
import sys
import json
from typing import Dict, List, Optional, Any

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class EdgeCaseTestBase(unittest.TestCase):
    """
    Base class for edge case tests with common setup and utility methods
    """
    
    def setUp(self):
        """Set up test environment"""
        # Create test directories if they don't exist
        self.test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_data')
        self.pdf_dir = os.path.join(self.test_dir, 'pdfs')
        self.json_dir = os.path.join(self.test_dir, 'json')
        
        os.makedirs(self.pdf_dir, exist_ok=True)
        os.makedirs(self.json_dir, exist_ok=True)
        
        # Initialize test data
        self.test_pdfs = {}
        self.test_jsons = {}
        
        # Load test configuration if available
        self.config_path = os.path.join(self.test_dir, 'test_config.json')
        self.config = self._load_config()
    
    def _load_config(self):
        """Load test configuration from JSON file"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading test configuration: {str(e)}")
        
        # Default configuration
        return {
            'test_pdfs': [],
            'test_jsons': [],
            'mock_api_responses': {},
            'test_thresholds': {
                'min_confidence': 0.6,
                'high_confidence': 0.8
            }
        }
    
    def _save_config(self):
        """Save test configuration to JSON file"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving test configuration: {str(e)}")
    
    def _create_test_pdf(self, name, content=None):
        """
        Create a test PDF file with specified content
        
        Args:
            name: Name of the PDF file
            content: Content to include in the PDF (if None, creates an empty PDF)
            
        Returns:
            str: Path to the created PDF file
        """
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        pdf_path = os.path.join(self.pdf_dir, f"{name}.pdf")
        
        # Create a PDF with the specified content
        c = canvas.Canvas(pdf_path, pagesize=letter)
        
        if content:
            if isinstance(content, str):
                # Single page with content
                c.drawString(100, 750, content)
                c.save()
            elif isinstance(content, list):
                # Multiple pages with content
                for page_content in content:
                    c.drawString(100, 750, page_content)
                    c.showPage()
                c.save()
            elif isinstance(content, dict):
                # Dictionary mapping page numbers to content
                for page_num, page_content in sorted(content.items()):
                    c.drawString(100, 750, page_content)
                    c.showPage()
                c.save()
        else:
            # Empty PDF
            c.save()
        
        self.test_pdfs[name] = pdf_path
        return pdf_path
    
    def _create_test_json(self, name, headers):
        """
        Create a test JSON file with specified headers
        
        Args:
            name: Name of the JSON file
            headers: List of header dictionaries
            
        Returns:
            str: Path to the created JSON file
        """
        json_path = os.path.join(self.json_dir, f"{name}.json")
        
        with open(json_path, 'w') as f:
            json.dump(headers, f, indent=2)
        
        self.test_jsons[name] = json_path
        return json_path
    
    def _create_standard_fdd_headers(self):
        """
        Create a standard set of FDD headers
        
        Returns:
            list: List of standard FDD header dictionaries
        """
        return [
            {
                "item_number": 1,
                "text": "ITEM 1. THE FRANCHISOR, AND ANY PARENTS, PREDECESSORS, AND AFFILIATES",
                "page_number": 1
            },
            {
                "item_number": 2,
                "text": "ITEM 2. BUSINESS EXPERIENCE",
                "page_number": 3
            },
            {
                "item_number": 3,
                "text": "ITEM 3. LITIGATION",
                "page_number": 5
            },
            {
                "item_number": 4,
                "text": "ITEM 4. BANKRUPTCY",
                "page_number": 7
            },
            {
                "item_number": 5,
                "text": "ITEM 5. INITIAL FEES",
                "page_number": 8
            },
            {
                "item_number": 6,
                "text": "ITEM 6. OTHER FEES",
                "page_number": 10
            },
            {
                "item_number": 7,
                "text": "ITEM 7. ESTIMATED INITIAL INVESTMENT",
                "page_number": 15
            },
            {
                "item_number": 8,
                "text": "ITEM 8. RESTRICTIONS ON SOURCES OF PRODUCTS AND SERVICES",
                "page_number": 20
            },
            {
                "item_number": 9,
                "text": "ITEM 9. FRANCHISEE'S OBLIGATIONS",
                "page_number": 25
            },
            {
                "item_number": 10,
                "text": "ITEM 10. FINANCING",
                "page_number": 30
            },
            {
                "item_number": 11,
                "text": "ITEM 11. FRANCHISOR'S ASSISTANCE, ADVERTISING, COMPUTER SYSTEMS, AND TRAINING",
                "page_number": 35
            },
            {
                "item_number": 12,
                "text": "ITEM 12. TERRITORY",
                "page_number": 45
            },
            {
                "item_number": 13,
                "text": "ITEM 13. TRADEMARKS",
                "page_number": 50
            },
            {
                "item_number": 14,
                "text": "ITEM 14. PATENTS, COPYRIGHTS, AND PROPRIETARY INFORMATION",
                "page_number": 55
            },
            {
                "item_number": 15,
                "text": "ITEM 15. OBLIGATION TO PARTICIPATE IN THE ACTUAL OPERATION OF THE FRANCHISE BUSINESS",
                "page_number": 60
            },
            {
                "item_number": 16,
                "text": "ITEM 16. RESTRICTIONS ON WHAT THE FRANCHISEE MAY SELL",
                "page_number": 65
            },
            {
                "item_number": 17,
                "text": "ITEM 17. RENEWAL, TERMINATION, TRANSFER, AND DISPUTE RESOLUTION",
                "page_number": 70
            },
            {
                "item_number": 18,
                "text": "ITEM 18. PUBLIC FIGURES",
                "page_number": 80
            },
            {
                "item_number": 19,
                "text": "ITEM 19. FINANCIAL PERFORMANCE REPRESENTATIONS",
                "page_number": 85
            },
            {
                "item_number": 20,
                "text": "ITEM 20. OUTLETS AND FRANCHISEE INFORMATION",
                "page_number": 90
            },
            {
                "item_number": 21,
                "text": "ITEM 21. FINANCIAL STATEMENTS",
                "page_number": 95
            },
            {
                "item_number": 22,
                "text": "ITEM 22. CONTRACTS",
                "page_number": 100
            },
            {
                "item_number": 23,
                "text": "ITEM 23. RECEIPTS",
                "page_number": 105
            }
        ]
    
    def _mock_pdf_processor(self, pdf_path, page_texts):
        """
        Create a mock PDF processor with predefined page texts
        
        Args:
            pdf_path: Path to the PDF file
            page_texts: Dictionary mapping page numbers to page texts
            
        Returns:
            object: Mock PDF processor
        """
        class MockPDFProcessor:
            def __init__(self, pdf_path, page_texts):
                self.pdf_path = pdf_path
                self.text_by_page = page_texts
                self.total_pages = max(page_texts.keys()) if page_texts else 0
                self.toc_page = None
                
                # Try to detect TOC page
                for page_num, text in page_texts.items():
                    if "TABLE OF CONTENTS" in text or "CONTENTS" in text:
                        self.toc_page = page_num
                        break
            
            def get_page_text(self, page_num):
                return self.text_by_page.get(page_num, "")
            
            def find_pattern_in_pdf(self, pattern, start_page=1, end_page=None):
                import re
                
                if end_page is None:
                    end_page = self.total_pages
                
                found_matches = {}
                for page_num in range(start_page, end_page + 1):
                    if page_num not in self.text_by_page:
                        continue
                        
                    page_text = self.text_by_page[page_num]
                    matches = []
                    
                    try:
                        for match in re.finditer(pattern, page_text, re.IGNORECASE):
                            matches.append((match.group(0), match.start()))
                    except Exception as e:
                        print(f"Error matching pattern '{pattern}': {str(e)}")
                    
                    if matches:
                        found_matches[page_num] = matches
                
                return found_matches
        
        return MockPDFProcessor(pdf_path, page_texts)
    
    def _mock_json_processor(self, json_path, headers):
        """
        Create a mock JSON processor with predefined headers
        
        Args:
            json_path: Path to the JSON file
            headers: List of header dictionaries
            
        Returns:
            object: Mock JSON processor
        """
        class MockJSONProcessor:
            def __init__(self, json_path, headers):
                self.json_path = json_path
                self.headers = headers
            
            def get_header_by_item_number(self, item_number):
                for header in self.headers:
                    if header.get('item_number') == item_number:
                        return header
                return None
            
            def get_all_headers(self):
                return self.headers
            
            def update_header_page_number(self, item_number, new_page_number):
                for i, header in enumerate(self.headers):
                    if header.get('item_number') == item_number:
                        self.headers[i]['page_number'] = new_page_number
                        return True
                return False
        
        return MockJSONProcessor(json_path, headers)
    
    def _assert_verification_result(self, result, expected_status=None, min_confidence=None):
        """
        Assert that a verification result meets expectations
        
        Args:
            result: Verification result dictionary
            expected_status: Expected verification status
            min_confidence: Minimum expected confidence score
        """
        self.assertIsNotNone(result)
        self.assertIn('item_number', result)
        self.assertIn('header_text', result)
        self.assertIn('expected_page', result)
        self.assertIn('confidence', result)
        self.assertIn('status', result)
        self.assertIn('method', result)
        
        if expected_status:
            self.assertEqual(result['status'], expected_status)
        
        if min_confidence is not None:
            self.assertGreaterEqual(result['confidence'], min_confidence)
