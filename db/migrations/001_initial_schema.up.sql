-- Tax God — Initial Schema Migration (all 28 tables)

CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) NOT NULL DEFAULT 'client',
    is_active BOOLEAN NOT NULL DEFAULT 1,
    is_verified BOOLEAN NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS accounts (
    id VARCHAR(36) PRIMARY KEY,
    owner_id VARCHAR(36) NOT NULL REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    account_type VARCHAR(50) NOT NULL,
    provider VARCHAR(255),
    account_number_last4 VARCHAR(4),
    currency VARCHAR(10) NOT NULL DEFAULT 'USD',
    balance FLOAT NOT NULL DEFAULT 0,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    notes TEXT,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS activity_logs (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36),
    category VARCHAR(50) NOT NULL,
    action VARCHAR(200) NOT NULL,
    detail TEXT,
    metadata_json JSON,
    ip_address VARCHAR(50),
    created_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_events (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id),
    action VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(36),
    changes TEXT,
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    created_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS bank_connections (
    id VARCHAR(36) PRIMARY KEY,
    owner_id VARCHAR(36) NOT NULL REFERENCES users(id),
    institution_name VARCHAR(200) NOT NULL,
    account_name VARCHAR(200) NOT NULL,
    account_mask VARCHAR(4) NOT NULL,
    plaid_access_token VARCHAR(500) NOT NULL,
    plaid_item_id VARCHAR(200) NOT NULL,
    last_synced DATETIME,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS build_logs (
    id VARCHAR(36) PRIMARY KEY,
    agent_name VARCHAR(100) NOT NULL,
    commit_sha VARCHAR(40),
    action VARCHAR(200) NOT NULL,
    files_changed JSON,
    detail TEXT,
    created_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS businesses (
    id VARCHAR(36) PRIMARY KEY,
    owner_id VARCHAR(36) NOT NULL REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    business_type VARCHAR(50) NOT NULL,
    ein VARCHAR(20),
    address TEXT,
    currency VARCHAR(10) NOT NULL DEFAULT 'USD',
    fiscal_year_start VARCHAR(10) NOT NULL DEFAULT '01-01',
    is_default BOOLEAN NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS chart_of_accounts (
    id VARCHAR(36) PRIMARY KEY,
    owner_id VARCHAR(36) NOT NULL REFERENCES users(id),
    business_id VARCHAR(36) REFERENCES businesses(id),
    code VARCHAR(20) NOT NULL,
    name VARCHAR(255) NOT NULL,
    account_type VARCHAR(20) NOT NULL,
    parent_id VARCHAR(36) REFERENCES chart_of_accounts(id),
    description TEXT,
    balance FLOAT NOT NULL DEFAULT 0.0,
    created_at DATETIME
);

CREATE TABLE IF NOT EXISTS client_assignments (
    id VARCHAR(36) PRIMARY KEY,
    client_id VARCHAR(36) NOT NULL REFERENCES clients(id),
    preparer_id VARCHAR(36) NOT NULL REFERENCES users(id),
    assigned_by VARCHAR(36) NOT NULL REFERENCES users(id),
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    assigned_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS clients (
    id VARCHAR(36) PRIMARY KEY,
    owner_id VARCHAR(36) NOT NULL REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    company VARCHAR(255),
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    notes TEXT,
    invite_code VARCHAR(50),
    tax_id VARCHAR(50),
    filing_type VARCHAR(50),
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS expenses (
    id VARCHAR(36) PRIMARY KEY,
    owner_id VARCHAR(36) NOT NULL REFERENCES users(id),
    business_id VARCHAR(36) REFERENCES businesses(id),
    date DATETIME NOT NULL,
    vendor VARCHAR(255) NOT NULL,
    amount FLOAT NOT NULL,
    category VARCHAR(100) NOT NULL,
    description TEXT,
    receipt_url VARCHAR(500),
    tax_deductible BOOLEAN NOT NULL DEFAULT 1,
    account_id VARCHAR(36) REFERENCES accounts(id),
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS integration_credentials (
    user_id VARCHAR(36) NOT NULL,
    provider VARCHAR(100) NOT NULL,
    payload_encrypted TEXT NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    PRIMARY KEY (user_id, provider)
);

CREATE TABLE IF NOT EXISTS invoices (
    id VARCHAR(36) PRIMARY KEY,
    owner_id VARCHAR(36) NOT NULL REFERENCES users(id),
    client_id VARCHAR(36) REFERENCES clients(id),
    invoice_number VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    amount FLOAT NOT NULL,
    tax_amount FLOAT NOT NULL DEFAULT 0,
    currency VARCHAR(10) NOT NULL DEFAULT 'USD',
    due_date DATETIME,
    paid_date DATETIME,
    items TEXT,
    notes TEXT,
    recurring BOOLEAN NOT NULL DEFAULT 0,
    recurring_frequency VARCHAR(20),
    recurring_next_date DATETIME,
    stripe_payment_intent_id VARCHAR(255),
    payment_link VARCHAR(500),
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS journal_entries (
    id VARCHAR(36) PRIMARY KEY,
    owner_id VARCHAR(36) NOT NULL REFERENCES users(id),
    business_id VARCHAR(36) REFERENCES businesses(id),
    date DATETIME NOT NULL,
    description VARCHAR(500) NOT NULL,
    reference VARCHAR(100),
    created_at DATETIME
);

CREATE TABLE IF NOT EXISTS journal_lines (
    id VARCHAR(36) PRIMARY KEY,
    entry_id VARCHAR(36) NOT NULL REFERENCES journal_entries(id),
    account_id VARCHAR(36) NOT NULL REFERENCES chart_of_accounts(id),
    debit FLOAT NOT NULL DEFAULT 0.0,
    credit FLOAT NOT NULL DEFAULT 0.0,
    memo VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS knowledge_entries (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36),
    category VARCHAR(50) NOT NULL,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    source VARCHAR(200),
    tags JSON,
    version INTEGER NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS notes (
    id VARCHAR(36) PRIMARY KEY,
    owner_id VARCHAR(36) NOT NULL REFERENCES users(id),
    client_id VARCHAR(36) REFERENCES clients(id),
    project_id VARCHAR(36) REFERENCES projects(id),
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    tags VARCHAR(500),
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS portal_messages (
    id VARCHAR(36) PRIMARY KEY,
    client_id VARCHAR(36) NOT NULL REFERENCES clients(id),
    sender VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    created_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS projects (
    id VARCHAR(36) PRIMARY KEY,
    owner_id VARCHAR(36) NOT NULL REFERENCES users(id),
    client_id VARCHAR(36) REFERENCES clients(id),
    name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    budget FLOAT,
    spent FLOAT NOT NULL DEFAULT 0,
    start_date DATETIME,
    end_date DATETIME,
    description TEXT,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS settings_audit_log (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    key_name VARCHAR(255) NOT NULL,
    action VARCHAR(50) NOT NULL,
    old_value_hash TEXT,
    new_value_hash TEXT,
    timestamp DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS spreadsheets (
    id VARCHAR(36) PRIMARY KEY,
    owner_id VARCHAR(36) NOT NULL REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    sheet_type VARCHAR(50) NOT NULL,
    data TEXT,
    notes TEXT,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS subscriptions (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) UNIQUE NOT NULL REFERENCES users(id),
    tier VARCHAR(50) NOT NULL DEFAULT 'free_trial',
    status VARCHAR(50) NOT NULL DEFAULT 'trialing',
    stripe_customer_id VARCHAR(255),
    stripe_subscription_id VARCHAR(255),
    trial_ends_at DATETIME,
    current_period_end DATETIME,
    cancel_at_period_end BOOLEAN NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS team_members (
    id VARCHAR(36) PRIMARY KEY,
    team_id VARCHAR(36) NOT NULL REFERENCES teams(id),
    user_id VARCHAR(36) NOT NULL REFERENCES users(id),
    role VARCHAR(50) NOT NULL DEFAULT 'preparer',
    joined_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS teams (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    owner_id VARCHAR(36) NOT NULL REFERENCES users(id),
    created_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS time_entries (
    id VARCHAR(36) PRIMARY KEY,
    owner_id VARCHAR(36) NOT NULL REFERENCES users(id),
    project_id VARCHAR(36) REFERENCES projects(id),
    client_id VARCHAR(36) REFERENCES clients(id),
    description VARCHAR(500) NOT NULL,
    hours FLOAT NOT NULL,
    date DATETIME NOT NULL,
    billable BOOLEAN NOT NULL DEFAULT 1,
    rate FLOAT,
    invoiced BOOLEAN NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS transactions (
    id VARCHAR(36) PRIMARY KEY,
    owner_id VARCHAR(36) NOT NULL REFERENCES users(id),
    account_id VARCHAR(36) NOT NULL REFERENCES accounts(id),
    date DATETIME NOT NULL,
    description VARCHAR(500) NOT NULL,
    amount FLOAT NOT NULL,
    category VARCHAR(100),
    reconciled BOOLEAN NOT NULL DEFAULT 0,
    expense_id VARCHAR(36) REFERENCES expenses(id),
    invoice_id VARCHAR(36) REFERENCES invoices(id),
    source VARCHAR(50) NOT NULL,
    created_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS user_settings (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) UNIQUE NOT NULL REFERENCES users(id),
    theme VARCHAR(20) NOT NULL DEFAULT 'system',
    notifications_enabled BOOLEAN NOT NULL DEFAULT 1,
    default_model VARCHAR(100) NOT NULL DEFAULT 'gpt-4o',
    timezone VARCHAR(50) NOT NULL DEFAULT 'UTC',
    settings_json TEXT,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS vendors (
    id VARCHAR(36) PRIMARY KEY,
    owner_id VARCHAR(36) NOT NULL REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    company VARCHAR(255),
    category VARCHAR(100) NOT NULL,
    tax_id VARCHAR(50),
    is_1099 BOOLEAN NOT NULL DEFAULT 0,
    total_paid FLOAT NOT NULL DEFAULT 0,
    notes TEXT,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);
