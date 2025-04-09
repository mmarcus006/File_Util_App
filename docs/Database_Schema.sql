-- Represents the financial institution
CREATE TABLE Institutions (
    institution_id INT IDENTITY(1,1) PRIMARY KEY,
    institution_name NVARCHAR(255) NOT NULL UNIQUE -- e.g., 'JPMorgan Chase', 'Morgan Stanley', 'Goldman Sachs'
);

-- Represents a single client account
CREATE TABLE Accounts (
    account_id INT IDENTITY(1,1) PRIMARY KEY,
    institution_id INT NOT NULL,
    account_number NVARCHAR(50) NOT NULL,
    account_holder_name NVARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT GETDATE(),
    CONSTRAINT UQ_Account_Institution UNIQUE (institution_id, account_number),
    CONSTRAINT FK_Account_Institution FOREIGN KEY (institution_id) REFERENCES Institutions(institution_id)
);
CREATE TABLE Statements (
    statement_id INT IDENTITY(1,1) PRIMARY KEY,
    account_id INT NOT NULL,
    statement_period_start_date DATE NOT NULL,
    statement_period_end_date DATE NOT NULL,
    beginning_market_value DECIMAL(18,2) NOT NULL,
    ending_market_value DECIMAL(18,2) NOT NULL,
    change_in_market_value DECIMAL(18,2),
    net_contributions_withdrawals_period DECIMAL(18,2),
    beginning_cash_balance DECIMAL(18,2),
    ending_cash_balance DECIMAL(18,2),
    generated_at DATETIME DEFAULT GETDATE(),
    CONSTRAINT UQ_Statement_Account_Period UNIQUE (account_id, statement_period_end_date),
    CONSTRAINT FK_Statement_Account FOREIGN KEY (account_id) REFERENCES Accounts(account_id)
);
-- CREATE INDEX idx_statement_account_period ON Statements (account_id, statement_period_end_date);


-- Tax summary information for a specific statement period
CREATE TABLE TaxSummary (
    tax_summary_id INT IDENTITY(1,1) PRIMARY KEY,
    statement_id INT NOT NULL,
    total_dividends_period DECIMAL(18,2),
    total_dividends_ytd DECIMAL(18,2),
    total_taxable_interest_period DECIMAL(18,2),
    total_taxable_interest_ytd DECIMAL(18,2),
    total_tax_exempt_interest_period DECIMAL(18,2),
    total_tax_exempt_interest_ytd DECIMAL(18,2),
    total_realized_gain_loss_period DECIMAL(18,2),
    total_realized_gain_loss_ytd DECIMAL(18,2),
    total_realized_st_gain_loss_period DECIMAL(18,2),
    total_realized_st_gain_loss_ytd DECIMAL(18,2),
    total_realized_lt_gain_loss_period DECIMAL(18,2),
    total_realized_lt_gain_loss_ytd DECIMAL(18,2),
    CONSTRAINT UQ_TaxSummary_Statement UNIQUE (statement_id),
    CONSTRAINT FK_TaxSummary_Statement FOREIGN KEY (statement_id) REFERENCES Statements(statement_id)
);


-- Lookup table for asset classes
CREATE TABLE AssetClasses (
    asset_class_id INT IDENTITY(1,1) PRIMARY KEY,
    asset_class_name NVARCHAR(100) NOT NULL UNIQUE
);

-- Master table for securities
CREATE TABLE Securities (
    security_id INT IDENTITY(1,1) PRIMARY KEY,
    cusip NVARCHAR(9) UNIQUE,
    ticker_symbol NVARCHAR(10),
    security_description NVARCHAR(255) NOT NULL,
    asset_class_id INT,
    issuer_name NVARCHAR(255),
    coupon_rate DECIMAL(5,2),
    maturity_date DATE,
    CONSTRAINT FK_Security_AssetClass FOREIGN KEY (asset_class_id) REFERENCES AssetClasses(asset_class_id)
    -- Indexes added separately
);
-- CREATE INDEX idx_security_cusip ON Securities (cusip);
-- CREATE INDEX idx_security_ticker ON Securities (ticker_symbol);


-- Holdings snapshot for a specific statement
CREATE TABLE Holdings (
    holding_id INT IDENTITY(1,1) PRIMARY KEY,
    statement_id INT NOT NULL,
    security_id INT NOT NULL,
    quantity DECIMAL(18,6) NOT NULL,
    market_price DECIMAL(18,2) NOT NULL,
    market_value DECIMAL(18,2) NOT NULL,
    adjusted_cost_basis DECIMAL(18,2),
    unrealized_gain_loss DECIMAL(18,2),
    unrealized_gain_loss_term NVARCHAR(10),
    estimated_annual_income DECIMAL(18,2),
    current_yield DECIMAL(5,2),
    accrued_interest DECIMAL(18,2),
    CONSTRAINT FK_Holding_Statement FOREIGN KEY (statement_id) REFERENCES Statements(statement_id),
    CONSTRAINT FK_Holding_Security FOREIGN KEY (security_id) REFERENCES Securities(security_id)
    -- Index added separately
);
-- CREATE INDEX idx_holding_statement_security ON Holdings (statement_id, security_id);


-- Lookup table for transaction types
CREATE TABLE TransactionTypes (
    transaction_type_id INT IDENTITY(1,1) PRIMARY KEY,
    transaction_type_name NVARCHAR(50) NOT NULL UNIQUE
);

-- Individual transactions during the statement period
CREATE TABLE Transactions (
    transaction_id INT IDENTITY(1,1) PRIMARY KEY,
    statement_id INT NOT NULL,
    security_id INT,
    transaction_type_id INT NOT NULL,
    transaction_date DATE NOT NULL,
    settlement_date DATE,
    quantity DECIMAL(18,6),
    price_per_unit DECIMAL(18,2),
    net_amount DECIMAL(18,2) NOT NULL,
    realized_gain_loss DECIMAL(18,2),
    realized_gain_loss_term NVARCHAR(10),
    description_notes NVARCHAR(MAX),
    CONSTRAINT FK_Transaction_Statement FOREIGN KEY (statement_id) REFERENCES Statements(statement_id),
    CONSTRAINT FK_Transaction_Security FOREIGN KEY (security_id) REFERENCES Securities(security_id),
    CONSTRAINT FK_Transaction_Type FOREIGN KEY (transaction_type_id) REFERENCES TransactionTypes(transaction_type_id)
    -- Index added separately
);
-- CREATE INDEX idx_transaction_statement_date ON Transactions (statement_id, transaction_date);