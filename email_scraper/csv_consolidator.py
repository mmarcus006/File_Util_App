"""
Consolidates multiple CSV files into one, removing duplicates based on 
source_document_filename and email_address columns.
"""

import os
import pandas as pd
import logging
from typing import List, Optional
import sys

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Expected CSV header based on csv_writer.py
EXPECTED_HEADERS = [
    'email_address',
    'source_document_path',
    'source_document_filename',
    'page_number',
    'extraction_timestamp'
]

def get_csv_files(directory: str) -> List[str]:
    """
    Get all CSV files in the given directory.
    
    Args:
        directory: Path to directory containing CSV files
        
    Returns:
        List of full paths to CSV files
    """
    if not os.path.exists(directory):
        logging.error(f"Directory does not exist: {directory}")
        return []
    
    csv_files = []
    for file in os.listdir(directory):
        if file.lower().endswith('.csv'):
            csv_files.append(os.path.join(directory, file))
    
    logging.info(f"Found {len(csv_files)} CSV files in {directory}")
    return csv_files

def verify_csv_format(csv_path: str) -> bool:
    """
    Verify CSV file has the expected format.
    
    Args:
        csv_path: Path to CSV file
        
    Returns:
        True if format is valid, False otherwise
    """
    try:
        # Read just the header row
        df = pd.read_csv(csv_path, nrows=0)
        
        # Check if all expected headers are present
        for header in EXPECTED_HEADERS:
            if header not in df.columns:
                logging.warning(f"CSV file {csv_path} missing header: {header}")
                return False
        
        return True
    except Exception as e:
        logging.error(f"Error verifying CSV format for {csv_path}: {e}")
        return False

def combine_csvs(csv_files: List[str]) -> Optional[pd.DataFrame]:
    """
    Combine all valid CSV files into a single DataFrame.
    
    Args:
        csv_files: List of CSV file paths
        
    Returns:
        Combined DataFrame or None if no valid files
    """
    if not csv_files:
        logging.warning("No CSV files to combine")
        return None
    
    all_data = []
    for csv_file in csv_files:
        if verify_csv_format(csv_file):
            try:
                df = pd.read_csv(csv_file)
                all_data.append(df)
                logging.info(f"Added {len(df)} rows from {os.path.basename(csv_file)}")
            except Exception as e:
                logging.error(f"Error reading {csv_file}: {e}")
        else:
            logging.warning(f"Skipping {csv_file} due to invalid format")
    
    if not all_data:
        logging.error("No valid CSV files found")
        return None
    
    combined_df = pd.concat(all_data, ignore_index=True)
    logging.info(f"Combined DataFrame has {len(combined_df)} rows before deduplication")
    return combined_df

def check_output_file_exists(output_path: str) -> bool:
    """
    Check if output file already exists.
    
    Args:
        output_path: Path to check
        
    Returns:
        True if file exists, False otherwise
    """
    if os.path.exists(output_path):
        logging.warning(f"Output file already exists: {output_path}")
        return True
    return False

def save_combined_csv(df: pd.DataFrame, output_path: str) -> None:
    """
    Save DataFrame to CSV file.
    
    Args:
        df: DataFrame to save
        output_path: Path to save to
    """
    try:
        df.to_csv(output_path, index=False)
        logging.info(f"Successfully saved {len(df)} rows to {output_path}")
    except Exception as e:
        logging.error(f"Error saving to {output_path}: {e}")

def main():
    # Paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(current_dir, "output_csvs")
    output_file = os.path.join(current_dir, "0001_AllCSV.csv")
    
    # Check if output file exists
    if check_output_file_exists(output_file):
        response = input(f"Output file {output_file} already exists. Overwrite? (y/n): ")
        if response.lower() != 'y':
            logging.info("Operation cancelled by user")
            sys.exit(0)
    
    # Get and combine CSV files
    csv_files = get_csv_files(input_dir)
    if not csv_files:
        logging.error(f"No CSV files found in {input_dir}")
        sys.exit(1)
    
    combined_df = combine_csvs(csv_files)
    if combined_df is None:
        logging.error("Failed to combine CSV files")
        sys.exit(1)
    
    # Remove duplicates based on source_document_filename and email_address
    original_count = len(combined_df)
    combined_df = combined_df.drop_duplicates(subset=['source_document_filename', 'email_address'])
    logging.info(f"Removed {original_count - len(combined_df)} duplicate entries")
    
    # Save the result
    save_combined_csv(combined_df, output_file)

if __name__ == "__main__":
    main() 