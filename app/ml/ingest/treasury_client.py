"""
U.S. Treasury Fiscal Data API Client
Fetches Treasury yields (10Y, etc.) with retry logic and validation.
"""
import time
from datetime import datetime

import pandas as pd
import requests

from app.ml.config import HTTP_CONFIG, DATA_SOURCES
from app.ml.exceptions import DataFetchError, DataValidationError
from app.ml.logging_utils import get_ingest_logger

logger = get_ingest_logger()


def fetch_treasury_yields(
    maturity: str = "10-Year",
    months: int = 120,
    timeout: float = None,
    max_retries: int = None
) -> pd.DataFrame:
    """
    Fetch average interest rates from Treasury Fiscal Data API.
    
    Args:
        maturity: Security term (default: "10-Year")
        months: Number of months of history to fetch (default: 120)
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts
        
    Returns:
        DataFrame with columns: [date, yield_pct]
        
    Raises:
        DataFetchError: On persistent failure after retries
        DataValidationError: If response schema is invalid
    """
    timeout = timeout or HTTP_CONFIG.timeout
    max_retries = max_retries or HTTP_CONFIG.max_retries
    
    base_url = DATA_SOURCES.treasury_base_url
    endpoint = DATA_SOURCES.treasury_yields_endpoint
    
    # Build query parameters
    params = {
        "filter": f"security_desc:eq:Treasury Notes,security_term:eq:{maturity}",
        "sort": "-record_date",
        "page[size]": str(months)
    }
    
    url = f"{base_url}{endpoint}"
    
    last_error = None
    for attempt in range(max_retries):
        try:
            start_time = time.time()
            
            response = requests.get(url, params=params, timeout=timeout)
            
            duration_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                df = _parse_treasury_response(data, maturity)
                
                logger.info(
                    "data_fetch_complete",
                    source="Treasury",
                    maturity=maturity,
                    rows=len(df),
                    duration_ms=round(duration_ms, 2)
                )
                
                return df
            
            elif response.status_code in HTTP_CONFIG.retry_status_codes:
                last_error = f"HTTP {response.status_code}"
                logger.warning(
                    "fetch_retry",
                    source="Treasury",
                    attempt=attempt + 1,
                    status_code=response.status_code
                )
            else:
                raise DataFetchError(
                    source="Treasury",
                    reason=f"HTTP {response.status_code}: {response.text[:200]}",
                    status_code=response.status_code
                )
                
        except requests.exceptions.Timeout:
            last_error = "Timeout"
            logger.warning(
                "fetch_timeout",
                source="Treasury",
                attempt=attempt + 1,
                timeout=timeout
            )
        except requests.exceptions.ConnectionError as e:
            last_error = f"Connection error: {e}"
            logger.warning(
                "fetch_connection_error",
                source="Treasury",
                attempt=attempt + 1,
                error=str(e)
            )
        
        # Exponential backoff
        if attempt < max_retries - 1:
            sleep_time = HTTP_CONFIG.backoff_factor ** attempt
            time.sleep(sleep_time)
    
    raise DataFetchError(
        source="Treasury",
        reason=f"Failed after {max_retries} attempts. Last error: {last_error}"
    )


def _parse_treasury_response(data: dict, maturity: str) -> pd.DataFrame:
    """
    Parse Treasury API response into DataFrame.
    
    Args:
        data: Raw API response
        maturity: Security term for logging
        
    Returns:
        DataFrame with date and yield_pct columns
    """
    try:
        records_data = data.get("data", [])
    except (KeyError, AttributeError) as e:
        raise DataValidationError(
            dataset=f"Treasury/{maturity}",
            issues=[f"Invalid response structure: {e}"]
        )
    
    if not records_data:
        raise DataValidationError(
            dataset=f"Treasury/{maturity}",
            issues=["No data returned from API"]
        )
    
    records = []
    for item in records_data:
        try:
            date_str = item.get("record_date")
            rate_str = item.get("avg_interest_rate_amt")
            
            if not date_str or not rate_str:
                continue
            
            date = datetime.strptime(date_str, "%Y-%m-%d")
            yield_pct = float(rate_str)
            
            records.append({
                "date": date,
                "yield_pct": yield_pct
            })
        except (ValueError, KeyError) as e:
            logger.warning(
                "parse_item_error",
                source="Treasury",
                item=item,
                error=str(e)
            )
            continue
    
    if not records:
        raise DataValidationError(
            dataset=f"Treasury/{maturity}",
            issues=["No valid records parsed from response"]
        )
    
    df = pd.DataFrame(records)
    df = df.sort_values("date").reset_index(drop=True)
    
    # Aggregate to monthly (first of month)
    df["month"] = df["date"].dt.to_period("M")
    df_monthly = df.groupby("month").agg({
        "yield_pct": "mean"  # Average for the month
    }).reset_index()
    df_monthly["date"] = df_monthly["month"].dt.to_timestamp()
    df_monthly = df_monthly.drop(columns=["month"])
    
    return df_monthly[["date", "yield_pct"]]


def validate_yields_data(df: pd.DataFrame) -> list[str]:
    """
    Validate Treasury yields DataFrame for common issues.
    
    Args:
        df: Yields DataFrame to validate
        
    Returns:
        List of validation issues (empty if valid)
    """
    issues = []
    
    if df.empty:
        issues.append("DataFrame is empty")
        return issues
    
    # Check required columns
    required = ["date", "yield_pct"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        issues.append(f"Missing columns: {missing}")
    
    # Check for nulls
    null_count = df["yield_pct"].isna().sum()
    if null_count > 0:
        issues.append(f"Found {null_count} null values")
    
    # Check value range (yields should be reasonable 0-20%)
    if (df["yield_pct"] < 0).any() or (df["yield_pct"] > 20).any():
        issues.append("Found yields outside 0-20% range")
    
    return issues
