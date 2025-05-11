import os
import glob
import json
import logging
from collections import defaultdict
from typing import List, Dict, Set, Tuple

import pandas as pd
# from thefuzz import fuzz # No longer using thefuzz for primary matching
from sentence_transformers import SentenceTransformer # For semantic similarity
from sklearn.metrics.pairwise import cosine_similarity # To calculate similarity
import numpy as np

from config_loader import load_config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Global Model for Sentence Embeddings ---
# Load a pre-trained model. Choose one appropriate for your domain.
# 'all-MiniLM-L6-v2' is a good general-purpose model, fast and small.
# For more accuracy, consider larger models like 'all-mpnet-base-v2' or 'all-distilroberta-v1'
# The first time you run this, it will download the model.
try:
    EMBEDDING_MODEL = SentenceTransformer('all-MiniLM-L6-v2')
    logger.info("SentenceTransformer model 'all-MiniLM-L6-v2' loaded successfully.")
except Exception as e:
    logger.error(f"Failed to load SentenceTransformer model: {e}")
    logger.error("Please ensure 'sentence-transformers' is installed and you have an internet connection for the first download.")
    EMBEDDING_MODEL = None # Fallback or exit can be handled in main

def ensure_directories_exist(config: Dict) -> None:
    """Creates necessary directories defined in the config if they don't exist."""
    try:
        os.makedirs(config['mapping_files_directory'], exist_ok=True)
        logger.info(f"Ensured mapping directory exists: {config['mapping_files_directory']}")
        if not os.path.isdir(os.path.expanduser(config['json_files_directory'])): # Expand user path
            logger.warning(f"JSON files directory does not exist: {os.path.expanduser(config['json_files_directory'])}. This script might not find any files.")
    except OSError as e:
        logger.error(f"Error creating directory: {e}")
        raise

def extract_unique_observed_headers(config: Dict) -> Dict[str, Set[str]]:
    """
    Scans all JSON files and extracts unique column headers for each table type.
    Headers are lowercased and stripped for consistency.
    """
    json_dir = os.path.expanduser(config['json_files_directory']) # Expand user path
    file_pattern = config['item_20_file_pattern']
    tables_to_process_keys = config.get('tables_to_process', {}).keys()
    if not tables_to_process_keys:
        logger.error("No 'tables_to_process' defined in configuration.")
        return {}

    unique_headers_by_table = defaultdict(set)
    json_files_path_pattern = os.path.join(json_dir, file_pattern)
    json_files = glob.glob(json_files_path_pattern)

    if not json_files:
        logger.warning(f"No JSON files found in '{json_dir}' matching pattern '{file_pattern}'")
        return {}

    logger.info(f"Scanning {len(json_files)} JSON files for headers from '{json_files_path_pattern}'...")

    for filepath in json_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for table_key in tables_to_process_keys:
                if table_key in data:
                    table_data = data[table_key]
                    original_columns = table_data.get('columns', [])
                    for header in original_columns:
                        if header is not None and str(header).strip():
                            unique_headers_by_table[table_key].add(str(header).strip()) # Keep original case for embedding, lowercase later if needed
        except json.JSONDecodeError:
            logger.warning(f"Could not decode JSON from {filepath}. Skipping this file for header extraction.")
        except Exception as e:
            logger.warning(f"An unexpected error occurred while processing {filepath} for headers: {e}. Skipping.")
    
    return unique_headers_by_table


def generate_suggestions_semantic(
    observed_header: str,
    standardized_headers_for_table: List[str],
    std_headers_embeddings: np.ndarray, # Pre-computed embeddings for standardized headers
    threshold_semantic: float # Cosine similarity threshold (0.0 to 1.0)
) -> Tuple[str, float]:
    """
    Generates a suggested standardized header and cosine similarity score using semantic embeddings.
    """
    if EMBEDDING_MODEL is None:
        logger.warning("Embedding model not loaded. Cannot generate semantic suggestions.")
        return "(Embedding model error)", 0.0

    if not observed_header.strip(): # Handle empty observed header
        return "(Empty observed header)", 0.0

    # observed_header is already in its original case from extract_unique_observed_headers
    obs_embedding = EMBEDDING_MODEL.encode([observed_header])
    
    # Calculate cosine similarities
    similarities = cosine_similarity(obs_embedding, std_headers_embeddings)[0] # Get the first (and only) row of similarities
    
    best_match_idx = np.argmax(similarities)
    best_match_score = float(similarities[best_match_idx]) # Convert numpy float to python float
    best_match_standardized = standardized_headers_for_table[best_match_idx]

    suggestion_str = ""
    if best_match_standardized:
        if best_match_score >= threshold_semantic:
            suggestion_str = best_match_standardized
        else:
            suggestion_str = f"(Best semantic guess: '{best_match_standardized}' @{best_match_score:.2f})"
    else:
        suggestion_str = "(No semantic match found)"
        
    return suggestion_str, best_match_score


