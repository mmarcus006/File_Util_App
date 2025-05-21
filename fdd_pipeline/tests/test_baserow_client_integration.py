import pytest
import uuid
import time
import os
from pathlib import Path

# Adjust the Python path to include the project root for imports
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from fdd_pipeline.storage.baserow import BaserowClient, FDD_TABLE_ID, FRANCHISE_TABLE_ID, check_output_file_exists
from fdd_pipeline.config import BASEROW_API_URL, BASEROW_API_TOKEN # For checking if config is loaded

# Global list to store created record IDs for cleanup
records_to_delete = {"franchise": [], "fdd": []}

@pytest.fixture(scope="module")
def baserow_client():
    """Fixture to provide an initialized BaserowClient instance."""
    # Ensure API URL and Token are set before running tests
    if not BASEROW_API_URL or not BASEROW_API_TOKEN:
        pytest.skip("BASEROW_API_URL or BASEROW_API_TOKEN are not set. Skipping integration tests.")
    
    client = BaserowClient()
    yield client
    
    # --- Module-level cleanup ---
    # Delete all created records after tests in this module have run
    print("\nCleaning up created Baserow records...")
    for record_id in records_to_delete["fdd"]:
        try:
            client.delete_record(FDD_TABLE_ID, record_id)
            print(f"Cleaned up FDD record ID: {record_id}")
        except Exception as e:
            print(f"Error cleaning up FDD record ID {record_id}: {e}")
            
    for record_id in records_to_delete["franchise"]:
        try:
            client.delete_record(FRANCHISE_TABLE_ID, record_id)
            print(f"Cleaned up Franchise record ID: {record_id}")
        except Exception as e:
            print(f"Error cleaning up Franchise record ID {record_id}: {e}")
    print("Cleanup complete.")

def generate_unique_name(prefix="TestFranchise"):
    return f"{prefix}_{uuid.uuid4().hex[:8]}"

def generate_unique_doc_id(prefix="TestDoc"):
    return f"{prefix}_{uuid.uuid4().hex[:8]}"

# --- Test BaserowClient Methods ---

def test_create_and_get_franchise_record(baserow_client):
    unique_name = generate_unique_name()
    franchise_data = {
        "parent_company": unique_name,
        "franchise_website": f"http://{unique_name.lower()}.com",
        "email": f"contact@{unique_name.lower()}.com"
    }
    created_record = baserow_client.create_franchise_record(franchise_data)
    assert created_record is not None
    assert "id" in created_record
    assert created_record.get("parent_company") == unique_name
    records_to_delete["franchise"].append(created_record["id"])

    # Test get_record
    fetched_record = baserow_client.get_record(FRANCHISE_TABLE_ID, created_record["id"])
    assert fetched_record is not None
    assert fetched_record["id"] == created_record["id"]
    assert fetched_record.get("parent_company") == unique_name

def test_create_and_get_fdd_record(baserow_client):
    unique_doc_id = generate_unique_doc_id()
    fdd_data = {
        "document_id": unique_doc_id,
        "file_name": f"{unique_doc_id}.pdf",
        "original_pdf_url": f"http://example.com/pdfs/{unique_doc_id}.pdf"
    }
    created_record = baserow_client.create_record(FDD_TABLE_ID, fdd_data)
    assert created_record is not None
    assert "id" in created_record
    assert created_record.get("document_id") == unique_doc_id
    records_to_delete["fdd"].append(created_record["id"])

    # Test get_record
    fetched_record = baserow_client.get_record(FDD_TABLE_ID, created_record["id"])
    assert fetched_record is not None
    assert fetched_record["id"] == created_record["id"]
    assert fetched_record.get("document_id") == unique_doc_id

