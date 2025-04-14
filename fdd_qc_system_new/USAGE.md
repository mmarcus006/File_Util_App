"""
FDD Verification Package - Command-line interface documentation.

This file provides instructions on how to use the FDD Verification Package
from the command line.
"""

USAGE = """
# Running with the graphical user interface:
python main.py --ui

# Running from the command line:
python main.py --pdf path/to/document.pdf --json path/to/headers.json --output results.json

# Running as a Python module:
python -m fdd_verification

# Installation:
pip install -e .

# Then you can import and use in your own code:
from fdd_verification.core import PDFProcessor, JSONProcessor, EnhancedVerificationEngine

# Or run the verification directly:
from fdd_verification import run_verification
results = run_verification("path/to/document.pdf", "path/to/headers.json")
"""
