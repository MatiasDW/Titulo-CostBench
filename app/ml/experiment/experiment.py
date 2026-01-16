"""
PyCaret Time Series Experiment Module
Configures and runs model comparison for forecasting.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

import pandas as pd

from app.ml.config import FORECAST_CONFIG
from app.ml.logging_utils import get_experiment_logger
from app.ml.exceptions import ModelTrainingError

logger = get_experiment_logger()

# Flag to check if PyCaret is available
PYCARET_AVAILABLE = False
try:
    from pycaret.time_series import TSForecastingExperiment
    PYCARET_AVAILABLE = True
except ImportError:
    logger.warning("pycaret_not_installed", message="PyCaret not available. Install with: pip install pycaret[time_series]")


@dataclass
class ExperimentConfig:
    """Configuration for PyCaret time series experiment."""
    target: str = "price_usd"
    forecast_horizon: int = 1
    cv_folds: int = 5
    seasonal_period: int = 12
    random_seed: int = 42
    primary_metric: str = "MAE"
    exogenous_columns: list[str] = None
    
    def __post_init__(self):
        if self.exogenous_columns is None:
            self.exogenous_columns = []


@dataclass
class ComparisonResult:
    """Result of model comparison."""
    comparison_df: pd.DataFrame
    top_models: list
    best_model_name: str
    best_metric_value: float
    experiment_id: str
    timestamp: datetime


def setup_experiment(
    df: pd.DataFrame,
    config: ExperimentConfig = None,
    asset: str = "GOLD"
) -> Any:
    """
    Initialize PyCaret time series experiment.
    
    Args:
        df: Feature DataFrame with date index and target
        config: Experiment configuration
        asset: Asset name for logging
        
    Returns:
        Configured TSForecastingExperiment instance (or None if PyCaret unavailable)
        
    Raises:
        ModelTrainingError: If setup fails
    """
    if not PYCARET_AVAILABLE:
        logger.error("pycaret_unavailable", message="Cannot setup experiment without PyCaret")
        return None
    
    config = config or ExperimentConfig()
    
    # Prepare data
    df_exp = df.copy()
    
    # Ensure date is index
    if "date" in df_exp.columns:
        df_exp = df_exp.set_index("date")
    
    # Sort by index
    df_exp = df_exp.sort_index()
    
    # Filter to numeric columns only
    numeric_cols = df_exp.select_dtypes(include=["number"]).columns.tolist()
    df_exp = df_exp[numeric_cols]
    
    # Determine exogenous columns
    exog = None
    if config.exogenous_columns:
        available_exog = [c for c in config.exogenous_columns if c in df_exp.columns]
        if available_exog:
            exog = available_exog
            logger.info("exogenous_features_set", features=exog)
        else:
            logger.warning("no_exogenous_available", requested=config.exogenous_columns)
    
    try:
        exp = TSForecastingExperiment()
        
        exp.setup(
            data=df_exp,
            target=config.target,
            fh=config.forecast_horizon,
            fold=config.cv_folds,
            fold_strategy="expanding",  # Proper for time series
            seasonal_period=config.seasonal_period,
            numeric_imputation_target="ffill",
            session_id=config.random_seed,
            verbose=False,
            html=False  # Disable HTML output
        )
        
        logger.info(
            "experiment_setup_complete",
            asset=asset,
            target=config.target,
            horizon=config.forecast_horizon,
            folds=config.cv_folds,
            rows=len(df_exp),
            features=list(df_exp.columns)
        )
        
        return exp
        
    except Exception as e:
        raise ModelTrainingError(
            model_name="setup",
            reason=f"Failed to setup experiment: {str(e)}"
        )


def run_model_comparison(
    exp: Any,
    n_select: int = 3,
    sort_metric: str = None,
    include_models: list[str] = None,
    exclude_models: list[str] = None,
    asset: str = "GOLD"
) -> ComparisonResult:
    """
    Run compare_models() and return top candidates.
    
    Args:
        exp: PyCaret TSForecastingExperiment instance
        n_select: Number of top models to select
        sort_metric: Metric to sort by (default: MAE)
        include_models: List of models to include (None = all)
        exclude_models: List of models to exclude
        asset: Asset name for logging
        
    Returns:
        ComparisonResult with comparison DataFrame and top models
        
    Default models compared by PyCaret TS:
        - naive, snaive, polytrend, arima, auto_arima,
          exp_smooth, ets, theta, tbats, prophet, lr_cds_dt
    """
    if not PYCARET_AVAILABLE or exp is None:
        logger.error("cannot_compare_models", reason="PyCaret not available or experiment not setup")
        return None
    
    sort_metric = sort_metric or FORECAST_CONFIG.primary_metric
    
    # Default exclusions (Prophet requires extra setup)
    if exclude_models is None:
        exclude_models = ["prophet", "tbats"]  # Often slow or have dependencies
    
    experiment_id = f"exp_{asset}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        logger.info(
            "model_comparison_starting",
            asset=asset,
            n_select=n_select,
            sort_metric=sort_metric,
            exclude_models=exclude_models
        )
        
        # Run comparison
        best_models = exp.compare_models(
            n_select=n_select,
            sort=sort_metric,
            include=include_models,
            exclude=exclude_models,
            verbose=False
        )
        
        # Get comparison results
        comparison_df = exp.pull()
        
        # Handle single model return
        if not isinstance(best_models, list):
            best_models = [best_models]
        
        # Get best model info
        best_model = best_models[0]
        best_model_name = type(best_model).__name__
        best_metric_value = comparison_df.iloc[0][sort_metric] if sort_metric in comparison_df.columns else None
        
        result = ComparisonResult(
            comparison_df=comparison_df,
            top_models=best_models,
            best_model_name=best_model_name,
            best_metric_value=best_metric_value,
            experiment_id=experiment_id,
            timestamp=datetime.now()
        )
        
        logger.info(
            "model_comparison_complete",
            asset=asset,
            experiment_id=experiment_id,
            models_compared=len(comparison_df),
            best_model=best_model_name,
            best_metric=f"{sort_metric}={best_metric_value}",
            top_n=[type(m).__name__ for m in best_models]
        )
        
        return result
        
    except Exception as e:
        raise ModelTrainingError(
            model_name="compare_models",
            reason=f"Model comparison failed: {str(e)}"
        )


def get_default_models() -> list[str]:
    """
    Get list of default models available in PyCaret Time Series.
    
    Returns:
        List of model identifiers
    """
    return [
        "naive",      # Naive forecaster
        "snaive",     # Seasonal naive
        "polytrend",  # Polynomial trend
        "arima",      # ARIMA
        "auto_arima", # Auto ARIMA (pmdarima)
        "exp_smooth", # Exponential smoothing
        "ets",        # ETS
        "theta",      # Theta method
        "lr_cds_dt",  # Linear regression with deseasonalize
        "ridge_cds_dt",
        "lasso_cds_dt",
        "en_cds_dt",  # ElasticNet
        "knn_cds_dt", # KNN
        "dt_cds_dt",  # Decision tree
        "rf_cds_dt",  # Random forest
    ]


def get_model_description(model_name: str) -> str:
    """Get human-readable description of a model."""
    descriptions = {
        "naive": "Naive Forecaster - Uses last observation as forecast",
        "snaive": "Seasonal Naive - Uses observation from same season last cycle",
        "auto_arima": "Auto ARIMA - Automatically selects best ARIMA parameters",
        "arima": "ARIMA - Autoregressive Integrated Moving Average",
        "exp_smooth": "Exponential Smoothing - Weighted average with decay",
        "ets": "ETS - Error, Trend, Seasonality decomposition",
        "theta": "Theta Method - Decomposes into long/short term components",
        "lr_cds_dt": "Linear Regression with deseasonalization and detrending",
        "rf_cds_dt": "Random Forest with deseasonalization and detrending",
    }
    return descriptions.get(model_name, f"Model: {model_name}")
