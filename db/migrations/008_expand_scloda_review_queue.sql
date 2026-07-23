-- 008_expand_scloda_review_queue.sql
-- Add assignment and notification metadata to the human review queue.

BEGIN;

ALTER TABLE scloda_review_queue
    ADD COLUMN IF NOT EXISTS assignee_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL;

ALTER TABLE scloda_review_queue
    ADD COLUMN IF NOT EXISTS assignment_note TEXT;

ALTER TABLE scloda_review_queue
    ADD COLUMN IF NOT EXISTS assigned_at TIMESTAMPTZ;

ALTER TABLE scloda_review_queue
    ADD COLUMN IF NOT EXISTS notification_status VARCHAR(24) NOT NULL DEFAULT 'queued';

ALTER TABLE scloda_review_queue
    ADD COLUMN IF NOT EXISTS notification_channel VARCHAR(24) NOT NULL DEFAULT 'in_app';

ALTER TABLE scloda_review_queue
    ADD COLUMN IF NOT EXISTS notification_sent_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_scloda_review_assignee
    ON scloda_review_queue (assignee_user_id, status, created_at DESC);

COMMIT;
