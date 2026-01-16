"""
Champion Selection and Model Persistence
Selects best model from backtest results and persists to registry.
"""
import json
import pickle
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, date
from pathlib import Path
from typing import Any, Optional

import pandas as pd

from app.ml.config import FORECAST_CONFIG
from app.ml.validation.backtest_runner import BacktestResult
from app.ml.logging_utils import get_registry_logger
from app.ml.exceptions import ModelNotFoundError

logger = get_registry_logger()

# Default paths
DEFAULT_MODELS_DIR = Path("models")
DEFAULT_REGISTRY_PATH = Path("models/registry.json")


@dataclass
class ModelRegistryEntry:
    """Model registry entry with metadata."""
    id: str
    asset: str
    horizon: int
    model_name: str
    library: str
    library_version: str
    metrics: dict
    trained_until: str  # ISO date string
    data_version: str
    artifact_path: str
    created_at: str  # ISO datetime string
    is_active: bool = True
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "ModelRegistryEntry":
        return cls(**data)


def select_champion(
    backtest_results: list[BacktestResult],
    primary_metric: str = None,
    secondary_metric: str = None
) -> BacktestResult:
    """
    Select best model based on mean backtest metrics.
    
    Args:
        backtest_results: List of BacktestResult objects
        primary_metric: Primary sorting metric (default: MAE)
        secondary_metric: Tie-breaker metric (default: MAPE)
        
    Returns:
        Best BacktestResult
        
    Logs:
        INFO: Champion selected with metrics
    """
    primary_metric = primary_metric or FORECAST_CONFIG.primary_metric.lower()
    secondary_metric = secondary_metric or FORECAST_CONFIG.secondary_metric.lower()
    
    if not backtest_results:
        raise ValueError("No backtest results to select champion from")
    
    # Sort by primary metric, then secondary
    sorted_results = sorted(
        backtest_results,
        key=lambda r: (
            r.metrics_mean.get(primary_metric, float('inf')),
            r.metrics_mean.get(secondary_metric, float('inf'))
        )
    )
    
    champion = sorted_results[0]
    
    logger.info(
        "champion_selected",
        asset=champion.asset,
        model=champion.model_name,
        primary_metric=f"{primary_metric}={champion.metrics_mean.get(primary_metric):.4f}",
        secondary_metric=f"{secondary_metric}={champion.metrics_mean.get(secondary_metric):.4f}",
        candidates=len(backtest_results)
    )
    
    return champion


def save_champion(
    result: BacktestResult,
    data_version: str = None,
    models_dir: Path = None
) -> ModelRegistryEntry:
    """
    Persist model artifact and metadata to registry.
    
    Args:
        result: BacktestResult of champion model
        data_version: Version string for training data
        models_dir: Directory to save model artifacts
        
    Returns:
        ModelRegistryEntry with saved artifact info
        
    Actions:
        1. Pickle model to models/{asset}/{model_id}.pkl
        2. Add entry to registry
        3. Log structured entry
    """
    models_dir = models_dir or DEFAULT_MODELS_DIR
    data_version = data_version or datetime.now().strftime("%Y-%m-%d")
    
    # Generate model ID
    model_id = str(uuid.uuid4())[:8]
    
    # Create asset directory
    asset_dir = models_dir / result.asset.lower()
    asset_dir.mkdir(parents=True, exist_ok=True)
    
    # Save model artifact
    artifact_path = asset_dir / f"champion_{model_id}.pkl"
    try:
        with open(artifact_path, "wb") as f:
            pickle.dump(result.model, f)
        logger.info("model_artifact_saved", path=str(artifact_path))
    except Exception as e:
        logger.error("model_save_failed", error=str(e))
        artifact_path = Path("")  # Empty path on failure
    
    # Get library version
    try:
        import pycaret
        library_version = pycaret.__version__
    except ImportError:
        library_version = "unknown"
    
    # Create registry entry
    entry = ModelRegistryEntry(
        id=model_id,
        asset=result.asset,
        horizon=result.horizon,
        model_name=result.model_name,
        library="pycaret",
        library_version=library_version,
        metrics=result.metrics_mean,
        trained_until=result.training_end_date.strftime("%Y-%m-%d"),
        data_version=data_version,
        artifact_path=str(artifact_path),
        created_at=datetime.now().isoformat(),
        is_active=True
    )
    
    # Save to registry
    _add_to_registry(entry, models_dir)
    
    # Save backtest predictions
    predictions_path = asset_dir / f"predictions_{model_id}.csv"
    if not result.predictions.empty:
        result.predictions.to_csv(predictions_path, index=False)
        logger.info("predictions_saved", path=str(predictions_path))
    
    logger.info(
        "champion_persisted",
        model_id=model_id,
        asset=result.asset,
        model=result.model_name,
        metrics=result.metrics_mean
    )
    
    return entry


