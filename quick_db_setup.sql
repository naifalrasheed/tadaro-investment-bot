-- Quick Database Setup for Tadaro.ai Investment Bot
-- Run this directly in PostgreSQL to create the database schema

-- Connect to PostgreSQL:
-- psql -h db-tradaro-ai.cmp4q2awn0qu.us-east-1.rds.amazonaws.com -p 5432 -U naif_alrasheed -d postgres

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(200),
    google_id VARCHAR(50),
    has_completed_profiling BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Feature weights table
CREATE TABLE IF NOT EXISTS feature_weights (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    feature_name VARCHAR(100) NOT NULL,
    weight DECIMAL(5,4) NOT NULL DEFAULT 1.0000,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Stock preferences table
CREATE TABLE IF NOT EXISTS stock_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    symbol VARCHAR(10) NOT NULL,
    preference_type VARCHAR(20) NOT NULL,
    preference_score DECIMAL(5,4) DEFAULT 0.0000,
    feedback_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    analysis_data JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Portfolios table
CREATE TABLE IF NOT EXISTS portfolios (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    holdings JSON NOT NULL,
    total_value DECIMAL(15,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Stock analysis table
CREATE TABLE IF NOT EXISTS stock_analysis (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    symbol VARCHAR(10) NOT NULL,
    analysis_type VARCHAR(50) NOT NULL,
    analysis_data JSON NOT NULL,
    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User bias profiles table (CFA integration)
CREATE TABLE IF NOT EXISTS user_bias_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    bias_type VARCHAR(100) NOT NULL,
    bias_score DECIMAL(5,2) NOT NULL,
    detection_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    mitigation_strategy TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Investment decisions table
CREATE TABLE IF NOT EXISTS investment_decisions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    symbol VARCHAR(10) NOT NULL,
    decision_type VARCHAR(20) NOT NULL,
    amount DECIMAL(15,2),
    reasoning TEXT,
    biases_detected JSON,
    decision_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User risk profiles table
CREATE TABLE IF NOT EXISTS user_risk_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    risk_tolerance VARCHAR(20) NOT NULL,
    time_horizon INTEGER NOT NULL,
    investment_experience VARCHAR(20) NOT NULL,
    financial_situation VARCHAR(20) NOT NULL,
    profile_data JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_feature_weights_user ON feature_weights(user_id);
CREATE INDEX IF NOT EXISTS idx_stock_preferences_user ON stock_preferences(user_id);
CREATE INDEX IF NOT EXISTS idx_stock_preferences_symbol ON stock_preferences(symbol);
CREATE INDEX IF NOT EXISTS idx_portfolios_user ON portfolios(user_id);
CREATE INDEX IF NOT EXISTS idx_stock_analysis_user ON stock_analysis(user_id);
CREATE INDEX IF NOT EXISTS idx_stock_analysis_symbol ON stock_analysis(symbol);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO naif_alrasheed;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO naif_alrasheed;

-- Verify setup
SELECT 'Database schema created successfully!' AS status;