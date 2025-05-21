import pytest
import os
import uuid
import time
from pathlib import Path
import shutil
import requests # For testing presigned URL

# Adjust the Python path to include the project root for imports
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from fdd_pipeline.storage.cloud_storage import R2Client
from fdd_pipeline.config import (
    R2_ACCESS_KEY_ID, 
    R2_SECRET_ACCESS_KEY, 
    R2_ENDPOINT_URL, 
    R2_BUCKET_PDFS, 
    R2_BUCKET_LAYOUTJSON,
    R2_BUCKET_HEADERSJSON,
    R2_BUCKET_EXTRACTEDDATA,
    R2_BUCKET_COMPANYLOGOS,
    R2_BUCKET_BLOG
)

# Global list to store created objects for cleanup: (bucket_name, object_key)
objects_to_delete = []
local_temp_files_dirs = []

# Buckets to be used in tests. Ensure these are set in your .env for tests to run.
PRIMARY_TEST_BUCKET = R2_BUCKET_PDFS
# We'll use the specific config values directly in their respective tests.

@pytest.fixture(scope="module")
def r2_client():
    """Fixture to provide an initialized R2Client instance."""
    if not all([R2_ENDPOINT_URL, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY]):
        pytest.skip("R2 credentials (URL, Access Key, Secret Key) are not set. Skipping R2 integration tests.")
    
    if not PRIMARY_TEST_BUCKET:
        pytest.skip(f"Primary test bucket (R2_BUCKET_NAME from config: {PRIMARY_TEST_BUCKET}) is not configured. Skipping R2 integration tests.")
    
    client = R2Client(default_bucket_name=PRIMARY_TEST_BUCKET)
    
    try:
        available_buckets = client.list_buckets()
        if PRIMARY_TEST_BUCKET not in available_buckets:
             pytest.skip(f"Primary test bucket '{PRIMARY_TEST_BUCKET}' not found. Please create it or check config. Available: {available_buckets}")
        
        # Check for existence of other specific buckets if they are configured
        # This helps in giving early feedback if a specific test might be skipped.
        for specific_bucket_var in [R2_BUCKET_PDFS, R2_BUCKET_LAYOUTJSON, R2_BUCKET_HEADERSJSON, R2_BUCKET_EXTRACTEDDATA, R2_BUCKET_COMPANYLOGOS, R2_BUCKET_BLOG]:
            if specific_bucket_var and specific_bucket_var not in available_buckets:
                print(f"Warning: Specific test bucket '{specific_bucket_var}' not found in R2. Tests for this bucket will be skipped if the bucket variable is used.")

    except Exception as e:
        pytest.skip(f"Failed to connect or list buckets, error: {e}. Skipping R2 integration tests.")

    yield client
    
    print("\nCleaning up R2 objects and local temp files...")
    # Use a new client instance for cleanup, in case the yielded one has issues or was modified.
    # Ensure this cleanup client also has a valid default bucket if any cleanup methods rely on it implicitly (they shouldn't if target_bucket_name is always passed)
    cleanup_client = R2Client(default_bucket_name=PRIMARY_TEST_BUCKET if PRIMARY_TEST_BUCKET else None)
    for bucket_name, key in objects_to_delete:
        try:
            print(f"Attempting to delete s3://{bucket_name}/{key}")
            cleanup_client.delete_object(key, target_bucket_name=bucket_name)
        except Exception as e:
            print(f"Error cleaning up R2 object s3://{bucket_name}/{key}: {e}")
    
    for item_path_str in local_temp_files_dirs:
        item_path = Path(item_path_str)
        try:
            if item_path.is_file():
                item_path.unlink()
                print(f"Deleted local temp file: {item_path_str}")
            elif item_path.is_dir():
                shutil.rmtree(item_path)
                print(f"Deleted local temp directory: {item_path_str}")
        except Exception as e:
            print(f"Error cleaning up local item {item_path_str}: {e}")
    print("R2 cleanup complete.")

@pytest.fixture(scope="function")
def temp_test_file(file_content="This is content for an R2 integration test.", extension=".txt"):
    temp_file_name = f"test_upload_{uuid.uuid4().hex[:8]}{extension}"
    temp_file_path = Path(".") / temp_file_name 
    temp_file_path.write_text(file_content)
    local_temp_files_dirs.append(str(temp_file_path))
    yield temp_file_path

