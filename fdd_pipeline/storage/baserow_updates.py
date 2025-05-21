# Assuming 'client' is an instance of BaserowClient
# and check_output_file_exists is imported or defined

# Example: Get a document
# doc = client.get_document_by_document_id("some_unique_doc_id")
# if doc:
#     print(f"Found document: {doc.get('file_name')}")

# Example: Get 'Complete' FDDs
# completed_docs = client.get_documents_by_status("Complete", limit=5)
# for fdd_doc in completed_docs:
#     print(f"Completed FDD: {fdd_doc.get('id')} - {fdd_doc.get('file_name')}")

# Example: Update fields for an FDD record
# success = client.update_document_fields(fdd_row_id=1, fields_to_update={"qc": "PASSED", "qc_notes": "Looks good."})
# print(f"Update successful: {success}")

# Example: Create a new franchise
# new_franchise = client.create_franchise_record({
#     "parent_company": "My New Franchise Co", 
#     "franchise_website": "http://newfranchise.com"
# })
# if new_franchise:
#     print(f"Created franchise with ID: {new_franchise.get('id')}")
#     # Example: Link FDD to this new franchise
#     # client.link_fdd_to_franchise(fdd_row_id=2, franchise_row_ids=[new_franchise.get('id')])


# Example: Find a franchise
# found_franchises = client.find_franchise_by_name("My New Franchise Co")
# for fr in found_franchises:
# print(f"Found franchise by name search: {fr.get('parent_company')} (ID: {fr.get('id')})")

# Example: Check for output file (utility function)
# if not check_output_file_exists("path/to/my_output.json"):
#     # Proceed with processing
#     pass
# else:
#     print("Output file already exists, skipping processing.")
