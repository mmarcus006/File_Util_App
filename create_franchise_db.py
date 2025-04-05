import psycopg2
from psycopg2 import sql
from psycopg2 import OperationalError, ProgrammingError

# --- Database Connection Configuration ---
# !!! IMPORTANT: Replace with your actual database details !!!
DB_NAME = "franchise_db"
DB_USER = "franchise_user"
DB_PASSWORD = "strong_password"
DB_HOST = "localhost"  # Or your server IP/hostname
DB_PORT = "5432"      # Default PostgreSQL port

# --- SQL Commands to Create Schema ---

# Define ENUM types first (PostgreSQL specific)
ENUM_DEFINITIONS = """
DO $$ BEGIN
    CREATE TYPE user_role_enum AS ENUM ('Prospective', 'Franchisor', 'Admin', 'Consultant');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE verification_status_enum AS ENUM ('Pending', 'Verified', 'Rejected');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;
"""

# Define CREATE TABLE statements
TABLE_DEFINITIONS = """
-- I. Franchise & Classification Tables (Relatively Stable Data)

CREATE TABLE IF NOT EXISTS Industry (
    industry_id SERIAL PRIMARY KEY,
    industry_name VARCHAR(255) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS Category (
    category_id SERIAL PRIMARY KEY,
    industry_id INT REFERENCES Industry(industry_id) ON DELETE SET NULL,
    category_name VARCHAR(255) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS Franchise (
    franchise_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    slug VARCHAR(255) UNIQUE,
    logo_url VARCHAR(512),
    website_url VARCHAR(512),
    founded_year INT,
    franchising_since INT,
    hq_location VARCHAR(255),
    description TEXT,
    overview_narrative TEXT,
    primary_industry_id INT REFERENCES Industry(industry_id) ON DELETE SET NULL,
    primary_category_id INT REFERENCES Category(category_id) ON DELETE SET NULL,
    last_manual_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- Add index for faster name lookups
CREATE INDEX IF NOT EXISTS idx_franchise_name ON Franchise (name);

CREATE TABLE IF NOT EXISTS FranchiseCategory (
    franchise_id INT REFERENCES Franchise(franchise_id) ON DELETE CASCADE,
    category_id INT REFERENCES Category(category_id) ON DELETE CASCADE,
    PRIMARY KEY (franchise_id, category_id)
);

-- II. FDD Tracking & Core FDD Data Tables

CREATE TABLE IF NOT EXISTS FDD (
    fdd_id SERIAL PRIMARY KEY,
    franchise_id INT NOT NULL REFERENCES Franchise(franchise_id) ON DELETE CASCADE,
    publication_year INT NOT NULL,
    document_url VARCHAR(512),
    extracted_date DATE,
    state_filed_in VARCHAR(50) DEFAULT 'Base', -- e.g., 'Base', 'CA', 'MN'
    UNIQUE (franchise_id, publication_year, state_filed_in)
);
-- Index for faster lookup by franchise and year
CREATE INDEX IF NOT EXISTS idx_fdd_franchise_year ON FDD (franchise_id, publication_year DESC);

CREATE TABLE IF NOT EXISTS FDD_Executive ( -- Item 2
    executive_id SERIAL PRIMARY KEY,
    fdd_id INT NOT NULL REFERENCES FDD(fdd_id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    title VARCHAR(255),
    experience_summary TEXT
);

CREATE TABLE IF NOT EXISTS FDD_Litigation ( -- Item 3
    litigation_id SERIAL PRIMARY KEY,
    fdd_id INT NOT NULL REFERENCES FDD(fdd_id) ON DELETE CASCADE,
    case_summary TEXT NOT NULL,
    litigation_type VARCHAR(100) -- e.g., 'Franchisor vs Franchisee', 'Government'
);

CREATE TABLE IF NOT EXISTS FDD_Bankruptcy ( -- Item 4
    bankruptcy_id SERIAL PRIMARY KEY,
    fdd_id INT NOT NULL REFERENCES FDD(fdd_id) ON DELETE CASCADE,
    entity_involved VARCHAR(100), -- e.g., 'Franchisor', 'Parent', 'Executive'
    bankruptcy_summary TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS FDD_InitialFee ( -- Item 5
    initial_fee_id SERIAL PRIMARY KEY,
    fdd_id INT NOT NULL REFERENCES FDD(fdd_id) ON DELETE CASCADE,
    amount DECIMAL(15, 2),
    fee_range_min DECIMAL(15, 2),
    fee_range_max DECIMAL(15, 2),
    notes TEXT -- Conditions, refundability, payment terms
);

CREATE TABLE IF NOT EXISTS FDD_OngoingFee ( -- Item 6
    fee_id SERIAL PRIMARY KEY,
    fdd_id INT NOT NULL REFERENCES FDD(fdd_id) ON DELETE CASCADE,
    fee_type VARCHAR(100) NOT NULL, -- e.g., 'Royalty', 'Advertising', 'Technology'
    amount_formula VARCHAR(255) NOT NULL, -- e.g., '5%', '$100/month', '1% of Gross Sales'
    due_date_or_frequency VARCHAR(100), -- e.g., 'Monthly', 'Annually'
    notes TEXT
);
-- Index for faster lookup by FDD and fee type
CREATE INDEX IF NOT EXISTS idx_fdd_ongoingfee_type ON FDD_OngoingFee (fdd_id, fee_type);

CREATE TABLE IF NOT EXISTS FDD_InitialInvestmentItem ( -- Item 7
    cost_item_id SERIAL PRIMARY KEY,
    fdd_id INT NOT NULL REFERENCES FDD(fdd_id) ON DELETE CASCADE,
    item_name VARCHAR(255) NOT NULL, -- e.g., 'Real Estate Deposit', 'Initial Fee'
    min_cost DECIMAL(15, 2),
    max_cost DECIMAL(15, 2),
    method_of_payment VARCHAR(100), -- e.g., 'Lump Sum', 'As Incurred'
    due_date VARCHAR(100), -- e.g., 'Before Opening'
    paid_to VARCHAR(100), -- e.g., 'Franchisor', 'Third Party'
    notes TEXT -- Footnotes
);
-- Index for faster lookup by FDD
CREATE INDEX IF NOT EXISTS idx_fdd_initialinvestment_fdd ON FDD_InitialInvestmentItem (fdd_id);

CREATE TABLE IF NOT EXISTS FDD_SupplierRestriction ( -- Item 8
    restriction_id SERIAL PRIMARY KEY,
    fdd_id INT NOT NULL REFERENCES FDD(fdd_id) ON DELETE CASCADE,
    item_restricted VARCHAR(255), -- e.g., 'POS System', 'Food Ingredients'
    restriction_type VARCHAR(100), -- e.g., 'Must buy from Franchisor', 'Approved Supplier List'
    revenue_to_franchisor BOOLEAN,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS FDD_FranchiseeObligation ( -- Item 9
    obligation_id SERIAL PRIMARY KEY,
    fdd_id INT NOT NULL REFERENCES FDD(fdd_id) ON DELETE CASCADE,
    obligation_area VARCHAR(100), -- e.g., 'Site Selection', 'Training', 'Fees'
    summary TEXT,
    agreement_reference VARCHAR(100) -- e.g., 'Section 5.A'
);

CREATE TABLE IF NOT EXISTS FDD_FinancingOption ( -- Item 10
    financing_id SERIAL PRIMARY KEY,
    fdd_id INT NOT NULL REFERENCES FDD(fdd_id) ON DELETE CASCADE,
    financing_type VARCHAR(100), -- e.g., 'Direct from Franchisor', 'Third-Party Lender'
    summary_of_terms TEXT,
    notes TEXT -- Disclaimers, waivers
);

-- Master Catalog for Support Features (Used by Item 11)
CREATE TABLE IF NOT EXISTS SupportFeature (
    feature_id SERIAL PRIMARY KEY,
    feature_name VARCHAR(255) UNIQUE NOT NULL, -- e.g., 'Grand Opening Support'
    feature_type VARCHAR(100) -- e.g., 'Training', 'Marketing', 'Operational'
);

CREATE TABLE IF NOT EXISTS FDD_SupportProvided ( -- Item 11 Link Table
    fdd_support_id SERIAL PRIMARY KEY,
    fdd_id INT NOT NULL REFERENCES FDD(fdd_id) ON DELETE CASCADE,
    feature_id INT NOT NULL REFERENCES SupportFeature(feature_id) ON DELETE CASCADE,
    detail VARCHAR(255), -- e.g., '120 hours', 'Yes, Required', 'Optional'
    support_category VARCHAR(100), -- e.g., 'Pre-Opening', 'Ongoing', 'Training'
    UNIQUE (fdd_id, feature_id) -- Ensure feature listed only once per FDD
);

CREATE TABLE IF NOT EXISTS FDD_TrainingProgram ( -- Item 11 Training Details
    training_id SERIAL PRIMARY KEY,
    fdd_id INT NOT NULL REFERENCES FDD(fdd_id) ON DELETE CASCADE,
    program_name VARCHAR(255), -- e.g., 'Initial Management Training'
    timing VARCHAR(100), -- e.g., 'Before Opening'
    location VARCHAR(100), -- e.g., 'Headquarters', 'Online'
    hours_classroom INT,
    hours_on_the_job INT,
    subjects_covered TEXT
);

CREATE TABLE IF NOT EXISTS FDD_Territory ( -- Item 12
    territory_id SERIAL PRIMARY KEY,
    fdd_id INT NOT NULL REFERENCES FDD(fdd_id) ON DELETE CASCADE,
    is_exclusive BOOLEAN,
    territory_definition TEXT, -- e.g., radius, zip codes
    reservations TEXT, -- Rights reserved by franchisor
    relocation_options TEXT
);

CREATE TABLE IF NOT EXISTS FDD_Trademark ( -- Item 13
    trademark_id SERIAL PRIMARY KEY,
    fdd_id INT NOT NULL REFERENCES FDD(fdd_id) ON DELETE CASCADE,
    mark VARCHAR(255) NOT NULL, -- e.g., 'McDonald's'
    registration_status VARCHAR(100), -- e.g., 'Registered', 'Pending'
    usage_conditions TEXT
);

CREATE TABLE IF NOT EXISTS FDD_IntellectualProperty ( -- Item 14
    ip_id SERIAL PRIMARY KEY,
    fdd_id INT NOT NULL REFERENCES FDD(fdd_id) ON DELETE CASCADE,
    ip_type VARCHAR(100), -- e.g., 'Patent', 'Copyright', 'Trade Secret'
    description TEXT,
    usage_conditions TEXT
);

CREATE TABLE IF NOT EXISTS FDD_OperationalParticipation ( -- Item 15
    participation_id SERIAL PRIMARY KEY,
    fdd_id INT NOT NULL REFERENCES FDD(fdd_id) ON DELETE CASCADE,
    personal_participation_required BOOLEAN,
    manager_requirements TEXT,
    absentee_ownership_allowed BOOLEAN,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS FDD_ProductServiceRestriction ( -- Item 16
    restriction_id SERIAL PRIMARY KEY,
    fdd_id INT NOT NULL REFERENCES FDD(fdd_id) ON DELETE CASCADE,
    restriction_summary TEXT, -- Limitations on goods/services
    customer_restrictions TEXT
);

CREATE TABLE IF NOT EXISTS FDD_AgreementTerm ( -- Item 17
    term_id SERIAL PRIMARY KEY,
    fdd_id INT NOT NULL REFERENCES FDD(fdd_id) ON DELETE CASCADE,
    term_length_years INT,
    renewal_term_years VARCHAR(50), -- Can be INT or text like 'N/A'
    renewal_conditions TEXT,
    termination_grounds_franchisor TEXT,
    termination_grounds_franchisee TEXT,
    post_termination_obligations TEXT,
    transfer_conditions TEXT,
    dispute_resolution TEXT
);

CREATE TABLE IF NOT EXISTS FDD_PublicFigureEndorsement ( -- Item 18
    endorsement_id SERIAL PRIMARY KEY,
    fdd_id INT NOT NULL REFERENCES FDD(fdd_id) ON DELETE CASCADE,
    figure_name VARCHAR(255),
    compensation TEXT,
    figure_investment TEXT
);

CREATE TABLE IF NOT EXISTS FDD_FinancialPerformanceMetric ( -- Item 19
    fpr_metric_id SERIAL PRIMARY KEY,
    fdd_id INT NOT NULL REFERENCES FDD(fdd_id) ON DELETE CASCADE,
    performance_year INT, -- The year(s) the data represents
    metric_name VARCHAR(255) NOT NULL, -- e.g., 'Average Gross Sales'
    value DECIMAL(18, 2), -- Increased precision for financials
    unit VARCHAR(50), -- e.g., 'USD', '%', 'Ratio'
    subset_description TEXT, -- e.g., 'Top 10%', 'Company-Owned'
    notes TEXT -- Footnotes, assumptions
);
-- Index for faster lookup by FDD and metric name
CREATE INDEX IF NOT EXISTS idx_fdd_fpr_metric_name ON FDD_FinancialPerformanceMetric (fdd_id, metric_name);

CREATE TABLE IF NOT EXISTS FDD_OutletData ( -- Item 20
    outlet_data_id SERIAL PRIMARY KEY,
    fdd_id INT NOT NULL REFERENCES FDD(fdd_id) ON DELETE CASCADE,
    data_year INT NOT NULL, -- Year the data represents
    state_or_region VARCHAR(50) NOT NULL DEFAULT 'USA', -- e.g., 'CA', 'USA', 'International'
    franchised_start_count INT,
    franchised_opened INT,
    franchised_terminated INT,
    franchised_non_renewed INT,
    franchised_reacquired INT,
    franchised_ceased INT,
    franchised_end_count INT,
    corporate_start_count INT,
    corporate_opened INT,
    corporate_closed INT,
    corporate_end_count INT,
    projected_openings_franchised INT,
    projected_openings_corporate INT,
    franchisee_list_available BOOLEAN,
    UNIQUE (fdd_id, data_year, state_or_region) -- Ensure one entry per region per year per FDD
);
-- Index for faster lookup by FDD and year/region
CREATE INDEX IF NOT EXISTS idx_fdd_outletdata_year_region ON FDD_OutletData (fdd_id, data_year, state_or_region);

CREATE TABLE IF NOT EXISTS FDD_ContractReference ( -- Item 22
    contract_ref_id SERIAL PRIMARY KEY,
    fdd_id INT NOT NULL REFERENCES FDD(fdd_id) ON DELETE CASCADE,
    contract_name VARCHAR(255) NOT NULL, -- e.g., 'Franchise Agreement'
    exhibit_letter VARCHAR(10) -- e.g., 'Exhibit A'
);

-- III. Platform Feature & User Tables (Not Directly FDD-Sourced)

CREATE TABLE IF NOT EXISTS FranchiseRanking (
    ranking_id SERIAL PRIMARY KEY,
    franchise_id INT NOT NULL REFERENCES Franchise(franchise_id) ON DELETE CASCADE,
    list_name VARCHAR(100) NOT NULL, -- e.g., 'Entrepreneur Franchise 500'
    year INT NOT NULL,
    rank INT,
    UNIQUE (franchise_id, list_name, year)
);

CREATE TABLE IF NOT EXISTS FranchiseFAQ (
    faq_id SERIAL PRIMARY KEY,
    franchise_id INT NOT NULL REFERENCES Franchise(franchise_id) ON DELETE CASCADE,
    question TEXT NOT NULL,
    answer TEXT
);

CREATE TABLE IF NOT EXISTS "User" ( -- Quoted "User" as it can be a reserved word
    user_id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL, -- Store hashed passwords only!
    role user_role_enum NOT NULL,
    date_registered TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- Index for faster email lookup (login)
CREATE INDEX IF NOT EXISTS idx_user_email ON "User" (email);

CREATE TABLE IF NOT EXISTS Lead (
    lead_id SERIAL PRIMARY KEY,
    franchise_id INT NOT NULL REFERENCES Franchise(franchise_id) ON DELETE CASCADE,
    user_id INT REFERENCES "User"(user_id) ON DELETE SET NULL, -- Allow anonymous leads
    name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    city VARCHAR(100),
    state VARCHAR(100),
    investment_budget VARCHAR(100),
    message TEXT,
    date_submitted TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- Index for faster lookup by franchise or user
CREATE INDEX IF NOT EXISTS idx_lead_franchise ON Lead (franchise_id);
CREATE INDEX IF NOT EXISTS idx_lead_user ON Lead (user_id);


CREATE TABLE IF NOT EXISTS Favorite (
    user_id INT NOT NULL REFERENCES "User"(user_id) ON DELETE CASCADE,
    franchise_id INT NOT NULL REFERENCES Franchise(franchise_id) ON DELETE CASCADE,
    date_favorited TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, franchise_id)
);

CREATE TABLE IF NOT EXISTS FranchisorAccount (
    franchisor_account_id SERIAL PRIMARY KEY,
    franchise_id INT UNIQUE NOT NULL REFERENCES Franchise(franchise_id) ON DELETE CASCADE,
    user_id INT UNIQUE NOT NULL REFERENCES "User"(user_id) ON DELETE CASCADE,
    contact_name VARCHAR(255),
    contact_email VARCHAR(255),
    verification_status verification_status_enum NOT NULL DEFAULT 'Pending'
);

CREATE TABLE IF NOT EXISTS Article (
    article_id SERIAL PRIMARY KEY,
    title VARCHAR(512) NOT NULL,
    content TEXT,
    author_id INT REFERENCES "User"(user_id) ON DELETE SET NULL,
    published_date DATE,
    category VARCHAR(100),
    slug VARCHAR(512) UNIQUE
);
-- Index for faster lookup by slug or category
CREATE INDEX IF NOT EXISTS idx_article_slug ON Article (slug);
CREATE INDEX IF NOT EXISTS idx_article_category ON Article (category);

"""

