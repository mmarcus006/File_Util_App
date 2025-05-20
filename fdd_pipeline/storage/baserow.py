"""
Client for interacting with Baserow database
"""

import requests
import logging
from typing import Dict, List, Any, Optional
import sys
from pathlib import Path

# Add parent directory to path for direct script execution
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fdd_pipeline.config import BASEROW_API_URL, BASEROW_API_TOKEN

logger = logging.getLogger(__name__)

class BaserowClient:
    """Client for interacting with Baserow database."""
    
    def __init__(self):
        """Initialize with API credentials."""
        self.api_url = BASEROW_API_URL
        self.api_token = BASEROW_API_TOKEN
        self.headers = {
            "Authorization": f"Token {self.api_token}",
            "Content-Type": "application/json"
        }
    
    def create_record(self, table_id: int, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new record in a Baserow table."""
        url = f"{self.api_url}/api/database/rows/table/{table_id}/?user_field_names=true"
        
        try:
            response = requests.post(url, json=fields, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating record: {str(e)}")
            return None
    
    def update_record(self, table_id: int, row_id: int, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing record in a Baserow table."""
        url = f"{self.api_url}/api/database/rows/table/{table_id}/{row_id}/?user_field_names=true"
        
        try:
            response = requests.patch(url, json=fields, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error updating record {row_id}: {str(e)}")
            return None
    
    def get_record(self, table_id: int, row_id: int) -> Optional[Dict[str, Any]]:
        """Get a record by ID from a Baserow table."""
        url = f"{self.api_url}/api/database/rows/table/{table_id}/{row_id}/?user_field_names=true"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching record {row_id}: {str(e)}")
            return None
    
    def query_records(self, table_id: int, filters: Optional[Dict[str, Any]] = None, 
                      order_by: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Query records from a Baserow table with filters."""
        url = f"{self.api_url}/api/database/rows/table/{table_id}/?user_field_names=true&size={limit}"
        
        if order_by:
            url += f"&order_by={order_by}"
            
        try:
            # If filters are provided, apply them in the request
            if filters:
                response = requests.post(
                    url, 
                    json={"filter_type": "AND", "filters": filters},
                    headers=self.headers
                )
            else:
                response = requests.get(url, headers=self.headers)
                
            response.raise_for_status()
            result = response.json()
            return result.get("results", [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Error querying records: {str(e)}")
            return []
            
    def get_pending_documents(self, table_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get documents with 'pending' status."""
        filters = [
            {"field": "status", "type": "equal", "value": "pending"}
        ]
        return self.query_records(table_id, filters=filters, limit=limit)
    
    def update_document_status(self, table_id: int, row_id: int, 
                              status: str, stage: Optional[str] = None, 
                              error_message: Optional[str] = None) -> bool:
        """Update a document's processing status."""
        fields = {"status": status}
        
        if stage:
            fields["current_stage"] = stage
            
        if error_message:
            fields["error_message"] = error_message
            
        result = self.update_record(table_id, row_id, fields)
        return result is not None 