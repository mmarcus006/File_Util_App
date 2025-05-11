import os
import glob
import json
import csv
import logging
from collections import defaultdict
from typing import List, Dict, Any, Optional

import pandas as pd

from config_loader import load_config # Assuming config_loader.py is in the same directory

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ensure_directories_exist(config: Dict) -> None:
    """Creates necessary output directories defined in the config if they don't exist."""
    try:
        os.makedirs(config['output_csv_directory'], exist_ok=True)
        logger.info(f"Ensured output CSV directory exists: {config['output_csv_directory']}")
        
        # mapping_files_directory should exist with mapping files, log if not
        if not os.path.isdir(config['mapping_files_directory']):
            logger.error(f"Mapping files directory does not exist: {config['mapping_files_directory']}. This script requires mapping files to run correctly.")
            raise FileNotFoundError(f"Mapping directory {config['mapping_files_directory']} not found.")
        # json_files_directory should exist with input files
        if not os.path.isdir(os.path.expanduser(config['json_files_directory'])):
            logger.error(f"JSON files directory does not exist: {os.path.expanduser(config['json_files_directory'])}. Cannot process files.")
            raise FileNotFoundError(f"JSON input directory {os.path.expanduser(config['json_files_directory'])} not found.")

    except OSError as e:
        logger.error(f"Error creating directory: {e}")
        raise

def load_table_mapping_from_excel(table_key: str, config: Dict) -> Dict[str, Optional[str]]:
    """
    Loads header mapping for a table from its Excel file.
    Returns dict: { 'observed_lowercase_header': 'Standardized_Header_OR_None' }
    'None' means the observed header should be ignored.
    """
    mapping_dir = config['mapping_files_directory']
    excel_cols_cfg = config['excel_mapping_columns']
    excel_filepath = os.path.join(mapping_dir, f"{table_key}_mappings.xlsx")

    mapping_dict = {}

    if not os.path.exists(excel_filepath):
        logger.error(f"Mapping file NOT FOUND for table '{table_key}' at '{excel_filepath}'. No columns will be mapped for this table from any FDD file.")
        return mapping_dict # Return empty, so no mapping occurs for this table

    try:
        df_map = pd.read_excel(excel_filepath, engine='openpyxl')
        
        obs_col = excel_cols_cfg['observed']
        std_user_col = excel_cols_cfg['standardized_user']

        if obs_col not in df_map.columns or std_user_col not in df_map.columns:
            logger.error(f"Mapping file '{excel_filepath}' is missing required columns ('{obs_col}' or '{std_user_col}'). Cannot load mappings for table '{table_key}'.")
            return mapping_dict

        for _, row in df_map.iterrows():
            observed = str(row[obs_col]).strip().lower() if pd.notna(row[obs_col]) else None
            standardized = str(row[std_user_col]).strip() if pd.notna(row[std_user_col]) and str(row[std_user_col]).strip() else None
            
            if observed: # Only add if observed header is not empty
                mapping_dict[observed] = standardized # Value can be None if user wants to ignore
        logger.info(f"Successfully loaded {len(mapping_dict)} mappings for table '{table_key}' from '{excel_filepath}'.")
    except Exception as e:
        logger.error(f"Error loading mapping file {excel_filepath} for table '{table_key}': {e}")
    
    return mapping_dict


def extract_uuid_from_filename(filename: str) -> str:
    base_name = os.path.basename(filename)
    return base_name.split('_')[0]


def coerce_data_type(value: Any, target_type: Optional[str], header_name: str) -> Any:
    if value is None or (isinstance(value, str) and not value.strip()):
        return None 

    original_value_str = str(value).strip()

    if target_type == 'int':
        try:
            # Handle potential floats being passed as int (e.g., "2021.0")
            # Also handles "+12", "-5" directly
            if '.' in original_value_str:
                 return int(float(original_value_str))
            return int(original_value_str)
        except ValueError:
            logger.debug(f"Could not convert '{original_value_str}' to int for header '{header_name}'. Returning as original string.")
            return original_value_str # Return original on failure
    elif target_type == 'float':
        try:
            return float(original_value_str)
        except ValueError:
            logger.debug(f"Could not convert '{original_value_str}' to float for header '{header_name}'. Returning as original string.")
            return original_value_str
    # For 'str' or unknown target_type, just return the stripped string
    return original_value_str