def create_database_schema():
    """Connects to the PostgreSQL database and executes the schema creation SQL."""
    conn = None
    cursor = None
    try:
        print(f"Connecting to database '{DB_NAME}' on {DB_HOST}:{DB_PORT}...")
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        conn.autocommit = False # Use transactions
        cursor = conn.cursor()

        print("Creating ENUM types (if they don't exist)...")
        cursor.execute(ENUM_DEFINITIONS)
        print("ENUM types checked/created.")

        print("Creating tables (if they don't exist)...")
        # Split statements in case one fails, though defining within transaction helps
        # For simplicity here, executing as one block. Consider splitting for large schemas.
        cursor.execute(TABLE_DEFINITIONS)
        print("Tables and indexes checked/created.")

        # Commit the transaction
        conn.commit()
        print("Schema creation successful!")

    except OperationalError as e:
        print(f"Database connection error: {e}")
        print("Please ensure the database server is running and connection details are correct.")
        print("Also, make sure you have run the manual setup steps (CREATE DATABASE, CREATE USER, GRANT PRIVILEGES).")
    except ProgrammingError as e:
        print(f"Database programming error: {e}")
        print("There might be an issue with the SQL syntax or permissions.")
        if conn:
            conn.rollback() # Rollback transaction on error
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        print("Database connection closed.")

if __name__ == "__main__":
    create_database_schema()