@pytest.fixture(scope="function")
def temp_test_dir():
    base_dir_name = f"test_dir_upload_{uuid.uuid4().hex[:8]}"
    base_dir_path = Path(".") / base_dir_name
    base_dir_path.mkdir(parents=True, exist_ok=True)
    (base_dir_path / "file1.txt").write_text("File one content.")
    (base_dir_path / "subdir").mkdir(exist_ok=True)
    (base_dir_path / "subdir" / "file2.txt").write_text("File two in subdirectory.")
    local_temp_files_dirs.append(str(base_dir_path))
    yield base_dir_path

# --- Generic R2Client Method Tests (using PRIMARY_TEST_BUCKET as default) ---

def test_list_buckets(r2_client):
    buckets = r2_client.list_buckets()
    assert isinstance(buckets, list)
    assert PRIMARY_TEST_BUCKET in buckets

def test_generic_upload_download_delete_object_default_bucket(r2_client, temp_test_file):
    object_key = f"generic_ops/default_bucket/{temp_test_file.name}"
    assert r2_client.upload_file(str(temp_test_file), object_key), "Upload to default failed"
    objects_to_delete.append((PRIMARY_TEST_BUCKET, object_key))
    assert r2_client.object_exists(object_key)
    metadata = r2_client.get_object_metadata(object_key)
    assert metadata is not None and metadata['ContentLength'] > 0
    download_path = Path(".") / f"downloaded_generic_default_{object_key.replace('/', '_')}"
    local_temp_files_dirs.append(str(download_path))
    assert r2_client.download_file(object_key, str(download_path))
    assert download_path.read_text() == temp_test_file.read_text()
    assert r2_client.delete_object(object_key)
    assert not r2_client.object_exists(object_key)
    if (PRIMARY_TEST_BUCKET, object_key) in objects_to_delete: objects_to_delete.remove((PRIMARY_TEST_BUCKET, object_key))

@pytest.mark.skipif(not R2_BUCKET_PDFS or R2_BUCKET_PDFS == PRIMARY_TEST_BUCKET, reason="R2_BUCKET_PDFS not configured or same as PRIMARY. Skipping specific target bucket test for generic functions.")
def test_generic_upload_download_delete_specific_target_bucket(r2_client, temp_test_file):
    target_bucket = R2_BUCKET_PDFS
    object_key = f"generic_ops/specific_target_bucket/{temp_test_file.name}"
    assert r2_client.upload_file(str(temp_test_file), object_key, target_bucket_name=target_bucket)
    objects_to_delete.append((target_bucket, object_key))
    assert r2_client.object_exists(object_key, target_bucket_name=target_bucket)
    assert not r2_client.object_exists(object_key, target_bucket_name=PRIMARY_TEST_BUCKET) # Ensure not in default
    download_path = Path(".") / f"downloaded_generic_specific_{object_key.replace('/', '_')}"
    local_temp_files_dirs.append(str(download_path))
    assert r2_client.download_file(object_key, str(download_path), source_bucket_name=target_bucket)
    assert download_path.read_text() == temp_test_file.read_text()
    assert r2_client.delete_object(object_key, target_bucket_name=target_bucket)
    assert not r2_client.object_exists(object_key, target_bucket_name=target_bucket)
    if (target_bucket, object_key) in objects_to_delete: objects_to_delete.remove((target_bucket, object_key))

def test_list_objects_functionality(r2_client, temp_test_file):
    prefix = f"listing_func_test_{uuid.uuid4().hex[:4]}/"
    obj_key1 = f"{prefix}fileA.txt"
    obj_key2 = f"{prefix}sub_dir/fileB.txt"
    r2_client.upload_file(str(temp_test_file), obj_key1) 
    objects_to_delete.append((PRIMARY_TEST_BUCKET, obj_key1))
    Path("temp_file_for_list.txt").write_text("another list test file") # Create another temp file
    r2_client.upload_file("temp_file_for_list.txt", obj_key2)
    objects_to_delete.append((PRIMARY_TEST_BUCKET, obj_key2))
    Path("temp_file_for_list.txt").unlink() # Clean up local

    listed = r2_client.list_objects(prefix=prefix)
    assert obj_key1 in listed and obj_key2 in listed
    assert len(r2_client.list_objects(prefix=f"{prefix}fileA")) == 1