def process_single_fdd_json(
    filepath: str,
    uuid: str,
    table_key: str,
    table_config_from_yaml: Dict,
    header_mapping_for_table: Dict[str, Optional[str]],
    data_type_rules: Dict[str, str]
) -> List[Dict[str, Any]]:
    """
    Processes a single table within one FDD JSON file.
    """
    processed_rows_for_table = []
    standardized_headers_for_table = table_config_from_yaml['standardized_headers']

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            fdd_data = json.load(f)

        if table_key not in fdd_data:
            return [] 

        table_json_data = fdd_data[table_key]
        original_columns_from_json = table_json_data.get('columns', [])
        rows_from_json = table_json_data.get('rows', [])

        if not original_columns_from_json:
            return []
        
        idx_to_standardized_header = {}
        for i, original_header_val in enumerate(original_columns_from_json):
            if original_header_val is None: continue
            
            original_header_norm = str(original_header_val).strip().lower()
            
            # Check if this normalized original header exists in our loaded mapping
            if original_header_norm in header_mapping_for_table:
                standardized_target_header = header_mapping_for_table[original_header_norm]
                if standardized_target_header: # User mapped it to a non-empty standardized header
                    idx_to_standardized_header[i] = standardized_target_header
                # If standardized_target_header is None (user left it blank in Excel), column is skipped
            # If original_header_norm not in header_mapping_for_table, it's unmapped, also skipped

        for row_values in rows_from_json:
            standardized_row_data = {'uuid': uuid}
            for std_hdr in standardized_headers_for_table: # Initialize all target cols
                standardized_row_data[std_hdr] = ''

            for original_idx, cell_value in enumerate(row_values):
                if original_idx in idx_to_standardized_header:
                    target_header = idx_to_standardized_header[original_idx]
                    target_type = data_type_rules.get(target_header) # Default to string if not in rules
                    coerced_value = coerce_data_type(cell_value, target_type, target_header)
                    standardized_row_data[target_header] = coerced_value
            
            processed_rows_for_table.append(standardized_row_data)

    except json.JSONDecodeError:
        logger.warning(f"Could not decode JSON from {filepath}. Skipping this file for table '{table_key}'.")
    except Exception as e:
        logger.error(f"An unexpected error occurred while processing {table_key} in {filepath}: {e}")
    
    return processed_rows_for_table


def write_data_to_csv(
    data_list: List[Dict[str, Any]], 
    output_filepath: str, 
    fieldnames_with_uuid: List[str]
) -> None:
    """Writes a list of dictionaries to a CSV file. Overwrites if exists."""
    try:
        with open(output_filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames_with_uuid, extrasaction='ignore')
            writer.writeheader()
            if data_list:
                writer.writerows(data_list)
        logger.info(f"Successfully wrote {len(data_list)} rows to {output_filepath}")
    except IOError as e:
        logger.error(f"Could not write to CSV file {output_filepath}. Error: {e}")
    except Exception as e:
        logger.error(f"An unexpected error during CSV writing for {output_filepath}: {e}")


def main():
    """Main function to process FDD JSONs and generate merged CSVs."""
    try:
        config = load_config()
    except Exception as e:
        logger.critical(f"CRITICAL: Failed to load configuration. Exiting. Error: {e}")
        return

    try:
        ensure_directories_exist(config)
    except Exception as e:
        logger.critical(f"CRITICAL: Failed to ensure required directories. Exiting. Error: {e}")
        return

    json_dir_abs = os.path.expanduser(config['json_files_directory'])
    json_file_paths = glob.glob(os.path.join(json_dir_abs, config['item_20_file_pattern']))
    
    if not json_file_paths:
        logger.warning(f"No FDD JSON files found in '{json_dir_abs}' matching '{config['item_20_file_pattern']}'. Exiting.")
        return
    
    logger.info(f"Found {len(json_file_paths)} FDD JSON files to process.")

    all_processed_data_by_table = defaultdict(list)
    data_type_rules = config.get('data_type_rules', {})

    # Load all table mappings first
    table_header_mappings_loaded = {}
    fatal_mapping_error = False
    for table_key_from_config in config.get('tables_to_process', {}).keys():
        mapping = load_table_mapping_from_excel(table_key_from_config, config)
        # If a mapping file is explicitly missing and it's critical, you might decide to stop.
        # For now, an error is logged, and processing for that table will effectively skip columns.
        excel_filepath = os.path.join(config['mapping_files_directory'], f"{table_key_from_config}_mappings.xlsx")
        if not os.path.exists(excel_filepath):
            logger.error(f"CRITICAL: Mapping file for table '{table_key_from_config}' expected at '{excel_filepath}' but not found. This table cannot be processed correctly.")
            # fatal_mapping_error = True # Uncomment if you want to halt all processing
        table_header_mappings_loaded[table_key_from_config] = mapping
    
    if fatal_mapping_error:
        logger.critical("Halting due to critical missing mapping files.")
        return

    for fdd_json_path in json_file_paths:
        uuid = extract_uuid_from_filename(fdd_json_path)
        if not uuid:
            logger.warning(f"Could not extract UUID from {fdd_json_path}. Skipping this file.")
            continue

        for table_key, table_conf_details in config.get('tables_to_process', {}).items():
            current_mapping_for_table = table_header_mappings_loaded.get(table_key, {})
            if not current_mapping_for_table and os.path.exists(os.path.join(config['mapping_files_directory'], f"{table_key}_mappings.xlsx")):
                 logger.warning(f"Mapping for table '{table_key}' was loaded as empty, though file exists. Check mapping file content or loading logic.")

            rows_for_file_table = process_single_fdd_json(
                fdd_json_path, uuid, table_key, table_conf_details, current_mapping_for_table, data_type_rules
            )
            all_processed_data_by_table[table_key].extend(rows_for_file_table)

    # Write each table's aggregated data to its CSV
    output_dir = config['output_csv_directory']
    for table_key, data_list in all_processed_data_by_table.items():
        table_conf_details = config.get('tables_to_process', {}).get(table_key)
        if not table_conf_details:
            logger.warning(f"No configuration found for table key '{table_key}' in 'tables_to_process'. Skipping CSV write for this key.")
            continue
            
        output_filename = table_conf_details['output_csv_filename']
        csv_output_filepath = os.path.join(output_dir, output_filename)
        
        csv_fieldnames = ['uuid'] + table_conf_details['standardized_headers']
        write_data_to_csv(data_list, csv_output_filepath, csv_fieldnames)

    logger.info("FDD JSON processing complete.")

if __name__ == "__main__":
    main()