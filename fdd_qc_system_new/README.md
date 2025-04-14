# FDD Verification Package

A comprehensive system for verifying FDD (Franchise Disclosure Document) headers in PDF documents.

## Overview

This package provides tools for extracting and verifying headers from FDD documents using a progressive enhancement strategy:
1. Pattern matching verification
2. Transformer-based verification
3. LLM-based verification for difficult cases

## Features

- PDF text extraction and processing
- Header pattern matching and verification
- Advanced NLP-based verification
- Transformer model embeddings for semantic matching
- LLM integration for complex verification cases
- Comprehensive test suite with sample data

## Installation

```bash
pip install -e .
```

## Usage

```python
from fdd_verification.core import PDFProcessor, JSONProcessor, EnhancedVerificationEngine

# Initialize processors
pdf_processor = PDFProcessor("path/to/fdd.pdf")
json_processor = JSONProcessor("path/to/headers.json")

# Create verification engine
engine = EnhancedVerificationEngine(pdf_processor, json_processor)

# Verify all headers
results = engine.verify_all_headers()

# Get verification summary
summary = engine.get_verification_summary()
print(summary)
```

## Package Structure

- `fdd_verification/`: Main package
  - `core/`: Core verification components
  - `utils/`: Utility functions
  - `nlp/`: NLP processing modules
  - `ui/`: User interface components
  - `data/`: Data management

- `tests/`: Test suite
  - `unit/`: Unit tests
  - `integration/`: Integration tests
  - `data/`: Test data samples

## Development

For development, install the package with development dependencies:

```bash
pip install -e ".[dev]"
```

Run tests:

```bash
pytest tests/
```

## License

MIT
