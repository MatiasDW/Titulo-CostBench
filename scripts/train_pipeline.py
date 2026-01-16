"""
ML Training Pipeline
Trains forecasting models for multiple assets with PyCaret.
Selects optimal model per asset and saves to registry.

Speed optimizations:
- n_jobs=-1 for parallel model training
- turbo=True to skip slow models  
- Include only fast, reliable models
- Parallel asset training with ThreadPoolExecutor
"""
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Optional
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.ml.config import FORECAST_CONFIG, DATA_SOURCES
from app.ml.logging_utils import get_logger
from app.ml.exceptions import DataFetchError, ModelTrainingError

logger = get_logger("train_pipeline")


# ============================================
# Configuration
# ============================================

# Assets to train (each gets its own optimal model)
ASSETS_CONFIG = {
    "GOLD": {
        "series_key": "gold",
        "display_name": "Gold (USD/oz)",
        "color": "#bf8700"
    },
    "COPPER": {
        "series_key": "copper", 
        "display_name": "Copper (USD/lb)",
        "color": "#da3633"
    },
    "BTC": {
        "series_key": "btc",
        "display_name": "Bitcoin (CLP)",
        "color": "#f2a900"
    },
    "ETH": {
        "series_key": "eth",
        "display_name": "Ethereum (CLP)",
        "color": "#627eea"
    },
    "OIL": {
        "series_key": "oil",
        "display_name": "WTI Oil (USD/bbl)",
        "color": "#c9d1d9"
    },
}

# Fast models only (turbo mode)
FAST_MODELS = [
    "naive",       # Baseline - always fast
    "snaive",      # Seasonal naive - fast
    "polytrend",   # Polynomial trend - fast
    "exp_smooth",  # Exponential smoothing - fast
    "theta",       # Theta method - fast
    "arima",       # ARIMA - medium
    "auto_arima",  # Auto ARIMA - medium-slow but best performance
    "lr_cds_dt",   # Linear regression - fast
]

# Slow models to exclude for speed
SLOW_MODELS = [
    "prophet",  # Requires extra dependencies, slow
    "tbats",    # Very slow
    "lightgbm_cds_dt",  # May not be installed
    "catboost_cds_dt",
]


# ============================================
# Data Loading
# ============================================

def load_asset_data(asset: str, macro_data: dict) -> pd.DataFrame:
    """
    Load historical price data for an asset from macro data.
    
    Returns DataFrame with [date, price_usd]
    """
    series_key = ASSETS_CONFIG.get(asset, {}).get("series_key", asset.lower())
    
    if series_key not in macro_data:
        raise DataFetchError(
            source="macro_data",
            reason=f"Series {series_key} not found in macro data"
        )
    
    data = macro_data[series_key]
    
    if isinstance(data, list):
        df = pd.DataFrame(data)
    elif isinstance(data, pd.DataFrame):
        df = data.copy()
    else:
        raise DataFetchError(
            source="macro_data",
            reason=f"Unexpected data type for {series_key}: {type(data)}"
        )
    
    # Normalize column names
    if 'date' not in df.columns:
        if 'index' in df.columns:
            df = df.rename(columns={'index': 'date'})
        elif df.index.name == 'date':
            df = df.reset_index()
    
    if 'value' in df.columns:
        df = df.rename(columns={'value': 'price_usd'})
    
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    
    # Aggregate to monthly
    df['month'] = df['date'].dt.to_period('M')
    df_monthly = df.groupby('month').agg({
        'price_usd': 'last'
    }).reset_index()
    df_monthly['date'] = df_monthly['month'].dt.to_timestamp()
    df_monthly = df_monthly.drop(columns=['month'])
    
    return df_monthly[['date', 'price_usd']]


# ============================================
# Training Functions
# ============================================

