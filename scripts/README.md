# Scripts Directory

Standalone CLI scripts for data pipeline and ML training.

## Usage

```bash
# From project root:
python scripts/train_pipeline.py    # Train ML models
python scripts/verify_apis.py       # Test external APIs
python scripts/run_pipeline.py      # Full data pipeline
```

## Files

| Script | Purpose |
|--------|---------|
| `train_pipeline.py` | Multi-asset ML training with pmdarima |
| `verify_apis.py` | Test BDE, BLS, Treasury connections |
| `run_pipeline.py` | Execute full data ingestion pipeline |
| `populate_analytics.py` | Populate analytics tables |
| `inspect_data.py` | Inspect parquet files |
| `test_bcch.py` | Test Banco Central API |
