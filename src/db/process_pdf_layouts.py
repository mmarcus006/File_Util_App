import os
import subprocess
import time
import json
import csv
import requests
from pathlib import Path
import socket
import pandas as pd

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
        # Path to the virtual environment activation script
        venv_path = r"\\wsl.localhost\Ubuntu\home\miller\Projects\pdf-document-layout-analysis\.venv\bin\activate.fish"
        
        # Docker run command
        docker_cmd = [
            "docker", "run", "--rm", "--name", "pdf-document-layout-analysis", 
            "--gpus", '"device=0"', "-p", "5060:5060", 
            "--entrypoint", "./start.sh", "huridocs/pdf-document-layout-analysis:v0.0.23"
        ]
        
        # Start the process
        process = subprocess.Popen(
            docker_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=True
        )
        
        # Wait for the API to become available
        wait_for_api_availability()
        
        return True
    except Exception as e:
        print(f"Error starting container: {e}")
        return False

def wait_for_api_availability(host="localhost", port=5060, timeout=120):
    """Wait for the API to become available"""
    start_time = time.time()
    
    print(f"Waiting for API to become available at {host}:{port}...")
    
    while time.time() - start_time < timeout:
        try:
            # Try connecting to the port
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                # Port is open, try making a request to verify API is running
                try:
                    # Simple request to see if API responds
                    response = requests.get(f"http://{host}:{port}")
                    if response.status_code == 200:
                        print("API is available!")
                        return True
                except requests.RequestException:
                    pass  # API not fully ready yet
            
            time.sleep(2)
            print(".", end="", flush=True)
        except Exception:
            pass
    
    print(f"\nTimeout waiting for API after {timeout} seconds")
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
    # Define paths (similar to main, maybe refactor later if needed)
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "huridoc_analysis_output")
    os.makedirs(output_dir, exist_ok=True)
    tracking_file_path = r"C:\\Projects\\File_Util_App\\src\\processed_files_tracking.json" # Use double backslashes for Windows paths in strings

    # Check if the container is running, start if not
    if not check_container_running():
        if not start_container():
            print("Failed to start container. Exiting single PDF processing.")
            return

    # Check if already processed using tracking file
    if check_already_processed(pdf_path, output_dir, tracking_file_path):
        print(f"Already processed (found in tracking file): {pdf_path}, skipping.")
        return

    try:
        # Generate output filename
        pdf_filename = os.path.basename(pdf_path)
        pdf_basename = os.path.splitext(pdf_filename)[0]
        output_filename = f"{pdf_basename}_huridocs_analysis.json"
        output_path = os.path.join(output_dir, output_filename)

        print(f"Processing single PDF: {pdf_path}")

        # Analyze the PDF
        # Assuming analyze_pdf can handle direct Windows paths if running on Windows
        # Or if the container setup handles path mapping appropriately.
        # If WSL conversion is strictly needed, the convert_windows_path_to_wsl
        # function would need to be called here, but it was commented out in main.
        results = analyze_pdf(pdf_path)

        # Save results
        save_results_to_json(results, output_path)
        print(f"Analysis results saved to: {output_path}")

        # After successful processing, update tracking file
        update_tracking_file(output_path, tracking_file_path)

        print(f"Successfully processed single PDF: {pdf_path}")

    except Exception as e:
        print(f"Error processing single PDF {pdf_path}: {e}")

def main():
    # Define paths
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "huridoc_analysis_output")
    os.makedirs(output_dir, exist_ok=True)
    fdd_csv_path = r"C:\Projects\File_Util_App\db_replica\fdd.csv"
    tracking_file_path = r"C:\Projects\File_Util_App\src\processed_files_tracking.json"
    
    # Check if the container is running, start if not
    if not check_container_running():
        if not start_container():
            print("Failed to start container. Exiting.")
            return
    
    # Read the FDD CSV file
    df = pd.read_csv(fdd_csv_path, delimiter='|', skiprows=0)
    
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
        if check_already_processed(windows_path, output_dir, tracking_file_path):
            print(f"Already processed (found in tracking file): {windows_path}, skipping.")
            continue
        
        try:
            # Convert to WSL path
            #wsl_path = convert_windows_path_to_wsl(windows_path)
            
            # Generate output filename
            pdf_filename = os.path.basename(windows_path)
            pdf_basename = os.path.splitext(pdf_filename)[0]
            output_filename = f"{pdf_basename}_huridocs_analysis.json"
            output_path = os.path.join(output_dir, output_filename)
            
            print(f"Processing PDF: {windows_path}")
            print(f"Using WSL path: {windows_path}")
            
            # Analyze the PDF
            results = analyze_pdf(windows_path)
            
            # Save results
            save_results_to_json(results, output_path)
            print(f"Analysis results saved to: {output_path}")
            
            # Update the dataframe
            df.at[index, 'layout_analysis_json_path'] = output_path
            df.at[index, 'huridoc_analysis_complete'] = True
            
            # Save the updated dataframe
            df.to_csv(fdd_csv_path, sep='|', index=False)
            
            # After successful processing, update tracking file
            update_tracking_file(output_path, tracking_file_path)
            
        except Exception as e:
            print(f"Error processing PDF {windows_path}: {e}")
    
    print("Processing complete!")

if __name__ == "__main__":
    main() 