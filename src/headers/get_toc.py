import fitz  # PyMuPDF
import re
import os
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from pydantic import BaseModel, ValidationError

# Only needed if you run this script directly and need to import project config
import sys
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from src.config import FDD_PDF_FOLDER
else:
    from ..config import FDD_PDF_FOLDER

# Mistral API Client
from mistralai import Mistral

# ----------------------------
# Pydantic Models for Structured TOC Output
# ----------------------------

class FDDItem(BaseModel):
    """Represents a single item in the FDD Table of Contents."""
    item_name: str
    page_number: Optional[int] = None
    needs_review: bool = False

class FDDStructure(BaseModel):
    """Represents the entire structured FDD Table of Contents."""
    items: List[FDDItem]

# ----------------------------
# PDF Parsing and TOC Identification
# ----------------------------

def extract_text_from_pdf(pdf_path: str) -> List[Tuple[int, str]]:
    """
    Extract text from each page of a PDF file.
    Returns a list of (one-based page number, page_text).
    Only processes the first 30 pages as TOC and Item 1 will be in this range.
    """
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        raise ValueError(f"Failed to open PDF {pdf_path}: {str(e)}")

    pages_text = []
    # Only process the first 30 pages or all pages if fewer than 30
    max_pages = min(30, len(doc))
    for page_idx in range(max_pages):
        page = doc[page_idx]
        text = page.get_text()
        if text.strip():
            # Store the page index (0-based) + 1 to match PDF page numbers
            pages_text.append((page_idx + 1, text))
    doc.close()
    return pages_text

def is_likely_toc_structure(text: str) -> bool:
    """
    Checks if the text structure resembles a TOC:
    Looks for multiple lines ending in numeric page references.
    """
    lines = text.split('\n')
    count_ending_with_num = 0
    for ln in lines:
        if re.search(r"(?:\.|\s)+\d+\s*$", ln.strip()):
            count_ending_with_num += 1
    return (count_ending_with_num >= 5)

def identify_toc_pages(pages_text: List[Tuple[int, str]]) -> List[int]:
    """
    Identify page(s) likely containing the Table of Contents.
    Returns a list of consecutive zero-indexed page numbers (e.g. [1,2]).
    """
    toc_patterns = [
        r"(?i)\b(table\s+of\s+contents)\b",
        r"(?i)\b(contents)\b",
        r"(?i)\b(toc)\b"
    ]
    max_check = min(len(pages_text), 15)
    potential_toc_start = -1

    # Look in the first 15 pages max
    for page_num, text in pages_text[:max_check]:
        # Primary pattern check
        if re.search(toc_patterns[0], text) and is_likely_toc_structure(text):
            potential_toc_start = page_num
            break

        # Secondary patterns if primary not found
        if potential_toc_start == -1:
            for pat in toc_patterns[1:]:
                if re.search(pat, text) and is_likely_toc_structure(text):
                    potential_toc_start = page_num
                    break
            if potential_toc_start != -1:
                break

    if potential_toc_start == -1:
        return []

    # Heuristic for multi-page TOCs
    toc_pages = [potential_toc_start]
    current = potential_toc_start
    while current + 1 < len(pages_text):
        next_page_text = pages_text[current + 1][1]
        short_page = (len(pages_text[current][1].splitlines()) < 20)
        next_toc_like = re.search(r"^\s*(Item\s+\d+|Section\s+\d+|Exhibit\s+[A-Z])",
                                  next_page_text, re.IGNORECASE | re.MULTILINE)
        if short_page or next_toc_like:
            current += 1
            toc_pages.append(current)
        else:
            break

    return [p - 1 for p in toc_pages[:3]]  # limit to 3 consecutive pages

def extract_toc_text(pages_text: List[Tuple[int, str]], toc_pages: List[int]) -> str:
    """
    Extract text from the identified TOC page(s).
    Joins pages with a separator for clarity.
    """
    combined = []
    for idx in toc_pages:
        if 0 <= idx < len(pages_text):
            combined.append(pages_text[idx][1].strip())
    return "\n\n--- Page Break ---\n\n".join(combined)