def test_update_franchise_record(baserow_client):
    unique_name_initial = generate_unique_name("UpdateTestInitial")
    franchise_data = {"parent_company": unique_name_initial}
    created_record = baserow_client.create_franchise_record(franchise_data)
    assert created_record is not None
    records_to_delete["franchise"].append(created_record["id"])

    unique_name_updated = generate_unique_name("UpdateTestUpdated")
    update_fields = {"parent_company": unique_name_updated, "city": "Test City"}
    updated_record = baserow_client.update_record(FRANCHISE_TABLE_ID, created_record["id"], update_fields)
    assert updated_record is not None
    assert updated_record.get("parent_company") == unique_name_updated
    assert updated_record.get("city") == "Test City"

def test_update_fdd_record(baserow_client):
    unique_doc_id = generate_unique_doc_id("UpdateFDD")
    fdd_data = {"document_id": unique_doc_id, "file_name": "initial.pdf"}
    created_record = baserow_client.create_record(FDD_TABLE_ID, fdd_data)
    assert created_record is not None
    records_to_delete["fdd"].append(created_record["id"])

    updated_file_name = "updated.pdf"
    update_fields = {"file_name": updated_file_name, "error_message": "Test Error"}
    updated_record = baserow_client.update_record(FDD_TABLE_ID, created_record["id"], update_fields)
    assert updated_record is not None
    assert updated_record.get("file_name") == updated_file_name
    assert updated_record.get("error_message") == "Test Error"

def test_delete_franchise_record(baserow_client):
    unique_name = generate_unique_name("DeleteTest")
    franchise_data = {"parent_company": unique_name}
    created_record = baserow_client.create_franchise_record(franchise_data)
    assert created_record is not None
    # Don't add to global cleanup, as this test specifically handles deletion

    delete_success = baserow_client.delete_record(FRANCHISE_TABLE_ID, created_record["id"])
    assert delete_success

    # Verify it's gone
    fetched_record = baserow_client.get_record(FRANCHISE_TABLE_ID, created_record["id"])
    assert fetched_record is None # Or however your client indicates not found (e.g. error in _request leading to None)

def test_query_franchise_records(baserow_client):
    unique_name_query = generate_unique_name("QueryFranchise")
    # Create a few records
    for i in range(3):
        record = baserow_client.create_franchise_record({"parent_company": f"{unique_name_query}_{i}", "zip_code": f"9021{i}"})
        assert record is not None
        records_to_delete["franchise"].append(record["id"])
    
    time.sleep(1) # Give Baserow a moment to index if needed

    # Test query with filter
    filters_obj = {"filter_type": "AND", "filters": [{"field": "parent_company", "type": "contains", "value": unique_name_query}]}
    results = baserow_client.query_records(FRANCHISE_TABLE_ID, filters_obj=filters_obj, limit=5)
    assert len(results) >= 3 # Could be more if previous tests failed cleanup, but should find our 3
    for r in results:
        if r["id"] in records_to_delete["franchise"]: # Only check relevant records
            assert unique_name_query in r.get("parent_company", "")

    # Test query with search
    results_search = baserow_client.query_records(FRANCHISE_TABLE_ID, search=f"{unique_name_query}_1", limit=5)
    assert len(results_search) >= 1
    assert any(f"{unique_name_query}_1" in r.get("parent_company", "") for r in results_search if r["id"] in records_to_delete["franchise"])

    # Test query with order_by (e.g., by id descending)
    results_ordered = baserow_client.query_records(FRANCHISE_TABLE_ID, order_by="-id", limit=3)
    assert len(results_ordered) <= 3 # We asked for 3
    if len(results_ordered) > 1:
        assert results_ordered[0]["id"] > results_ordered[1]["id"]


def test_get_document_by_document_id(baserow_client):
    unique_doc_id = generate_unique_doc_id("GetByDocID")
    fdd_data = {"document_id": unique_doc_id, "file_name": f"{unique_doc_id}.pdf"}
    created_record = baserow_client.create_record(FDD_TABLE_ID, fdd_data)
    assert created_record is not None
    records_to_delete["fdd"].append(created_record["id"])
    time.sleep(1) # Allow for potential indexing delays

    fetched_doc = baserow_client.get_document_by_document_id(unique_doc_id)
    assert fetched_doc is not None
    assert fetched_doc["id"] == created_record["id"]
    assert fetched_doc.get("document_id") == unique_doc_id

