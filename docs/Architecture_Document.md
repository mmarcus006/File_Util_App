## 2. Architecture Document - Bank Statement Analyzer

**1. Overview**

This document outlines the architecture for the Bank Statement Analyzer application. It's designed as a single Python application leveraging Streamlit for the user interface and integrating various libraries for backend processing.

**2. Components**

1.  **Frontend (Streamlit):**
    *   Provides the web UI for file uploads.
    *   Displays processing status and results/errors.
    *   Interacts with the Backend Logic component.
2.  **Backend Logic (Python Modules/Functions):**
    *   Orchestrates the entire workflow from upload to database storage.
    *   Contains core application logic.
3.  **PDF Processor (`pdf_processor.py`):**
    *   **Institution Identification:** Uses `PyMuPDF` to extract initial text, applies regex to identify the bank.
    *   **PDF to Markdown Conversion:** Interfaces with the `Docling` library/API.
4.  **AI Extractor (`llm_extractor.py`):**
    *   Manages interaction with the chosen LLM via `LiteLLM`.
    *   Selects the appropriate bank-specific prompt.
    *   Sends markdown data and receives JSON response through `LiteLLM`.
    *   Handles API authentication (via LiteLLM configuration) and basic error handling.
5.  **Data Parser & Validator (`data_parser.py`, `models.py`):**
    *   Uses `Pydantic` models (`models.py`) to define the expected structure of the LLM's output.
    *   Parses and validates the received JSON against these Pydantic models.
    *   Transforms validated Pydantic models into SQLAlchemy models.
6.  **Database Interface (`database.py`, `db_models.py`):**
    *   Uses `SQLAlchemy` ORM.
    *   Defines database models (`db_models.py` or within `database.py`) mirroring the SQL schema.
    *   Manages the connection to the SQLite database (`database.db`).
    *   Handles session management and CRUD operations (primarily insertion).
7.  **Configuration (`config.py`):**
    *   Stores settings like API keys (ideally loaded from environment variables or a secure file).

**3. Data Flow**

```mermaid
graph LR
    A[User] -->|1. Upload PDF| B(Streamlit UI);
    B -->|2. PDF Bytes| C(Backend Logic);
    C -->|3. PDF Bytes| D(PDF Processor);
    D -->|4. Extract Text (PyMuPDF)| D;
    D -->|5. Identify Institution (Regex)| D;
    D -->|6. Institution Name| C;
    D -->|7. Convert PDF->MD (Docling)| D;
    D -->|8. Markdown Content| C;
    C -->|9. Select Prompt + Markdown| E(AI Extractor);
    E -->|10. Call LLM via LiteLLM| F(LiteLLM Abstraction);
    F -->|11. JSON Response| E;
    E -->|12. Raw JSON| C;
    C -->|13. Raw JSON| G(Data Parser / Validator);
    G -->|14. Validate w/ Pydantic Models| G;
    G -->|15. Validated Pydantic Object| C;
    C -->|16. Map Pydantic->SQLAlchemy| C;
    C -->|17. SQLAlchemy Objects| H(Database Interface);
    H -->|18. Save to SQLite DB| I(SQLite Database);
    C -->|19. Status/Result| B;
    B -->|20. Display Status/Result| A;

    style F fill:#f9d,stroke:#333,stroke-width:2px;
    style I fill:#ccf,stroke:#333,stroke-width:2px;
```

**4. Technology Choices Justification**

*   **Python:** Versatile language with strong libraries for web dev, data processing, AI, and databases.
*   **Streamlit:** Rapid UI development specifically for data applications, simple to learn and deploy locally.
*   **SQLite:** Lightweight, file-based database, perfect for local single-user applications, requires no separate server setup.
*   **SQLAlchemy:** Mature and powerful ORM for Python, simplifies database interactions and schema management.
*   **Pydantic:** Excellent for data validation and defining clear data structures, integrates well with APIs and ORMs.
*   **PyMuPDF:** Efficient and robust library for extracting text and metadata from PDFs, needed for institution identification.
*   **Docling:** Specialized tool for high-fidelity PDF to Markdown conversion, providing better structure for AI extraction than raw text.
*   **LiteLLM:** Abstraction library to interact consistently with various LLM APIs (including Gemini), simplifying model switching and configuration.

**5. Error Handling Strategy**

*   Each major step (Identification, Conversion, Extraction, Validation, Storage) will be wrapped in `try...except` blocks.
*   Specific exceptions (e.g., `FileNotFoundError`, `ValidationError` from Pydantic, `google.api_core.exceptions`, `sqlalchemy.exc.SQLAlchemyError`) will be caught where possible.
*   Exceptions related to `LiteLLM` interactions will also be handled.
*   Generic `Exception` will catch unexpected errors.
*   Errors will be logged (to console initially) and reported back to the Streamlit UI.
*   Processing for a statement will halt upon encountering a critical error.

---