"""
Commodity Data Client
Fetches Gold and Copper prices from existing internal APIs or parquet files.
"""
import os
from datetime import datetime
from pathlib import Path

import pandas as pd

from app.ml.config import DATA_SOURCES
from app.ml.exceptions import DataFetchError, DataValidationError
from app.ml.logging_utils import get_ingest_logger

logger = get_ingest_logger()

# Default paths for parquet data
DEFAULT_MACRO_PATH = Path("data/market/macro_indicators.parquet")


def fetch_commodity_prices(
    assets: list[str] = None,
    start_date: str = "2015-01-01",
    parquet_path: Path = None
) -> pd.DataFrame:
    """
    Load commodity prices from existing data sources.
    
    Strategy:
        1. Try to read from parquet file (fastest)
        2. If parquet unavailable, call internal API
    
    Args:
        assets: List of assets to fetch (default: ["GOLD", "COPPER"])
        start_date: Filter data from this date onwards
        parquet_path: Path to macro indicators parquet file
        
    Returns:
        DataFrame with columns: [date, asset, price_usd]
        
    Raises:
        DataFetchError: If data cannot be loaded
    """
    assets = assets or ["GOLDAMGBD228NLBM", "PCOPPUSDM"]
    parquet_path = parquet_path or DEFAULT_MACRO_PATH
    
    # Try parquet first
    if parquet_path.exists():
        try:
            df = _load_from_parquet(parquet_path, assets, start_date)
            logger.info(
                "data_fetch_complete",
                source="parquet",
                path=str(parquet_path),
                assets=assets,
                rows=len(df)
            )
            return df
        except Exception as e:
            logger.warning(
                "parquet_load_failed",
                path=str(parquet_path),
                error=str(e)
            )
    
    # Fallback: try individual series parquet files
    df = _load_from_series_files(assets, start_date)
    if not df.empty:
        return df
    
    raise DataFetchError(
        source="commodity",
        reason=f"No data source available for assets: {assets}"
    )


def _load_from_parquet(
    parquet_path: Path, 
    assets: list[str], 
    start_date: str
) -> pd.DataFrame:
    """
    Load commodity data from macro_indicators parquet.
    """
    df = pd.read_parquet(parquet_path)
    
    # Find columns that match our assets
    # The macro parquet has various series - filter to commodities
    commodity_cols = [c for c in df.columns if any(
        a.upper() in c.upper() for a in ["GOLD", "COPPER", "PCOPPUSDM", "GOLDAMGBD"]
    )]
    
    if "date" in df.columns:
        date_col = "date"
    elif "index" in df.columns:
        date_col = "index"
    else:
        # Assume index is date
        df = df.reset_index()
        date_col = df.columns[0]
    
    if not commodity_cols:
        raise DataValidationError(
            dataset="macro_indicators",
            issues=["No commodity columns found in parquet"]
        )
    
    # Melt to long format
    df[date_col] = pd.to_datetime(df[date_col])
    df = df[df[date_col] >= start_date]
    
    records = []
    for col in commodity_cols:
        asset_name = _normalize_asset_name(col)
        for _, row in df.iterrows():
            if pd.notna(row.get(col)):
                records.append({
                    "date": row[date_col],
                    "asset": asset_name,
                    "price_usd": float(row[col])
                })
    
    return pd.DataFrame(records)


def _load_from_series_files(assets: list[str], start_date: str) -> pd.DataFrame:
    """
    Load from individual series parquet files in data/market/.
    """
    market_dir = Path("data/market")
    records = []
    
    for asset in assets:
        # Try different naming conventions
        possible_files = [
            market_dir / f"{asset}.parquet",
            market_dir / f"{asset.lower()}.parquet",
            market_dir / f"series_{asset}.parquet"
        ]
        
        for file_path in possible_files:
            if file_path.exists():
                try:
                    df = pd.read_parquet(file_path)
                    
                    # Normalize column names
                    df.columns = df.columns.str.lower()
                    
                    if "date" in df.columns:
                        df["date"] = pd.to_datetime(df["date"])
                    else:
                        df = df.reset_index()
                        df.columns = ["date"] + list(df.columns[1:])
                        df["date"] = pd.to_datetime(df["date"])
                    
                    df = df[df["date"] >= start_date]
                    
                    # Find value column
                    value_col = None
                    for col in ["value", "close", "price", asset.lower()]:
                        if col in df.columns:
                            value_col = col
                            break
                    
                    if value_col:
                        for _, row in df.iterrows():
                            if pd.notna(row[value_col]):
                                records.append({
                                    "date": row["date"],
                                    "asset": _normalize_asset_name(asset),
                                    "price_usd": float(row[value_col])
                                })
                        
                        logger.info(
                            "series_file_loaded",
                            asset=asset,
                            path=str(file_path),
                            rows=len(df)
                        )
                        break
                        
                except Exception as e:
                    logger.warning(
                        "series_file_error",
                        asset=asset,
                        path=str(file_path),
                        error=str(e)
                    )
    
    return pd.DataFrame(records)


def _normalize_asset_name(raw_name: str) -> str:
    """
    Normalize asset name to standard format.
    
    Examples:
        GOLDAMGBD228NLBM -> GOLD
        PCOPPUSDM -> COPPER
    """
    raw_upper = raw_name.upper()
    
    if "GOLD" in raw_upper:
        return "GOLD"
    elif "COPP" in raw_upper or "PCOPPUSDM" in raw_upper:
        return "COPPER"
    elif "OIL" in raw_upper or "WTICO" in raw_upper:
        return "OIL"
    else:
        return raw_name.upper()


def get_asset_series_id(asset: str) -> str:
    """
    Get the series ID for a given asset name.
    
    Args:
        asset: Asset name (GOLD, COPPER)
        
    Returns:
        Series ID for internal API calls
    """
    mapping = {
        "GOLD": DATA_SOURCES.gold_series,
        "COPPER": DATA_SOURCES.copper_series,
    }
    return mapping.get(asset.upper(), asset)


def validate_commodity_data(df: pd.DataFrame) -> list[str]:
    """
    Validate commodity DataFrame for common issues.
    
    Args:
        df: Commodity DataFrame to validate
        
    Returns:
        List of validation issues (empty if valid)
    """
    issues = []
    
    if df.empty:
        issues.append("DataFrame is empty")
        return issues
    
    # Check required columns
    required = ["date", "asset", "price_usd"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        issues.append(f"Missing columns: {missing}")
    
    # Check for nulls
    null_count = df["price_usd"].isna().sum()
    if null_count > 0:
        issues.append(f"Found {null_count} null prices")
    
    # Check price range (should be positive)
    if (df["price_usd"] <= 0).any():
        issues.append("Found non-positive prices")
    
    # Check assets
    expected_assets = {"GOLD", "COPPER"}
    found_assets = set(df["asset"].unique())
    missing_assets = expected_assets - found_assets
    if missing_assets:
        issues.append(f"Missing assets: {missing_assets}")
    
    return issues
