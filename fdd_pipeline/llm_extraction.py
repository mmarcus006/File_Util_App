# fdd_pipeline/llm_extraction/client.py
from __future__ import annotations

import base64, json, logging, os, pathlib, typing as t
from pydantic import BaseModel
import sys
from pathlib import Path
from openai import OpenAI
# Add parent directory to path for direct script execution
sys.path.insert(0, str(Path(__file__).parent.parent))

from fdd_pipeline.models import Franchise
from fdd_pipeline.exceptions import LLMExtractionError, InvalidLLMJson, ValidationError

_log = logging.getLogger(__name__)

# --------------------------------------------------------------------------------------
# 1) Client bootstrap
# --------------------------------------------------------------------------------------
_API_KEY   = os.getenv("OPENROUTER_API_KEY")
_BASE_URL  = "https://openrouter.ai/api/v1"
_TITLE     = os.getenv("OPEN_ROUTER_SITE_TITLE", "FDD-Pipeline")
_MODEL     = os.getenv("LLM_MODEL", "openai/gpt-4o-mini")
_PDF_ENGINE = os.getenv("PDF_ENGINE", "pdf-text")  # Options: "mistral-ocr", "pdf-text", "native"

# Better error for API key
if not _API_KEY:
    raise RuntimeError(
        "OPENROUTER_API_KEY not set in environment. "
        "Please set this environment variable before running the script. "
        "You can get an API key from https://openrouter.ai/"
    )

try:
    client = OpenAI(base_url=_BASE_URL, api_key=_API_KEY)
except Exception as e:
    raise RuntimeError(f"Failed to initialize OpenAI client: {e}")

# --------------------------------------------------------------------------------------
# 2) Helpers
# --------------------------------------------------------------------------------------
def _encode_pdf_to_base64(path: pathlib.Path) -> str:
    """Encode PDF file to base64 string."""
    if not path.exists(): 
        raise FileNotFoundError(path)
    with open(path, "rb") as pdf_file:
        return base64.b64encode(pdf_file.read()).decode('utf-8')

def _build_messages(prompt: str, b64_pdf: str, pdf_filename: str = "document.pdf") -> list[dict]:
    """Build the messages array with text prompt and PDF file."""
    return [{
        "role": "user",
        "content": [
            {"type": "text", "text": prompt},
            {
                "type": "file",
                "file": {
                    "filename": pdf_filename,
                    "file_data": f"data:application/pdf;base64,{b64_pdf}",
                },
            },
        ],
    }]

def _check_output_file_exists(output_path: str) -> bool:
    """Check if the output file already exists."""
    return os.path.exists(output_path)

def _prepare_json_schema(schema: dict) -> dict:
    """
    Ensure the JSON schema is properly formatted for OpenRouter structured outputs.
    
    Args:
        schema: The original schema (typically from Pydantic model_json_schema)
        
    Returns:
        A schema formatted for OpenRouter's structured outputs
    """
    # Ensure additionalProperties is false to prevent hallucinated fields
    if "additionalProperties" not in schema:
        schema["additionalProperties"] = False
    
    # Ensure we have a top-level type
    if "type" not in schema:
        schema["type"] = "object"
    
    return schema

