-- 007_add_scloda_observability_and_knowledge.sql
-- Persistent traces + DB-backed retrieval cache for Scloda.

BEGIN;

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

CREATE INDEX IF NOT EXISTS idx_scloda_traces_created_at
    ON scloda_traces (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_scloda_traces_status
    ON scloda_traces (response_status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_scloda_traces_user_id
    ON scloda_traces (user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_scloda_traces_task_type
    ON scloda_traces (task_type, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_scloda_knowledge_source
    ON scloda_knowledge_chunks (source_kind, source_key);
CREATE INDEX IF NOT EXISTS idx_scloda_knowledge_indexed_at
    ON scloda_knowledge_chunks (indexed_at DESC);
CREATE INDEX IF NOT EXISTS idx_scloda_review_status
    ON scloda_review_queue (status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_scloda_review_trace
    ON scloda_review_queue (trace_id);
CREATE INDEX IF NOT EXISTS idx_scloda_capability_parent
    ON scloda_capability_nodes (parent_slug);

COMMIT;
