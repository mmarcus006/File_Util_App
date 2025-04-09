# Changelog

## [Unreleased]

### Added
- Created project structure with app, components, utils, models, and services directories
- Initialized Git repository with .gitignore for Python projects
- Created README.md with project overview and instructions
- Created requirements.txt with core dependencies and development tools
- Implemented Pydantic models for data validation (`models.py`)
- Implemented SQLAlchemy ORM models for database interaction (`db_models.py`)
- Added database interface for SQLite (`database.py`)
- Created configuration module for managing environment variables (`config.py`)
- Implemented PDF processor for text extraction and institution identification (`pdf_processor.py`)
- Created LLM extractor for interacting with Gemini API (`llm_extractor.py`)
- Added data parser for validation and database storage (`data_parser.py`)
- Created Streamlit UI components for file upload and processing (`upload_component.py`)
- Set up main Streamlit application entry point (`main.py`)
- Created basic test scaffold for database models (`test_db_models.py`)
- Implemented database initialization logic to create tables

### Updated
- Enhanced database interface with comprehensive CRUD operations
- Added robust error handling with custom exception classes
- Created unit tests for PDF processor, database interface, and error handling
- Implemented data parser for mapping between Pydantic and SQLAlchemy models
- Added database initialization utility for creating tables
