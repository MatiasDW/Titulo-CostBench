# CostBench DB Migrations

How to apply in local or production Postgres (requires `psql` and env var `DATABASE_URL` or equivalent credentials).

## Order
1. `001_base_schema.sql` – creates tables/indexes for a fresh database.
2. `002_upgrade_existing.sql` – safely upgrades an existing DB (adds unique constraint, converts timestamps to `timestamptz`, ensures indexes).
3. `003_create_users.sql` + `003_add_profile_fields.sql` – users/auth schema and profile fields.
4. `004_add_onboarding.sql` + `004_add_trading_and_kyc.sql` – onboarding preferences, KYC fields, and paper trading tables.
5. `005_add_markov_combinations.sql` – storage for Markov transition outputs.
6. `006_create_real_estate_metrics.sql` – storage for Real Estate quant metrics.

## Usage
From repo root, with Docker DB running:
```bash
PGPASSWORD=postgres psql -h localhost -U postgres -d costbench -f db/migrations/001_base_schema.sql
PGPASSWORD=postgres psql -h localhost -U postgres -d costbench -f db/migrations/002_upgrade_existing.sql
PGPASSWORD=postgres psql -h localhost -U postgres -d costbench -f db/migrations/003_create_users.sql
PGPASSWORD=postgres psql -h localhost -U postgres -d costbench -f db/migrations/003_add_profile_fields.sql
PGPASSWORD=postgres psql -h localhost -U postgres -d costbench -f db/migrations/004_add_onboarding.sql
PGPASSWORD=postgres psql -h localhost -U postgres -d costbench -f db/migrations/004_add_trading_and_kyc.sql
PGPASSWORD=postgres psql -h localhost -U postgres -d costbench -f db/migrations/005_add_markov_combinations.sql
PGPASSWORD=postgres psql -h localhost -U postgres -d costbench -f db/migrations/006_create_real_estate_metrics.sql
```

For production, swap host/user/db/password accordingly or use `psql "$DATABASE_URL" -f ...`.

Notes:
- Scripts are idempotent and avoid dropping data; run them again safely.
- `macro_indicators` should be upserted (not replaced) by the pipeline to preserve constraints.
