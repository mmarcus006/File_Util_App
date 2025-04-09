import os
import subprocess
import time
import json
import csv
import socket
from pathlib import Path
import requests
import pandas as pd
import ray
from typing import Tuple, Dict, Any, List

# 1. Configuration & Constants
# Use environment variables for production flexibility:
CONTAINER_NAME = os.environ.get("PDF_CONTAINER_NAME", "pdf-document-layout-analysis")
CONTAINER_IMAGE = os.environ.get("PDF_CONTAINER_IMAGE", "huridocs/pdf-document-layout-analysis:v0.0.23")
CONTAINER_PORT = int(os.environ.get("PDF_CONTAINER_PORT", "5060"))
CONTAINER_GPU = os.environ.get("PDF_CONTAINER_GPU", "device=0")

# Host/port the container’s API is served on each machine. 
API_HOST = os.environ.get("PDF_API_HOST", "localhost")
API_PORT = int(os.environ.get("PDF_API_PORT", "5060"))

# Path to the virtual environment activation script (if needed). 
# In many production setups, this might be unnecessary if Docker alone is used.
VENV_PATH = os.environ.get(
    "PDF_CONTAINER_VENV_PATH",
    r"\\wsl.localhost\Ubuntu\home\miller\Projects\pdf-document-layout-analysis\.venv\bin\activate.fish"
)

# Fallback time to wait (in seconds) for the container’s API to become available.
API_START_TIMEOUT = 180


# =============================================================================
# 2. Shared Utility Functions
# =============================================================================

def check_container_running(container_name: str = CONTAINER_NAME) -> bool:
    """
    Check if the specified Docker container is running on this machine.
    """
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


def start_container() -> bool:
    """
    Start the Docker container for PDF document layout analysis on this machine, 
    if not already running. Returns True on success, False on failure.
    """
    print(f"[ContainerManager] Starting Docker container '{CONTAINER_NAME}'...")
    try:
        docker_cmd = [
            "docker", "run", 
            "--rm",
            "--name", CONTAINER_NAME, 
            "--gpus", f"\"{CONTAINER_GPU}\"",
            "-p", f"{CONTAINER_PORT}:{CONTAINER_PORT}", 
            "--entrypoint", "./start.sh",
            CONTAINER_IMAGE
        ]
        
        _ = subprocess.Popen(
            docker_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=True
        )
        
        # Wait for the API to become available
        success = wait_for_api_availability(host=API_HOST, port=API_PORT, timeout=API_START_TIMEOUT)
        return success
    except Exception as exc:
        print(f"[ContainerManager] Error starting container '{CONTAINER_NAME}': {exc}")
        return False


def wait_for_api_availability(host: str = API_HOST, port: int = API_PORT, timeout: int = API_START_TIMEOUT) -> bool:
    """
    Wait up to 'timeout' seconds for the local container’s API to become available on `host:port`.
    """
    start_time = time.time()
    print(f"[ContainerManager] Waiting for API to become available at {host}:{port}...")

    while time.time() - start_time < timeout:
        try:
            # Try a socket connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((host, port))
            sock.close()

            if result == 0:
                # If port is open, do a quick HTTP check
                try:
                    response = requests.get(f"http://{host}:{port}", timeout=2)
                    if response.status_code == 200:
                        print("[ContainerManager] API is available!")
                        return True
                except requests.RequestException:
                    pass
            print(".", end="", flush=True)
            time.sleep(2)
        except Exception:
            pass
    
    print(f"\n[ContainerManager] Timeout waiting for API after {timeout} seconds")
    return False


def analyze_pdf(pdf_path: str, fast_mode: bool = False, extraction_format: str = "") -> dict:
    """
    Send a PDF to the local layout analysis API and return the results as a dict.
    """
    url = f"http://{API_HOST}:{API_PORT}"
    
    # Prepare form data
    files = {"file": open(pdf_path, "rb")}
    data = {}
    
    if fast_mode:
        data["fast"] = "false"
    
    if extraction_format:
        data["extraction_format"] = extraction_format
    
    response = requests.post(url, files=files, data=data)
    files["file"].close()
    
    # Raise an exception if the request failed
    response.raise_for_status()
    return response.json()


