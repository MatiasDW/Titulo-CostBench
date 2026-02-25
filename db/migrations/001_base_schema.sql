-- 001_base_schema.sql
-- Creates core tables for CostBench in a fresh environment.
-- Idempotent for new installs; existing tables are left untouched.

BEGIN;

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

-- Indexes
CREATE INDEX IF NOT EXISTS idx_ranking_date ON ranking(process_date);
CREATE INDEX IF NOT EXISTS idx_ranking_inst_date ON ranking(institution, process_date);
CREATE INDEX IF NOT EXISTS idx_macro_lookup ON macro_indicators(series_id, date);

COMMIT;
