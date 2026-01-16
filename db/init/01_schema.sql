-- Init Script for CostBench Database

CREATE TABLE IF NOT EXISTS ranking (
    id SERIAL PRIMARY KEY,
    process_date DATE NOT NULL,
    institution VARCHAR(255) NOT NULL,
    product VARCHAR(255) NOT NULL,
    cost_clp NUMERIC(12, 2),
    cost_uf NUMERIC(12, 4),
    cost_usd NUMERIC(12, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS macro_indicators (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    series_id VARCHAR(50) NOT NULL,
    value NUMERIC(10, 4),
    source VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date, series_id)
);

-- Index for faster queries
CREATE INDEX idx_ranking_date ON ranking(process_date);
CREATE INDEX idx_macro_lookup ON macro_indicators(series_id, date);