def test_presigned_url_generation(r2_client, temp_test_file):
    object_key = f"presigned_tests/{temp_test_file.name}"
    r2_client.upload_file(str(temp_test_file), object_key)
    objects_to_delete.append((PRIMARY_TEST_BUCKET, object_key))
    url = r2_client.generate_presigned_url(object_key, expiration=60)
    assert url and "https://" in url and object_key in url
    try:
        response = requests.get(url, timeout=10)
        assert response.status_code == 200
        assert response.text == temp_test_file.read_text()
    except requests.exceptions.RequestException as e:
        print(f"\nWarning: GET to presigned URL failed: {e}. URL: {url}")

def test_directory_operations_default_bucket(r2_client, temp_test_dir):
    upload_prefix = f"dir_ops_default_{uuid.uuid4().hex[:6]}"
    assert r2_client.upload_directory(str(temp_test_dir), prefix=upload_prefix)
    objects_to_delete.extend([
        (PRIMARY_TEST_BUCKET, f"{upload_prefix}/file1.txt"),
        (PRIMARY_TEST_BUCKET, f"{upload_prefix}/subdir/file2.txt")
    ])
    time.sleep(0.5) # Brief pause for consistency
    assert r2_client.object_exists(f"{upload_prefix}/file1.txt")
    download_dir_path = Path(".") / f"downloaded_dir_default_{uuid.uuid4().hex[:6]}"
    local_temp_files_dirs.append(str(download_dir_path))
    assert r2_client.download_directory(upload_prefix, str(download_dir_path))
    assert (download_dir_path / "file1.txt").read_text() == "File one content."
    assert (download_dir_path / "subdir/file2.txt").read_text() == "File two in subdirectory."

@pytest.mark.skipif(not R2_BUCKET_PDFS or R2_BUCKET_PDFS == PRIMARY_TEST_BUCKET, reason="R2_BUCKET_PDFS not configured or same as PRIMARY. Skipping specific bucket dir ops.")
def test_directory_operations_specific_bucket(r2_client, temp_test_dir):
    target_bucket = R2_BUCKET_PDFS
    upload_prefix = f"dir_ops_specific_{uuid.uuid4().hex[:6]}"
    assert r2_client.upload_directory(str(temp_test_dir), prefix=upload_prefix, target_bucket_name=target_bucket)
    objects_to_delete.extend([
        (target_bucket, f"{upload_prefix}/file1.txt"),
        (target_bucket, f"{upload_prefix}/subdir/file2.txt")
    ])
    time.sleep(0.5)
    assert r2_client.object_exists(f"{upload_prefix}/file1.txt", target_bucket_name=target_bucket)
    download_dir_path = Path(".") / f"downloaded_dir_specific_{uuid.uuid4().hex[:6]}"
    local_temp_files_dirs.append(str(download_dir_path))
    assert r2_client.download_directory(upload_prefix, str(download_dir_path), source_bucket_name=target_bucket)
    assert (download_dir_path / "file1.txt").read_text() == "File one content."

# --- Tests for Specific Bucket Helper Methods --- 

@pytest.mark.skipif(not R2_BUCKET_PDFS, reason="R2_BUCKET_PDFS not configured. Skipping PDF ops test.")
def test_pdf_operations(r2_client, temp_test_file):
    bucket_to_test = R2_BUCKET_PDFS
    object_key = f"pdfs/test_doc_{temp_test_file.name}"
    assert r2_client.upload_pdf(str(temp_test_file), object_key), "upload_pdf failed"
    objects_to_delete.append((bucket_to_test, object_key))
    assert r2_client.object_exists(object_key, target_bucket_name=bucket_to_test), "Object should exist in PDF bucket"
    download_path = Path(".") / f"downloaded_{object_key.replace('/', '_')}"
    local_temp_files_dirs.append(str(download_path))
    assert r2_client.download_pdf(object_key, str(download_path)), "download_pdf failed"
    assert download_path.read_text() == temp_test_file.read_text()
    assert r2_client.delete_object(object_key, target_bucket_name=bucket_to_test), "Delete from PDF bucket failed"
    if (bucket_to_test, object_key) in objects_to_delete: objects_to_delete.remove((bucket_to_test, object_key))

