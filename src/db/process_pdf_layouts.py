import os
import sys
import subprocess
import time
import json
import csv
import requests
from pathlib import Path
import socket
import pandas as pd

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

# Now import from config
from src.config import TRACKING_FILE, FDD_CSV_FILE, HURIDOC_OUTPUT_DIR, is_wsl, get_wsl_path, WSL_PATHS

def check_container_running(container_name="pdf-document-layout-analysis"):
    """Check if the specified Docker container is running"""
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", f"name={container_name}", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            check=True
        )
        return container_name in result.stdout
    except subprocess.CalledProcessError:
        return False

def start_container():
    """Start the Docker container for PDF document layout analysis"""
    print("Starting Docker container for PDF document layout analysis...")
    
    try:
        # Check if Docker is running
        subprocess.run(["docker", "info"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Check if container is already running
        if check_container_running():
            print("Container is already running, will use existing instance")
            return True
            
        # Docker run command - modified for different platforms
        if sys.platform == "darwin":  # macOS
            # Check if Apple Silicon
            is_apple_silicon = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"], 
                capture_output=True, 
                text=True
            ).stdout.strip().startswith("Apple")
            
            if is_apple_silicon:
                print("Starting container for Apple Silicon (without GPU acceleration)")
                # Simpler command without GPU acceleration but should work reliably
                docker_cmd = [
                    "docker", "run", "-d", "--rm", "--name", "pdf-document-layout-analysis", 
                    "-p", "5060:5060", 
                    "--entrypoint", "./start.sh", "huridocs/pdf-document-layout-analysis:v0.0.23"
                ]
            else:
                print("Starting container for Intel Mac")
                docker_cmd = [
                    "docker", "run", "-d", "--rm", "--name", "pdf-document-layout-analysis", 
                    "-p", "5060:5060", 
                    "--entrypoint", "./start.sh", "huridocs/pdf-document-layout-analysis:v0.0.23"
                ]
        else:  # Linux/Windows
            docker_cmd = [
                "docker", "run", "-d", "--rm", "--name", "pdf-document-layout-analysis", 
                "--gpus", '"device=0"', "-p", "5060:5060", 
                "--entrypoint", "./start.sh", "huridocs/pdf-document-layout-analysis:v0.0.23"
            ]
        
        # Start the process
        print(f"Running command: {' '.join(docker_cmd)}")
        result = subprocess.run(
            docker_cmd if sys.platform != "win32" else " ".join(docker_cmd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=sys.platform == "win32"  # Use shell on Windows only
        )
        
        if result.returncode != 0:
            print(f"Error starting container: {result.stderr}")
            return False
            
        print("Container started in detached mode, waiting for API...")
        
        # Wait for the API to become available with increased timeout
        if wait_for_api_availability(timeout=300):  # 5 minutes timeout
            print("Container started successfully!")
            return True
        else:
            print("Container didn't start properly within the timeout period.")
            # Don't stop container since it might still be initializing
            print("You may need to manually check 'docker logs pdf-document-layout-analysis'")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"Error: Docker isn't running or isn't installed. Details: {e}")
        return False
    except Exception as e:
        print(f"Error starting container: {e}")
        return False

def wait_for_api_availability(host="localhost", port=5060, timeout=300):
    """Wait for the API to become available"""
    start_time = time.time()
    
    print(f"Waiting for API to become available at {host}:{port} (timeout: {timeout}s)...")
    attempt = 0
    
    while time.time() - start_time < timeout:
        attempt += 1
        try:
            # Try connecting to the port
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                # Port is open, try making a request to verify API is running
                try:
                    print(f"Port {port} is open, checking if API is responding...")
                    # First try POST request which is what's used for processing
                    try:
                        response = requests.post(f"http://{host}:{port}", timeout=10)
                        if response.status_code in [200, 400, 422]:  # 400/422 are expected if no file provided
                            print(f"API is available! Response status: {response.status_code}")
                            return True
                    except:
                        # Try GET request as fallback
                        response = requests.get(f"http://{host}:{port}", timeout=10)
                        if response.status_code in [200, 405]:  # 405 is Method Not Allowed (expected)
                            print(f"API is available! Response status: {response.status_code}")
                            return True
                        else:
                            print(f"API returned status code {response.status_code}, waiting...")
                except requests.RequestException as e:
                    print(f"API not fully ready yet: {e}")
            else:
                if attempt % 10 == 0:  # Only print every 10 attempts to reduce noise
                    print(f"Attempt {attempt}: Port {port} not open yet (result: {result})...")
            
            if attempt < 30:
                # Sleep for shorter duration initially
                time.sleep(2)
            else:
                # Sleep longer after many attempts
                time.sleep(5)
                
        except Exception as e:
            print(f"Error checking API availability: {e}")
            time.sleep(2)
    
    print(f"\nTimeout waiting for API after {timeout} seconds")
    # Try to get the Docker logs to help diagnose issues
    try:
        result = subprocess.run(
            ["docker", "logs", "pdf-document-layout-analysis"],
            capture_output=True,
            text=True,
            check=False
        )
        print("Docker container logs (last 500 chars):")
        print(result.stdout[-500:] if result.stdout else "No output")
        print("Error logs:")
        print(result.stderr[-500:] if result.stderr else "No errors")
    except Exception as e:
        print(f"Could not fetch container logs: {e}")
    
    return False

def convert_windows_path_to_wsl(windows_path: str) -> str:
    """Convert Windows path to WSL path format"""
    # Handle drive letter (C: -> /mnt/c)
    if ":" in windows_path:
        drive, rest = windows_path.split(":", 1)
        wsl_path = f"/mnt/{drive.lower()}{rest}"
    else:
        wsl_path = windows_path
    
    # Replace backslashes with forward slashes
    wsl_path = wsl_path.replace("\\", "/")
    
    return wsl_path

def analyze_pdf(pdf_path: str, fast_mode: bool = False, extraction_format: str = "") -> dict:
    """Send PDF to layout analysis API and return results"""
    url = "http://localhost:5060"
    
    # Prepare form data
    files = {"file": open(pdf_path, "rb")}
    data = {}
    
    if fast_mode:
        data["fast"] = "false"
    
    if extraction_format:
        data["extraction_format"] = extraction_format
    
    # Make the API call
    response = requests.post(url, files=files, data=data)
    
    # Close the file
    files["file"].close()
    
    # Return response as dictionary
    return response.json()

def save_results_to_json(results: dict, output_path: str) -> None:
    """Save API results to JSON file"""
    output_dir = os.path.dirname(output_path)
    os.makedirs(output_dir, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

def check_already_processed(pdf_path: str, output_dir: str, tracking_file_path: str) -> bool:
    """Check if a PDF has already been processed by checking the tracking file or existing output files."""
    # Generate expected output filename and PDF base name
    pdf_filename = os.path.basename(pdf_path)
    pdf_basename = os.path.splitext(pdf_filename)[0]
    expected_output_filename = f"{pdf_basename}_huridocs_analysis.json"
    expected_output_path = os.path.normpath(os.path.join(output_dir, expected_output_filename))

    # 1. Check the tracking file first
    if os.path.exists(tracking_file_path):
        try:
            with open(tracking_file_path, 'r') as f:
                processed_files = json.load(f)
            if expected_output_path in processed_files:
                # Found in tracking file
                return True
        except json.JSONDecodeError:
            print(f"Warning: Tracking file {tracking_file_path} is corrupted. Skipping tracking file check.")
            pass # Proceed to directory check if tracking file is invalid

    # 2. If not found in tracking file (or file is corrupted/missing), check the output directory
    try:
        for filename in os.listdir(output_dir):
            if filename.endswith("_huridocs_analysis.json"):
                # Extract base name from the JSON filename
                json_basename = filename.replace("_huridocs_analysis.json", "")
                if json_basename == pdf_basename:
                    # Found a matching JSON file in the output directory
                    print(f"Found existing output file for {pdf_basename} in {output_dir}, skipping.")
                    # Optional: Add the found path to the tracking file for consistency?
                    # update_tracking_file(os.path.join(output_dir, filename), tracking_file_path)
                    return True
    except FileNotFoundError:
        # Output directory might not exist yet if this is the first run
        return False

    # If neither check found the file, it hasn't been processed
    return False

def update_tracking_file(output_path: str, tracking_file_path: str):
    """Add a newly processed file to the tracking file"""
    processed_files = []
    
    # Load existing data if file exists
    if os.path.exists(tracking_file_path):
        try:
            with open(tracking_file_path, 'r') as f:
                processed_files = json.load(f)
        except json.JSONDecodeError:
            pass
    
    # Add the new path if not already in the list
    output_path = os.path.normpath(output_path)
    if output_path not in processed_files:
        processed_files.append(output_path)
    
    # Save updated list
    with open(tracking_file_path, 'w') as f:
        json.dump(processed_files, f, indent=2)

def process_single_pdf(pdf_path: str) -> None:
    """Processes a single PDF file using the layout analysis API."""
    # Use paths from config
    output_dir = str(HURIDOC_OUTPUT_DIR)
    os.makedirs(output_dir, exist_ok=True)
    tracking_file_path = TRACKING_FILE

    # Check if the container is running, start if not
    if not check_container_running():
        if not start_container():
            print("Failed to start container. Exiting single PDF processing.")
            return

    # Check if already processed using tracking file
    if check_already_processed(pdf_path, output_dir, str(tracking_file_path)):
        print(f"Already processed (found in tracking file): {pdf_path}, skipping.")
        return

    try:
        # Generate output filename
        pdf_filename = os.path.basename(pdf_path)
        pdf_basename = os.path.splitext(pdf_filename)[0]
        output_filename = f"{pdf_basename}_huridocs_analysis.json"
        output_path = os.path.join(output_dir, output_filename)

        print(f"Processing single PDF: {pdf_path}")

        # Convert path for WSL if needed
        if is_wsl():
            pdf_path = get_wsl_path(pdf_path)

        # Analyze the PDF
        results = analyze_pdf(pdf_path)

        # Save results
        save_results_to_json(results, output_path)
        print(f"Analysis results saved to: {output_path}")

        # After successful processing, update tracking file
        update_tracking_file(output_path, str(tracking_file_path))

        print(f"Successfully processed single PDF: {pdf_path}")

    except Exception as e:
        print(f"Error processing single PDF {pdf_path}: {e}")

def main():
    # Use paths from config
    output_dir = str(HURIDOC_OUTPUT_DIR)
    os.makedirs(output_dir, exist_ok=True)
    fdd_csv_path = FDD_CSV_FILE
    tracking_file_path = TRACKING_FILE
    
    # Check if the container is running, start if not
    if not check_container_running():
        if not start_container():
            print("Failed to start container. Exiting.")
            return
    
    # Read the FDD CSV file
    df = pd.read_csv(str(fdd_csv_path), delimiter='|', skiprows=0)
    
    # Add new columns if they don't exist
    if 'layout_analysis_json_path' not in df.columns:
        df['layout_analysis_json_path'] = None
    
    if 'huridoc_analysis_complete' not in df.columns:
        df['huridoc_analysis_complete'] = False
    
    # Process each PDF
    for index, row in df.iterrows():
        if pd.isna(row['original_pdf_path']) or row['huridoc_analysis_complete']:
            continue
        
        windows_path = row['original_pdf_path']
        
        # Check if already processed using tracking file
        if check_already_processed(windows_path, output_dir, str(tracking_file_path)):
            print(f"Already processed (found in tracking file): {windows_path}, skipping.")
            continue
        
        try:
            # Convert path for WSL if needed
            pdf_path = get_wsl_path(windows_path) if is_wsl() else windows_path
            
            # Generate output filename
            pdf_filename = os.path.basename(pdf_path)
            pdf_basename = os.path.splitext(pdf_filename)[0]
            output_filename = f"{pdf_basename}_huridocs_analysis.json"
            output_path = os.path.join(output_dir, output_filename)
            
            print(f"Processing PDF: {pdf_path}")
            
            # Analyze the PDF
            results = analyze_pdf(pdf_path)
            
            # Save results
            save_results_to_json(results, output_path)
            print(f"Analysis results saved to: {output_path}")
            
            # Update the dataframe
            df.at[index, 'layout_analysis_json_path'] = output_path
            df.at[index, 'huridoc_analysis_complete'] = True
            
            # Save the updated dataframe
            df.to_csv(str(fdd_csv_path), sep='|', index=False)
            
            # After successful processing, update tracking file
            update_tracking_file(output_path, str(tracking_file_path))
            
        except Exception as e:
            print(f"Error processing PDF {pdf_path}: {e}")
    
    print("Processing complete!")

if __name__ == "__main__":
    main() 