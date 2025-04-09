"""
Utility for exporting Supabase table data to CSV files.

This script fetches all tables with more than 10 rows from Supabase
and exports each table as a CSV file to the db_replica folder.
"""
import os
import sys
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
from supabase import Client

# Add src directory to path for local imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import local modules
from config import SUPABASE_CONFIG, DB_SCHEMA
from db.supabase_utils import get_supabase_client

def create_directory_if_not_exists(directory_path: str) -> None:
    """
    Create directory if it doesn't exist.
    
    Args:
        directory_path: Path to the directory to create
    """
    path = Path(directory_path)
    if not path.exists():
        print(f"Creating directory: {directory_path}")
        path.mkdir(parents=True, exist_ok=True)

def get_tables_with_min_rows(client: Client, min_rows: int = 10) -> List[str]:
    """
    Get all tables in the public schema that have at least min_rows rows.
    
    Args:
        client: Supabase client instance.
        min_rows: Minimum number of rows a table should have
        
    Returns:
        List of table names
    """
    # Use the exact table names from AllTables_Headers.json
    tables_to_check = [
        'app_users',
        'blog_posts',
        'category',
        'fdd',
        'fdd_bankruptcy',
        'fdd_documents',
        'fdd_executive',
        # 'fdd_exhibits_simple', # Removed - this table has been dropped
        'fdd_initialfee',
        'fdd_initialinvestmentitem',
        'fdd_layout_exhibit',
        'fdd_layout_section',
        'fdd_litigation',
        'fdd_ongoingfee',
        'franchise', # Assuming this exists from schema setup
        'franchise_category', # Assuming this exists from schema setup
        'industry', # Assuming this exists from schema setup
        # Remove tables not present in AllTables_Headers.json like:
        # 'fdds', 'fdd_sections', 'fdd_exhibits', 'fdd_layout', 'split_fdd'
    ]
    
    print(f"Checking tables in schema: {DB_SCHEMA}")
    tables_with_min_rows = []
    
    # Check each table for row count using direct table access
    for table in tables_to_check:
        try:
            print(f"Checking table: {table}")
            # First check if table exists by selecting a single row
            response = client.table(table).select("*").limit(1).execute()
            
            # If we get here, the table exists
            # Now get the count by actually fetching all data (limited for efficiency)
            # We'll use this count to decide if we should export later
            all_data = client.table(table).select("*").execute()
            
            # Handle different response structures
            if hasattr(all_data, 'data'):
                row_count = len(all_data.data) if all_data.data else 0
            elif hasattr(all_data, 'model_dump'):
                resp_data = all_data.model_dump()
                row_count = len(resp_data.get('data', [])) if 'data' in resp_data else 0
            else:
                row_count = 0
            
            print(f"Table {table} has {row_count} rows")
            
            if row_count >= min_rows:
                tables_with_min_rows.append(table)
                
        except Exception as e:
            # Table likely doesn't exist or there's another issue
            error_msg = str(e)
            if "does not exist" in error_msg:
                print(f"Table {table} does not exist in the database")
            else:
                print(f"Error checking table {table}: {error_msg}")
            continue
    
    return tables_with_min_rows

def export_table_to_csv(client: Client, table_name: str, output_dir: str) -> bool:
    """
    Export a table to a CSV file.
    
    Args:
        client: Supabase client instance.
        table_name: Name of the table to export
        output_dir: Directory to save the CSV file
        
    Returns:
        True if export was successful, False otherwise
    """
    try:
        print(f"Exporting table: {table_name}")
        
        # Use the direct table interface to fetch all records
        response = client.table(table_name).select("*").execute()
        
        # Extract data from response
        if hasattr(response, 'data'):
            data = response.data
        elif hasattr(response, 'model_dump'):
            resp_data = response.model_dump()
            data = resp_data.get('data', [])
        else:
            print(f"Unexpected response format for table: {table_name}")
            return False
        
        if not data:
            print(f"No data found in table: {table_name}")
            return False
        
        # Convert to DataFrame and export to CSV
        df = pd.DataFrame(data)
        output_file = os.path.join(output_dir, f"{table_name}.csv")
        
        try:
            df.to_csv(output_file, index=False)
            print(f"Successfully exported {table_name} to {output_file}")
            return True
        except Exception as e:
            print(f"Error writing CSV for {table_name}: {str(e)}")
            return False
            
    except Exception as e:
        print(f"Error exporting table {table_name}: {str(e)}")
        return False

def main() -> None:
    """
    Main function to export tables from Supabase to CSV files.
    """
    # Get Supabase client
    client = get_supabase_client()
    if not client:
        print("Failed to get Supabase client. Exiting.")
        return

    # Define the output directory
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "db_replica")
    create_directory_if_not_exists(output_dir)
    
    # Adjust minimum rows to 1 temporarily if you want to export tables that have any data
    tables = get_tables_with_min_rows(client, 10)
    
    if not tables:
        print("No tables found with more than 10 rows.")
        return
    
    print(f"Found {len(tables)} tables with more than 10 rows: {', '.join(tables)}")
    
    # Export each table to CSV
    export_count = 0
    for table in tables:
        if export_table_to_csv(client, table, output_dir):
            export_count += 1
    
    print(f"Export completed. Exported {export_count} out of {len(tables)} tables to {output_dir}")

if __name__ == "__main__":
    main() 