@pytest.mark.skipif(not R2_BUCKET_LAYOUTJSON, reason="R2_BUCKET_LAYOUTJSON not configured. Skipping LayoutJSON ops test.")
def test_layoutjson_operations(r2_client, temp_test_file):
    bucket_to_test = R2_BUCKET_LAYOUTJSON
    object_key = f"layouts/test_layout_{temp_test_file.name}"
    # Create a dummy json string for layout file
    json_content = '{"page": 1, "text": "dummy layout test"}'
    json_file = temp_test_file # re-purpose fixture by changing content and name for this test
    json_file_path = json_file.with_name(f"test_layout_{uuid.uuid4().hex[:4]}.json")
    json_file_path.write_text(json_content)
    if str(json_file) in local_temp_files_dirs: local_temp_files_dirs.remove(str(json_file)) # remove old name if present
    local_temp_files_dirs.append(str(json_file_path)) # add new name
    
    assert r2_client.upload_layoutjson(str(json_file_path), object_key), "upload_layoutjson failed"
    objects_to_delete.append((bucket_to_test, object_key))
    assert r2_client.object_exists(object_key, target_bucket_name=bucket_to_test)
    download_path = Path(".") / f"downloaded_{object_key.replace('/', '_')}"
    local_temp_files_dirs.append(str(download_path))
    assert r2_client.download_layoutjson(object_key, str(download_path))
    assert download_path.read_text() == json_content
    assert r2_client.delete_object(object_key, target_bucket_name=bucket_to_test)
    if (bucket_to_test, object_key) in objects_to_delete: objects_to_delete.remove((bucket_to_test, object_key))

@pytest.mark.skipif(not R2_BUCKET_HEADERSJSON, reason="R2_BUCKET_HEADERSJSON not configured. Skipping HeadersJSON ops test.")
def test_headersjson_operations(r2_client, temp_test_file):
    bucket_to_test = R2_BUCKET_HEADERSJSON
    object_key = f"headers/test_headers_{temp_test_file.name}"
    json_content = '{"header1": "value1"}'
    json_file_path = temp_test_file.with_name(f"test_headers_{uuid.uuid4().hex[:4]}.json")
    json_file_path.write_text(json_content)
    if str(temp_test_file) in local_temp_files_dirs: local_temp_files_dirs.remove(str(temp_test_file))
    local_temp_files_dirs.append(str(json_file_path))

    assert r2_client.upload_headersjson(str(json_file_path), object_key), "upload_headersjson failed"
    objects_to_delete.append((bucket_to_test, object_key))
    assert r2_client.object_exists(object_key, target_bucket_name=bucket_to_test)
    download_path = Path(".") / f"downloaded_{object_key.replace('/', '_')}"
    local_temp_files_dirs.append(str(download_path))
    assert r2_client.download_headersjson(object_key, str(download_path))
    assert download_path.read_text() == json_content
    assert r2_client.delete_object(object_key, target_bucket_name=bucket_to_test)
    if (bucket_to_test, object_key) in objects_to_delete: objects_to_delete.remove((bucket_to_test, object_key))

@pytest.mark.skipif(not R2_BUCKET_EXTRACTEDDATA, reason="R2_BUCKET_EXTRACTEDDATA not configured. Skipping ExtractedData ops test.")
def test_extracteddata_operations(r2_client, temp_test_file):
    bucket_to_test = R2_BUCKET_EXTRACTEDDATA
    object_key = f"extracted/test_data_{temp_test_file.name}"
    assert r2_client.upload_extracteddata(str(temp_test_file), object_key), "upload_extracteddata failed"
    objects_to_delete.append((bucket_to_test, object_key))
    assert r2_client.object_exists(object_key, target_bucket_name=bucket_to_test)
    download_path = Path(".") / f"downloaded_{object_key.replace('/', '_')}"
    local_temp_files_dirs.append(str(download_path))
    assert r2_client.download_extracteddata(object_key, str(download_path))
    assert download_path.read_text() == temp_test_file.read_text()
    assert r2_client.delete_object(object_key, target_bucket_name=bucket_to_test)
    if (bucket_to_test, object_key) in objects_to_delete: objects_to_delete.remove((bucket_to_test, object_key))

