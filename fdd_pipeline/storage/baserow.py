"""
Client for interacting with Baserow database
"""

import requests
import logging
from typing import Dict, List, Any, Optional
import sys
from pathlib import Path
import json # Added for filter serialization

# Add parent directory to path for direct script execution
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fdd_pipeline.config import BASEROW_API_URL, BASEROW_API_TOKEN

# Define table IDs as constants
FDD_TABLE_ID = 545655
FRANCHISE_TABLE_ID = 535901

logger = logging.getLogger(__name__)

# Helper function as per python_custom_rules
def check_output_file_exists(output_file_path: str) -> bool:
    """Checks if the output file already exists."""
    return Path(output_file_path).is_file()

class BaserowClient:
    """Client for interacting with Baserow database."""
    
    def __init__(self):
        """Initialize with API credentials."""
        self.api_url = BASEROW_API_URL
        if not self.api_url:
            logger.error("BASEROW_API_URL not configured.")
            raise ValueError("BASEROW_API_URL is not set.")
        self.api_token = BASEROW_API_TOKEN
        if not self.api_token:
            logger.error("BASEROW_API_TOKEN not configured.")
            raise ValueError("BASEROW_API_TOKEN is not set.")
        self.headers = {
            "Authorization": f"Token {self.api_token}",
            "Content-Type": "application/json"
        }
    
    def _request(self, method: str, url: str, params: Optional[Dict[str, Any]] = None, json_data: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Helper method for making requests to Baserow API."""
        try:
            response = requests.request(method, url, headers=self.headers, params=params, json=json_data)
            response.raise_for_status()
            if response.status_code == 204: # No content for delete
                return {"status": "success", "message": "Record deleted successfully."}
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err} - {response.text}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error making {method} request to {url}: {str(e)}")
        return None

    def create_record(self, table_id: int, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new record in a Baserow table."""
        url = f"{self.api_url}/api/database/rows/table/{table_id}/?user_field_names=true"
        return self._request("POST", url, json_data=fields)
    
    def update_record(self, table_id: int, row_id: int, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing record in a Baserow table."""
        url = f"{self.api_url}/api/database/rows/table/{table_id}/{row_id}/?user_field_names=true"
        return self._request("PATCH", url, json_data=fields)
    
    def get_record(self, table_id: int, row_id: int) -> Optional[Dict[str, Any]]:
        """Get a record by ID from a Baserow table."""
        url = f"{self.api_url}/api/database/rows/table/{table_id}/{row_id}/?user_field_names=true"
        return self._request("GET", url)

    def delete_record(self, table_id: int, row_id: int) -> bool:
        """Delete a record by ID from a Baserow table."""
        url = f"{self.api_url}/api/database/rows/table/{table_id}/{row_id}/"
        result = self._request("DELETE", url)
        return result is not None and result.get("status") == "success"

    def query_records(self, table_id: int, filters_obj: Optional[Dict[str, Any]] = None,
                      order_by: Optional[str] = None, limit: int = 100,
                      search: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Query records from a Baserow table with filters, search, and ordering.
        Filters should be provided as a Baserow filter object:
        e.g. {"filter_type": "AND", "filters": [{"field": "Name", "type": "equal", "value": "test"}]}
        """
        base_url = f"{self.api_url}/api/database/rows/table/{table_id}/"
        params = {"user_field_names": "true", "size": str(limit)}

        if order_by:
            params["order_by"] = order_by
        
        if search:
            params["search"] = search

        if filters_obj:
            params["filters"] = json.dumps(filters_obj)
            # According to Baserow docs, if 'filters' param is used, individual filter_field params are ignored.
            # The API docs imply GET for list with filters, though POST might also work. Sticking to GET.

        result = self._request("GET", base_url, params=params)
        return result.get("results", []) if result else []

    def get_document_by_document_id(self, document_id_val: str) -> Optional[Dict[str, Any]]:
        """Get a document from the FDD table by its document_id field."""
        filters_obj = {
            "filter_type": "AND",
            "filters": [
                {"field": "document_id", "type": "equal", "value": document_id_val}
            ]
        }
        results = self.query_records(FDD_TABLE_ID, filters_obj=filters_obj, limit=1)
        return results[0] if results else None
            
    def get_documents_by_status(self, status: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get documents from the FDD table with a specific 'Status'."""
        filters_obj = {
            "filter_type": "AND",
            "filters": [
                # Note: API docs show 'Status' (capital S) for fdd table field_4358323
                {"field": "Status", "type": "equal", "value": status}
            ]
        }
        return self.query_records(FDD_TABLE_ID, filters_obj=filters_obj, limit=limit)
    
    def update_document_fields(self, fdd_row_id: int, fields_to_update: Dict[str, Any]) -> bool:
        """Update specified fields for a document in the FDD table."""
        result = self.update_record(FDD_TABLE_ID, fdd_row_id, fields_to_update)
        return result is not None

    def link_fdd_to_franchise(self, fdd_row_id: int, franchise_row_ids: List[int]) -> bool:
        """Link an FDD record to one or more franchise records."""
        # The 'franchise_name' field in FDD table links to Franchise table
        fields_to_update = {"franchise_name": franchise_row_ids} 
        return self.update_document_fields(fdd_row_id, fields_to_update)

    def create_franchise_record(self, franchise_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new record in the FRANCHISE table."""
        return self.create_record(FRANCHISE_TABLE_ID, franchise_data)

    def find_franchise_by_name(self, name: str, search_field: str = "parent_company", limit: int = 10) -> List[Dict[str, Any]]:
        """
        Find franchise records by a text field (defaulting to 'parent_company').
        The 'franchise_name' field in the franchise table is a link, so we search a text field.
        """
        filters_obj = {
            "filter_type": "AND",
            "filters": [
                {"field": search_field, "type": "contains", "value": name}
            ]
        }
        return self.query_records(FRANCHISE_TABLE_ID, filters_obj=filters_obj, limit=limit)
    
    # The old update_document_status can be a specific use-case of update_document_fields
    # but is kept for now if specific logic around 'stage' field is still needed from the PDF.
    # If not, it can be deprecated.
    def update_document_status(self, row_id: int, 
                              status: str, stage: Optional[str] = None, 
                              error_message: Optional[str] = None) -> bool:
        """Update a document's processing status in the FDD table."""
        fields = {"Status": status} # Changed to capital S "Status"
        
        if stage: # Assuming 'current_stage' might not be an actual field, or needs mapping.
                  # The PDF or further schema checks would clarify. If 'current_stage' is not
                  # in FDD table, this part of the function will effectively do nothing for that key.
            fields["current_stage"] = stage # Placeholder if field name differs
            
        if error_message:
            fields["error_message"] = error_message # This field exists in FDD table
            
        result = self.update_record(FDD_TABLE_ID, row_id, fields)
        return result is not None 