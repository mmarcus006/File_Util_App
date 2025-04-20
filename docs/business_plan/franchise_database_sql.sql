-- PostgreSQL Database Schema for Franchise Directory
-- Based on prioritized data fields from previous analysis

-- Industries lookup table
CREATE TABLE industries (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create index on industry name for quick lookups
CREATE INDEX idx_industries_name ON industries(name);

-- Franchisors table (core information)
CREATE TABLE franchisors (
    id SERIAL PRIMARY KEY,
    brand_name VARCHAR(100) NOT NULL,
    legal_name VARCHAR(150) NOT NULL,
    slug VARCHAR(100) NOT NULL UNIQUE,
    industry_id INT REFERENCES industries(id),
    parent_company_id INT REFERENCES franchisors(id),
    headquarters_address VARCHAR(200),
    headquarters_city VARCHAR(100),
    headquarters_state VARCHAR(50),
    headquarters_zip VARCHAR(20),
    headquarters_country VARCHAR(50) DEFAULT 'USA',
    phone_number VARCHAR(30),
    website_url VARCHAR(200),
    email_contact VARCHAR(100),
    year_founded INT,
    year_franchising_began INT,
    business_description TEXT,
    description_summary VARCHAR(500),
    company_history TEXT,
    logo_url VARCHAR(255),
    business_type VARCHAR(50),
    business_model VARCHAR(50),
    social_media_facebook VARCHAR(255),
    social_media_twitter VARCHAR(255),
    social_media_instagram VARCHAR(255),
    social_media_linkedin VARCHAR(255),
    franchise_500_rank INT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for common search fields
CREATE INDEX idx_franchisors_brand_name ON franchisors(brand_name);
CREATE INDEX idx_franchisors_slug ON franchisors(slug);
CREATE INDEX idx_franchisors_industry_id ON franchisors(industry_id);
CREATE INDEX idx_franchisors_year_founded ON franchisors(year_founded);
CREATE INDEX idx_franchisors_year_franchising_began ON franchisors(year_franchising_began);

-- FDDs table (metadata for Franchise Disclosure Documents)
CREATE TABLE fdds (
    id SERIAL PRIMARY KEY,
    franchisor_id INT NOT NULL REFERENCES franchisors(id),
    year INT NOT NULL,
    effective_date DATE,
    state_filed VARCHAR(50),
    pdf_url VARCHAR(255),
    huridocs_json_url VARCHAR(255),
    section_map_url VARCHAR(255),
    extraction_status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(franchisor_id, year)
);

-- Create indexes for FDD lookups
CREATE INDEX idx_fdds_franchisor_id ON fdds(franchisor_id);
CREATE INDEX idx_fdds_year ON fdds(year);
CREATE INDEX idx_fdds_effective_date ON fdds(effective_date);

-- Fees table (time-series data for various fee types)
CREATE TABLE fees (
    id SERIAL PRIMARY KEY,
    fdd_id INT NOT NULL REFERENCES fdds(id),
    fee_type VARCHAR(50) NOT NULL,
    fee_structure_description TEXT,
    low_amount DECIMAL(12,2),
    high_amount DECIMAL(12,2),
    percentage DECIMAL(5,2),
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for fee lookups
CREATE INDEX idx_fees_fdd_id ON fees(fdd_id);
CREATE INDEX idx_fees_fee_type ON fees(fee_type);

-- Investments table (time-series data for investment categories)
CREATE TABLE investments (
    id SERIAL PRIMARY KEY,
    fdd_id INT NOT NULL REFERENCES fdds(id),
    investment_category VARCHAR(100) NOT NULL,
    low_estimate DECIMAL(12,2),
    high_estimate DECIMAL(12,2),
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for investment lookups
CREATE INDEX idx_investments_fdd_id ON investments(fdd_id);
CREATE INDEX idx_investments_category ON investments(investment_category);

-- Units history table (time-series data for franchise unit counts)
CREATE TABLE units_history (
    id SERIAL PRIMARY KEY,
    fdd_id INT NOT NULL REFERENCES fdds(id),
    year_covered INT NOT NULL,
    type VARCHAR(50) NOT NULL,
    outlets_start_year INT,
    outlets_opened INT,
    outlets_terminated INT,
    outlets_non_renewed INT,
    outlets_reacquired INT,
    outlets_ceased_other INT,
    outlets_end_year INT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for units history lookups
CREATE INDEX idx_units_history_fdd_id ON units_history(fdd_id);
CREATE INDEX idx_units_history_year_covered ON units_history(year_covered);
CREATE INDEX idx_units_history_type ON units_history(type);

-- Franchisor requirements table (time-series data for franchisee requirements)
CREATE TABLE franchisor_requirements (
    id SERIAL PRIMARY KEY,
    fdd_id INT NOT NULL REFERENCES fdds(id),
    net_worth_requirement DECIMAL(12,2),
    liquid_capital_requirement DECIMAL(12,2),
    experience_required BOOLEAN,
    experience_description TEXT,
    owner_operator_required BOOLEAN,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create index for requirements lookups
CREATE INDEX idx_franchisor_requirements_fdd_id ON franchisor_requirements(fdd_id);

-- Territory information table
CREATE TABLE territory_info (
    id SERIAL PRIMARY KEY,
    fdd_id INT NOT NULL REFERENCES fdds(id),
    exclusive_territory BOOLEAN,
    territory_size TEXT,
    territory_population TEXT,
    territory_protection TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create index for territory lookups
CREATE INDEX idx_territory_info_fdd_id ON territory_info(fdd_id);

-- Financial performance representations (Item 19) summary
CREATE TABLE fpr_summary (
    id SERIAL PRIMARY KEY,
    fdd_id INT NOT NULL REFERENCES fdds(id),
    has_item_19 BOOLEAN NOT NULL,
    average_unit_revenue DECIMAL(12,2),
    median_unit_revenue DECIMAL(12,2),
    average_unit_profit DECIMAL(12,2),
    top_quartile_revenue DECIMAL(12,2),
    bottom_quartile_revenue DECIMAL(12,2),
    summary_text TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create index for FPR lookups
CREATE INDEX idx_fpr_summary_fdd_id ON fpr_summary(fdd_id);
CREATE INDEX idx_fpr_summary_has_item_19 ON fpr_summary(has_item_19);

-- Key personnel table
CREATE TABLE key_personnel (
    id SERIAL PRIMARY KEY,
    franchisor_id INT NOT NULL REFERENCES franchisors(id),
    name VARCHAR(100) NOT NULL,
    title VARCHAR(100) NOT NULL,
    bio TEXT,
    is_sales_contact BOOLEAN DEFAULT FALSE,
    contact_email VARCHAR(100),
    contact_phone VARCHAR(30),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for personnel lookups
CREATE INDEX idx_key_personnel_franchisor_id ON key_personnel(franchisor_id);
CREATE INDEX idx_key_personnel_is_sales_contact ON key_personnel(is_sales_contact);

-- Legal information table
CREATE TABLE legal_info (
    id SERIAL PRIMARY KEY,
    fdd_id INT NOT NULL REFERENCES fdds(id),
    agreement_term INT,
    renewal_terms TEXT,
    litigation_history TEXT,
    bankruptcy_history TEXT,
    trademark_info TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create index for legal info lookups
CREATE INDEX idx_legal_info_fdd_id ON legal_info(fdd_id);

-- Media assets table
CREATE TABLE media_assets (
    id SERIAL PRIMARY KEY,
    franchisor_id INT NOT NULL REFERENCES franchisors(id),
    asset_type VARCHAR(50) NOT NULL,
    url VARCHAR(255) NOT NULL,
    title VARCHAR(100),
    description TEXT,
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for media lookups
CREATE INDEX idx_media_assets_franchisor_id ON media_assets(franchisor_id);
CREATE INDEX idx_media_assets_asset_type ON media_assets(asset_type);
CREATE INDEX idx_media_assets_is_primary ON media_assets(is_primary);

-- Website metadata table
CREATE TABLE website_metadata (
    id SERIAL PRIMARY KEY,
    franchisor_id INT NOT NULL REFERENCES franchisors(id),
    profile_creation_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    profile_last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    profile_verified BOOLEAN DEFAULT FALSE,
    profile_claimed BOOLEAN DEFAULT FALSE,
    profile_views INT DEFAULT 0,
    inquiry_count INT DEFAULT 0,
    featured_status BOOLEAN DEFAULT FALSE,
    search_keywords TEXT,
    profile_completeness INT DEFAULT 0,
    data_sources TEXT
);

-- Create indexes for website metadata lookups
CREATE INDEX idx_website_metadata_franchisor_id ON website_metadata(franchisor_id);
CREATE INDEX idx_website_metadata_profile_verified ON website_metadata(profile_verified);
CREATE INDEX idx_website_metadata_featured_status ON website_metadata(featured_status);

-- User reviews table
CREATE TABLE user_reviews (
    id SERIAL PRIMARY KEY,
    franchisor_id INT NOT NULL REFERENCES franchisors(id),
    user_id INT NOT NULL,
    rating INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    review_text TEXT,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for review lookups
CREATE INDEX idx_user_reviews_franchisor_id ON user_reviews(franchisor_id);
CREATE INDEX idx_user_reviews_user_id ON user_reviews(user_id);
CREATE INDEX idx_user_reviews_rating ON user_reviews(rating);

-- User questions table
CREATE TABLE user_questions (
    id SERIAL PRIMARY KEY,
    franchisor_id INT NOT NULL REFERENCES franchisors(id),
    user_id INT NOT NULL,
    question TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for question lookups
CREATE INDEX idx_user_questions_franchisor_id ON user_questions(franchisor_id);

-- Franchisor responses to questions
CREATE TABLE franchisor_responses (
    id SERIAL PRIMARY KEY,
    question_id INT NOT NULL REFERENCES user_questions(id),
    response TEXT NOT NULL,
    responder_name VARCHAR(100),
    responder_title VARCHAR(100),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create index for response lookups
CREATE INDEX idx_franchisor_responses_question_id ON franchisor_responses(question_id);

-- Comparison metrics table (calculated values)
CREATE TABLE comparison_metrics (
    id SERIAL PRIMARY KEY,
    franchisor_id INT NOT NULL REFERENCES franchisors(id),
    year INT NOT NULL,
    investment_to_sales_ratio DECIMAL(10,2),
    cost_per_square_foot DECIMAL(10,2),
    roi_estimate DECIMAL(10,2),
    breakeven_estimate INT,
    industry_rank INT,
    growth_rank INT,
    investment_tier VARCHAR(50),
    success_score DECIMAL(5,2),
    competitive_saturation VARCHAR(50),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(franchisor_id, year)
);

-- Create indexes for comparison metrics lookups
CREATE INDEX idx_comparison_metrics_franchisor_id ON comparison_metrics(franchisor_id);
CREATE INDEX idx_comparison_metrics_year ON comparison_metrics(year);
CREATE INDEX idx_comparison_metrics_investment_tier ON comparison_metrics(investment_tier);
