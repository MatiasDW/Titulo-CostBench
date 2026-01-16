"""
Feature Engineering Module
Builds features for time series forecasting including lags and exogenous variables.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import pandas as pd
import numpy as np

from app.ml.logging_utils import get_features_logger
from app.ml.exceptions import DataValidationError

logger = get_features_logger()


@dataclass
class ValidationResult:
    """Result of feature DataFrame validation."""
    is_valid: bool
    issues: list[str]
    warnings: list[str]


def build_features(
    commodity_df: pd.DataFrame,
    cpi_df: pd.DataFrame = None,
    yields_df: pd.DataFrame = None,
    target_asset: str = "GOLD",
    lags: list[int] = None,
    include_exogenous: bool = True
) -> pd.DataFrame:
    """
    Merge commodity prices with exogenous features.
    
    Args:
        commodity_df: Commodity prices with [date, asset, price_usd]
        cpi_df: CPI data with [date, value, pct_change_12m] (optional)
        yields_df: Treasury yields with [date, yield_pct] (optional)
        target_asset: Asset to filter (default: GOLD)
        lags: List of lag periods (default: [1, 3, 6, 12])
        include_exogenous: Whether to include CPI and yields
        
    Returns:
        DataFrame with [date, price_usd, price_lag_*, cpi_yoy_12m, yield_10y]
        
    Logs:
        WARNING if exogenous series have gaps > 2 months
    """
    lags = lags or [1, 3, 6, 12]
    
    # 1. Filter commodity data to target asset
    if "asset" in commodity_df.columns:
        target_df = commodity_df[
            commodity_df["asset"].str.upper() == target_asset.upper()
        ].copy()
    else:
        target_df = commodity_df.copy()
    
    if target_df.empty:
        raise DataValidationError(
            dataset=f"commodity/{target_asset}",
            issues=[f"No data found for asset: {target_asset}"]
        )
    
    # Ensure date column
    target_df["date"] = pd.to_datetime(target_df["date"])
    target_df = target_df.sort_values("date").reset_index(drop=True)
    
    # Aggregate to monthly (if not already)
    target_df["month"] = target_df["date"].dt.to_period("M")
    features_df = target_df.groupby("month").agg({
        "price_usd": "last"  # Take last price of month
    }).reset_index()
    features_df["date"] = features_df["month"].dt.to_timestamp()
    features_df = features_df.drop(columns=["month"])
    
    logger.info(
        "base_data_prepared",
        asset=target_asset,
        rows=len(features_df),
        date_range=f"{features_df['date'].min()} to {features_df['date'].max()}"
    )
    
    # 2. Create lag features
    for lag in lags:
        features_df[f"price_lag_{lag}"] = features_df["price_usd"].shift(lag)
        logger.info("lag_feature_created", lag=lag)
    
    # 3. Create momentum features
    features_df["price_pct_change_1m"] = features_df["price_usd"].pct_change(1) * 100
    features_df["price_pct_change_3m"] = features_df["price_usd"].pct_change(3) * 100
    features_df["price_pct_change_12m"] = features_df["price_usd"].pct_change(12) * 100
    
    # 4. Add exogenous features
    if include_exogenous:
        features_df = _merge_exogenous(features_df, cpi_df, yields_df)
    
    # 5. Drop rows with NaN from lags (initial rows)
    initial_rows = len(features_df)
    features_df = features_df.dropna(subset=[f"price_lag_{lags[-1]}"])
    dropped_rows = initial_rows - len(features_df)
    
    logger.info(
        "features_complete",
        asset=target_asset,
        total_features=len(features_df.columns),
        rows=len(features_df),
        rows_dropped_for_lags=dropped_rows
    )
    
    return features_df.reset_index(drop=True)


def _merge_exogenous(
    features_df: pd.DataFrame,
    cpi_df: pd.DataFrame = None,
    yields_df: pd.DataFrame = None
) -> pd.DataFrame:
    """
    Left-join exogenous variables to features DataFrame.
    Handles missing data with forward-fill and warnings.
    """
    # Merge CPI
    if cpi_df is not None and not cpi_df.empty:
        cpi_df = cpi_df.copy()
        cpi_df["date"] = pd.to_datetime(cpi_df["date"])
        cpi_df["month"] = cpi_df["date"].dt.to_period("M")
        
        # Aggregate to monthly
        cpi_monthly = cpi_df.groupby("month").agg({
            "value": "last",
            "pct_change_12m": "last"
        }).reset_index()
        cpi_monthly["date"] = cpi_monthly["month"].dt.to_timestamp()
        cpi_monthly = cpi_monthly.rename(columns={
            "value": "cpi_value",
            "pct_change_12m": "cpi_yoy_12m"
        })
        
        features_df = features_df.merge(
            cpi_monthly[["date", "cpi_value", "cpi_yoy_12m"]],
            on="date",
            how="left"
        )
        
        # Check for missing values
        missing_cpi = features_df["cpi_yoy_12m"].isna().sum()
        if missing_cpi > 0:
            logger.warning(
                "exogenous_data_missing",
                feature="cpi_yoy_12m",
                missing_months=missing_cpi,
                fallback="forward_fill"
            )
            features_df["cpi_value"] = features_df["cpi_value"].ffill()
            features_df["cpi_yoy_12m"] = features_df["cpi_yoy_12m"].ffill()
    else:
        logger.warning(
            "exogenous_data_unavailable",
            feature="CPI",
            fallback="excluded"
        )
    
    # Merge Treasury Yields
    if yields_df is not None and not yields_df.empty:
        yields_df = yields_df.copy()
        yields_df["date"] = pd.to_datetime(yields_df["date"])
        yields_df = yields_df.rename(columns={"yield_pct": "yield_10y"})
        
        features_df = features_df.merge(
            yields_df[["date", "yield_10y"]],
            on="date",
            how="left"
        )
        
        # Check for missing values
        missing_yields = features_df["yield_10y"].isna().sum()
        if missing_yields > 0:
            logger.warning(
                "exogenous_data_missing",
                feature="yield_10y",
                missing_months=missing_yields,
                fallback="forward_fill"
            )
            features_df["yield_10y"] = features_df["yield_10y"].ffill()
    else:
        logger.warning(
            "exogenous_data_unavailable",
            feature="Treasury Yields",
            fallback="excluded"
        )
    
    return features_df


def validate_feature_df(df: pd.DataFrame) -> ValidationResult:
    """
    Schema and frequency validation for feature DataFrame.
    
    Checks:
        - Monthly frequency (no gaps > 35 days)
        - No future dates
        - price_usd > 0
        - No duplicate dates
        
    Returns:
        ValidationResult with is_valid, issues, and warnings
    """
    issues = []
    warnings = []
    
    if df.empty:
        issues.append("DataFrame is empty")
        return ValidationResult(is_valid=False, issues=issues, warnings=warnings)
    
    # Check required columns
    required = ["date", "price_usd"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        issues.append(f"Missing required columns: {missing}")
    
    # Check date column
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
        
        # No future dates
        future_dates = df[df["date"] > datetime.now()]
        if len(future_dates) > 0:
            issues.append(f"Found {len(future_dates)} future dates")
        
        # No duplicates
        duplicates = df["date"].duplicated().sum()
        if duplicates > 0:
            issues.append(f"Found {duplicates} duplicate dates")
        
        # Monthly frequency check
        df_sorted = df.sort_values("date")
        date_diffs = df_sorted["date"].diff().dt.days
        large_gaps = date_diffs[date_diffs > 35]
        if len(large_gaps) > 0:
            warnings.append(f"Found {len(large_gaps)} gaps > 35 days")
    
    # Price validation
    if "price_usd" in df.columns:
        null_prices = df["price_usd"].isna().sum()
        if null_prices > 0:
            issues.append(f"Found {null_prices} null prices")
        
        negative_prices = (df["price_usd"] <= 0).sum()
        if negative_prices > 0:
            issues.append(f"Found {negative_prices} non-positive prices")
    
    # Check exogenous coverage
    exogenous_cols = ["cpi_yoy_12m", "yield_10y"]
    for col in exogenous_cols:
        if col in df.columns:
            null_count = df[col].isna().sum()
            if null_count > df.shape[0] * 0.1:  # > 10% missing
                warnings.append(f"Exogenous {col} has {null_count} missing values ({null_count/len(df)*100:.1f}%)")
    
    is_valid = len(issues) == 0
    
    if is_valid:
        logger.info("validation_passed", rows=len(df), warnings=len(warnings))
    else:
        logger.error("validation_failed", issues=issues, warnings=warnings)
    
    return ValidationResult(is_valid=is_valid, issues=issues, warnings=warnings)


def get_feature_columns(df: pd.DataFrame) -> dict[str, list[str]]:
    """
    Categorize columns in feature DataFrame.
    
    Returns:
        Dict with keys: target, lags, exogenous, momentum
    """
    columns = {
        "target": ["price_usd"],
        "lags": [c for c in df.columns if c.startswith("price_lag_")],
        "exogenous": [c for c in df.columns if c in ["cpi_value", "cpi_yoy_12m", "yield_10y"]],
        "momentum": [c for c in df.columns if "pct_change" in c],
        "date": ["date"]
    }
    
    return columns