def train_asset_model(
    asset: str,
    df: pd.DataFrame,
    n_select: int = 3,
    cv_folds: int = 3,  # Reduced for speed
    forecast_horizon: int = 1
) -> dict:
    """
    Train and compare models for a single asset.
    
    Uses PyCaret with speed optimizations:
    - turbo=True (excludes slow models)
    - n_jobs=-1 (parallel training)
    - Reduced CV folds
    
    Returns dict with best model info and comparison results.
    """
    try:
        from pycaret.time_series import TSForecastingExperiment
    except ImportError:
        return {
            "asset": asset,
            "status": "error",
            "error": "PyCaret not installed"
        }
    
    logger.info("training_started", asset=asset, rows=len(df))
    start_time = datetime.now()
    
    try:
        # Prepare data - set date as index
        df_exp = df.set_index('date').sort_index()
        
        # Initialize experiment
        exp = TSForecastingExperiment()
        
        exp.setup(
            data=df_exp,
            target='price_usd',
            fh=forecast_horizon,
            fold=cv_folds,
            fold_strategy='expanding',
            session_id=42,
            verbose=False,
            html=False,
            n_jobs=-1  # Parallel training
        )
        
        # Compare models with turbo mode (fast models only)
        best_models = exp.compare_models(
            n_select=n_select,
            sort='MAE',
            include=FAST_MODELS,
            turbo=True,  # Skip cross-validation for slow models
            verbose=False
        )
        
        # Get comparison results
        comparison_df = exp.pull()
        
        # Handle single model return
        if not isinstance(best_models, list):
            best_models = [best_models]
        
        best_model = best_models[0]
        best_model_name = type(best_model).__name__
        
        # Get metrics
        best_row = comparison_df.iloc[0]
        metrics = {
            "mae": float(best_row.get('MAE', 0)),
            "rmse": float(best_row.get('RMSE', 0)),
            "mape": float(best_row.get('MAPE', 0)) if 'MAPE' in best_row else None
        }
        
        # All model results for comparison chart
        all_models = []
        for idx, row in comparison_df.iterrows():
            all_models.append({
                "model": str(idx) if isinstance(idx, str) else row.get('Model', f'model_{idx}'),
                "mae": float(row.get('MAE', 0)),
                "rmse": float(row.get('RMSE', 0)),
                "mape": float(row.get('MAPE', 0)) if 'MAPE' in row else None
            })
        
        duration = (datetime.now() - start_time).total_seconds()
        
        logger.info(
            "training_complete",
            asset=asset,
            best_model=best_model_name,
            mae=metrics['mae'],
            duration_seconds=round(duration, 1)
        )
        
        return {
            "asset": asset,
            "status": "success",
            "best_model": best_model_name,
            "metrics": metrics,
            "all_models": all_models[:10],  # Top 10 for chart
            "training_duration": duration,
            "data_points": len(df),
            "trained_at": datetime.now().isoformat(),
            "model_object": best_model,
            "experiment": exp
        }
        
    except Exception as e:
        logger.error("training_failed", asset=asset, error=str(e))
        return {
            "asset": asset,
            "status": "error",
            "error": str(e)
        }


def train_all_assets_parallel(
    macro_data: dict,
    max_workers: int = 3
) -> dict:
    """
    Train models for all assets in parallel.
    
    Uses ThreadPoolExecutor for concurrent training.
    Each asset gets its own optimal model.
    
    Returns dict with results per asset.
    """
    results = {}
    
    logger.info("parallel_training_started", assets=list(ASSETS_CONFIG.keys()))
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        
        for asset in ASSETS_CONFIG.keys():
            try:
                df = load_asset_data(asset, macro_data)
                if len(df) < 24:  # Need at least 2 years of data
                    logger.warning("insufficient_data", asset=asset, rows=len(df))
                    results[asset] = {
                        "asset": asset,
                        "status": "skipped",
                        "error": f"Insufficient data: {len(df)} rows"
                    }
                    continue
                    
                future = executor.submit(train_asset_model, asset, df)
                futures[future] = asset
                
            except Exception as e:
                logger.error("data_load_failed", asset=asset, error=str(e))
                results[asset] = {
                    "asset": asset,
                    "status": "error",
                    "error": str(e)
                }
        
        # Collect results
        for future in as_completed(futures):
            asset = futures[future]
            try:
                result = future.result()
                results[asset] = result
            except Exception as e:
                results[asset] = {
                    "asset": asset,
                    "status": "error",
                    "error": str(e)
                }
    
    return results


# ============================================
# Save Results
# ============================================