def test_get_documents_by_status(baserow_client):
    unique_status = f"Status_{uuid.uuid4().hex[:6]}" # e.g., "TestStatus_abc123"
    doc_id_1 = generate_unique_doc_id(f"StatusTest1_{unique_status}")
    doc_id_2 = generate_unique_doc_id(f"StatusTest2_{unique_status}")

    rec1 = baserow_client.create_record(FDD_TABLE_ID, {"document_id": doc_id_1, "Status": unique_status})
    assert rec1 is not None
    records_to_delete["fdd"].append(rec1["id"])
    
    rec2 = baserow_client.create_record(FDD_TABLE_ID, {"document_id": doc_id_2, "Status": unique_status})
    assert rec2 is not None
    records_to_delete["fdd"].append(rec2["id"])
    
    # Create a doc with a different status
    other_status_doc = baserow_client.create_record(FDD_TABLE_ID, {"document_id": generate_unique_doc_id("OtherStatus"), "Status": "DIFFERENT_STATUS"})
    assert other_status_doc is not None
    records_to_delete["fdd"].append(other_status_doc["id"])
    
    time.sleep(1) # Allow for potential indexing

    docs = baserow_client.get_documents_by_status(unique_status, limit=5)
    assert len(docs) >= 2 # Should find at least our two
    
    found_ids = [d["id"] for d in docs]
    assert rec1["id"] in found_ids
    assert rec2["id"] in found_ids
    assert other_status_doc["id"] not in found_ids
    for doc in docs:
        if doc["id"] in [rec1["id"], rec2["id"]]:
             # Baserow returns status as an object: {"id": 123, "value": "Pending", "color": "..."}
            status_field = doc.get("Status")
            assert status_field is not None
            assert status_field.get("value") == unique_status


def test_update_document_fields(baserow_client):
    doc_id = generate_unique_doc_id("UpdateFields")
    created_record = baserow_client.create_record(FDD_TABLE_ID, {"document_id": doc_id, "file_name": "original.txt"})
    assert created_record is not None
    records_to_delete["fdd"].append(created_record["id"])

    fields_to_update = {"file_name": "updated_via_method.txt", "error_message": "Fields updated!"}
    success = baserow_client.update_document_fields(created_record["id"], fields_to_update)
    assert success

    # Verify
    updated_doc = baserow_client.get_record(FDD_TABLE_ID, created_record["id"])
    assert updated_doc is not None
    assert updated_doc.get("file_name") == "updated_via_method.txt"
    assert updated_doc.get("error_message") == "Fields updated!"


def test_link_fdd_to_franchise(baserow_client):
    # 1. Create a franchise record
    franchise_name = generate_unique_name("LinkFranchise")
    franchise_rec = baserow_client.create_franchise_record({"parent_company": franchise_name})
    assert franchise_rec is not None
    records_to_delete["franchise"].append(franchise_rec["id"])

    # 2. Create an FDD record
    fdd_doc_id = generate_unique_doc_id("LinkFDD")
    fdd_rec = baserow_client.create_record(FDD_TABLE_ID, {"document_id": fdd_doc_id})
    assert fdd_rec is not None
    records_to_delete["fdd"].append(fdd_rec["id"])

    # 3. Link them
    link_success = baserow_client.link_fdd_to_franchise(fdd_rec["id"], [franchise_rec["id"]])
    assert link_success

    # 4. Verify link
    # The 'franchise_name' field in FDD table is the link. It returns an array of objects.
    # Each object has an 'id' (the row_id from franchise table) and 'value' (primary field of franchise table)
    time.sleep(0.5) # Give a moment for link to reflect
    linked_fdd_doc = baserow_client.get_record(FDD_TABLE_ID, fdd_rec["id"])
    assert linked_fdd_doc is not None
    franchise_link_field = linked_fdd_doc.get("franchise_name")
    assert isinstance(franchise_link_field, list)
    assert len(franchise_link_field) == 1
    assert franchise_link_field[0]["id"] == franchise_rec["id"]
    # The 'value' would typically be the primary field of the linked franchise record.
    # In our case, 'franchise_id' (UUID) is primary, but Baserow might show 'parent_company' if it's the first text field.
    # This assertion depends on Baserow's display logic for linked fields.
    # assert franchise_link_field[0].get("value") == franchise_name # This might fail if primary is not 'parent_company'

