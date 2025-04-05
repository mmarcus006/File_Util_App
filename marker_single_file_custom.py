from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.config.parser import ConfigParser

config = {
    #"output_format": "json",
    "output_format": "markdown",
    "use_llm": "true",
    "disable_image_extraction": "true",
    "enable_table_ocr": "true",
    "detect_boxes": "true",
    "pdftext_workers": 8,
    "timeout": 480,
    "max_retries": 3,
    "retry_delay": 5,
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

if __name__ == "__main__":
    my_file = "C:/Projects/File_Util_App/samples/DPJ2012Trust_MS.pdf"
    rendered = converter(my_file)
    new_file = "C:/Projects/File_Util_App/samples/DPJ2012Trust_MS_rendered.md"
    with open(new_file, "w") as f:
        f.write(str(rendered))
    print(f"Rendered file saved to {new_file}")
