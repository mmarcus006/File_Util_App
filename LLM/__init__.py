"""LLM module for FDD data extraction using AI models."""

# Import important components to expose at the module level
from LLM.config import (
    SYSTEM_PROMPT_TEMPLATE,
    PDF_SEARCH_DIRECTORIES,
    PDF_KEYWORDS,
    OUTPUT_FILENAMES,
    GEMINI_MODEL_NAME,
    OPENAI_MODEL_NAME
)

from LLM.schemas import ExtractionOutput

from LLM.pdf_processor import (
    find_fdd_intro_pdfs,
    extract_fdd_data_with_gemini,
    output_file_exists
)