def save_results_to_json(results: dict, output_path: str) -> None:
    """
    Save the analysis results to a JSON file, creating directories if needed.
    """
    output_dir = os.path.dirname(output_path)
    os.makedirs(output_dir, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


def convert_windows_path_to_wsl(windows_path: str) -> str:
    """
    Convert Windows path to WSL path format, if needed. 
    In production, you might want to do more thorough checks.
    """
    if ":" in windows_path:
        drive, rest = windows_path.split(":", 1)
        wsl_path = f"/mnt/{drive.lower()}{rest}"
    else:
        wsl_path = windows_path
    return wsl_path.replace("\\", "/")  # backslashes to forward slashes


# =============================================================================
# 3. Actors to Manage Container & Write CSV Concurrency-Safely
# =============================================================================

@ray.remote
class ContainerManager:
    """
    A Ray actor that runs once per node. Responsible for ensuring the container is 
    running locally on that node.
    """
    def __init__(self):
        # We'll do a one-time setup in the constructor
        if not check_container_running(CONTAINER_NAME):
            started = start_container()
            if not started:
                raise RuntimeError(f"[ContainerManager] Could not start container '{CONTAINER_NAME}' on this node.")

    def ping(self) -> bool:
        """
        Quick test method to confirm this actor is alive.
        """
        return True


@ray.remote
class CSVWriterActor:
    """
    A Ray actor responsible for concurrency-safe updates to a CSV and a tracking JSON file. 
    This pattern ensures that multiple workers can “enqueue” updates, and the actor serializes them.

    In production, consider using a real database for concurrency. 
    But for demonstration, we lock the CSV and JSON via a single-threaded actor approach.
    """
    def __init__(self, fdd_csv_path: str, tracking_file_path: str):
        self.fdd_csv_path = fdd_csv_path
        self.tracking_file_path = tracking_file_path
        
        # Load the DataFrame once
        self.df = pd.read_csv(fdd_csv_path, delimiter='|', skiprows=0)
        if 'layout_analysis_json_path' not in self.df.columns:
            self.df['layout_analysis_json_path'] = None
        if 'huridoc_analysis_complete' not in self.df.columns:
            self.df['huridoc_analysis_complete'] = False
        
        # Load or initialize the tracking file
        self.processed_files = []
        if os.path.exists(tracking_file_path):
            try:
                with open(tracking_file_path, 'r', encoding='utf-8') as f:
                    self.processed_files = json.load(f)
            except json.JSONDecodeError:
                self.processed_files = []

    def mark_processed(self, idx: int, output_path: str):
        """
        Mark a single record in the CSV as processed, update tracking, and persist changes.
        """
        # Update the DF in memory
        self.df.at[idx, 'layout_analysis_json_path'] = output_path
        self.df.at[idx, 'huridoc_analysis_complete'] = True

        # Update the tracking file in memory
        norm_path = os.path.normpath(output_path)
        if norm_path not in self.processed_files:
            self.processed_files.append(norm_path)
        
        # Persist changes to disk
        self._save_changes()

    def mark_failed(self, idx: int):
        """
        Mark a single record as failed or incomplete if an error occurs.
        """
        self.df.at[idx, 'layout_analysis_json_path'] = None
        self.df.at[idx, 'huridoc_analysis_complete'] = False
        self._save_changes()

    def has_processed(self, pdf_path: str, output_dir: str) -> bool:
        """
        Check if a PDF has already been processed.
        """
        pdf_filename = os.path.basename(pdf_path)
        pdf_basename = os.path.splitext(pdf_filename)[0]
        output_filename = f"{pdf_basename}_huridocs_analysis.json"
        output_path = os.path.normpath(os.path.join(output_dir, output_filename))
        
        return output_path in self.processed_files

    def _save_changes(self):
        """
        Internal method to flush changes to disk (CSV and JSON).
        """
        self.df.to_csv(self.fdd_csv_path, sep='|', index=False)
        
        with open(self.tracking_file_path, 'w', encoding='utf-8') as f:
            json.dump(self.processed_files, f, indent=2)


# =============================================================================
# 4. The Remote Worker Function
# =============================================================================

@ray.remote
def process_pdf_remote(row_idx: int,
                       windows_path: str,
                       output_dir: str,
                       fast_mode: bool,
                       extraction_format: str,
                       container_ref,
                       writer_ref) -> Tuple[int, bool, str]:
    """
    This remote function is assigned a single PDF to analyze.

    :param row_idx: The row index in the CSV.
    :param windows_path: The Windows path of the PDF file.
    :param output_dir: Where to store the results JSON.
    :param fast_mode: Whether to request fast analysis from the API.
    :param extraction_format: If needed, pass any special extraction format to the API.
    :param container_ref: A handle to the ContainerManager actor (ensures container is up).
    :param writer_ref: A handle to the CSVWriterActor (for concurrency-safe tracking).
    :return: (row_idx, success_bool, message)
    """
    try:
        # Ensure container is up on this node by calling a trivial actor method
        # (this triggers the ContainerManager’s __init__ if not already launched).
        container_ok = ray.get(container_ref.ping.remote())
        if not container_ok:
            return (row_idx, False, "Container not running")

        # Check if already processed
        already_done = ray.get(writer_ref.has_processed.remote(windows_path, output_dir))
        if already_done:
            msg = f"[Worker] Already processed (found in tracking): {windows_path}, skipping."
            print(msg)
            return (row_idx, True, msg)

        # If needed, convert path to WSL. Here we simply skip if we want to keep Windows path usage:
        # wsl_path = convert_windows_path_to_wsl(windows_path)

        # Prepare output path
        pdf_filename = os.path.basename(windows_path)
        pdf_basename = os.path.splitext(pdf_filename)[0]
        output_filename = f"{pdf_basename}_huridocs_analysis.json"
        final_output_path = os.path.join(output_dir, output_filename)
        
        print(f"[Worker] Processing PDF: {windows_path}")

        # Analyze the PDF
        results = analyze_pdf(windows_path, fast_mode=fast_mode, extraction_format=extraction_format)
        
        # Save JSON
        save_results_to_json(results, final_output_path)
        print(f"[Worker] Analysis results saved to: {final_output_path}")

        # Mark the PDF as processed in CSV & tracking
        writer_ref.mark_processed.remote(row_idx, final_output_path)

        return (row_idx, True, "Success")
    except Exception as exc:
        err_msg = f"[Worker] Error processing PDF {windows_path}: {exc}"
        print(err_msg)
        writer_ref.mark_failed.remote(row_idx)
        return (row_idx, False, str(exc))


# =============================================================================
# 5. The Main Entrypoint
# =============================================================================

def main():
    """
    Main function to be run from the HEAD node in your Ray cluster.
    """
    # -------------------------------------------------------------------------
    # Ray Cluster Initialization
    # -------------------------------------------------------------------------
    # In production, you'd run:
    #   ray start --head --port=6379  (on the head node)
    #   ray start --address='head_ip:6379' (on each worker node)
    #
    # Then, below, you'd do:
    #   ray.init(address="auto")
    #
    # For local testing only, you could do just ray.init() with no address.
    # -------------------------------------------------------------------------
    ray.init(address="auto")

    # Define input paths
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent
    output_dir = os.path.join(project_root, "data", "huridoc_analysis_output")
    os.makedirs(output_dir, exist_ok=True)

    fdd_csv_path = r"C:\Projects\File_Util_App\db_replica\fdd.csv"
    tracking_file_path = r"C:\Projects\File_Util_App\src\processed_files_tracking.json"

    # Create or retrieve the ContainerManager (once per node)
    # This will ensure the container is started locally on each node when used.
    container_manager = ContainerManager.options(
        name="container_manager",  # optional: name the actor
        get_if_exists=True,        # if the actor already exists, reuse it
        max_concurrency=1          # only handle one "startup" at a time
    ).remote()

    # Create a single CSV/Tracking writer actor
    writer_actor = CSVWriterActor.options(
        name="csv_writer_actor",
        get_if_exists=True
    ).remote(fdd_csv_path, tracking_file_path)

    # Load the local DF just to figure out which rows to process
    df_local = pd.read_csv(fdd_csv_path, delimiter='|', skiprows=0)
    if 'layout_analysis_json_path' not in df_local.columns:
        df_local['layout_analysis_json_path'] = None
    if 'huridoc_analysis_complete' not in df_local.columns:
        df_local['huridoc_analysis_complete'] = False

    # Collect tasks
    tasks = []
    for idx, row in df_local.iterrows():
        if pd.isna(row['original_pdf_path']):
            continue
        if row['huridoc_analysis_complete']:
            continue

        windows_path = row['original_pdf_path']
        fast_mode = False  # set as needed
        extraction_format = ""  # set as needed

        # Dispatch to a remote worker
        future = process_pdf_remote.remote(
            row_idx=idx,
            windows_path=windows_path,
            output_dir=output_dir,
            fast_mode=fast_mode,
            extraction_format=extraction_format,
            container_ref=container_manager,
            writer_ref=writer_actor
        )
        tasks.append(future)

    # Gather results
    results = ray.get(tasks)
    success_count = sum(1 for (_, success, _) in results if success)
    fail_count = len(results) - success_count

    print(f"[Main] Processing complete! Success: {success_count}, Fail: {fail_count}")

    # Optionally: you might want to re-pull the updated CSV in the driver to reflect changes:
    # updated_df = ray.get(writer_actor.get_df.remote())
    # but in this example, we trust the actor saved the CSV already.

    # Final shutdown (optional, if you want to kill the cluster after).
    # ray.shutdown()


if __name__ == "__main__":
    main()