# --------------------------------------------------------------------------------------
# 3) Public call
# --------------------------------------------------------------------------------------
def call_openrouter(
    pdf_path: pathlib.Path,
    prompt: str,
    response_schema: dict,
    model: str = _MODEL,
    temperature: float = 0.0,
    pdf_engine: str = _PDF_ENGINE,
) -> dict:
    """
    Call OpenRouter API with structured output support.
    
    Uses OpenRouter's structured outputs feature to ensure the model response
    follows the provided JSON schema. This helps prevent parsing errors and
    improves reliability of extracted data.
    
    Returns raw JSON dict validated by OpenRouter's `json_schema` feature.
    """
    try:
        # Get the PDF filename from the path
        pdf_filename = pdf_path.name
        
        # Encode the PDF
        b64 = _encode_pdf_to_base64(pdf_path)
        
        # Configure PDF processing plugins - will be passed via extra_body
        pdf_plugins = [
            {
                "id": "file-parser",
                "pdf": {
                    "engine": pdf_engine
                }
            }
        ]
        
        # Prepare the schema for structured outputs
        formatted_schema = _prepare_json_schema(response_schema)
        
        # Make the API call with structured outputs
        # Pass plugins via extra_body instead of directly as an argument
        resp = client.chat.completions.create(
            model=model,
            temperature=temperature,
            messages=_build_messages(prompt, b64, pdf_filename),
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "fdd_extraction",
                    "strict": True,
                    "schema": formatted_schema,
                },
            },
            extra_body={"plugins": pdf_plugins},
        )
        raw = resp.choices[0].message.content
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise InvalidLLMJson(f"LLM returned invalid JSON: {exc}") from exc
    except Exception as exc:
        raise LLMExtractionError(f"OpenRouter request failed: {exc}") from exc

def extract_and_save(
    pdf_path: pathlib.Path,
    prompt: str,
    model_cls: t.Type[BaseModel],
    out_json_path: str,
    model: str = _MODEL,
    temperature: float = 0.0,
    pdf_engine: str = _PDF_ENGINE,
) -> BaseModel:
    """
    Extract data from PDF using LLM with structured outputs, validate with Pydantic model, and save to JSON.
    
    Uses OpenRouter's structured outputs feature to ensure the model responds with 
    valid JSON matching the Pydantic model schema, preventing parsing errors and
    improving extraction reliability.
    
    Args:
        pdf_path: Path to the PDF file
        prompt: Instruction prompt for the LLM
        model_cls: Pydantic model class to validate response
        out_json_path: Output path for the JSON file
        model: LLM model to use
        temperature: Sampling temperature
        pdf_engine: PDF processing engine to use ("mistral-ocr", "pdf-text", or "native")
        
    Returns:
        Validated Pydantic model instance
    """
    # Check if output file already exists
    if _check_output_file_exists(out_json_path):
        _log.warning(f"Output file {out_json_path} already exists. Overwriting.")
    
    # Verify input PDF exists
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found at {pdf_path}")
    
    # Get the model's JSON schema and prepare it for structured outputs
    model_schema = model_cls.model_json_schema()
    
    # Get raw JSON from LLM using structured outputs
    raw_data = call_openrouter(
        pdf_path=pdf_path,
        prompt=prompt,
        response_schema=model_schema,
        model=model,
        temperature=temperature,
        pdf_engine=pdf_engine,
    )
    
    # Validate with Pydantic model
    try:
        validated_data = model_cls.model_validate(raw_data)
    except Exception as exc:
        raise ValidationError(f"Failed to validate LLM response: {exc}") from exc
    
    # Save to JSON file
    with open(out_json_path, "w") as f:
        f.write(validated_data.model_dump_json(indent=2))
    
    return validated_data

if __name__ == "__main__":
    # Define paths
    pdf_path = Path("C:/projects/File_Util_App/output/split_pdfs/0a6a4155-b831-4d28-a7bf-f7eb1da5d2ad/intro.pdf")
    out_json_path = "example_fdd_structured.json"
    
    # Extract, validate and save
    try:
        # Verify PDF file exists
        if not pdf_path.exists():
            print(f"Error: PDF file not found at {pdf_path}")
            sys.exit(1)
            
        doc = extract_and_save(
            pdf_path=pdf_path,
            prompt="Extract all franchise information from this PDF document according to the FDD format.",
            model_cls=Franchise,
            out_json_path=out_json_path,
            model="mistralai/mistral-large",
            pdf_engine="pdf-text",  # Using the free engine for text-based PDFs
        )
        print(f"Successfully extracted data to {out_json_path}")
    except Exception as e:
        print(f"Error during extraction: {e}")
        sys.exit(1)  