@pytest.mark.skipif(not R2_BUCKET_COMPANYLOGOS, reason="R2_BUCKET_COMPANYLOGOS not configured. Skipping CompanyLogos ops test.")
def test_companylogo_operations(r2_client, temp_test_file):
    # Assuming logos are images, but for test simplicity, use text file
    bucket_to_test = R2_BUCKET_COMPANYLOGOS
    object_key = f"logos/test_logo_{temp_test_file.name}.png" # example with .png
    assert r2_client.upload_companylogo(str(temp_test_file), object_key), "upload_companylogo failed"
    objects_to_delete.append((bucket_to_test, object_key))
    assert r2_client.object_exists(object_key, target_bucket_name=bucket_to_test)
    download_path = Path(".") / f"downloaded_{Path(object_key).name}"
    local_temp_files_dirs.append(str(download_path))
    assert r2_client.download_companylogo(object_key, str(download_path))
    assert download_path.read_text() == temp_test_file.read_text()
    assert r2_client.delete_object(object_key, target_bucket_name=bucket_to_test)
    if (bucket_to_test, object_key) in objects_to_delete: objects_to_delete.remove((bucket_to_test, object_key))

@pytest.mark.skipif(not R2_BUCKET_BLOG, reason="R2_BUCKET_BLOG not configured. Skipping Blog ops test.")
def test_blogfile_operations(r2_client, temp_test_file):
    bucket_to_test = R2_BUCKET_BLOG
    object_key = f"blog_articles/test_article_{temp_test_file.name}"
    assert r2_client.upload_blogfile(str(temp_test_file), object_key), "upload_blogfile failed"
    objects_to_delete.append((bucket_to_test, object_key))
    assert r2_client.object_exists(object_key, target_bucket_name=bucket_to_test)
    download_path = Path(".") / f"downloaded_{object_key.replace('/', '_')}"
    local_temp_files_dirs.append(str(download_path))
    assert r2_client.download_blogfile(object_key, str(download_path))
    assert download_path.read_text() == temp_test_file.read_text()
    assert r2_client.delete_object(object_key, target_bucket_name=bucket_to_test)
    if (bucket_to_test, object_key) in objects_to_delete: objects_to_delete.remove((bucket_to_test, object_key))


def test_error_handling_no_bucket_for_client(temp_test_file):
    if not all([R2_ENDPOINT_URL, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY]):
        pytest.skip("R2 credentials not set, skipping no_bucket_specified_error_handling test.")
    client_no_default = R2Client(default_bucket_name=None) # Explicitly no default
    with pytest.raises(ValueError, match="R2 bucket name must be provided"):
        client_no_default.upload_file(str(temp_test_file), "test.txt")
    # This test ensures specific methods ALSO fail if their target bucket isn't configured AND client has no default
    # However, our specific methods directly use config imports which should be strings (even if empty)
    # The ValueError would come from _get_target_bucket if that string config value is empty.
    # Example with PDF (assuming R2_BUCKET_PDFS could be empty string from os.getenv if not set)
    # To make this more robust, we'd mock config values to be None or empty.
    # For now, this primarily tests the generic upload_file path when no bucket is resolvable.

# To run tests: Ensure .env has R2 credentials and all R2_BUCKET_* variables are set to existing buckets.
# pytest fdd_pipeline/tests/test_cloud_storage_integration.py

# To run these tests:
# 1. Ensure Cloudflare R2 is accessible and credentials (R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_ENDPOINT_URL) are in .env.
# 2. Ensure bucket names (R2_BUCKET_NAME, R2_BUCKET_PDFS) are in .env and these buckets exist in your R2 account.
# 3. Navigate to the root of your project in the terminal.
# 4. Run: pytest fdd_pipeline/tests/test_cloud_storage_integration.py 