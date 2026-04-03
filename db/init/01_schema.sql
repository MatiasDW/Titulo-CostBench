-- CostBench – Complete Database Init Script
-- This runs automatically on a fresh `docker compose up` when db/data is empty.
-- It creates ALL tables needed for the application.
--
-- For existing databases, use the individual migration files in db/migrations/
-- applied in order: 001 → 002 → 003 → 004

BEGIN;

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- Core Tables
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CREATE TABLE IF NOT EXISTS ranking (
    id SERIAL PRIMARY KEY,
    process_date DATE NOT NULL,
    institution VARCHAR(255) NOT NULL,
    product VARCHAR(255) NOT NULL,
    cost_clp NUMERIC(12, 2),
    cost_uf NUMERIC(12, 4),
    cost_usd NUMERIC(12, 2),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT ranking_process_institution_product_uk UNIQUE (process_date, institution, product)
);

CREATE TABLE IF NOT EXISTS macro_indicators (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    series_id VARCHAR(50) NOT NULL,
    value NUMERIC(10, 4),
    source VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT macro_indicators_date_series_id_uk UNIQUE (date, series_id)
);

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- Users & Auth (from migration 003 + 004)
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CREATE TABLE IF NOT EXISTS users (
    id          SERIAL PRIMARY KEY,
    email       VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role        VARCHAR(20) NOT NULL DEFAULT 'user' CHECK (role IN ('admin', 'user')),
    risk_profile VARCHAR(20) CHECK (risk_profile IN ('conservative', 'moderate', 'aggressive')),
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    interests   TEXT[] DEFAULT '{}',
    onboarding_completed BOOLEAN NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Case-insensitive unique email index
CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (LOWER(email));

-- Auto-update updated_at on row change
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_users_updated_at ON users;
CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- Real Estate Quant Metrics
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CREATE TABLE IF NOT EXISTS real_estate_metrics (
    id SERIAL PRIMARY KEY,
    comuna VARCHAR(100) NOT NULL,
    segment_type VARCHAR(50) NOT NULL,
    uf_m2 NUMERIC(10, 2) NOT NULL,
    gross_cap_rate NUMERIC(6, 4) NOT NULL,
    net_cap_rate NUMERIC(6, 4) NOT NULL,
    vacancy_rate NUMERIC(6, 4) NOT NULL,
    days_on_market INTEGER NOT NULL,
    run_date TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- Indexes
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CREATE INDEX IF NOT EXISTS idx_ranking_date ON ranking(process_date);
CREATE INDEX IF NOT EXISTS idx_ranking_inst_date ON ranking(institution, process_date);
CREATE INDEX IF NOT EXISTS idx_macro_lookup ON macro_indicators(series_id, date);
CREATE INDEX IF NOT EXISTS idx_real_estate_metrics_comuna ON real_estate_metrics(comuna);
CREATE INDEX IF NOT EXISTS idx_real_estate_metrics_run_date ON real_estate_metrics(run_date DESC);

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- Seed: Default Admin User
-- Email:    admin@costbench.cl
-- Password: CostBench2025!
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

INSERT INTO users (email, password_hash, role, is_active, onboarding_completed)
VALUES (
    'admin@costbench.cl',
    '$2b$12$4uA6kLg9Tk53QdN1GmOtH.TgYAJUi2cGw1AEnAzAXUJucz9jKz8oa',
    'admin',
    TRUE,
    TRUE
)
ON CONFLICT ((LOWER(email))) DO NOTHING;

COMMIT;
