-- Migration 004: Add KYC fields to users + create trading tables
-- Paper trading system: wallets, positions, trade history

-- ── KYC fields on users ──
ALTER TABLE users ADD COLUMN IF NOT EXISTS rut VARCHAR(12) UNIQUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS date_of_birth DATE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS nationality VARCHAR(60);
ALTER TABLE users ADD COLUMN IF NOT EXISTS address VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS city VARCHAR(80);
ALTER TABLE users ADD COLUMN IF NOT EXISTS occupation VARCHAR(100);
ALTER TABLE users ADD COLUMN IF NOT EXISTS income_range VARCHAR(40);
ALTER TABLE users ADD COLUMN IF NOT EXISTS investment_experience VARCHAR(20);

-- ── Wallets ──
CREATE TABLE IF NOT EXISTS wallets (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    balance NUMERIC(16, 2) NOT NULL DEFAULT 10000000,
    initial_balance NUMERIC(16, 2) NOT NULL DEFAULT 10000000,
    currency VARCHAR(8) NOT NULL DEFAULT 'CLP',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Open Positions ──
CREATE TABLE IF NOT EXISTS positions (
    id SERIAL PRIMARY KEY,
    wallet_id INTEGER NOT NULL REFERENCES wallets(id) ON DELETE CASCADE,
    asset VARCHAR(20) NOT NULL,
    direction VARCHAR(10) NOT NULL DEFAULT 'long',
    quantity NUMERIC(16, 8) NOT NULL,
    entry_price NUMERIC(16, 4) NOT NULL,
    invested_amount NUMERIC(16, 2) NOT NULL,
    opened_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Trade History (closed trades) ──
CREATE TABLE IF NOT EXISTS trade_history (
    id SERIAL PRIMARY KEY,
    wallet_id INTEGER NOT NULL REFERENCES wallets(id) ON DELETE CASCADE,
    asset VARCHAR(20) NOT NULL,
    direction VARCHAR(10) NOT NULL,
    quantity NUMERIC(16, 8) NOT NULL,
    entry_price NUMERIC(16, 4) NOT NULL,
    exit_price NUMERIC(16, 4) NOT NULL,
    invested_amount NUMERIC(16, 2) NOT NULL,
    pnl NUMERIC(16, 2) NOT NULL,
    pnl_percent NUMERIC(8, 2) NOT NULL,
    opened_at TIMESTAMPTZ NOT NULL,
    closed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_positions_wallet_id ON positions(wallet_id);
CREATE INDEX IF NOT EXISTS idx_trade_history_wallet_id ON trade_history(wallet_id);
CREATE INDEX IF NOT EXISTS idx_trade_history_closed_at ON trade_history(closed_at DESC);
