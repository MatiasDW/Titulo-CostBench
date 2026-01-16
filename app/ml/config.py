"""
ML Pipeline Configuration
Centralized settings for forecasting and clustering modules.
"""
from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True)
class HTTPConfig:
    """HTTP client configuration with retry logic."""
    timeout: float = 30.0
    connect_timeout: float = 10.0
    max_retries: int = 3
    backoff_factor: float = 1.5
    retry_status_codes: tuple[int, ...] = (429, 500, 502, 503, 504)


@dataclass(frozen=True)
class ForecastConfig:
    """Forecasting experiment configuration."""
    target: str = "price_usd"
    forecast_horizon: int = 1
    cv_folds: int = 5
    seasonal_period: int = 12  # Monthly data
    initial_train_window: int = 36  # 3 years minimum
    random_seed: int = 42
    primary_metric: str = "MAE"
    secondary_metric: str = "MAPE"


@dataclass(frozen=True)
class DataSourceConfig:
    """Data source endpoints and series IDs."""
    # BLS CPI
    bls_base_url: str = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
    bls_cpi_series: str = "CUUR0000SA0"
    
    # Treasury
    treasury_base_url: str = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/"
    treasury_yields_endpoint: str = "v2/accounting/od/avg_interest_rates"
    
    # Internal API (existing)
    internal_api_base: str = "/api/v1/market/history"
    gold_series: str = "GOLDAMGBD228NLBM"
    copper_series: str = "PCOPPUSDM"


@dataclass(frozen=True)
class ClusterConfig:
    """Investor clustering configuration."""
    k_range: tuple[int, ...] = (2, 3, 4, 5)
    features: tuple[str, ...] = (
        "investment_horizon_years",
        "loss_capacity_pct",
        "risk_tolerance_1_10",
        "experience_years"
    )
    random_seed: int = 42


# Global instances
HTTP_CONFIG = HTTPConfig()
FORECAST_CONFIG = ForecastConfig()
DATA_SOURCES = DataSourceConfig()
CLUSTER_CONFIG = ClusterConfig()
