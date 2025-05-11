import yaml
import os
import logging
from typing import Dict, Any

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = "/Users/miller/projects/File_Util_App/Item20/config.yaml"

def load_config(config_path: str = DEFAULT_CONFIG_PATH) -> Dict[str, Any]:
    """
    Loads the YAML configuration file.

    Args:
        config_path: Path to the YAML configuration file.

    Returns:
        A dictionary containing the configuration.

    Raises:
        FileNotFoundError: If the config file is not found.
        yaml.YAMLError: If there's an error parsing the YAML.
        SystemExit: On critical failure to load config.
    """
    if not os.path.exists(config_path):
        logger.error(f"Configuration file not found: {config_path}")
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        logger.info(f"Configuration loaded successfully from {config_path}")
        return config
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML configuration file {config_path}: {e}")
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred while loading config {config_path}: {e}")
        raise

if __name__ == '__main__':
    # This part is for testing the loader itself, not for production use by other scripts.
    # In a production setup, other scripts import and call load_config().
    try:
        cfg = load_config()
        # Example: Ensure directories from config can be created if this script were to manage them
        # This logic is typically in the main application scripts.
        # os.makedirs(cfg.get('json_files_directory', 'fdd_json_data_default'), exist_ok=True)
        # os.makedirs(cfg.get('mapping_files_directory', 'mapping_files_default'), exist_ok=True)
        # os.makedirs(cfg.get('output_csv_directory', 'output_csvs_default'), exist_ok=True)
        logger.info("Config loaded for standalone test. Required directories should be handled by main scripts.")
    except Exception as e:
        logger.critical(f"Failed to load or use config in standalone test: {e}")
        # sys.exit(1) # In a real app, might exit if config is essential