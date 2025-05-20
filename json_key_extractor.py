import os
import json
from typing import List, Set
from pathlib import Path


def get_json_files(folder_path: str) -> List[str]:
    """Get all JSON files from a directory.

    Args:
        folder_path: Path to the folder containing JSON files

    Returns:
        List of paths to JSON files
    """
    json_files = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith('.json'):
                json_files.append(os.path.join(root, file))
    return json_files


def extract_keys_from_json_file(file_path: str) -> Set[str]:
    """Extract all keys from a JSON file.

    Args:
        file_path: Path to the JSON file

    Returns:
        Set of keys found in the JSON file
    """
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            # Flatten nested dictionaries if needed
            keys = set()
            
            def collect_keys(obj, prefix=''):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        current_key = f"{prefix}.{key}" if prefix else key
                        keys.add(current_key)
                        collect_keys(value, current_key)
                elif isinstance(obj, list) and obj:
                    collect_keys(obj[0], prefix)
            
            collect_keys(data)
            return keys
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return set()


def collect_unique_keys(folder_path: str) -> List[str]:
    """Collect unique keys from all JSON files in a directory.

    Args:
        folder_path: Path to the folder containing JSON files

    Returns:
        List of unique keys sorted alphabetically
    """
    all_keys = set()
    json_files = get_json_files(folder_path)
    
    for file_path in json_files:
        print(f"Processing: {file_path}")
        keys = extract_keys_from_json_file(file_path)
        all_keys.update(keys)
    
    return sorted(list(all_keys))


def check_output_file_exists(output_file: str) -> bool:
    """Check if output file exists.

    Args:
        output_file: Path to the output file

    Returns:
        True if file exists, False otherwise
    """
    return os.path.exists(output_file)


def write_keys_to_csv(keys: List[str], output_file: str) -> None:
    """Write keys to a CSV file.

    Args:
        keys: List of keys to write
        output_file: Path to the output file
    """
    with open(output_file, 'w') as f:
        f.write('\n'.join(keys))
    print(f"Successfully wrote {len(keys)} unique keys to {output_file}")


def process_json_files(folder_path: str, output_file: str = "unique_keys.csv") -> None:
    """Process JSON files in a folder and output unique keys to a CSV.

    Args:
        folder_path: Path to the folder containing JSON files
        output_file: Path to the output CSV file
    """
    if check_output_file_exists(output_file):
        print(f"Output file {output_file} already exists. Please provide a different file name or remove the existing file.")
        return
    
    # Convert string path to Path object
    path_obj = Path(folder_path)
    if not path_obj.exists() or not path_obj.is_dir():
        print(f"Folder {folder_path} does not exist or is not a directory.")
        return
    
    print(f"Processing JSON files in {folder_path}...")
    unique_keys = collect_unique_keys(folder_path)
    
    if unique_keys:
        write_keys_to_csv(unique_keys, output_file)
    else:
        print("No keys found in JSON files.")


# Example usage
if __name__ == "__main__":
    # Set folder path here - no CLI arguments
    input_folder = "output/sections/item_20"
    output_csv = "unique_json_keys.csv"
    
    process_json_files(input_folder, output_csv) 