import json
from typing import Dict, Optional, Tuple, List
from pydantic import ValidationError
import os

from database.models import Item1Detail

# Mapping from Pydantic model fields to database column names (as per PRD 5.2.2 & 5.3.3)
# This is used if direct Pydantic model attribute names differ from DB, 
# but in our current db_handler.add_item1_data, we are explicitly mapping.
# If we wanted a more generic standardization function, this map would be key.
FIELD_NAME_MAPPING = {
    "brand_name": "item1_brand_name",
    "legal_name": "item1_legal_name",
    "parent_company": "item1_parent_company",
    "address": "item1_address",
    "city": "item1_city",
    "state": "item1_state",
    "zip_code": "item1_zip_code",
    "website": "item1_website",
    "phone": "item1_phone",
    "email": "item1_email",
    "founded_year": "item1_founded_year",
    "franchising_since": "item1_franchising_since",
    "business_description": "item1_business_description",
    "fdd_issue_date": "item1_fdd_issue_date",
    "fdd_amendment_date": "item1_fdd_amendment_date"
}

def parse_item1_json_file(file_path: str) -> Tuple[Optional[Item1Detail], Optional[str]]:
    """
    Parses an Item 1 JSON file, validates its content using the Item1Detail Pydantic model.

    Args:
        file_path (str): The path to the Item 1 JSON file.

    Returns:
        Tuple[Optional[Item1Detail], Optional[str]]: 
            A tuple containing the parsed and validated Item1Detail object and None if successful,
            or (None, error_message_string) if parsing or validation fails.
    """
    if not os.path.exists(file_path):
        return None, f"File not found: {file_path}"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return None, f"Malformed JSON in {file_path}: {e}"
    except Exception as e:
        return None, f"Error reading {file_path}: {e}"

    try:
        item1_detail = Item1Detail(**data)
        return item1_detail, None
    except ValidationError as e:
        # Log detailed Pydantic validation errors
        error_details = []
        for error in e.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            msg = error["msg"]
            error_details.append(f"Field '{field}': {msg}")
        return None, f"Pydantic validation failed for {file_path}: {'; '.join(error_details)}"
    except Exception as e:
        # Catch any other unexpected errors during model instantiation
        return None, f"Unexpected error during Pydantic model instantiation for {file_path}: {e}"

def standardize_data_keys(item1_detail: Item1Detail) -> Dict[str, any]:
    """
    Converts a validated Item1Detail Pydantic object into a dictionary 
    with keys suitable for database insertion, based on the FIELD_NAME_MAPPING.
    The current db_handler.add_item1_data does this mapping explicitly.
    This function provides an alternative way if a generic dict is needed first.

    Args:
        item1_detail (Item1Detail): The validated Pydantic model instance.

    Returns:
        Dict[str, any]: A dictionary with standardized keys.
    """
    data_dict = item1_detail.model_dump(exclude_none=True) # Get a dict from Pydantic model
    standardized_dict = {}
    for pydantic_key, db_key in FIELD_NAME_MAPPING.items():
        if pydantic_key in data_dict:
            standardized_dict[db_key] = data_dict[pydantic_key]
        else:
            # Handle cases where a field might be optional and not present
            standardized_dict[db_key] = None 
    return standardized_dict

# Example Usage (for testing - typically called from other modules)
if __name__ == '__main__':
    # Create a dummy valid JSON file for testing
    valid_json_content = {
        "brand_name": "Test Valid Brand",
        "legal_name": "Test Valid Legal LLC",
        "website": "http://valid.example.com",
        "email": "valid@example.com",
        "founded_year": 2020,
        "franchising_since": 2021,
        "fdd_issue_date": "2023-01-01",
        "business_description": "A valid test business."
    }
    valid_json_path = "./temp_valid_item1.json"
    with open(valid_json_path, 'w') as f:
        json.dump(valid_json_content, f)

    # Create a dummy malformed JSON file
    malformed_json_path = "./temp_malformed_item1.json"
    with open(malformed_json_path, 'w') as f:
        f.write("{\"brand_name\": \"Test Malformed Brand\", ") # Missing closing brace

    # Create a dummy JSON file with validation errors
    invalid_data_json_content = {
        "brand_name": "Test Invalid Data Brand",
        "founded_year": "not_a_year" # Invalid type
    }
    invalid_data_json_path = "./temp_invalid_data_item1.json"
    with open(invalid_data_json_path, 'w') as f:
        json.dump(invalid_data_json_content, f)

    print("--- Testing Valid JSON ---")
    parsed_data, error = parse_item1_json_file(valid_json_path)
    if error:
        print(f"Error parsing valid JSON: {error}")
    else:
        print(f"Successfully parsed valid JSON: {parsed_data.brand_name}")
        # print(parsed_data.model_dump_json(indent=2))
        # standardized = standardize_data_keys(parsed_data)
        # print(f"Standardized data: {standardized}")
        assert parsed_data is not None
        assert parsed_data.brand_name == "Test Valid Brand"

    print("\n--- Testing Malformed JSON ---")
    parsed_data, error = parse_item1_json_file(malformed_json_path)
    if error:
        print(f"Correctly caught error for malformed JSON: {error}")
        assert parsed_data is None
    else:
        print("Failed to catch error for malformed JSON")

    print("\n--- Testing JSON with Pydantic Validation Error ---")
    parsed_data, error = parse_item1_json_file(invalid_data_json_path)
    if error:
        print(f"Correctly caught Pydantic validation error: {error}")
        assert parsed_data is None
        assert "Field 'founded_year'" in error
    else:
        print("Failed to catch Pydantic validation error")
        
    print("\n--- Testing Non-existent File ---")
    parsed_data, error = parse_item1_json_file("non_existent_file.json")
    if error:
        print(f"Correctly caught error for non-existent file: {error}")
        assert parsed_data is None
        assert "File not found" in error
    else:
        print("Failed to catch error for non-existent file")

    # Clean up dummy files
    os.remove(valid_json_path)
    os.remove(malformed_json_path)
    os.remove(invalid_data_json_path)
    print("\njson_parser.py test operations completed.") 