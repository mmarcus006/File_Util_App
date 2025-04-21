"""
Script to set up the Supabase database schema based on the provided schema files.
"""
import sys
import time
import os
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Add src directory to path for local imports if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Import config after environment variables are loaded
from src.config import SUPABASE_CONFIG, DB_SCHEMA

try:
    from supabase import create_client, Client
except ImportError:
    print("Error: supabase package not installed. Install it with: pip install supabase")
    sys.exit(1)

def get_supabase_client() -> Client:
    """
    Create and return a Supabase client.
    
    Returns:
        Supabase client instance
    """
    url = SUPABASE_CONFIG['url']
    key = SUPABASE_CONFIG['service_role_key']
    return create_client(url, key)

def execute_query(client: Client, query: str) -> Dict[str, Any]:
    """
    Execute a SQL query against Supabase PostgreSQL database using the client.
    
    Args:
        client: Supabase client instance
        query: SQL query to execute
        
    Returns:
        Dict containing query results or error information
    """
    try:
        print(f"Executing query: {query[:60]}...")  # Print first 60 chars of query for debugging
        response = client.rpc('exec_sql', {'sql': query}).execute()
        
        # Access the response data and error
        data = response.model_dump() if hasattr(response, 'model_dump') else {"data": response.data}
        
        # Check for errors in the response
        if "error" in data and data["error"]:
            return {"error": str(data["error"])}
        
        # If execution was successful but no data returned
        if not data.get("data"):
            return {"message": "Query executed successfully (no data returned)"}
            
        return data.get("data", {})
    except Exception as e:
        print(f"Error executing query: {e}")
        return {"error": str(e), "query": query}