def _add_to_registry(entry: ModelRegistryEntry, models_dir: Path):
    """Add entry to JSON registry file."""
    registry_path = models_dir / "registry.json"
    
    # Load existing registry
    if registry_path.exists():
        with open(registry_path, "r") as f:
            registry = json.load(f)
    else:
        registry = {"models": []}
    
    # Deactivate previous champions for this asset
    for existing in registry["models"]:
        if existing.get("asset") == entry.asset and existing.get("is_active"):
            existing["is_active"] = False
    
    # Add new entry
    registry["models"].append(entry.to_dict())
    
    # Save registry
    models_dir.mkdir(parents=True, exist_ok=True)
    with open(registry_path, "w") as f:
        json.dump(registry, f, indent=2)
    
    logger.info("registry_updated", path=str(registry_path))


def get_latest_champion(asset: str, models_dir: Path = None) -> ModelRegistryEntry:
    """
    Load most recent active champion metadata for asset.
    
    Args:
        asset: Asset name
        models_dir: Models directory
        
    Returns:
        ModelRegistryEntry for active champion
        
    Raises:
        ModelNotFoundError: If no champion found
    """
    models_dir = models_dir or DEFAULT_MODELS_DIR
    registry_path = models_dir / "registry.json"
    
    if not registry_path.exists():
        raise ModelNotFoundError(asset)
    
    with open(registry_path, "r") as f:
        registry = json.load(f)
    
    # Find active champion for asset
    for entry_data in reversed(registry.get("models", [])):
        if entry_data.get("asset", "").upper() == asset.upper() and entry_data.get("is_active"):
            return ModelRegistryEntry.from_dict(entry_data)
    
    raise ModelNotFoundError(asset)


def load_champion_model(entry: ModelRegistryEntry) -> Any:
    """
    Load pickled model from artifact path.
    
    Args:
        entry: ModelRegistryEntry with artifact_path
        
    Returns:
        Loaded model object
    """
    artifact_path = Path(entry.artifact_path)
    
    if not artifact_path.exists():
        raise FileNotFoundError(f"Model artifact not found: {artifact_path}")
    
    with open(artifact_path, "rb") as f:
        model = pickle.load(f)
    
    logger.info("model_loaded", model_id=entry.id, model=entry.model_name)
    
    return model


def list_models(asset: str = None, models_dir: Path = None) -> list[ModelRegistryEntry]:
    """
    List all models in registry, optionally filtered by asset.
    
    Args:
        asset: Filter by asset (optional)
        models_dir: Models directory
        
    Returns:
        List of ModelRegistryEntry objects
    """
    models_dir = models_dir or DEFAULT_MODELS_DIR
    registry_path = models_dir / "registry.json"
    
    if not registry_path.exists():
        return []
    
    with open(registry_path, "r") as f:
        registry = json.load(f)
    
    entries = []
    for entry_data in registry.get("models", []):
        if asset is None or entry_data.get("asset", "").upper() == asset.upper():
            entries.append(ModelRegistryEntry.from_dict(entry_data))
    
    return entries
