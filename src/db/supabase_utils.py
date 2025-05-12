"""
Utility functions for interacting with Supabase.
"""
from typing import Any, Dict, Optional
import requests
from requests.exceptions import RequestException
import json
import os
import sys
from dotenv import load_dotenv

# Add src directory to path for local imports if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Import config after environment variables are loaded
from config import SUPABASE_CONFIG

def execute_query(query: str, unsafe: bool = False) -> Dict[str, Any]:
    """
    Execute a SQL query against the Supabase PostgreSQL database using the SQL API.
    
    Args:
        query: SQL query to execute
        unsafe: Whether to execute in unsafe mode (needed for data modification)
        
    Returns:
        Dict containing query results or error information
    """
    url = f"{SUPABASE_CONFIG['url']}/rest/v1/sql"
    headers = {
        "apikey": SUPABASE_CONFIG["service_role_key"],
        "Authorization": f"Bearer {SUPABASE_CONFIG['service_role_key']}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    
    try:
        payload = {
            "query": query,
            # Set true if query will modify data (INSERT, UPDATE, DELETE)
            "command": unsafe
        }
        
        print(f"Sending POST to {url} with payload: {payload}")
        response = requests.post(url, headers=headers, json=payload)
        print(f"Received status code: {response.status_code}")
        print(f"Received response text: {response.text[:200]}...")
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        return {"error": str(e), "query": query}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON response", "response": response.text}

def get_supabase_client():
    """
    Get a Supabase client instance for working with the REST API.
    This function requires the supabase-py package.
    
    Returns:
        Supabase client instance
    """
    try:
        # Try to import supabase
        from supabase import create_client
        
        url = SUPABASE_CONFIG["url"]
        key = SUPABASE_CONFIG["service_role_key"]
        client = create_client(url, key)
        return client
    except ImportError:
        print("Error: supabase-py package not installed. Run 'pip install supabase'.")
        return None
