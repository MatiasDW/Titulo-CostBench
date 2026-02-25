-- 002_upgrade_existing.sql
-- Brings an existing CostBench database up to the current schema safely.
-- Adds constraints and converts timestamps without dropping data.

BEGIN;

-- ranking.created_at to timestamptz
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'ranking'
          AND column_name = 'created_at'
          AND udt_name = 'timestamp'
    ) THEN
        ALTER TABLE ranking
        ALTER COLUMN created_at TYPE timestamptz
        USING created_at AT TIME ZONE 'UTC';
    END IF;
END$$;

-- macro_indicators.created_at to timestamptz
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'macro_indicators'
          AND column_name = 'created_at'
          AND udt_name = 'timestamp'
    ) THEN
        ALTER TABLE macro_indicators
        ALTER COLUMN created_at TYPE timestamptz
        USING created_at AT TIME ZONE 'UTC';
    END IF;
END$$;

-- Unique constraint on ranking (process_date, institution, product)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'ranking_process_institution_product_uk'
    ) THEN
        ALTER TABLE ranking
        ADD CONSTRAINT ranking_process_institution_product_uk
        UNIQUE (process_date, institution, product);
    END IF;
END$$;

-- Recreate indexes if missing
CREATE INDEX IF NOT EXISTS idx_ranking_date ON ranking(process_date);
CREATE INDEX IF NOT EXISTS idx_ranking_inst_date ON ranking(institution, process_date);
CREATE INDEX IF NOT EXISTS idx_macro_lookup ON macro_indicators(series_id, date);

COMMIT;
