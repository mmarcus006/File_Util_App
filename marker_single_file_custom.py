from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.config.parser import ConfigParser
import os
import json
from pathlib import Path

# Custom JSON encoder to handle objects that aren't JSON serializable
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        # Try to convert to dictionary if object has to_dict method
        if hasattr(obj, 'to_dict') and callable(getattr(obj, 'to_dict')):
            return obj.to_dict()
        # Try to convert to dictionary if object has __dict__ attribute
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        # For marker JSONOutput objects
        elif hasattr(obj, 'output') and hasattr(obj, 'metadata'):
            return {
                'output': obj.output,
                'metadata': obj.metadata
            }
        # Handle other special types here
        try:
            return str(obj)
        except:
            return f"<Object of type {type(obj).__name__} not serializable>"

# Merged config dictionary
config = {
    "output_format": "json",
    "use_llm": "true",
    "page_range": "1-30",
    "disable_image_extraction": "true",
    "enable_table_ocr": "true",
    "detect_boxes": "true",
    "pdftext_workers": 1,
    "timeout": 1080,
    "max_retries": 3,
    "retry_delay": 5,
    "llm_service": "marker.services.ollama.OllamaService",
    "ollama_model": "gemma3:12b-it-q4_K_M",
    "ollama_api_url": "http://localhost:11434",
    "ollama_api_key": "ollama"
}
config_parser = ConfigParser(config)

converter = PdfConverter(
    config=config_parser.generate_config_dict(),
    artifact_dict=create_model_dict(),
    processor_list=config_parser.get_processors(),
    renderer=config_parser.get_renderer(),
    llm_service=config_parser.get_llm_service()
)

# Merged main execution block with relative paths
if __name__ == "__main__":
    # Define relative paths for input/output
    input_pdf_file: str = "samples/input.pdf"  # Default input PDF
    output_base_name: str = "output_rendered" # Base name for output files
    output_dir_name: str = "output" # Output directory

    # Get the directory of the current script
    script_dir = Path(__file__).parent.resolve()

    # Construct full paths
    full_pdf_path = script_dir / input_pdf_file
    output_dir = script_dir / output_dir_name
    output_json_path = output_dir / f"{output_base_name}.json"
    output_txt_path = output_dir / f"{output_base_name}.txt" # Fallback path

    # Check if input file exists
    if not full_pdf_path.is_file():
        print(f"Error: Input PDF file not found at {full_pdf_path}")
    else:
        # Perform conversion
        print(f"Processing PDF: {full_pdf_path}") # Added print statement
        rendered = converter(str(full_pdf_path)) # converter expects string path

        # Create output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"Ensured output directory exists: {output_dir}") # Added print

        try:
            # Try to save using custom encoder
            print(f"Attempting to save JSON output to {output_json_path}") # Added print
            with open(output_json_path, "w", encoding="utf-8") as f:
                json.dump(rendered, f, indent=4, cls=CustomJSONEncoder)
            print(f"JSON output saved successfully.") # Changed print
        except Exception as e:
            print(f"Error saving JSON: {e}")

            # Fallback to string representation
            try:
                print(f"Attempting fallback save to text: {output_txt_path}") # Added print
                with open(output_txt_path, "w", encoding="utf-8") as f:
                    f.write(str(rendered))
                print(f"Fallback output saved successfully.") # Changed print
            except Exception as fallback_e:
                 print(f"Error saving fallback text file: {fallback_e}")
