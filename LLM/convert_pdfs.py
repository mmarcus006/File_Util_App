#!/usr/bin/env python3
"""
Convert PDF files in prompts/pdf_example to Markdown and JSON using IBM Docling with RapidOCR and high table accuracy.
"""

import sys
import os
import json
from pathlib import Path
from huggingface_hub import snapshot_download
from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions, RapidOcrOptions, TableFormerMode


def get_pdf_paths(input_dir: Path) -> list[Path]:
    """Return a list of all PDF files in the given directory."""
    return [p for p in input_dir.iterdir() if p.is_file() and p.suffix.lower() == ".pdf"]


def ensure_directory(path: Path) -> None:
    """Create the directory if it doesn't exist."""
    path.mkdir(parents=True, exist_ok=True)


def output_files_exist(pdf_path: Path, output_dir: Path) -> bool:
    """Check if both markdown and JSON output files already exist for the given PDF."""
    stem = pdf_path.stem
    return (
        (output_dir / f"{stem}.md").exists()
        and (output_dir / f"{stem}.json").exists()
        and (output_dir / f"{stem}.html").exists()
    )


def init_converter() -> DocumentConverter:
    """Initialize the DocumentConverter with RapidOCR and high-accuracy table mode."""
    # Download RapidOCR models
    download_path = snapshot_download(repo_id="SWHL/RapidOCR")
    # Set model paths
    det_model_path = os.path.join(download_path, "PP-OCRv4", "en_PP-OCRv3_det_infer.onnx")
    rec_model_path = os.path.join(download_path, "PP-OCRv4", "ch_PP-OCRv4_rec_server_infer.onnx")
    cls_model_path = os.path.join(download_path, "PP-OCRv3", "ch_ppocr_mobile_v2.0_cls_train.onnx")

    # Configure OCR and pipeline options
    ocr_options = RapidOcrOptions(
        det_model_path=det_model_path,
        rec_model_path=rec_model_path,
        cls_model_path=cls_model_path,
    )
    pipeline_options = PdfPipelineOptions(
        ocr_options=ocr_options,
        do_table_structure=True
    )
    pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE

    # Create and return the converter
    return DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )


def convert_and_save(pdf_path: Path, output_dir: Path, converter: DocumentConverter) -> None:
    """Convert a single PDF to markdown and JSON, then save the outputs."""
    result = converter.convert(source=str(pdf_path))
    doc = result.document

    # Export to markdown
    md = doc.export_to_markdown()
    md_path = output_dir / f"{pdf_path.stem}.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md)

    # Export to JSON
    try:
        json_str = doc.model_dump_json(indent=2)
    except AttributeError:
        json_str = json.dumps(doc.model_dump(), indent=2)
    json_path = output_dir / f"{pdf_path.stem}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(json_str)

    # Export to HTML
    html_str = doc.export_to_html()
    html_path = output_dir / f"{pdf_path.stem}.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_str)

    print(
        f"Converted {pdf_path.name} -> {md_path.name}, {json_path.name}, {html_path.name}"
    )


def main() -> None:
    # Determine paths relative to this script
    script_dir = Path(__file__).resolve().parent
    root_dir = script_dir.parent
    input_dir = root_dir / "prompts" / "pdf_example"
    output_dir = input_dir / "output"

    ensure_directory(output_dir)

    # Gather all PDF files
    pdf_files = get_pdf_paths(input_dir)
    if not pdf_files:
        print(f"No PDF files found in {input_dir}")
        sys.exit(0)

    converter = init_converter()

    # Process each PDF
    for pdf_path in pdf_files:
        if output_files_exist(pdf_path, output_dir):
            print(f"Skipping {pdf_path.name}; output already exists.")
            continue
        convert_and_save(pdf_path, output_dir, converter)


if __name__ == "__main__":
    main() 