def update_excel_mapping_file(
    table_key: str,
    observed_headers_set: Set[str], # These are original case
    config: Dict
) -> None:
    """
    Creates or updates an Excel mapping file for a given table using semantic similarity.
    """
    if EMBEDDING_MODEL is None and not os.path.exists(os.path.join(config['mapping_files_directory'], f"{table_key}_mappings.xlsx")):
        logger.error(f"Embedding model failed to load, and no existing mapping file for {table_key}. Cannot proceed with this table.")
        # Create an empty Excel file so the process isn't entirely blocked if other tables can proceed
        empty_df = pd.DataFrame(columns=list(config['excel_mapping_columns'].values()))
        try:
            empty_df.to_excel(os.path.join(config['mapping_files_directory'], f"{table_key}_mappings.xlsx"), index=False, engine='openpyxl')
            logger.info(f"Created empty mapping file for {table_key} due to embedding model error.")
        except Exception as e_write:
            logger.error(f"Failed to write empty mapping file for {table_key}: {e_write}")
        return


    mapping_dir = config['mapping_files_directory']
    excel_cols_cfg = config['excel_mapping_columns']
    
    table_specific_config = config.get('tables_to_process', {}).get(table_key)
    if not table_specific_config or 'standardized_headers' not in table_specific_config:
        logger.error(f"Configuration for table '{table_key}' or its standardized_headers is missing.")
        return
        
    std_headers_for_table = table_specific_config['standardized_headers']
    if not std_headers_for_table:
        logger.warning(f"No standardized headers defined for table '{table_key}'. Cannot generate suggestions.")
        # Still create/update the Excel file, but without suggestions.
        std_headers_embeddings = np.array([])
    elif EMBEDDING_MODEL:
        std_headers_embeddings = EMBEDDING_MODEL.encode(std_headers_for_table)
    else: # EMBEDDING_MODEL is None but std_headers_for_table exists
        std_headers_embeddings = np.array([]) # Cannot create embeddings
        logger.warning(f"Embedding model not available, suggestions for {table_key} will be limited/absent.")


    # Semantic match threshold (0.0 to 1.0) - can be made configurable
    # Note: config['match_threshold'] is 0-100, for semantic we use 0-1.
    # Let's assume semantic_match_threshold is desired to be similar, so divide by 100
    semantic_match_threshold = float(config.get('match_threshold', 80)) / 100.0 
    if semantic_match_threshold < 0.0 or semantic_match_threshold > 1.0:
        logger.warning(f"Invalid semantic_match_threshold derived ({semantic_match_threshold}). Defaulting to 0.7")
        semantic_match_threshold = 0.7


    excel_filepath = os.path.join(mapping_dir, f"{table_key}_mappings.xlsx")
    
    new_rows_data = []
    unmapped_requiring_review_count = 0
    df_columns_ordered = list(excel_cols_cfg.values())
    
    if os.path.exists(excel_filepath):
        try:
            df_existing = pd.read_excel(excel_filepath, engine='openpyxl')
            # Observed headers in Excel are stored in their original case as extracted by `extract_unique_observed_headers`
            # And then displayed as such. The comparison key is this original case string.
            if excel_cols_cfg['observed'] not in df_existing.columns:
                logger.warning(f"Column '{excel_cols_cfg['observed']}' missing in {excel_filepath}. Treating as new mapping file.")
                df_existing = pd.DataFrame(columns=df_columns_ordered)
        except Exception as e:
            logger.warning(f"Could not read existing mapping file {excel_filepath}. Will create a new one. Error: {e}")
            df_existing = pd.DataFrame(columns=df_columns_ordered)
    else:
        df_existing = pd.DataFrame(columns=df_columns_ordered)

    logger.info(f"Processing mappings for table: {table_key} into {excel_filepath}")

    # Get set of observed headers already in the Excel for quick lookup
    existing_obs_headers_in_excel = set(df_existing[excel_cols_cfg['observed']].astype(str).tolist())


    for obs_header_original_case in sorted(list(observed_headers_set)):
        if obs_header_original_case in existing_obs_headers_in_excel:
            # Header exists in Excel. Update suggestion/score if user hasn't mapped it.
            # Find the row index. df_existing observed headers are original case strings.
            try:
                idx = df_existing[df_existing[excel_cols_cfg['observed']] == obs_header_original_case].index[0]
            except IndexError:
                logger.error(f"Logic error: Observed header '{obs_header_original_case}' reported in existing_obs_headers_in_excel but not found in DataFrame. Skipping update for this header.")
                continue

            user_standardized_val = df_existing.loc[idx, excel_cols_cfg['standardized_user']]
            
            if pd.isna(user_standardized_val) or str(user_standardized_val).strip() == "":
                # User hasn't filled it. Provide/update suggestion.
                if std_headers_embeddings.size > 0: # Check if embeddings are available
                    suggestion, score = generate_suggestions_semantic(obs_header_original_case, std_headers_for_table, std_headers_embeddings, semantic_match_threshold)
                    df_existing.loc[idx, excel_cols_cfg['standardized_suggested']] = suggestion
                    df_existing.loc[idx, excel_cols_cfg['confidence_score']] = f"{score:.2f}" # Store as string for Excel
                else:
                    df_existing.loc[idx, excel_cols_cfg['standardized_suggested']] = "(No embeddings for suggestions)"
                    df_existing.loc[idx, excel_cols_cfg['confidence_score']] = "N/A"
                
                if not (suggestion and score >= semantic_match_threshold and not suggestion.startswith("(")):
                    unmapped_requiring_review_count += 1
        else:
            # New observed header, not in Excel yet. Add it.
            if std_headers_embeddings.size > 0:
                suggestion, score = generate_suggestions_semantic(obs_header_original_case, std_headers_for_table, std_headers_embeddings, semantic_match_threshold)
                score_str = f"{score:.2f}"
            else:
                suggestion = "(No embeddings for suggestions)"
                score_str = "N/A"

            new_row = {
                excel_cols_cfg['observed']: obs_header_original_case, # Store original case
                excel_cols_cfg['standardized_user']: "",
                excel_cols_cfg['standardized_suggested']: suggestion,
                excel_cols_cfg['confidence_score']: score_str,
                excel_cols_cfg['notes']: "New - Please Review"
            }
            new_rows_data.append(new_row)
            if not (suggestion and score >= semantic_match_threshold and not suggestion.startswith("(")): # Check score for new rows too
                 unmapped_requiring_review_count += 1

    if new_rows_data:
        df_new_rows = pd.DataFrame(new_rows_data) # Columns will be inferred
        df_to_write = pd.concat([df_existing, df_new_rows], ignore_index=True)
    else:
        df_to_write = df_existing
    
    for col_name_key, col_name_val in excel_cols_cfg.items():
        if col_name_val not in df_to_write.columns:
            df_to_write[col_name_val] = "" if col_name_key == 'standardized_user' or col_name_key == 'notes' else None

    df_to_write = df_to_write.drop_duplicates(subset=[excel_cols_cfg['observed']], keep='first')
    df_to_write = df_to_write[df_columns_ordered]

    # Attempt to write using openpyxl; fallback to xlsxwriter if it fails
    write_success = False
    try:
        df_to_write.to_excel(excel_filepath, index=False, engine='openpyxl')
        write_success = True
        used_engine = 'openpyxl'
    except Exception as e_open:
        logger.error(f"Could not write to Excel file {excel_filepath} with openpyxl. Error: {e_open}")
        try:
            with pd.ExcelWriter(excel_filepath, engine='xlsxwriter') as writer:
                df_to_write.to_excel(writer, index=False)
            write_success = True
            used_engine = 'xlsxwriter'
        except Exception as e_xlsx:
            logger.error(f"Retry with xlsxwriter failed for {excel_filepath}. Error: {e_xlsx}")
    if not write_success:
        return
    logger.info(f"Mapping file '{excel_filepath}' updated/created successfully using {used_engine} engine.")
    if unmapped_requiring_review_count > 0:
        logger.warning(f"  ATTENTION: {unmapped_requiring_review_count} observed headers in '{table_key}' might require manual mapping in '{excel_filepath}'.")
    if not observed_headers_set:
        logger.info(f"  No observed headers found for table '{table_key}' in any JSON files during this run.")


