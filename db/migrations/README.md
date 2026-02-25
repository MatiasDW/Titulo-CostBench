# CostBench DB Migrations

How to apply in local or production Postgres (requires `psql` and env var `DATABASE_URL` or equivalent credentials).

## Order
1. `001_base_schema.sql` – creates tables/indexes for a fresh database.
2. `002_upgrade_existing.sql` – safely upgrades an existing DB (adds unique constraint, converts timestamps to `timestamptz`, ensures indexes).

## Usage
From repo root, with Docker DB running:
```bash
PGPASSWORD=postgres psql -h localhost -U postgres -d costbench -f db/migrations/001_base_schema.sql
PGPASSWORD=postgres psql -h localhost -U postgres -d costbench -f db/migrations/002_upgrade_existing.sql
```

For production, swap host/user/db/password accordingly or use `psql "$DATABASE_URL" -f ...`.

Notes:
- Scripts are idempotent and avoid dropping data; run them again safely.
- `macro_indicators` should be upserted (not replaced) by the pipeline to preserve constraints.