def save_training_results(results: dict, output_dir: Path = Path("models")):
    """
    Save training results to registry and JSON.
    """
    import json
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Summary for API/frontend
    summary = {
        "trained_at": datetime.now().isoformat(),
        "assets": {}
    }
    
    for asset, result in results.items():
        if result.get("status") == "success":
            # Remove non-serializable objects
            clean_result = {k: v for k, v in result.items() 
                          if k not in ["model_object", "experiment"]}
            summary["assets"][asset] = clean_result
            
            # Save model using registry
            try:
                from app.ml.registry.model_registry import save_champion
                from app.ml.validation.backtest_runner import BacktestResult
                
                # Create BacktestResult for registry
                backtest_result = BacktestResult(
                    asset=asset,
                    model_name=result["best_model"],
                    model=result.get("model_object"),
                    horizon=1,
                    folds=3,
                    metrics_per_fold=[result["metrics"]],
                    metrics_mean=result["metrics"],
                    metrics_std={"mae": 0, "rmse": 0, "mape": 0},
                    predictions=pd.DataFrame(),
                    training_end_date=datetime.now()
                )
                
                entry = save_champion(
                    backtest_result,
                    data_version=datetime.now().strftime("%Y-%m-%d"),
                    models_dir=output_dir
                )
                
                summary["assets"][asset]["model_id"] = entry.id
                
            except Exception as e:
                logger.warning("registry_save_failed", asset=asset, error=str(e))
        else:
            summary["assets"][asset] = {
                "status": result.get("status"),
                "error": result.get("error")
            }
    
    # Save summary JSON for frontend
    summary_path = output_dir / "training_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info("results_saved", path=str(summary_path))
    
    return summary


# ============================================
# Main Entry Point
# ============================================

def run_training_pipeline(macro_data: dict = None) -> dict:
    """
    Main entry point for training pipeline.
    
    Args:
        macro_data: Optional pre-loaded macro data dict.
                   If None, will load from parquet/API.
    
    Returns:
        Training summary dict for all assets.
    """
    logger.info("pipeline_started")
    
    # Load macro data if not provided
    if macro_data is None:
        macro_data = _load_macro_data()
    
    # Train all assets in parallel
    results = train_all_assets_parallel(macro_data, max_workers=3)
    
    # Save results
    summary = save_training_results(results)
    
    # Print summary
    print("\n" + "="*60)
    print("🎯 TRAINING SUMMARY")
    print("="*60)
    
    for asset, result in results.items():
        if result.get("status") == "success":
            print(f"✅ {asset}: {result['best_model']} (MAE: {result['metrics']['mae']:.2f})")
        else:
            print(f"❌ {asset}: {result.get('error', 'Unknown error')}")
    
    print("="*60 + "\n")
    
    return summary


def _load_macro_data() -> dict:
    """
    Load macro data from existing parquet file.
    
    The parquet has LONG format with columns:
        [date, value, series_id, source]
        
    We filter by series_id and return a dict mapping
    friendly names to DataFrames.
    """
    from pathlib import Path
    
    macro_path = Path("data/market/macro_indicators.parquet")
    
    if not macro_path.exists():
        raise FileNotFoundError(f"Macro data not found at {macro_path}")
    
    df = pd.read_parquet(macro_path)
    
    # Series ID mapping: series_id -> friendly name
    SERIES_MAPPING = {
        "GOLDAMGBD228NLBM": "gold",
        "PCOPPUSDM": "copper",
        "BTC-CLP": "btc",
        "ETH-CLP": "eth",
        "DCOILWTICO": "oil",
        "CPIAUCSL": "cpi",
        "DGS10": "yields",
        "SLVPRUSD": "silver",
        "XRP-CLP": "xrp",
        "SOL-CLP": "sol",
    }
    
    macro_data = {}
    
    for series_id, friendly_name in SERIES_MAPPING.items():
        # Filter to this series
        series_df = df[df["series_id"] == series_id].copy()
        
        if series_df.empty:
            logger.warning("series_not_found", series_id=series_id)
            continue
        
        # Prepare DataFrame with expected columns
        series_df = series_df[["date", "value"]].copy()
        series_df = series_df.rename(columns={"value": "price_usd"})
        series_df["date"] = pd.to_datetime(series_df["date"])
        series_df = series_df.sort_values("date").reset_index(drop=True)
        series_df = series_df.dropna(subset=["price_usd"])
        
        macro_data[friendly_name] = series_df
        logger.info("series_loaded", series=friendly_name, rows=len(series_df))
    
    return macro_data



# ============================================
# CLI
# ============================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Train ML forecasting models")
    parser.add_argument("--assets", nargs="+", help="Specific assets to train")
    parser.add_argument("--workers", type=int, default=3, help="Parallel workers")
    
    args = parser.parse_args()
    
    if args.assets:
        # Filter to specific assets
        ASSETS_CONFIG = {k: v for k, v in ASSETS_CONFIG.items() if k in args.assets}
    
    summary = run_training_pipeline()
    
    print("Training complete. Results saved to models/training_summary.json")
