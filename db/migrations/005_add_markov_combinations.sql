-- 005_add_markov_combinations.sql
-- Create table for storing historical Markov transition matrices and Granger Causality scores

CREATE TABLE IF NOT EXISTS markov_combinations (
    id SERIAL PRIMARY KEY,
    predictor VARCHAR(50) NOT NULL,
    target VARCHAR(50) NOT NULL,
    p_value NUMERIC(10, 8) NOT NULL,
    lag1_correlation NUMERIC(10, 4) NOT NULL,
    transition_matrix JSONB NOT NULL,
    run_date TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index by date and target for faster analytical queries
CREATE INDEX IF NOT EXISTS idx_markov_target_date ON markov_combinations (target, run_date);
CREATE INDEX IF NOT EXISTS idx_markov_predictor_target ON markov_combinations (predictor, target);