def create_schema(client: Client):
    """Create the database schema in Supabase."""
    # Enable RLS for security
    enable_rls = """
    -- Enable RLS on all tables we create
    ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON TABLES FROM public;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO authenticated;
    """
    
    # Adapted schema from db_create_update_v2.py for PostgreSQL
    # Updated based on AllTables_Headers.json and inferred relationships
    schema_sql = """
    -- I. Industry and Classification Tables (Assumed necessary, adapt if needed)
    CREATE TABLE IF NOT EXISTS public.Industry (
        industry_id SERIAL PRIMARY KEY,
        industry_name TEXT UNIQUE NOT NULL
    );
    COMMENT ON TABLE public.Industry IS 'List of distinct industries.';

    CREATE TABLE IF NOT EXISTS public.Category (
        category_id SERIAL PRIMARY KEY,
        industry_id INTEGER REFERENCES public.Industry(industry_id) ON DELETE SET NULL,
        category_name TEXT UNIQUE NOT NULL
    );
    COMMENT ON TABLE public.Category IS 'List of distinct categories, potentially linked to industries.';

    CREATE TABLE IF NOT EXISTS public.Franchise (
        franchise_id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        slug TEXT UNIQUE,
        logo_url TEXT,
        website_url TEXT,
        founded_year INTEGER,
        franchising_since INTEGER,
        hq_location TEXT,
        description TEXT,
        overview_narrative TEXT,
        primary_industry_id INTEGER REFERENCES public.Industry(industry_id) ON DELETE SET NULL,
        primary_category_id INTEGER REFERENCES public.Category(category_id) ON DELETE SET NULL,
        last_manual_update TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    COMMENT ON TABLE public.Franchise IS 'Core information about each franchise brand.';
    CREATE INDEX IF NOT EXISTS idx_franchise_name ON public.Franchise (name);

    CREATE TABLE IF NOT EXISTS public.FranchiseCategory (
        franchise_id INTEGER NOT NULL REFERENCES public.Franchise(franchise_id) ON DELETE CASCADE,
        category_id INTEGER NOT NULL REFERENCES public.Category(category_id) ON DELETE CASCADE,
        PRIMARY KEY (franchise_id, category_id)
    );
    COMMENT ON TABLE public.FranchiseCategory IS 'Associative table linking franchises to categories.';

    -- II. FDD Tracking & Core FDD Data Tables (Based on AllTables_Headers.json)
    CREATE TABLE IF NOT EXISTS public.fdd (
        fdd_id SERIAL PRIMARY KEY,
        franchise_id INTEGER NOT NULL REFERENCES public.Franchise(franchise_id) ON DELETE CASCADE,
        publication_year INTEGER NOT NULL,
        document_url TEXT,
        original_pdf_path TEXT,
        layout_analysis_output_path TEXT,
        processed_structured_data_path TEXT,
        processing_state TEXT, -- Consider ENUM type later if values are fixed
        last_processing_attempt TIMESTAMP WITH TIME ZONE,
        extracted_date DATE,
        state_filed_in TEXT DEFAULT 'Base' NOT NULL,
        UNIQUE (franchise_id, publication_year, state_filed_in)
    );
    COMMENT ON TABLE public.fdd IS 'Tracks individual Franchise Disclosure Documents.';
    CREATE INDEX IF NOT EXISTS idx_fdd_franchise_year ON public.fdd (franchise_id, publication_year DESC);

    -- FDD Layout Information (Based on AllTables_Headers.json)
    CREATE TABLE IF NOT EXISTS public.fdd_layout_section (
        section_id SERIAL PRIMARY KEY,
        fdd_id INTEGER NOT NULL REFERENCES public.fdd(fdd_id) ON DELETE CASCADE,
        identified_item_number INTEGER,
        identified_header_text TEXT,
        start_page INTEGER,
        end_page INTEGER
    );
    COMMENT ON TABLE public.fdd_layout_section IS 'Identified standard FDD sections (Items 1-23) layout within a PDF.';

    CREATE TABLE IF NOT EXISTS public.fdd_layout_exhibit (
        exhibit_id SERIAL PRIMARY KEY,
        fdd_id INTEGER NOT NULL REFERENCES public.fdd(fdd_id) ON DELETE CASCADE,
        identified_exhibit_letter TEXT,
        identified_title TEXT,
        start_page INTEGER,
        end_page INTEGER
    );
    COMMENT ON TABLE public.fdd_layout_exhibit IS 'Identified exhibits layout within an FDD PDF.';

    -- FDD Split PDF Tracking (Assumed necessary, adapt if needed)
    CREATE TABLE IF NOT EXISTS public.Split_PDF_Files (
        split_pdf_id SERIAL PRIMARY KEY,
        fdd_id INTEGER NOT NULL REFERENCES public.fdd(fdd_id) ON DELETE CASCADE,
        franchise_id INTEGER NOT NULL REFERENCES public.Franchise(franchise_id) ON DELETE CASCADE, -- Redundant? fdd links franchise
        original_pdf_path TEXT NOT NULL,
        split_pdf_path TEXT NOT NULL,
        content_type TEXT NOT NULL, -- e.g., 'section', 'exhibit'
        content_identifier TEXT, -- e.g., 'Item 7', 'Exhibit A'
        start_page INTEGER,
        end_page INTEGER,
        UNIQUE(fdd_id, content_type, content_identifier)
    );
    COMMENT ON TABLE public.Split_PDF_Files IS 'Tracks individual PDF files created by splitting original FDDs.';

    -- FDD Extracted Content Tables (Based on AllTables_Headers.json)
    CREATE TABLE IF NOT EXISTS public.fdd_executive (
        executive_id SERIAL PRIMARY KEY,
        fdd_id INTEGER NOT NULL REFERENCES public.fdd(fdd_id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        title TEXT,
        experience_summary TEXT
    );
    COMMENT ON TABLE public.fdd_executive IS 'Executive information extracted from FDD Item 2.';

    CREATE TABLE IF NOT EXISTS public.fdd_litigation (
        litigation_id SERIAL PRIMARY KEY,
        fdd_id INTEGER NOT NULL REFERENCES public.fdd(fdd_id) ON DELETE CASCADE,
        case_summary TEXT NOT NULL,
        litigation_type TEXT -- Consider ENUM type later
    );
    COMMENT ON TABLE public.fdd_litigation IS 'Litigation details extracted from FDD Item 3.';

    CREATE TABLE IF NOT EXISTS public.fdd_bankruptcy (
        bankruptcy_id SERIAL PRIMARY KEY,
        fdd_id INTEGER NOT NULL REFERENCES public.fdd(fdd_id) ON DELETE CASCADE,
        entity_involved TEXT,
        bankruptcy_summary TEXT NOT NULL
    );
    COMMENT ON TABLE public.fdd_bankruptcy IS 'Bankruptcy details extracted from FDD Item 4.';

    CREATE TABLE IF NOT EXISTS public.fdd_initialfee (
        initial_fee_id SERIAL PRIMARY KEY,
        fdd_id INTEGER NOT NULL REFERENCES public.fdd(fdd_id) ON DELETE CASCADE,
        amount REAL,
        fee_range_min REAL,
        fee_range_max REAL,
        notes TEXT
    );
    COMMENT ON TABLE public.fdd_initialfee IS 'Initial franchise fee details from FDD Item 5.';

    CREATE TABLE IF NOT EXISTS public.fdd_ongoingfee (
        fee_id SERIAL PRIMARY KEY,
        fdd_id INTEGER NOT NULL REFERENCES public.fdd(fdd_id) ON DELETE CASCADE,
        fee_type TEXT NOT NULL, -- e.g., 'Royalty', 'Advertising'
        amount_formula TEXT NOT NULL,
        due_date_or_frequency TEXT,
        notes TEXT
    );
    COMMENT ON TABLE public.fdd_ongoingfee IS 'Ongoing fees details from FDD Item 6.';
    CREATE INDEX IF NOT EXISTS idx_fdd_ongoingfee_type ON public.fdd_ongoingfee (fdd_id, fee_type);

    CREATE TABLE IF NOT EXISTS public.fdd_initialinvestmentitem (
        cost_item_id SERIAL PRIMARY KEY,
        fdd_id INTEGER NOT NULL REFERENCES public.fdd(fdd_id) ON DELETE CASCADE,
        item_name TEXT NOT NULL,
        min_cost REAL,
        max_cost REAL,
        method_of_payment TEXT,
        due_date TEXT,
        paid_to TEXT,
        notes TEXT
    );
    COMMENT ON TABLE public.fdd_initialinvestmentitem IS 'Initial investment cost items from FDD Item 7.';
    CREATE INDEX IF NOT EXISTS idx_fdd_initialinvestment_fdd ON public.fdd_initialinvestmentitem (fdd_id);

    -- User Management Table (Based on AllTables_Headers.json)
    CREATE TABLE IF NOT EXISTS public.app_users (
        user_id SERIAL PRIMARY KEY,
        auth_user_id UUID UNIQUE REFERENCES auth.users(id) ON DELETE SET NULL, -- Link to Supabase Auth user
        name TEXT,
        email TEXT UNIQUE NOT NULL,
        role TEXT NOT NULL CHECK (role IN ('Prospective', 'Franchisor', 'Admin', 'Consultant')),
        date_registered TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    COMMENT ON TABLE public.app_users IS 'Application users, linked to Supabase Auth.';
    CREATE INDEX IF NOT EXISTS idx_user_email ON public.app_users (email);
    CREATE INDEX IF NOT EXISTS idx_user_auth_id ON public.app_users (auth_user_id);

    -- Blog Content Table (Based on AllTables_Headers.json)
    CREATE TABLE IF NOT EXISTS public.blog_posts (
        id SERIAL PRIMARY KEY,
        slug TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        excerpt TEXT,
        content TEXT,
        author TEXT, -- Consider linking to app_users if authors are users
        date DATE,
        category TEXT, -- Consider linking to Category table if appropriate
        image TEXT, -- URL or path?
        image_alt TEXT,
        published BOOLEAN DEFAULT false,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    COMMENT ON TABLE public.blog_posts IS 'Content for the application blog.';

    -- FDD Document Tracking Table (Based on AllTables_Headers.json)
    CREATE TABLE IF NOT EXISTS public.fdd_documents (
        id SERIAL PRIMARY KEY,
        fdd_id INTEGER REFERENCES public.fdd(fdd_id) ON DELETE SET NULL, -- Link to the specific FDD record if available
        file_hash TEXT UNIQUE, -- Hash of the PDF file content
        file_path TEXT, -- Original storage path
        franchisor TEXT, -- Extracted/matched franchisor name
        issuance_date DATE,
        amendment_status TEXT, -- e.g., 'Original', 'Amended'
        amendment_date DATE,
        processed_status TEXT DEFAULT 'Pending', -- e.g., 'Pending', 'Processing', 'Complete', 'Error'
        docling_processed BOOLEAN DEFAULT false, -- Specific processor flag
        is_duplicate BOOLEAN DEFAULT false,
        extracted_text TEXT, -- Potentially large, consider alternatives if needed
        markdown_path TEXT,
        json_path TEXT UNIQUE,
        html_path TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        error_message TEXT,
        original_doc_id TEXT -- Identifier from the source system/scrape
    );
    COMMENT ON TABLE public.fdd_documents IS 'Tracks individual source FDD documents and their processing status/outputs.';
    CREATE INDEX IF NOT EXISTS idx_fdd_documents_hash ON public.fdd_documents(file_hash);
    CREATE INDEX IF NOT EXISTS idx_fdd_documents_fdd_id ON public.fdd_documents(fdd_id);

    -- Exhibit Simple Table (Present in JSON, purpose might overlap with fdd_layout_exhibit)
    -- Table removed (migration: drop_deprecated_simple_tables)
    -- CREATE TABLE IF NOT EXISTS public.fdd_exhibits_simple (
    --     id SERIAL PRIMARY KEY,
    --     fdd_id INTEGER NOT NULL, -- Needs FK reference, but which table? fdd or fdd_documents? Assuming fdd for now.
    --     exhibit_letter TEXT,
    --     title TEXT,
    --     start_page INTEGER,
    --     end_page INTEGER,
    --     FOREIGN KEY (fdd_id) REFERENCES public.fdd(id) ON DELETE CASCADE -- Adjusted FK assumption
    -- );
    -- COMMENT ON TABLE public.fdd_exhibits_simple IS 'Simplified exhibit list, potentially from an earlier schema or specific process.';
    -- CREATE INDEX IF NOT EXISTS idx_fdd_exhibits_simple_fdd_id ON public.fdd_exhibits_simple(fdd_id);
    """
    
    # Set up RLS policies for security
    rls_policies = """
    -- Enable Row Level Security on tables
    ALTER TABLE public.Industry ENABLE ROW LEVEL SECURITY;
    ALTER TABLE public.Category ENABLE ROW LEVEL SECURITY;
    ALTER TABLE public.Franchise ENABLE ROW LEVEL SECURITY;
    ALTER TABLE public.FranchiseCategory ENABLE ROW LEVEL SECURITY;
    ALTER TABLE public.fdd ENABLE ROW LEVEL SECURITY;
    ALTER TABLE public.fdd_layout_section ENABLE ROW LEVEL SECURITY;
    ALTER TABLE public.fdd_layout_exhibit ENABLE ROW LEVEL SECURITY;
    ALTER TABLE public.Split_PDF_Files ENABLE ROW LEVEL SECURITY;
    ALTER TABLE public.fdd_executive ENABLE ROW LEVEL SECURITY;
    ALTER TABLE public.fdd_litigation ENABLE ROW LEVEL SECURITY;
    ALTER TABLE public.fdd_bankruptcy ENABLE ROW LEVEL SECURITY;
    ALTER TABLE public.fdd_initialfee ENABLE ROW LEVEL SECURITY;
    ALTER TABLE public.fdd_ongoingfee ENABLE ROW LEVEL SECURITY;
    ALTER TABLE public.fdd_initialinvestmentitem ENABLE ROW LEVEL SECURITY;
    ALTER TABLE public.app_users ENABLE ROW LEVEL SECURITY;
    ALTER TABLE public.blog_posts ENABLE ROW LEVEL SECURITY;
    ALTER TABLE public.fdd_documents ENABLE ROW LEVEL SECURITY;
    -- ALTER TABLE public.fdd_exhibits_simple ENABLE ROW LEVEL SECURITY; -- Table removed

    -- Create permissive read policies (adjust as needed for specific roles)
    -- Public data readable by anyone (even unauthenticated)
    CREATE POLICY "Public read access for Industry" ON public.Industry FOR SELECT USING (true);
    CREATE POLICY "Public read access for Category" ON public.Category FOR SELECT USING (true);
    CREATE POLICY "Public read access for Franchise" ON public.Franchise FOR SELECT USING (true);
    CREATE POLICY "Public read access for FranchiseCategory" ON public.FranchiseCategory FOR SELECT USING (true);
    CREATE POLICY "Public read access for FDD" ON public.fdd FOR SELECT USING (true);
    CREATE POLICY "Public read access for FDD Layout Section" ON public.fdd_layout_section FOR SELECT USING (true);
    CREATE POLICY "Public read access for FDD Layout Exhibit" ON public.fdd_layout_exhibit FOR SELECT USING (true);
    CREATE POLICY "Public read access for Split PDF Files" ON public.Split_PDF_Files FOR SELECT USING (true);
    CREATE POLICY "Public read access for FDD Executive" ON public.fdd_executive FOR SELECT USING (true);
    CREATE POLICY "Public read access for FDD Litigation" ON public.fdd_litigation FOR SELECT USING (true);
    CREATE POLICY "Public read access for FDD Bankruptcy" ON public.fdd_bankruptcy FOR SELECT USING (true);
    CREATE POLICY "Public read access for FDD Initial Fee" ON public.fdd_initialfee FOR SELECT USING (true);
    CREATE POLICY "Public read access for FDD Ongoing Fee" ON public.fdd_ongoingfee FOR SELECT USING (true);
    CREATE POLICY "Public read access for FDD Initial Investment" ON public.fdd_initialinvestmentitem FOR SELECT USING (true);
    CREATE POLICY "Public read access for Blog Posts" ON public.blog_posts FOR SELECT USING (published = true); -- Only show published posts publicly
    CREATE POLICY "Public read access for FDD Documents" ON public.fdd_documents FOR SELECT USING (true); -- May need refinement
    -- CREATE POLICY "Public read access for FDD Exhibits Simple" ON public.fdd_exhibits_simple FOR SELECT USING (true); -- Table removed

    -- User specific policies
    -- Users can view their own profile info
    CREATE POLICY "User can view own user data" ON public.app_users FOR SELECT USING (auth.uid() = auth_user_id);
    -- Users can update their own profile info (name, etc., but not role or email easily)
    CREATE POLICY "User can update own user data" ON public.app_users FOR UPDATE USING (auth.uid() = auth_user_id) WITH CHECK (auth.uid() = auth_user_id);

    -- Authenticated user policies (if needed beyond public access)
    CREATE POLICY "Authenticated can read published blog posts" ON public.blog_posts FOR SELECT TO authenticated USING (published = true);

    -- Admin policies (Example using a custom 'admin' role check - requires setting up this role or using app_metadata)
    -- This is a placeholder; adapt based on your actual authorization scheme (e.g., check app_users.role)
    CREATE POLICY "Admin full access for Franchise" ON public.Franchise FOR ALL USING (public.is_admin(auth.uid())) WITH CHECK (public.is_admin(auth.uid()));
    CREATE POLICY "Admin full access for FDD" ON public.fdd FOR ALL USING (public.is_admin(auth.uid())) WITH CHECK (public.is_admin(auth.uid()));
    -- Add similar admin policies for other tables as needed...
    CREATE POLICY "Admin full access for app_users" ON public.app_users FOR ALL USING (public.is_admin(auth.uid())) WITH CHECK (public.is_admin(auth.uid()));
    CREATE POLICY "Admin full access for blog_posts" ON public.blog_posts FOR ALL USING (public.is_admin(auth.uid())) WITH CHECK (public.is_admin(auth.uid()));
    CREATE POLICY "Admin full access for fdd_documents" ON public.fdd_documents FOR ALL USING (public.is_admin(auth.uid())) WITH CHECK (public.is_admin(auth.uid()));

    -- Note: Need to create the is_admin function or use metadata checks for admin policies to work.
    -- Example function (needs to be created separately):
    /*
    CREATE OR REPLACE FUNCTION public.is_admin(user_id uuid)
    RETURNS boolean
    LANGUAGE sql
    SECURITY DEFINER SET search_path = public
    AS $$
        SELECT EXISTS (
            SELECT 1
            FROM public.app_users
            WHERE auth_user_id = user_id AND role = 'Admin'
        );
    $$;
    */
    """
    
    # Break schema into smaller chunks to prevent timeouts
    print("Creating database schema (this may take a minute)...")
    
    # Execute the schema in multiple statements
    statements = [enable_rls]
    
    # Split the schema_sql into individual table creation statements
    table_statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
    statements.extend(table_statements)
    
    # Add the RLS policies
    statements.append(rls_policies)
    
    success_count = 0
    error_count = 0
    
    for i, statement in enumerate(statements):
        if not statement.strip():
            continue
            
        print(f"Executing schema statement {i+1}/{len(statements)}...")
        result = execute_query(client, statement)
        
        if "error" in result:
            print(f"⚠️ Error in statement {i+1}: {result['error']}")
            error_count += 1
        else:
            success_count += 1
            
        # Add a small delay to avoid rate limiting
        time.sleep(0.5)
    
    print(f"Schema creation completed: {success_count} statements succeeded, {error_count} statements failed.")

def check_connection(client: Client) -> bool:
    """Check the connection to the Supabase database."""
    query = "SELECT current_database() as db, current_schema as schema"
    
    try:
        # Use the client to run a simple query
        response = client.rpc('exec_sql', {'sql': query}).execute()
        
        # Access the response data and error
        data = response.model_dump() if hasattr(response, 'model_dump') else {"data": response.data}
        
        # Check for errors in the response
        if "error" in data and data["error"]:
            print(f"Connection error: {data['error']}")
            return False
        else:
            print("Connected to Supabase database successfully.")
            if data.get("data"):
                print(f"Database info: {data['data']}")
            else:
                print("Query successful (no data returned)")
            return True
    except Exception as e:
        print(f"Connection error: {e}")
        return False

def main():
    """Main function to set up the Supabase database."""
    print(f"Connecting to Supabase at {SUPABASE_CONFIG['url']}...")
    
    try:
        # Create a Supabase client
        client = get_supabase_client()
        
        # Check the connection
        if check_connection(client):
            # Create the schema
            create_schema(client)
            print("Database setup complete.")
        else:
            print("Failed to connect to Supabase database.")
            sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 