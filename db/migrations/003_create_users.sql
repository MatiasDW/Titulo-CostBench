-- 003_create_users.sql
-- Creates the users table for authentication, roles, and risk profile storage.
-- Also seeds the default admin user.

BEGIN;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id          SERIAL PRIMARY KEY,
    email       VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role        VARCHAR(20) NOT NULL DEFAULT 'user' CHECK (role IN ('admin', 'user')),
    risk_profile VARCHAR(20) CHECK (risk_profile IN ('conservative', 'moderate', 'aggressive')),
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Unique index on email (case-insensitive lookups)
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

-- ──────────────────────────────────────────────
-- Seed: Default Admin User
-- Email:    admin@costbench.cl
-- Password: CostBench2025!
-- ──────────────────────────────────────────────
INSERT INTO users (email, password_hash, role, risk_profile, is_active)
VALUES (
    'admin@costbench.cl',
    '$2b$12$4uA6kLg9Tk53QdN1GmOtH.TgYAJUi2cGw1AEnAzAXUJucz9jKz8oa',
    'admin',
    NULL,
    TRUE
)
ON CONFLICT ((LOWER(email))) DO NOTHING;

COMMIT;
