"""
Pytest configuration file.
"""
import os
import sys
from pathlib import Path

# Add parent directory to Python path to allow importing fdd_pipeline
sys.path.insert(0, str(Path(__file__).parent.parent))

# Setup fixtures used across all tests
def pytest_configure(config):
    """Configure pytest for the project."""
    # Additional configuration can be added here if needed
    pass 