def main():
    """Main function to generate/update column mapping Excel files."""
    try:
        config = load_config()
    except Exception as e:
        logger.critical(f"Failed to start: Could not load configuration. {e}")
        return

    if EMBEDDING_MODEL is None: # Check if model loaded successfully at the start
        logger.critical("Sentence embedding model failed to load. Mapping generation quality will be severely impacted or fail. Exiting.")
        # Optionally, you could allow it to proceed and just create empty Excel files or rely on existing ones.
        # For now, let's exit if the primary matching mechanism is unavailable.
        return

    ensure_directories_exist(config)
    
    # Extract headers in their original casing for better semantic understanding
    observed_headers_by_table_original_case = extract_unique_observed_headers(config)

    if not observed_headers_by_table_original_case:
        logger.info("No headers extracted from any JSON files. Mapping generation will not proceed further for tables.")
        for table_key in config.get('tables_to_process', {}).keys():
            excel_filepath = os.path.join(config['mapping_files_directory'], f"{table_key}_mappings.xlsx")
            if not os.path.exists(excel_filepath):
                 update_excel_mapping_file(table_key, set(), config)
        return

    logger.info("--- Unique Observed Headers (Original Case) ---")
    for table, headers in observed_headers_by_table_original_case.items():
        logger.info(f"  Table '{table}': {len(headers)} unique headers found.")

    for table_key in config.get('tables_to_process', {}).keys():
        current_table_observed_headers = observed_headers_by_table_original_case.get(table_key, set())
        update_excel_mapping_file(table_key, current_table_observed_headers, config)
    
    logger.info(f"\nMapping generation process complete. Please review the Excel files in: {config['mapping_files_directory']}")

if __name__ == "__main__":
    main()