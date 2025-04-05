# Supabase Database Integration

This guide explains how to set up and use the Supabase PostgreSQL database integration for the File Utility Application.

## Configuration

The Supabase credentials are stored in `src/config.py`. This file contains:

- Supabase URL
- Anon API Key
- Service Role API Key
- JWT Secret

These credentials should be kept private and never committed to version control.

## Database Schema

The database schema is based on the SQLite schema used in the local application, but adapted for PostgreSQL:

1. **Industry and Classification Tables**
   - Industry
   - Category
   - Franchise
   - FranchiseCategory

2. **FDD Tracking & Core FDD Data Tables**
   - FDD
   - FDD_Layout_Section
   - FDD_Layout_Exhibit
   - Split_PDF_Files
   - FDD_Executive
   - FDD_Litigation
   - FDD_Bankruptcy
   - and many more tables for specific FDD content

3. **User Management**
   - app_users (linked to Supabase Auth)

4. **Simple FDD Tables** (from original schema)
   - fdds_simple
   - fdd_sections_simple
   - fdd_exhibits_simple

## Security

The database is secured using Row Level Security (RLS) policies:

- All tables have RLS enabled
- Read access to most data is available to all authenticated users
- Write access is restricted to authenticated users
- User data is restricted to the user themselves and administrators

## Setting Up the Database

To set up the Supabase database:

1. Run the `src/setup_supabase_db.py` script to create the schema and RLS policies.

```bash
python src/setup_supabase_db.py
```

2. Import data from your local SQLite database (if needed):

```bash
python src/import_data_to_supabase.py
```

## Connecting to Supabase

You can connect to the Supabase database in your application:

```python
from src.config import SUPABASE_CONFIG
from supabase import create_client

url = SUPABASE_CONFIG["url"]
key = SUPABASE_CONFIG["anon_key"]  # Use anon_key for client-side code
client = create_client(url, key)

# Example: Fetch franchises
response = client.table("Franchise").select("*").execute()
```

## Utilities

The `src/supabase_utils.py` file provides helper functions for interacting with Supabase:

- `execute_query(query, params)`: Execute a SQL query with parameters
- `get_supabase_client()`: Get a configured Supabase client instance

## Supabase SQL Functions and API Endpoints

When executing raw SQL queries in Supabase, you need to use the correct API endpoints and parameter names:

1. **Endpoint**: `/rest/v1/rpc/exec_sql`
2. **Parameter**: The SQL query should be passed in a parameter named `sql` (not `sql_query`)

Example:
```python
# Correct way to execute SQL
payload = {"sql": "SELECT * FROM franchise;"}
response = requests.post(f"{url}/rest/v1/rpc/exec_sql", headers=headers, json=payload)

# Incorrect way (will cause 404 error)
payload = {"sql_query": "SELECT * FROM franchise;"}  # Wrong parameter name
```

If you encounter 404 errors mentioning "Could not find the function", double-check that you're using:
- The correct endpoint path
- The correct parameter name in your payload

## Important Notes

1. **Security**: Never expose the service_role_key in client-side code. It bypasses RLS and should only be used on the server.

2. **Data Sync**: The application currently doesn't automatically sync between local SQLite and Supabase. You'll need to run the import script manually when needed.

3. **API Access**: In addition to SQL, you can use Supabase's REST API to interact with the data.

## Troubleshooting

If you encounter issues:

1. Check connection strings in `src/config.py`
2. Verify Supabase project settings
3. Check for RLS policy conflicts
4. Look for database errors in the Supabase dashboard
5. Verify that you're using the correct parameter names in API calls 