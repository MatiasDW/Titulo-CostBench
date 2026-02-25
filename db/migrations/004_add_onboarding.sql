-- 004_add_onboarding.sql
-- Adds user preferences / onboarding fields to the users table.

BEGIN;

-- User interests (stored as text array) and onboarding flag
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS interests TEXT[] DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS onboarding_completed BOOLEAN NOT NULL DEFAULT FALSE;

-- Mark existing admin as onboarded
UPDATE users SET onboarding_completed = TRUE WHERE role = 'admin';

COMMIT;
