You are an expert in parsing Franchise Disclosure Documents (FDDs). Your task is to extract specific information from the provided FDD document.

**Extraction Range:**
Extract information only from the beginning of the document up to the point where "ITEM 2" (or "ITEM II") begins. Do not include any information from ITEM 2 onwards.

**Output Format:**
Provide the extracted data as a single JSON object.

**Data Fields to Extract:**
Based on the relevant fields from the `fdd_documents` and `franchisors` tables, extract the following information if found within the specified range:

*   **fiscal_year**: The fiscal year the FDD covers. Extract as an integer.
*   **issue_date**: The date the FDD was issued. Extract in YYYY-MM-DD format if possible, otherwise as text.
*   **brand_name**: The primary brand name of the franchise.
*   **legal_name**: The full legal name of the franchisor entity.
*   **parent_company**: The name of the parent company, if applicable and mentioned.
*   **phone_number**: A primary contact phone number for the franchisor.
*   **website_url**: The main website URL for the franchisor or franchise.
*   **email_contact**: A primary email address for contact.
*   **headquarters_address**: The street address of the franchisor's headquarters.
*   **headquarters_city**: The city of the franchisor's headquarters.
*   **headquarters_state**: The state or province of the franchisor's headquarters.
*   **headquarters_zip**: The zip or postal code of the franchisor's headquarters.
*   **headquarters_country**: The country of the franchisor's headquarters.
*   **year_founded**: The year the franchisor company was founded. Extract as an integer.
*   **year_franchising_began**: The year the franchisor began offering franchises. Extract as an integer.
*   **business_description**: A brief description of the franchised business offered (often found in the introduction or Item 1).
*   **company_history**: A brief summary of the franchisor's history (often found in the introduction or Item 1).

**Instructions:**
1.  Read the document carefully from the beginning up to the start of "ITEM 2".
2.  Identify the values for each of the listed data fields within this range.
3.  If a field is not found in the specified range, use `null` as the value for that field in the JSON output.
4.  Ensure the output is a valid JSON object containing only the fields listed above. Do not include fields like `id`, `franchisor_id`, `source_file`, `created_at`, or `logo_url` as they are not extractable from the text in this context.
5.  For text fields, provide the extracted text as a string. For integer fields, provide the value as a JSON number or `null`. For date fields, provide the value as a string in YYYY-MM-DD format or `null`.