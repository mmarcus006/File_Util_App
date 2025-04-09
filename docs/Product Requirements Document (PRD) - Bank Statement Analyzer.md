## 1. Product Requirements Document (PRD) - Bank Statement Analyzer

**1. Introduction**

The Bank Statement Analyzer is a Python-based web application designed to automate the extraction and storage of financial data from PDF bank statements of JPMorgan Chase (JPM), Morgan Stanley (MS), and Goldman Sachs (GS). The application will provide a user-friendly interface for uploading statements, process them to extract key financial data points using AI, and store the structured data in a local SQLite database for potential future analysis or reporting.

**2. Goals**

*   Provide a simple web interface for uploading PDF bank statements.
*   Automatically identify the financial institution (JPM, MS, GS) from the uploaded PDF.
*   Convert the PDF content into markdown format suitable for AI processing.
*   Utilize the LiteLLM library to interface with the Google Gemini API (or potentially other models) to accurately extract predefined financial data points from the markdown content.
*   Validate and structure the extracted data using Pydantic models.
*   Store the structured data persistently in a unified SQLite database schema using SQLAlchemy.
*   Handle potential errors during PDF processing, conversion, and data extraction gracefully.

**3. User Stories**

*   As a user, I want to upload a single PDF bank statement (JPM, MS, or GS) through a web interface.
*   As a user, I want the application to automatically determine which bank the statement is from.
*   As a user, I want the application to process the statement and extract key financial information (account details, summary values, holdings, transactions, tax info).
*   As a user, I want the extracted data to be stored in a structured database so I can potentially query it later.
*   As a user, I want to receive feedback on whether the upload and processing were successful or if errors occurred.

**4. Functional Requirements**

*   **FR1: PDF Upload:** The application must provide a web interface (Streamlit) allowing users to upload a single PDF file.
*   **FR2: Institution Identification:** Upon upload, the application must analyze the PDF content (using PyMuPDF for initial text extraction) to identify whether the statement belongs to JPMorgan Chase, Morgan Stanley, or Goldman Sachs using predefined regular expressions or keywords.
*   **FR3: PDF to Markdown Conversion:** The application must use the Docling library to convert the full content of the uploaded PDF into markdown format.
*   **FR4: Data Extraction via LLM:**
    *   The application must construct a specific prompt for the identified institution, including the markdown content and the target Pydantic JSON schema.
    *   The application must use LiteLLM to send the prompt to the configured LLM endpoint (e.g., Google Gemini).
    *   The application must receive the JSON response via LiteLLM.
*   **FR5: Data Validation & Structuring:** The application must use Pydantic models to validate the structure and data types of the JSON response received from the LLM.
*   **FR6: Database Storage:**
    *   The application must connect to a local SQLite database using SQLAlchemy.
    *   The application must map the validated Pydantic data models to SQLAlchemy database models.
    *   The application must insert the extracted and structured data into the appropriate database tables, ensuring relationships are maintained. Data for an already existing statement period for a given account should ideally be updated or skipped to avoid duplicates.
*   **FR7: User Feedback:** The Streamlit interface must display status messages to the user (e.g., "Uploading...", "Identifying Institution...", "Converting to Markdown...", "Extracting Data...", "Saving to Database...", "Success!", "Error: [details]").
*   **FR8: Error Handling:** The application must handle potential errors gracefully, including:
    *   Invalid file uploads (non-PDF).
    *   Failure to identify the institution.
    *   Errors during PDF-to-Markdown conversion (Docling errors).
    *   Errors calling the LLM via LiteLLM (network issues, API key errors, rate limits, LiteLLM configuration errors).
    *   Invalid JSON response from the LLM.
    *   Pydantic validation errors.
    *   Database connection or insertion errors.
    *   Inform the user about the nature of the error.

**5. Non-Functional Requirements**

*   **NFR1: Technology Stack:** The application must be built using Python, Streamlit (Frontend), SQLite (DB), SQLAlchemy (ORM), Pydantic, PyMuPDF, Docling, and LiteLLM.
*   **NFR2: Performance:** PDF processing and AI extraction should complete within a reasonable time frame (e.g., < 60 seconds per statement, dependent on PDF size and API latency).
*   **NFR3: Usability:** The Streamlit interface should be simple and intuitive for uploading files.
*   **NFR4: Data Privacy:** As the application handles sensitive financial data, processing should ideally occur locally as much as possible. API calls via LiteLLM transmit statement data; users should be aware of this. No data should be stored outside the local SQLite database. API keys must be handled securely (e.g., environment variables, config files).
*   **NFR5: Scalability:** The initial version targets local use with SQLite. Future scaling might require a different database backend.
*   **NFR6: Maintainability:** Code should be well-structured, commented, and follow Python best practices.

**6. Data Model (Database Schema)**

*   *(See Section 3 below for the full SQL Schema)* - Includes tables: `Institutions`, `Accounts`, `Statements`, `TaxSummary`, `AssetClasses`, `Securities`, `Holdings`, `TransactionTypes`, `Transactions`.

**7. Extraction Logic**

1.  **Upload:** Streamlit `file_uploader`.
2.  **Identify:** Open PDF with PyMuPDF, extract text from the first 1-2 pages, apply regex patterns for "J.P. Morgan", "Morgan Stanley", "Goldman Sachs".
3.  **Convert:** Pass PDF file path/bytes to Docling API/library to get markdown output.
4.  **Extract:** Select the appropriate bank-specific Gemini prompt, insert markdown content, send to Gemini API, request JSON output matching the defined Pydantic model (`StatementData`).
5.  **Validate:** Parse the LLM's JSON response using the `StatementData` Pydantic model. If validation fails, report error.
6.  **Store:** Map validated Pydantic model data to SQLAlchemy models and commit to the SQLite database session. Handle potential conflicts (e.g., duplicate statement periods).

**8. API Integration (LLM via LiteLLM)**

*   Use the `LiteLLM` library to manage interactions with the chosen LLM (initially Gemini).
*   Configure `LiteLLM` with the necessary API keys and model details (managed securely).
*   Utilize the LLM's function calling/JSON mode capabilities by providing the Pydantic model schema within the prompt to ensure structured output, managed via LiteLLM's interface.
*   Implement retry logic for transient API errors if necessary, potentially leveraging LiteLLM's features.

**9. Future Considerations**

*   Support for additional financial institutions.
*   More sophisticated error reporting and handling.
*   Data visualization or reporting features within Streamlit.
*   Support for password-protected PDFs.
*   Batch processing of multiple PDFs.
*   Option to export data from the database.
*   Deployment options (e.g., Docker, cloud service).

---
