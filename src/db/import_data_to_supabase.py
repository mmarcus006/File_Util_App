#!/usr/bin/env python
"""
Import data from a local SQLite database to Supabase.
"""
import json
import os
import sqlite3
import sys
from typing import Any, Dict, List, Optional, Tuple, Union, cast

import requests
from dotenv import load_dotenv
from supabase import create_client, Client

# Add src directory to path for local imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Get Supabase credentials from config file (which now uses environment variables)
try:
    # Import the config module after environment variables are loaded
    from src.config import SUPABASE_CONFIG, DB_SCHEMA
    SUPABASE_URL = SUPABASE_CONFIG["url"]
    SUPABASE_KEY = SUPABASE_CONFIG["service_role_key"]
except (ImportError, KeyError):
    # Fallback to direct environment variables if config module not available
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Error: Supabase credentials not found in environment or config")
        print("Please set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables")
        sys.exit(1)

def get_supabase_client() -> Client:
    """
    Create and return a Supabase client.
    
    Returns:
        Client: The Supabase client instance
    """
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def execute_query(client: Client, query: str) -> Dict[str, Any]:
    """
    Execute a SQL query against Supabase PostgreSQL database using the client.
    
    Args:
        client: Supabase client instance
        query: SQL query to execute
        
    Returns:
        Dict containing query results or error information
    """
    try:
        print(f"Executing query: {query[:60]}...")  # Print first 60 chars of query for debugging
        response = client.rpc('exec_sql', {'sql': query}).execute()
        
        # Access the response data and error
        data = response.model_dump() if hasattr(response, 'model_dump') else {"data": response.data}
        
        # Check for errors in the response
        if "error" in data and data["error"]:
            return {"error": str(data["error"])}
        
        # If execution was successful but no data returned
        if not data.get("data"):
            return {"message": "Query executed successfully (no data returned)"}
            
        return cast(Dict[str, Any], data.get("data", {}))
    except Exception as e:
        print(f"Error executing query: {e}")
        return {"error": str(e), "query": query}

