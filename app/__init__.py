"""
Bank Statement Analyzer application.

This package provides functionality for analyzing and storing financial data from bank statements.
"""

import logging
from app.config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO if not Config.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)