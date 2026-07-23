-- 009_enable_pgvector_for_scloda_knowledge.sql
-- Enable pgvector and add a native vector column for Scloda retrieval.

BEGIN;

CREATE EXTENSION IF NOT EXISTS vector;

ALTER TABLE scloda_knowledge_chunks
    ADD COLUMN IF NOT EXISTS embedding_vector vector(1536);

CREATE INDEX IF NOT EXISTS idx_scloda_knowledge_embedding_hnsw
    ON scloda_knowledge_chunks
    USING hnsw (embedding_vector vector_cosine_ops);

COMMIT;