def execute_insert(client: Client, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Insert data into a Supabase table.
    
    Args:
        client: Supabase client instance
        table: Name of the table to insert into
        data: Dictionary containing column names and values
        
    Returns:
        Dict containing response data or error information
    """
    try:
        # Use the data API for insertions
        response = client.table(table).insert(data).execute()
        
        # Access the response data and error
        resp_data = response.model_dump() if hasattr(response, 'model_dump') else {"data": response.data}
        
        # Check for errors in the response
        if "error" in resp_data and resp_data["error"]:
            return {"error": str(resp_data["error"])}
        
        return cast(Dict[str, Any], resp_data.get("data", {}))
    except Exception as e:
        error_msg = str(e)
        print(f"Error details: {error_msg}")
        
        # Check if table exists
        try:
            # Try to check if the table exists by selecting a single row
            check_table = client.table(table).select("*").limit(1).execute()
            if hasattr(check_table, 'data') and len(check_table.data) >= 0:
                print(f"Table '{table}' exists but insert failed. Possible schema mismatch.")
                # Print table columns we're trying to insert
                print(f"Attempting to insert columns: {list(data.keys())}")
        except Exception as check_err:
            print(f"Table '{table}' may not exist: {str(check_err)}")
        
        return {"error": error_msg, "table": table, "data_keys": list(data.keys())}

def get_all_tables(conn: sqlite3.Connection) -> List[str]:
    """Get all table names from the SQLite database."""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    return [row[0] for row in cursor.fetchall()]

def get_table_schema(conn: sqlite3.Connection, table_name: str) -> List[Tuple[str, str]]:
    """Get schema (column names and types) for a table."""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [(row[1], row[2]) for row in cursor.fetchall()]

def get_table_data(conn: sqlite3.Connection, table_name: str) -> List[Dict[str, Any]]:
    """Get all data from a table as dictionaries."""
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    columns = [description[0] for description in cursor.description]
    results = []
    for row in cursor.fetchall():
        row_dict = {}
        for i, col in enumerate(columns):
            row_dict[col] = row[i]
        results.append(row_dict)
    return results

def import_table(client: Client, conn: sqlite3.Connection, tables: List[str]) -> Tuple[int, int]:
    """
    Import data from multiple SQLite tables to Supabase in a specific order.
    
    Args:
        client: Supabase client instance
        conn: SQLite connection
        tables: List of all table names found in SQLite
        
    Returns:
        Tuple of (total_success_count, total_error_count)
    """
    # Define the order to import tables based on AllTables_Headers.json and inferred dependencies
    import_order = [
        "industry",       # Base table
        "category",       # Depends on Industry
        "franchise",      # Depends on Industry, Category
        "franchise_category", # Depends on Franchise, Category
        "fdd",            # Depends on Franchise
        "fdd_layout_section", # Depends on FDD
        "fdd_layout_exhibit", # Depends on FDD
        "fdd_executive",    # Depends on FDD
        "fdd_litigation",   # Depends on FDD
        "fdd_bankruptcy",   # Depends on FDD
        "fdd_initialfee",   # Depends on FDD
        "fdd_ongoingfee",   # Depends on FDD
        "fdd_initialinvestmentitem", # Depends on FDD
        "app_users",      # Independent or depends on auth.users
        "blog_posts",     # Mostly independent, maybe author/category links
        "fdd_documents",  # May depend on FDD
        # "fdd_exhibits_simple", # Removed - this table has been dropped
        # Removed: Split_PDF_Files (not in SQLite import list?), fdds_simple, fdd_sections_simple
    ]
    
    # Sort tables by import order
    ordered_tables = []
    for table in import_order:
        if table in tables:
            ordered_tables.append(table)
    
    # Add any remaining tables not explicitly ordered
    for table in tables:
        if table not in ordered_tables:
            ordered_tables.append(table)
    
    total_success = 0
    total_error = 0
    for table in ordered_tables: # Use the ordered list for iteration
        print(f"\n--- Importing table: {table} ---")
        try:
            data = get_table_data(conn, table)
        except sqlite3.Error as e:
            print(f"Error reading data from SQLite table {table}: {e}")
            total_error += 1 # Count this as an error for the table
            continue # Skip to the next table
            
        print(f"Found {len(data)} rows in SQLite table {table}")
        
        if not data:
            print(f"No data to import for table {table}. Skipping.")
            continue
        
        # Map SQLite table names to Supabase table names if needed
        table_map = {
            # Remove mappings to *_simple tables as they are likely deprecated or replaced
            # "fdds": "fdds_simple", 
            # "fdd_sections": "fdd_sections_simple",
            # "fdd_exhibits": "fdd_exhibits_simple", 
            # Add specific mappings ONLY if SQLite name differs from Supabase name
            # e.g., if SQLite had 'MyUsers' and Supabase has 'app_users'
            # 'MyUsers': 'app_users' 
        }
        
        # Get the Supabase table name
        supabase_table_name = table_map.get(table.lower(), table.lower())
        print(f"Using Supabase table name: {supabase_table_name}")
        
        success_count = 0 # Reset for each table
        error_count = 0   # Reset for each table
        
        # Determine row limit for test mode
        test_mode = os.getenv("IMPORT_TEST_MODE", "False").lower() in ("true", "1", "t")
        row_limit = 5 if test_mode else len(data)
        
        if test_mode:
            print(f"Running in TEST MODE - processing only first {row_limit} rows for {table}")
        else:
            print(f"Running in FULL MODE for {table}")
            
        for idx, row in enumerate(data[:row_limit]):
            # Skip empty rows
            if not row:
                continue
            
            # Convert None to NULL for SQL
            for key, value in row.items():
                if value is None:
                    row[key] = None
            
            print(f"Processing row {idx+1}/{row_limit} for table {table}...")
            
            # Insert the row
            result = execute_insert(client, supabase_table_name, row)
            if "error" in result:
                print(f"Error inserting row {idx+1} into {supabase_table_name}: {result.get('error', 'Unknown error')}")
                # Optionally print the row data that failed
                # print(f"Failed row data: {row}")
                error_count += 1
            else:
                # print(f"Successfully inserted row {idx+1} into {supabase_table_name}")
                success_count += 1
                
            # Show progress less frequently for large tables
            rows_processed = success_count + error_count
            if rows_processed % 50 == 0 and rows_processed > 0:
                print(f"Progress for {table}: {rows_processed}/{row_limit} rows attempted ({success_count} success, {error_count} errors)")
        
        print(f"Completed importing {table}: {success_count} rows imported successfully, {error_count} errors out of {row_limit} attempted.")
        total_success += success_count
        total_error += error_count
    
    print(f"\n--- Import Summary --- ")
    print(f"Total rows imported successfully across all tables: {total_success}")
    print(f"Total errors encountered across all tables: {total_error}")
    return total_success, total_error

def main() -> None:
    """Main function to import data from SQLite to Supabase."""
    if len(sys.argv) < 2:
        print("Usage: python import_data_to_supabase.py <sqlite_db_path>")
        sys.exit(1)
    
    sqlite_db_path = sys.argv[1]
    
    if not os.path.exists(sqlite_db_path):
        print(f"Error: Database file {sqlite_db_path} does not exist")
        sys.exit(1)
    
    print(f"Connecting to SQLite database: {sqlite_db_path}")
    conn = sqlite3.connect(sqlite_db_path)
    
    # Get Supabase client
    print(f"Connecting to Supabase at {SUPABASE_URL}...")
    client = get_supabase_client()
    
    # Get all tables
    tables = get_all_tables(conn)
    print(f"Found {len(tables)} tables in SQLite database: {', '.join(tables)}")
    
    # Import tables using the refactored function
    total_success, total_error = import_table(client, conn, tables)
    
    print(f"\nOverall Import completed: {total_success} rows imported successfully, {total_error} errors encountered.")
    conn.close()

if __name__ == "__main__":
    main() 