def test_find_franchise_by_name(baserow_client):
    search_name = generate_unique_name("FindByName")
    # Create a record with this name in parent_company
    rec = baserow_client.create_franchise_record({"parent_company": search_name, "city": "SearchVille"})
    assert rec is not None
    records_to_delete["franchise"].append(rec["id"])
    
    # Create another non-matching record
    other_rec = baserow_client.create_franchise_record({"parent_company": generate_unique_name("OtherFind"), "city": "OtherCity"})
    assert other_rec is not None
    records_to_delete["franchise"].append(other_rec["id"])

    time.sleep(1) # Allow for indexing

    # Search by the default 'parent_company' field
    found_franchises = baserow_client.find_franchise_by_name(search_name, limit=5)
    assert len(found_franchises) >= 1
    
    found_ids = [f["id"] for f in found_franchises]
    assert rec["id"] in found_ids
    assert other_rec["id"] not in found_ids
    
    # Ensure correct field was searched
    assert found_franchises[0].get("parent_company") == search_name

    # Test with a non-default search_field if you have one (e.g., 'franchise_tagline' if it existed)
    # For now, we test that searching a different field doesn't find it if the value isn't there
    found_by_city = baserow_client.find_franchise_by_name("SearchVille", search_field="city", limit=5)
    assert len(found_by_city) >=1
    assert any(f.get("city") == "SearchVille" for f in found_by_city if f["id"] == rec["id"])


def test_update_document_status_method(baserow_client):
    doc_id = generate_unique_doc_id("UpdateStatusMethod")
    created_record = baserow_client.create_record(FDD_TABLE_ID, {"document_id": doc_id})
    assert created_record is not None
    records_to_delete["fdd"].append(created_record["id"])

    new_status = f"Status_Processed_{uuid.uuid4().hex[:4]}"
    error_msg = "Test error message for status update."
    # The 'stage' field's existence is uncertain, so this test focuses on 'Status' and 'error_message'
    # which are confirmed fields in the FDD table schema.
    success = baserow_client.update_document_status(
        created_record["id"], 
        status=new_status,
        error_message=error_msg
        # stage="SomeStage" # Not testing 'stage' actively as its schema mapping is unclear
    )
    assert success

    # Verify
    updated_doc = baserow_client.get_record(FDD_TABLE_ID, created_record["id"])
    assert updated_doc is not None
    status_field = updated_doc.get("Status")
    assert status_field is not None
    assert status_field.get("value") == new_status
    assert updated_doc.get("error_message") == error_msg

# --- Test utility function ---
def test_check_output_file_exists():
    temp_dir = Path("temp_test_dir_for_check_output")
    temp_dir.mkdir(exist_ok=True)
    
    test_file_path_str = str(temp_dir / "test_output_file.txt")
    
    # Test when file does not exist
    assert not check_output_file_exists(test_file_path_str)

    # Create the file
    with open(test_file_path_str, "w") as f:
        f.write("test content")
    
    # Test when file exists
    assert check_output_file_exists(test_file_path_str)

    # Cleanup
    os.remove(test_file_path_str)
    os.rmdir(temp_dir)

# To run these tests:
# 1. Ensure Baserow is running and accessible.
# 2. Ensure BASEROW_API_URL and BASEROW_API_TOKEN are correctly set in fdd_pipeline/config.py or environment.
# 3. Navigate to the root of your project in the terminal.
# 4. Run: pytest fdd_pipeline/tests/test_baserow_client_integration.py
