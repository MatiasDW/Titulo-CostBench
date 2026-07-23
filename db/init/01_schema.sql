-- CostBench – Complete Database Init Script
-- This runs automatically on a fresh `docker compose up` when db/data is empty.
-- It creates ALL tables needed for the application.
--
-- For existing databases, use the individual migration files in db/migrations/
-- applied in order: 001 → 002 → 003 → 004

BEGIN;

CREATE EXTENSION IF NOT EXISTS vector;

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
-- Scloda Observability & Knowledge Cache
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CREATE TABLE IF NOT EXISTS scloda_traces (
    id SERIAL PRIMARY KEY,
    trace_id VARCHAR(36) NOT NULL UNIQUE,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    request_kind VARCHAR(32) NOT NULL DEFAULT 'chat',
    task_type VARCHAR(40),
    user_message TEXT NOT NULL,
    response_text TEXT,
    history_count INTEGER NOT NULL DEFAULT 0,
    screening_reason VARCHAR(64),
    guardrail_action VARCHAR(64),
    response_status VARCHAR(32) NOT NULL DEFAULT 'ok',
    confidence VARCHAR(16),
    error_code VARCHAR(120),
    model_requested VARCHAR(120),
    model_resolved VARCHAR(120),
    embedding_model VARCHAR(120),
    judge_model VARCHAR(120),
    tools_used JSONB NOT NULL DEFAULT '[]'::jsonb,
    tool_payloads JSONB NOT NULL DEFAULT '[]'::jsonb,
    retrieved_chunks JSONB NOT NULL DEFAULT '[]'::jsonb,
    judge_summary JSONB,
    prompt_tokens INTEGER NOT NULL DEFAULT 0,
    completion_tokens INTEGER NOT NULL DEFAULT 0,
    total_tokens INTEGER NOT NULL DEFAULT 0,
    latency_ms INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS scloda_knowledge_chunks (
    id SERIAL PRIMARY KEY,
    source_kind VARCHAR(50) NOT NULL,
    source_key VARCHAR(140) NOT NULL,
    title VARCHAR(255) NOT NULL,
    chunk_index INTEGER NOT NULL DEFAULT 0,
    content TEXT NOT NULL,
    content_hash VARCHAR(64) NOT NULL UNIQUE,
    token_estimate INTEGER NOT NULL DEFAULT 0,
    embedding JSONB,
    embedding_vector vector(1536),
    embedding_model VARCHAR(120),
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    indexed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS scloda_review_queue (
    id SERIAL PRIMARY KEY,
    trace_id VARCHAR(36) NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    status VARCHAR(24) NOT NULL DEFAULT 'pending',
    priority VARCHAR(16) NOT NULL DEFAULT 'medium',
    reason VARCHAR(80) NOT NULL,
    task_type VARCHAR(40),
    model_resolved VARCHAR(120),
    assignee_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    assignment_note TEXT,
    assigned_at TIMESTAMPTZ,
    notification_status VARCHAR(24) NOT NULL DEFAULT 'queued',
    notification_channel VARCHAR(24) NOT NULL DEFAULT 'in_app',
    notification_sent_at TIMESTAMPTZ,
    user_message TEXT NOT NULL,
    agent_response TEXT,
    reviewer_notes TEXT,
    resolution_summary TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS scloda_capability_nodes (
    id SERIAL PRIMARY KEY,
    slug VARCHAR(80) NOT NULL UNIQUE,
    parent_slug VARCHAR(80),
    label VARCHAR(160) NOT NULL,
    domain VARCHAR(60) NOT NULL,
    status VARCHAR(24) NOT NULL DEFAULT 'planned',
    maturity_score INTEGER NOT NULL DEFAULT 0,
    description TEXT NOT NULL,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- Indexes
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CREATE INDEX IF NOT EXISTS idx_ranking_date ON ranking(process_date);
CREATE INDEX IF NOT EXISTS idx_ranking_inst_date ON ranking(institution, process_date);
CREATE INDEX IF NOT EXISTS idx_macro_lookup ON macro_indicators(series_id, date);
CREATE INDEX IF NOT EXISTS idx_real_estate_metrics_comuna ON real_estate_metrics(comuna);
CREATE INDEX IF NOT EXISTS idx_real_estate_metrics_run_date ON real_estate_metrics(run_date DESC);
CREATE INDEX IF NOT EXISTS idx_scloda_traces_created_at ON scloda_traces(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_scloda_traces_status ON scloda_traces(response_status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_scloda_traces_task_type ON scloda_traces(task_type, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_scloda_knowledge_source ON scloda_knowledge_chunks(source_kind, source_key);
CREATE INDEX IF NOT EXISTS idx_scloda_knowledge_indexed_at ON scloda_knowledge_chunks(indexed_at DESC);
CREATE INDEX IF NOT EXISTS idx_scloda_knowledge_embedding_hnsw ON scloda_knowledge_chunks USING hnsw (embedding_vector vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_scloda_review_status ON scloda_review_queue(status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_scloda_review_trace ON scloda_review_queue(trace_id);
CREATE INDEX IF NOT EXISTS idx_scloda_review_assignee ON scloda_review_queue(assignee_user_id, status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_scloda_capability_parent ON scloda_capability_nodes(parent_slug);

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
