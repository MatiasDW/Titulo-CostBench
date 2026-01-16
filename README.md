# Bank Cost Benchmark API

Portfolio analytics and ML forecasting platform for Chilean financial data.

## 🚀 Quick Start

```bash
# Start services
docker-compose up -d

# Frontend (React)
cd frontend && npm run dev  # http://localhost:5173
```

## 📁 Project Structure

```
├── app/                    # Flask application
│   ├── blueprints/         # API endpoints
│   │   ├── market_api.py   # BDE/BLS/Treasury data
│   │   ├── ml_api.py       # ML models & forecasts
│   │   └── ...
│   ├── ml/                 # ML pipeline
│   │   ├── ingest/         # Data clients (BDE, BLS, Treasury)
│   │   ├── train/          # pmdarima training & scheduling
│   │   ├── features/       # Feature engineering
│   │   └── registry/       # Model persistence
│   └── services/           # Business logic
├── frontend/               # React + Vite
├── scripts/                # CLI utilities
│   ├── train_pipeline.py   # ML training script
│   └── verify_apis.py      # API connection tests
├── data/                   # Parquet data files
└── models/                 # Trained model artifacts
```

## 🔌 API Endpoints

### Market Data

| Endpoint | Source | Description |
|----------|--------|-------------|
| `GET /api/v1/market/bde/uf` | BDE | UF diaria (rule-based index) |
| `GET /api/v1/market/bde/usdclp` | BDE | USD/CLP observado |
| `GET /api/v1/market/bls/cpi` | BLS | CPI USA (CUUR0000SA0) |
| `GET /api/v1/market/treasury/yields` | Treasury | 10Y yield |
| `GET /api/v1/market/status` | - | Source availability check |

### ML Models

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/models` | List all trained champions |
| `GET /api/v1/models/{asset}/best` | Best model for asset |
| `GET /api/v1/models/{asset}/forecast?h=3` | Generate forecast |

### Examples

```bash
# Fetch UF (last year, monthly)
curl "http://localhost:5000/api/v1/market/bde/uf?monthly=true"

# Fetch USD/CLP (daily)
curl "http://localhost:5000/api/v1/market/bde/usdclp?monthly=false&start=2025-01-01"

# Get champion model for COPPER
curl "http://localhost:5000/api/v1/models/COPPER/best"

# 3-month forecast
curl "http://localhost:5000/api/v1/models/USDCLP/forecast?h=3"
```

## 🤖 ML Pipeline

### Trained Models

| Asset | Model | MAPE | Confidence |
|-------|-------|------|------------|
| GOLD | ARIMA(0,1,0) | 0.00% | 🟢 Excellent |
| OIL | ARIMA(1,1,1) | 1.92% | 🟢 Excellent |
| UF | ARIMA(0,2,2) | 0.63% | 🟢 Excellent |
| USDCLP | ARIMA(1,1,0) | 4.22% | 🟡 Good |
| COPPER | ARIMA(1,1,0) | 6.14% | 🟠 Volatile |

### Retraining Schedule

- **Quincenal** (days 1 & 15): pmdarima auto_arima
- **Monthly**: PyCaret benchmark (optional, offline)

### Manual Training

```bash
# Inside container
docker exec titulo-app-1 python scripts/train_pipeline.py

# Quick test
docker exec titulo-app-1 python -c "
from app.ml.train.scheduler import trigger_training_now
print(trigger_training_now())
"
```

## 📊 Data Sources

| Source | Data | Credentials |
|--------|------|-------------|
| **BDE** (Banco Central Chile) | UF, USD/CLP | `BDE_USER`, `BDE_PASS` |
| **BLS** (Bureau of Labor Statistics) | CPI USA | None required |
| **Treasury** (US Fiscal Data) | 10Y Yields | None required |

### About UF

> **Note**: UF (Unidad de Fomento) is a **rule-based index** calculated by the Banco Central de Chile.
> It's derived from CPI Chile using geometric interpolation between days 10→9 of each month.
> For E2: We consume UF directly from BDE.
> For E3: We'll model IPC Chile and derive UF mathematically.

[Methodology](https://www.bcentral.cl/areas/estadisticas/indices-indicadores)

## 🔧 Configuration

`.env` file:
```
FLASK_ENV=development
SECRET_KEY=your-secret

# BDE (Banco Central)
BDE_USER=your-email
BDE_PASS=your-password

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/costbench
```

## 📝 License

Academic project - Universidad Carlemany
