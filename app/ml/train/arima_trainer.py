"""
Lightweight Training with pmdarima
Fast auto_arima training for production environment.
Consistent output contract for all training results.
"""
import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, Any

import pandas as pd
import numpy as np

from app.ml.logging_utils import get_logger
from app.ml.exceptions import ModelTrainingError

logger = get_logger("ml.train.arima")

# Minimum samples required
MIN_SAMPLES = 24

# Try pmdarima
try:
    import pmdarima as pm
    from pmdarima import auto_arima
    PMDARIMA_AVAILABLE = True
except ImportError:
    PMDARIMA_AVAILABLE = False
    logger.warning("pmdarima_not_available", 
                   message="Install with: pip install pmdarima")


def train_asset_model(asset: str, df: pd.DataFrame) -> dict:
    """
    Train auto_arima model for an asset.
    
    CONSISTENT OUTPUT CONTRACT:
    {
        "status": "ok" | "error",
        "asset": str,
        "best_model": str | None,
        "metrics": {"mae": float, "rmse": float, "mape": float} | {},
        "model_path": str | None,
        "error": str | None
    }
    """
    try:
        # Validate input
        if df is None or len(df) < MIN_SAMPLES:
            return {
                "status": "error",
                "asset": asset,
                "best_model": None,
                "metrics": {},
                "model_path": None,
                "error": f"not_enough_data (got {len(df) if df is not None else 0}, need {MIN_SAMPLES})"
            }
        
        if not PMDARIMA_AVAILABLE:
            return {
                "status": "error",
                "asset": asset,
                "best_model": None,
                "metrics": {},
                "model_path": None,
                "error": "pmdarima not installed"
            }
        
        # Prepare data
        df = df.copy()
        target_col = "value" if "value" in df.columns else "price_usd"
        
        if target_col not in df.columns:
            return {
                "status": "error",
                "asset": asset,
                "best_model": None,
                "metrics": {},
                "model_path": None,
                "error": f"target column 'value' or 'price_usd' not found"
            }
        
        y = df[target_col].values
        
        # Train/test split (last 6 months for validation)
        test_size = min(6, len(y) // 5)
        y_train = y[:-test_size] if test_size > 0 else y
        y_test = y[-test_size:] if test_size > 0 else None
        
        logger.info("training_started", asset=asset, train_size=len(y_train))
        start_time = datetime.now()
        
        # Fit auto_arima
        model = auto_arima(
            y_train,
            seasonal=False,
            stepwise=True,
            suppress_warnings=True,
            error_action="ignore",
            trace=False,
            n_jobs=1
        )
        
        order = model.order
        
        # Calculate metrics on test set
        metrics = {"mae": 0.0, "rmse": 0.0, "mape": 0.0}
        
        if y_test is not None and len(y_test) > 0:
            predictions = model.predict(n_periods=len(y_test))
            errors = y_test - predictions
            
            metrics["mae"] = float(np.mean(np.abs(errors)))
            metrics["rmse"] = float(np.sqrt(np.mean(errors ** 2)))
            
            non_zero = y_test != 0
            if np.any(non_zero):
                metrics["mape"] = float(np.mean(np.abs(errors[non_zero] / y_test[non_zero])) * 100)
        
        # Save model
        model_path = save_champion(asset, model, order, metrics)
        
        duration = (datetime.now() - start_time).total_seconds()
        
        logger.info(
            "training_complete",
            asset=asset,
            order=str(order),
            mae=round(metrics["mae"], 4),
            duration=round(duration, 2)
        )
        
        return {
            "status": "ok",
            "asset": asset,
            "best_model": f"ARIMA{order}",
            "metrics": metrics,
            "model_path": model_path,
            "error": None
        }
        
    except Exception as e:
        logger.error("training_failed", asset=asset, error=str(e))
        return {
            "status": "error",
            "asset": asset,
            "best_model": None,
            "metrics": {},
            "model_path": None,
            "error": str(e)
        }


def save_champion(
    asset: str,
    model: Any,
    order: tuple,
    metrics: dict,
    output_dir: Path = Path("models")
) -> str:
    """Save trained model and metadata to registry with confidence levels."""
    import pickle
    
    # Import series config for confidence levels
    try:
        from app.ml.series_config import (
            get_series_config, 
            get_confidence_from_mape,
            CONFIDENCE_LEVELS
        )
        series_info = get_series_config(asset)
    except ImportError:
        series_info = None
    
    asset_dir = output_dir / asset.lower()
    asset_dir.mkdir(parents=True, exist_ok=True)
    
    # Save model pickle
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_path = asset_dir / f"arima_{timestamp}.pkl"
    
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
    
    # Determine confidence from MAPE
    mape = metrics.get("mape", 5.0)
    confidence = get_confidence_from_mape(mape) if series_info else "good"
    
    # Override for high-volatility assets
    if series_info and series_info.get("is_high_volatility"):
        confidence = "volatile" if confidence in ["excellent", "good"] else confidence
    
    # Build registry entry
    entry = {
        "asset": asset,
        "model_type": "auto_arima",
        "order": list(order),
        "metrics": metrics,
        "model_path": str(model_path),
        "trained_at": datetime.now().isoformat(),
        "is_champion": True,
        "confidence": confidence,
        "confidence_label": CONFIDENCE_LEVELS.get(confidence, {}).get("label", confidence)
    }
    
    # Add special notes
    if series_info:
        if series_info.get("is_rule_based"):
            entry["is_rule_based"] = True
            entry["rule_note"] = series_info.get("rule_note", "")
        if series_info.get("is_high_volatility"):
            entry["is_high_volatility"] = True
            entry["volatility_note"] = series_info.get("volatility_note", "")
        entry["description"] = series_info.get("description", "")
    
    # Update registry
    registry_path = output_dir / "registry.json"
    
    if registry_path.exists():
        with open(registry_path, "r") as f:
            registry = json.load(f)
    else:
        registry = {"models": {}, "updated_at": None}
    
    registry["models"][asset] = entry
    registry["updated_at"] = datetime.now().isoformat()
    
    with open(registry_path, "w") as f:
        json.dump(registry, f, indent=2)
    
    logger.info("champion_saved", asset=asset, model_path=str(model_path), confidence=confidence)
    
    return str(model_path)



def load_champion(asset: str, output_dir: Path = Path("models")):
    """Load champion model for an asset."""
    import pickle
    
    registry_path = output_dir / "registry.json"
    
    if not registry_path.exists():
        raise FileNotFoundError("No registry found")
    
    with open(registry_path, "r") as f:
        registry = json.load(f)
    
    if asset not in registry.get("models", {}):
        raise KeyError(f"No champion for {asset}")
    
    entry = registry["models"][asset]
    model_path = Path(entry["model_path"])
    
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    with open(model_path, "rb") as f:
        model = pickle.load(f)
    
    return model, entry


def forecast(asset: str, horizon: int = 3, output_dir: Path = Path("models")) -> dict:
    """Generate forecast using champion model."""
    try:
        model, entry = load_champion(asset, output_dir)
        predictions = model.predict(n_periods=horizon)
        
        return {
            "status": "ok",
            "asset": asset,
            "model": entry["model_type"],
            "order": entry["order"],
            "horizon": horizon,
            "predictions": predictions.tolist(),
            "trained_at": entry["trained_at"]
        }
    except Exception as e:
        return {
            "status": "error",
            "asset": asset,
            "error": str(e)
        }
