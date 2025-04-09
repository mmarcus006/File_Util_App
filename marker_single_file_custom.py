from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.config.parser import ConfigParser
import os
import json

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

config = {
    "output_format": "json",
    #"output_format": "markdown",
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
    "ollama_model": "gemma3",
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

if __name__ == "__main__":
    SINGLE_FILE_PATH = r"C:\\Projects\\File_Util_App\\9Round_Franchising_LLC_FDD_2024_ID636440\\bbd94cce-d087-49e0-a7b7-ba787df47de7_origin.pdf" # Specify the full path to the single PDF to test
    rendered = converter(SINGLE_FILE_PATH)
    
    # Create output directory if it doesn't exist
    output_dir = "C:/Projects/File_Util_App/output"
    os.makedirs(output_dir, exist_ok=True)
    
    new_file = os.path.join(output_dir, "9Round_Franchising_LLC_FDD_2024_ID636440_rendered.json")
    
    try:
        # Try to save using custom encoder
        with open(new_file, "w", encoding="utf-8") as f:
            json.dump(rendered, f, indent=4, cls=CustomJSONEncoder)
        print(f"JSON output saved to {new_file}")
    except Exception as e:
        print(f"Error saving JSON: {e}")
        
        # Fallback to string representation
        fallback_file = os.path.join(output_dir, "9Round_Franchising_LLC_FDD_2024_ID636440_rendered.txt")
        with open(fallback_file, "w", encoding="utf-8") as f:
            f.write(str(rendered))
        print(f"Fallback output saved to {fallback_file}")
