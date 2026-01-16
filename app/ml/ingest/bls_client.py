"""
BLS (Bureau of Labor Statistics) API Client
Fetches CPI data with retry logic and validation.
"""
import time
from datetime import datetime
from typing import Any

import pandas as pd
import requests

from app.ml.config import HTTP_CONFIG, DATA_SOURCES
from app.ml.exceptions import DataFetchError, DataValidationError
from app.ml.logging_utils import get_ingest_logger

logger = get_ingest_logger()


def fetch_cpi_series(
    series_id: str = None,
    start_year: int = 2015,
    end_year: int | None = None,
    timeout: float = None,
    max_retries: int = None
) -> pd.DataFrame:
    """
    Fetch CPI data from BLS API with retry logic.
    
    Args:
        series_id: BLS series ID (default: CUUR0000SA0 - CPI-U All Items SA)
        start_year: Start year for data (default: 2015)
        end_year: End year for data (default: current year)
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts
        
    Returns:
        DataFrame with columns: [date, value, pct_change_1m, pct_change_12m]
        
    Raises:
        DataFetchError: On persistent failure after retries
        DataValidationError: If response schema is invalid
    """
    # Apply defaults
    series_id = series_id or DATA_SOURCES.bls_cpi_series
    end_year = end_year or datetime.now().year
    timeout = timeout or HTTP_CONFIG.timeout
    max_retries = max_retries or HTTP_CONFIG.max_retries
    
    url = DATA_SOURCES.bls_base_url
    payload = {
        "seriesid": [series_id],
        "startyear": str(start_year),
        "endyear": str(end_year),
        "calculations": True
    }
    
    headers = {"Content-Type": "application/json"}
    
    last_error = None
    for attempt in range(max_retries):
        try:
            start_time = time.time()
            
            response = requests.post(
                url, 
                json=payload, 
                headers=headers, 
                timeout=timeout
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("status") != "REQUEST_SUCCEEDED":
                    raise DataFetchError(
                        source="BLS",
                        reason=f"API returned status: {data.get('status')}",
                        status_code=response.status_code
                    )
                
                df = _parse_bls_response(data, series_id)
                
                logger.info(
                    "data_fetch_complete",
                    source="BLS",
                    series=series_id,
                    rows=len(df),
                    duration_ms=round(duration_ms, 2),
                    start_year=start_year,
                    end_year=end_year
                )
                
                return df
            
            elif response.status_code in HTTP_CONFIG.retry_status_codes:
                last_error = f"HTTP {response.status_code}"
                logger.warning(
                    "fetch_retry",
                    source="BLS",
                    attempt=attempt + 1,
                    status_code=response.status_code
                )
            else:
                raise DataFetchError(
                    source="BLS",
                    reason=f"HTTP {response.status_code}: {response.text[:200]}",
                    status_code=response.status_code
                )
                
        except requests.exceptions.Timeout:
            last_error = "Timeout"
            logger.warning(
                "fetch_timeout",
                source="BLS",
                attempt=attempt + 1,
                timeout=timeout
            )
        except requests.exceptions.ConnectionError as e:
            last_error = f"Connection error: {e}"
            logger.warning(
                "fetch_connection_error",
                source="BLS",
                attempt=attempt + 1,
                error=str(e)
            )
        
        # Exponential backoff
        if attempt < max_retries - 1:
            sleep_time = HTTP_CONFIG.backoff_factor ** attempt
            time.sleep(sleep_time)
    
    raise DataFetchError(
        source="BLS",
        reason=f"Failed after {max_retries} attempts. Last error: {last_error}"
    )


def _parse_bls_response(data: dict, series_id: str) -> pd.DataFrame:
    """
    Parse BLS API response into DataFrame.
    
    Args:
        data: Raw API response
        series_id: Series ID for validation
        
    Returns:
        DataFrame with date, value, and percentage changes
    """
    try:
        series_data = data["Results"]["series"][0]["data"]
    except (KeyError, IndexError) as e:
        raise DataValidationError(
            dataset=f"BLS/{series_id}",
            issues=[f"Invalid response structure: {e}"]
        )
    
    records = []
    for item in series_data:
        try:
            year = int(item["year"])
            period = item["period"]
            
            # Skip annual data (M13)
            if period == "M13":
                continue
                
            month = int(period.replace("M", ""))
            date = datetime(year, month, 1)
            value = float(item["value"])
            
            # Extract percentage changes if available
            pct_1m = None
            pct_12m = None
            if "calculations" in item and "pct_changes" in item["calculations"]:
                pct_changes = item["calculations"]["pct_changes"]
                pct_1m = float(pct_changes.get("1", 0)) if pct_changes.get("1") else None
                pct_12m = float(pct_changes.get("12", 0)) if pct_changes.get("12") else None
            
            records.append({
                "date": date,
                "value": value,
                "pct_change_1m": pct_1m,
                "pct_change_12m": pct_12m
            })
        except (ValueError, KeyError) as e:
            logger.warning(
                "parse_item_error",
                source="BLS",
                item=item,
                error=str(e)
            )
            continue
    
    if not records:
        raise DataValidationError(
            dataset=f"BLS/{series_id}",
            issues=["No valid records parsed from response"]
        )
    
    df = pd.DataFrame(records)
    df = df.sort_values("date").reset_index(drop=True)
    
    return df


def validate_cpi_data(df: pd.DataFrame) -> list[str]:
    """
    Validate CPI DataFrame for common issues.
    
    Args:
        df: CPI DataFrame to validate
        
    Returns:
        List of validation issues (empty if valid)
    """
    issues = []
    
    if df.empty:
        issues.append("DataFrame is empty")
        return issues
    
    # Check required columns
    required = ["date", "value"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        issues.append(f"Missing columns: {missing}")
    
    # Check for nulls in value
    null_count = df["value"].isna().sum()
    if null_count > 0:
        issues.append(f"Found {null_count} null values")
    
    # Check value range (CPI should be positive)
    if (df["value"] <= 0).any():
        issues.append("Found non-positive values")
    
    # Check date gaps (monthly data)
    df_sorted = df.sort_values("date")
    date_diffs = df_sorted["date"].diff().dt.days
    large_gaps = date_diffs[date_diffs > 35].count()
    if large_gaps > 0:
        issues.append(f"Found {large_gaps} gaps > 35 days")
    
    return issues
