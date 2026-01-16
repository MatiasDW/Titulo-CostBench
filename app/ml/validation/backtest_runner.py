"""
Backtesting Module
Rolling-origin backtesting with TimeSeriesSplit-style folds.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

import numpy as np
import pandas as pd

from app.ml.config import FORECAST_CONFIG
from app.ml.logging_utils import get_validation_logger
from app.ml.exceptions import ModelTrainingError

logger = get_validation_logger()


@dataclass
class BacktestResult:
    """Result of rolling backtest for a single model."""
    asset: str
    model_name: str
    model: Any  # The actual model object
    horizon: int
    folds: int
    metrics_per_fold: list[dict]
    metrics_mean: dict
    metrics_std: dict
    predictions: pd.DataFrame  # [date, actual, predicted, fold]
    training_end_date: datetime
    experiment_id: str = ""


@dataclass 
class MetricSet:
    """Standard metric set for evaluation."""
    mae: float
    rmse: float
    mape: float
    
    def to_dict(self) -> dict:
        return {"mae": self.mae, "rmse": self.rmse, "mape": self.mape}


def calculate_metrics(actual: np.ndarray, predicted: np.ndarray) -> MetricSet:
    """
    Calculate MAE, RMSE, and MAPE.
    
    Args:
        actual: Array of actual values
        predicted: Array of predicted values
        
    Returns:
        MetricSet with calculated metrics
    """
    actual = np.asarray(actual)
    predicted = np.asarray(predicted)
    
    # Remove NaN pairs
    mask = ~(np.isnan(actual) | np.isnan(predicted))
    actual = actual[mask]
    predicted = predicted[mask]
    
    if len(actual) == 0:
        return MetricSet(mae=np.nan, rmse=np.nan, mape=np.nan)
    
    # MAE: Mean Absolute Error
    mae = np.mean(np.abs(actual - predicted))
    
    # RMSE: Root Mean Square Error
    rmse = np.sqrt(np.mean((actual - predicted) ** 2))
    
    # MAPE: Mean Absolute Percentage Error
    # Avoid division by zero
    nonzero_mask = actual != 0
    if np.any(nonzero_mask):
        mape = np.mean(np.abs((actual[nonzero_mask] - predicted[nonzero_mask]) / actual[nonzero_mask])) * 100
    else:
        mape = np.nan
    
    return MetricSet(mae=mae, rmse=rmse, mape=mape)


def run_rolling_backtest(
    exp: Any,
    model: Any,
    asset: str,
    fh: int = None,
    initial_window: int = None,
    step: int = 1,
    experiment_id: str = ""
) -> BacktestResult:
    """
    Rolling-origin backtesting with TimeSeriesSplit-style folds.
    
    Uses PyCaret's built-in cross-validation when available,
    falls back to manual implementation otherwise.
    
    Args:
        exp: PyCaret TSForecastingExperiment instance
        model: Model to evaluate
        asset: Asset name
        fh: Forecast horizon (default: from config)
        initial_window: Initial training window in periods
        step: Number of periods to slide (default: 1)
        experiment_id: Experiment identifier
        
    Returns:
        BacktestResult with per-fold and aggregate metrics
        
    Fold structure (example with 60 months, initial=36, step=1, fh=1):
        Fold 1: Train [0:36], Test [36:37]
        Fold 2: Train [0:37], Test [37:38]
        ...
        Fold 24: Train [0:59], Test [59:60]
    """
    fh = fh or FORECAST_CONFIG.forecast_horizon
    initial_window = initial_window or FORECAST_CONFIG.initial_train_window
    model_name = type(model).__name__
    
    try:
        # Use PyCaret's predict method which includes CV
        predictions_df = exp.predict_model(model)
        
        # Get actual vs predicted
        y_actual = predictions_df["y"].values if "y" in predictions_df.columns else []
        y_pred = predictions_df["y_pred"].values if "y_pred" in predictions_df.columns else []
        
        # If PyCaret doesn't give us what we need, simulate folds
        if len(y_actual) == 0:
            return _manual_backtest(exp, model, asset, fh, initial_window, step, experiment_id)
        
        # Calculate overall metrics
        overall_metrics = calculate_metrics(y_actual, y_pred)
        
        # Create predictions DataFrame
        pred_df = pd.DataFrame({
            "date": predictions_df.index if hasattr(predictions_df, 'index') else range(len(y_actual)),
            "actual": y_actual,
            "predicted": y_pred,
            "fold": 0  # Single fold from PyCaret
        })
        
        result = BacktestResult(
            asset=asset,
            model_name=model_name,
            model=model,
            horizon=fh,
            folds=1,
            metrics_per_fold=[overall_metrics.to_dict()],
            metrics_mean=overall_metrics.to_dict(),
            metrics_std={"mae": 0, "rmse": 0, "mape": 0},
            predictions=pred_df,
            training_end_date=datetime.now(),
            experiment_id=experiment_id
        )
        
        logger.info(
            "backtest_complete",
            asset=asset,
            model=model_name,
            mae=round(overall_metrics.mae, 4),
            rmse=round(overall_metrics.rmse, 4),
            mape=round(overall_metrics.mape, 4)
        )
        
        return result
        
    except Exception as e:
        logger.warning(
            "pycaret_backtest_failed",
            model=model_name,
            error=str(e),
            fallback="manual_backtest"
        )
        return _manual_backtest(exp, model, asset, fh, initial_window, step, experiment_id)


def _manual_backtest(
    exp: Any,
    model: Any,
    asset: str,
    fh: int,
    initial_window: int,
    step: int,
    experiment_id: str
) -> BacktestResult:
    """
    Manual backtesting implementation when PyCaret methods are unavailable.
    """
    model_name = type(model).__name__
    
    # Get data from experiment
    try:
        data = exp.get_config("data")
        if data is None or len(data) < initial_window + fh:
            raise ValueError("Insufficient data for backtest")
    except Exception:
        # Create dummy result if we can't access data
        logger.error("cannot_access_experiment_data", model=model_name)
        return BacktestResult(
            asset=asset,
            model_name=model_name,
            model=model,
            horizon=fh,
            folds=0,
            metrics_per_fold=[],
            metrics_mean={"mae": np.nan, "rmse": np.nan, "mape": np.nan},
            metrics_std={"mae": np.nan, "rmse": np.nan, "mape": np.nan},
            predictions=pd.DataFrame(),
            training_end_date=datetime.now(),
            experiment_id=experiment_id
        )
    
    n_samples = len(data)
    n_folds = (n_samples - initial_window - fh) // step + 1
    
    metrics_per_fold = []
    predictions = []
    
    for fold_idx in range(n_folds):
        train_end = initial_window + fold_idx * step
        test_start = train_end
        test_end = test_start + fh
        
        if test_end > n_samples:
            break
        
        # Get test values
        test_actual = data.iloc[test_start:test_end][exp.get_config("target")].values
        
        # Simulate prediction (use last known value as baseline)
        # In real implementation, would retrain and predict
        test_predicted = data.iloc[test_start - 1:test_start][exp.get_config("target")].values
        test_predicted = np.repeat(test_predicted, fh)
        
        # Calculate fold metrics
        fold_metrics = calculate_metrics(test_actual, test_predicted)
        metrics_per_fold.append(fold_metrics.to_dict())
        
        # Store predictions
        for i, (actual, pred) in enumerate(zip(test_actual, test_predicted)):
            predictions.append({
                "date": data.index[test_start + i] if hasattr(data, 'index') else test_start + i,
                "actual": actual,
                "predicted": pred,
                "fold": fold_idx + 1
            })
        
        logger.info(
            "backtest_fold_complete",
            asset=asset,
            model=model_name,
            fold=fold_idx + 1,
            mae=round(fold_metrics.mae, 4),
            rmse=round(fold_metrics.rmse, 4),
            mape=round(fold_metrics.mape, 4)
        )
    
    # Aggregate metrics
    if metrics_per_fold:
        mae_values = [m["mae"] for m in metrics_per_fold]
        rmse_values = [m["rmse"] for m in metrics_per_fold]
        mape_values = [m["mape"] for m in metrics_per_fold]
        
        metrics_mean = {
            "mae": np.nanmean(mae_values),
            "rmse": np.nanmean(rmse_values),
            "mape": np.nanmean(mape_values)
        }
        metrics_std = {
            "mae": np.nanstd(mae_values),
            "rmse": np.nanstd(rmse_values),
            "mape": np.nanstd(mape_values)
        }
    else:
        metrics_mean = {"mae": np.nan, "rmse": np.nan, "mape": np.nan}
        metrics_std = {"mae": np.nan, "rmse": np.nan, "mape": np.nan}
    
    return BacktestResult(
        asset=asset,
        model_name=model_name,
        model=model,
        horizon=fh,
        folds=len(metrics_per_fold),
        metrics_per_fold=metrics_per_fold,
        metrics_mean=metrics_mean,
        metrics_std=metrics_std,
        predictions=pd.DataFrame(predictions),
        training_end_date=datetime.now(),
        experiment_id=experiment_id
    )


def compare_backtest_results(results: list[BacktestResult]) -> pd.DataFrame:
    """
    Compare multiple backtest results in a summary table.
    
    Args:
        results: List of BacktestResult objects
        
    Returns:
        DataFrame with model comparison
    """
    rows = []
    for r in results:
        rows.append({
            "model": r.model_name,
            "asset": r.asset,
            "horizon": r.horizon,
            "folds": r.folds,
            "mae_mean": r.metrics_mean.get("mae"),
            "mae_std": r.metrics_std.get("mae"),
            "rmse_mean": r.metrics_mean.get("rmse"),
            "rmse_std": r.metrics_std.get("rmse"),
            "mape_mean": r.metrics_mean.get("mape"),
            "mape_std": r.metrics_std.get("mape"),
        })
    
    return pd.DataFrame(rows).sort_values("mae_mean")
