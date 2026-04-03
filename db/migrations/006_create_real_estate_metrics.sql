-- 006_create_real_estate_metrics.sql
-- Adds storage for Real Estate quant metrics used by /api/v1/real-estate/*

BEGIN;

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

CREATE INDEX IF NOT EXISTS idx_real_estate_metrics_comuna
    ON real_estate_metrics (comuna);

CREATE INDEX IF NOT EXISTS idx_real_estate_metrics_run_date
    ON real_estate_metrics (run_date DESC);

COMMIT;