# ----------------------------
# LLM-Based TOC Extraction
# ----------------------------

def load_prompt(file_path: str) -> str:
    """Utility to load a text prompt from disk."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Prompt file not found: {file_path}")
    except Exception as e:
        print(f"Error reading prompt file {file_path}: {e}")
    return ""

def extract_toc_with_llm(toc_text: str) -> Optional[FDDStructure]:
    """
    Use the Mistral API to extract structured TOC from text.
    Returns an FDDStructure or None on failure.
    """
    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        print("Error: MISTRAL_API_KEY environment variable not set.")
        return None

    model_name = "mistral-large-latest"
    client = Mistral(api_key=api_key)

    system_prompt_path = Path("prompts/toc_system_instructions.md")
    user_prompt_path = Path("prompts/toc_extraction_prompt.md")

    system_prompt = load_prompt(str(system_prompt_path))
    user_prompt = load_prompt(str(user_prompt_path))

    if not (system_prompt and user_prompt):
        print("Error: Missing prompt content. Check prompt files.")
        return None

    final_user_prompt = f"{user_prompt}\n\n{toc_text}"

    try:
        chat_response = client.chat.complete(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": final_user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        
        # LLM response in JSON string format
        response_content = chat_response.choices[0].message.content # type: ignore
        if not response_content:
            print("Empty response from LLM")
            return None
            
        # Parse JSON and validate with Pydantic
        try:
            structured_toc = FDDStructure.model_validate_json(response_content) # type: ignore
            return structured_toc
        except ValidationError as ve:
            print(f"LLM response failed validation: {ve}")
            print(f"Response content: {response_content[:200]}...")  # Print first 200 chars for debugging
            return None
            
    except ValidationError as ve:
        print(f"LLM response failed validation: {ve}")
        return None
    except Exception as e:
        print(f"LLM extraction error: {e}")
        return None

# ----------------------------
# Item 1 Detection via Simple Regex
# ----------------------------

def find_item1_start_page(
    pages_text: List[Tuple[int, str]],
    toc_pages: List[int]
) -> Optional[int]:
    """
    Finds the FIRST instance of "Item 1" by regex after the last TOC page.
    Returns one-based page number or None if not found.
    """
    if not pages_text:
        return None

    start_idx = 0
    if toc_pages:
        start_idx = max(toc_pages) + 1  # start searching after TOC

    pattern = re.compile(r"Item.{0,3}1", re.IGNORECASE)

    for page_num, text in pages_text[start_idx:]:
        # If a match is found anywhere on the page, return that page number
        # (page_num is already 1-based from extract_text_from_pdf)
        if pattern.search(text):
            return page_num

    return None

# ----------------------------
# Adjusting TOC Page Numbers
# ----------------------------

def adjust_toc_page_numbers(structured_toc: FDDStructure, page_adjustment: int) -> FDDStructure:
    """
    Adjusts each item's page number by the given offset and flags suspicious entries.
    """
    adjusted_items = []

    for item in structured_toc.items:
        new_page = None
        if item.page_number is not None:
            new_page = item.page_number + page_adjustment
            if new_page < 1:  # suspicious
                item.needs_review = True
        else:
            item.needs_review = True

        adjusted_items.append(FDDItem(
            item_name=item.item_name,
            page_number=new_page,
            needs_review=item.needs_review
        ))

    return FDDStructure(items=adjusted_items)

# ----------------------------
# High-Level TOC Extraction
# ----------------------------

def get_structured_toc(pdf_path: str) -> Optional[Tuple[FDDStructure, List[int]]]:
    """
    Extracts the Table of Contents structure from a PDF, attempts to locate Item 1,
    and applies a page number offset if possible. Also returns the 0-based indices
    of the pages identified as containing the TOC.
    Flags for review if Item 1 is never found in the actual PDF pages.

    Returns:
        Optional[Tuple[FDDStructure, List[int]]]: A tuple containing the adjusted
            FDDStructure and the list of 0-based TOC page indices, or None if extraction fails.
    """
    try:
        # 1) Extract all text
        pages_text = extract_text_from_pdf(pdf_path)
        if not pages_text:
            print(f"No text found in {pdf_path}.")
            return None

        # 2) Identify TOC pages (0-based indices)
        toc_indices = identify_toc_pages(pages_text)
        if not toc_indices:
            print("No TOC page identified.")
            return None

        # 3) Extract TOC text
        toc_text = extract_toc_text(pages_text, toc_indices)
        if not toc_text.strip():
            print("Empty TOC text after extraction.")
            return None

        # 4) Ask LLM to parse the TOC
        raw_toc = extract_toc_with_llm(toc_text)
        if not raw_toc:
            print("LLM-based TOC extraction returned nothing.")
            return None

        # 5) Find first instance of "Item 1" after TOC
        item1_pdf_page_idx = find_item1_start_page(pages_text, toc_indices)

        # 6) If the TOC references an Item 1, compute adjustment
        page_adjustment = 0
        item1_in_toc = next(
            (x for x in raw_toc.items if x.item_name and "item 1" in x.item_name.lower()),
            None
        )

        if item1_pdf_page_idx is None:
            # Could not locate an actual Item 1 in the PDF => Flag for review if it's in the extracted TOC
            if item1_in_toc:
                item1_in_toc.needs_review = True
        else:
            # Attempt to adjust page numbers
            if item1_in_toc and (item1_in_toc.page_number is not None):
                try:
                    # Both page numbers are now 1-based, so we can directly compute the difference
                    page_adjustment = item1_pdf_page_idx - item1_in_toc.page_number
                except Exception as e:
                    print(f"Error computing page adjustment: {e}")
                    page_adjustment = 0

        # 7) Apply final adjustment
        adjusted_toc = adjust_toc_page_numbers(raw_toc, page_adjustment)
        # Reverted: Return toc_indices along with the adjusted_toc
        return adjusted_toc, toc_indices

    except ValueError as e:
        print(f"Error opening or processing PDF: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

# ----------------------------
# JSON Output Function
# ----------------------------

def _save_toc_to_json(
    output_path: Path,
    toc_data: FDDStructure,
    toc_pages_indices: List[int]
) -> None:
    """
    Saves the structured TOC data and the identified TOC page numbers to a JSON file.

    Args:
        output_path: The full path to save the JSON file.
        toc_data: The structured TOC data (FDDStructure).
        toc_pages_indices: List of 0-based page indices where TOC was found.
    """
    # Convert 0-based indices to 1-based page numbers for output
    toc_pages_found = [idx + 1 for idx in toc_pages_indices]

    output_content = {
        "toc_structure": toc_data.model_dump(mode='json'), # Use pydantic's serialization
        "toc_pages_found": toc_pages_found
    }
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_content, f, indent=2, ensure_ascii=False)
        print(f"  Successfully saved TOC data to: {output_path}")
    except IOError as e:
        print(f"  Error writing JSON file {output_path}: {e}")
    except Exception as e:
        print(f"  Unexpected error during JSON saving: {e}")

# ----------------------------
# Refactored Processing Functions
# ----------------------------

def process_single_pdf_file(pdf_path_str: str, output_dir: Path) -> None:
    """Processes a single PDF file and saves the TOC to JSON."""
    pdf_path = Path(pdf_path_str)
    print(f"--- Processing Single File ---\n{pdf_path}")
    if not pdf_path.is_file():
        print(f"Invalid file path: {pdf_path}")
        return

    filename = pdf_path.name
    toc_result_tuple = get_structured_toc(str(pdf_path)) # Pass string path

    if toc_result_tuple:
        toc_structure, toc_indices = toc_result_tuple
        print(f"\n--- {filename} TOC ---\nItems Extracted: {len(toc_structure.items)}")
        json_filename = f"{pdf_path.stem}_toc.json"
        output_json_path = output_dir / json_filename
        _save_toc_to_json(output_json_path, toc_structure, toc_indices)

        # Optional: Still print summary to console
        # for item in toc_structure.items:
        #     pg_display = item.page_number if item.page_number is not None else "N/A"
        #     review_flag = " (REVIEW)" if item.needs_review else ""
        #     print(f"  - {item.item_name} [Page {pg_display}]{review_flag}")
    else:
        print(f"Failed to extract TOC from {filename}")

def process_pdf_folder_updated(folder_path_str: str, output_dir: Path) -> None:
    """
    Processes all PDF files in a folder and saves each TOC to a separate JSON file.
    """
    folder_path = Path(folder_path_str)
    print(f"--- Processing Folder ---\n{folder_path}")
    if not folder_path.is_dir():
        print(f"Error: '{folder_path}' is not a valid directory.")
        return

    pdf_files = list(folder_path.rglob("*.pdf"))
    print(f"Found {len(pdf_files)} PDF(s) in {folder_path}")

    processed_count = 0
    failed_count = 0

    for pdf_path in pdf_files:
        print(f"\nProcessing: {pdf_path.name}")
        toc_result_tuple = get_structured_toc(str(pdf_path))

        if toc_result_tuple:
            toc_structure, toc_indices = toc_result_tuple
            print(f"  Extracted {len(toc_structure.items)} TOC items.")
            json_filename = f"{pdf_path.stem}_toc.json"
            output_json_path = output_dir / json_filename
            _save_toc_to_json(output_json_path, toc_structure, toc_indices)
            processed_count += 1
        else:
            print("  Failed to extract TOC.")
            failed_count += 1

    print("\n--- Folder Processing Summary ---")
    print(f"Successfully processed: {processed_count}")
    print(f"Failed to process: {failed_count}")

# ----------------------------
# Main Execution
# ----------------------------

def main() -> None:
    """
    Main function to run as a script. Set `PROCESS_SINGLE_FILE` to choose between
    a single PDF path or a folder containing multiple PDFs.
    Saves extracted TOCs to JSON files in the 'output/toc_json' directory.
    """
    PROCESS_SINGLE_FILE = False # Set to False to process a folder
    # Define paths relative to the project root for better portability
    project_root = Path(__file__).parent.parent.parent
    SINGLE_FILE_PATH_STR = r"C:\\Projects\\File_Util_App\\9Round_Franchising_LLC_FDD_2024_ID636440\\bbd94cce-d087-49e0-a7b7-ba787df47de7_origin.pdf" # Example, adjust as needed
    FOLDER_PATH_STR = str(FDD_PDF_FOLDER) if 'FDD_PDF_FOLDER' in globals() and FDD_PDF_FOLDER else str(project_root / "data" / "fdd_pdfs") # Default if not imported

    # Define and create the output directory
    output_directory = project_root / "output" / "toc_json"
    try:
        output_directory.mkdir(parents=True, exist_ok=True)
        print(f"Ensured output directory exists: {output_directory}")
    except OSError as e:
        print(f"Error creating output directory {output_directory}: {e}")
        return # Cannot proceed without output directory

    if PROCESS_SINGLE_FILE:
        process_single_pdf_file(SINGLE_FILE_PATH_STR, output_directory)
    else:
        process_pdf_folder_updated(FOLDER_PATH_STR, output_directory)

if __name__ == "__main__":
    # Optional .env loading for MISTRAL_API_KEY
    try:
        from dotenv import load_dotenv
        # Load from .env file in the project root
        dotenv_path = Path(__file__).parent.parent.parent / '.env'
        load_dotenv(dotenv_path=dotenv_path)
        print(f"Attempted to load environment variables from: {dotenv_path}")
        if not os.environ.get("MISTRAL_API_KEY"):
             print("Warning: MISTRAL_API_KEY not found after loading .env")
    except ImportError:
        print("python-dotenv not installed. Ensure MISTRAL_API_KEY is set in environment.")
    except Exception as e:
        print(f"Error loading .env file: {e}")

    main()
