"""
FDD QC App Data Handling module for the FDD Header Quality Control System.
Contains data management and file handling functionality.
"""

import os
import json
from typing import Dict, List, Optional, Set, Any

class FDDQCDataManager:
    """Data manager for the FDD QC App"""
    
    def __init__(self):
        """Initialize the data manager"""
        self.corrected_files = self._load_corrected_files_list()
        self.flagged_pairs = {}
        self.current_file_id = None
    
    def _get_project_root(self) -> str:
        """
        Get the project root directory path
        
        Returns:
            str: Path to the project root directory
        """
        # UI module is at fdd_verification/ui, so go up two levels to get project root
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    
    def _load_corrected_files_list(self) -> set:
        """
        Load the list of already corrected file IDs
        
        Returns:
            set: Set of corrected file IDs
        """
        corrected_files = set()
        corrected_file_path = os.path.join(self._get_project_root(), "output", "corrected_files.json")
        if os.path.exists(corrected_file_path):
            try:
                with open(corrected_file_path, 'r') as f:
                    corrected_files = set(json.load(f))
                print(f"Loaded {len(corrected_files)} previously corrected files.")
            except Exception as e:
                print(f"Error loading corrected files list: {e}")
        return corrected_files
    
    def _save_corrected_files_list(self):
        """Save the updated list of corrected file IDs"""
        corrected_file_path = os.path.join(self._get_project_root(), "output", "corrected_files.json")
        try:
            os.makedirs(os.path.dirname(corrected_file_path), exist_ok=True)
            with open(corrected_file_path, 'w') as f:
                json.dump(list(self.corrected_files), f)
            print(f"Saved {len(self.corrected_files)} corrected files to list.")
        except Exception as e:
            print(f"Error saving corrected files list: {e}")
    
    def load_flagged_pairs(self, flagged_pairs: Dict[str, Dict[str, str]]):
        """
        Load flagged pairs for review
        
        Args:
            flagged_pairs: Dictionary of pairs flagged during batch processing.
                          Format: {file_id: {'pdf': pdf_path, 'json': json_path, 'results': results_path}}
        """
        self.flagged_pairs = flagged_pairs
    
    def get_uncorrected_files(self) -> List[str]:
        """
        Get list of flagged file IDs that haven't been corrected yet
        
        Returns:
            list: List of uncorrected file IDs
        """
        return [file_id for file_id in self.flagged_pairs.keys() 
                if file_id not in self.corrected_files]
    
    def mark_file_as_corrected(self, file_id: str):
        """
        Mark a file as corrected
        
        Args:
            file_id: ID of the file to mark as corrected
        """
        if file_id:
            self.corrected_files.add(file_id)
            self._save_corrected_files_list()
    
    def get_flagged_pair_info(self, file_id: str) -> Optional[Dict[str, str]]:
        """
        Get information about a flagged pair
        
        Args:
            file_id: ID of the flagged pair
            
        Returns:
            dict: Dictionary with pdf, json, and results paths, or None if not found
        """
        return self.flagged_pairs.get(file_id)
    
    def load_verification_results(self, results_path: str) -> Dict[int, Dict[str, Any]]:
        """
        Load verification results from a JSON file
        
        Args:
            results_path: Path to the results JSON file
            
        Returns:
            dict: Dictionary of verification results
        """
        results = {}
        if os.path.exists(results_path):
            try:
                with open(results_path, 'r') as f:
                    loaded_results = json.load(f)
                
                # Convert string keys to integers if needed
                for key, value in loaded_results.items():
                    try:
                        item_number = int(key)
                        results[item_number] = value
                    except ValueError:
                        # If key can't be converted to int, keep as is
                        results[key] = value
                
                print(f"Loaded {len(results)} verification results from {results_path}")
            except Exception as e:
                print(f"Error loading verification results: {e}")
        
        return results
    
    def save_verification_results(self, results: Dict[int, Dict[str, Any]], output_path: str) -> bool:
        """
        Save verification results to a JSON file
        
        Args:
            results: Dictionary of verification results
            output_path: Path to save the results
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"Saved verification results to {output_path}")
            return True
        except Exception as e:
            print(f"Error saving verification results: {e}")
            return False
    
    def save_corrected_json(self, json_processor, original_json_path: str) -> Optional[str]:
        """
        Save corrected JSON data
        
        Args:
            json_processor: JSONProcessor instance with updated data
            original_json_path: Path to the original JSON file
            
        Returns:
            str: Path to the saved file, or None if failed
        """
        if not json_processor or not original_json_path:
            print("No JSON data to save")
            return None
        
        try:
            # Create the output directory if it doesn't exist
            corrected_output_dir = os.path.join(self._get_project_root(), "output", "corrected_json")
            os.makedirs(corrected_output_dir, exist_ok=True)
            
            # Generate filename based on the original JSON, adding '_corrected'
            original_basename = os.path.basename(original_json_path)
            suggested_filename = original_basename.replace(".json", "_corrected.json")
            if suggested_filename == original_basename:  # Ensure suffix is added
                suggested_filename = os.path.splitext(original_basename)[0] + "_corrected.json"
            
            # Full path to save the file
            output_path = os.path.join(corrected_output_dir, suggested_filename)
            
            # Save the data
            saved_path = json_processor.save_json(output_path)
            
            # Mark current file as corrected if we have a file ID
            if self.current_file_id:
                self.mark_file_as_corrected(self.current_file_id)
            
            return saved_path
        
        except Exception as e:
            print(f"Error saving corrected JSON: {e}")
            return None
