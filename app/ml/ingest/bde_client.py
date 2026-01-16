"""
BDE (Banco Central de Chile) Client
Fetches USD/CLP and UF from official SIETE API.
"""
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

from app.ml.logging_utils import get_logger
from app.ml.exceptions import DataFetchError

logger = get_logger("ml.ingest.bde")

# Try bcchapi first
try:
    from bcchapi import Siete
    BCCHAPI_AVAILABLE = True
except ImportError:
    BCCHAPI_AVAILABLE = False
    logger.warning("bcchapi_not_available")


# BDE Series IDs
SERIES_IDS = {
    "USDCLP": "F073.TCO.PRE.Z.D",       # Tipo de cambio observado USD/CLP diario
    "UF": "F073.UFF.PRE.Z.D",            # Unidad de Fomento diaria
}


def fetch_usdclp(
    start_date: str = "2015-01-01",
    end_date: str = None,
    aggregate_monthly: bool = True
) -> pd.DataFrame:
    """Fetch USD/CLP exchange rate from Banco Central."""
    series_id = SERIES_IDS["USDCLP"]
    end_date = end_date or datetime.now().strftime("%Y-%m-%d")
    
    df = _fetch_bde_series(series_id, start_date, end_date, "USD/CLP")
    
    if aggregate_monthly and not df.empty:
        df = _aggregate_to_monthly(df)
    
    return df


def fetch_uf(
    start_date: str = "2015-01-01",
    end_date: str = None,
    aggregate_monthly: bool = True
) -> pd.DataFrame:
    """Fetch UF (Unidad de Fomento) from Banco Central."""
    series_id = SERIES_IDS["UF"]
    end_date = end_date or datetime.now().strftime("%Y-%m-%d")
    
    df = _fetch_bde_series(series_id, start_date, end_date, "UF")
    
    if aggregate_monthly and not df.empty:
        df = _aggregate_to_monthly(df)
    
    return df


def _fetch_bde_series(
    series_id: str,
    start_date: str,
    end_date: str,
    series_name: str
) -> pd.DataFrame:
    """Fetch series from BDE using bcchapi or requests fallback."""
    # Check credentials
    bde_user = os.getenv("BDE_USER")
    bde_pass = os.getenv("BDE_PASS")
    
    if not bde_user or not bde_pass:
        raise DataFetchError(
            source="BDE",
            reason="BDE_USER and BDE_PASS environment variables required"
        )
    
    if BCCHAPI_AVAILABLE:
        return _fetch_via_bcchapi(series_id, start_date, end_date, series_name)
    else:
        return _fetch_via_requests(series_id, start_date, end_date, series_name, bde_user, bde_pass)


def _fetch_via_bcchapi(
    series_id: str,
    start_date: str,
    end_date: str,
    series_name: str
) -> pd.DataFrame:
    """Fetch using bcchapi library with cuadro() method."""
    try:
        user = os.getenv("BDE_USER")
        pwd = os.getenv("BDE_PASS")
        
        siete = Siete(usr=user, pwd=pwd)
        
        # cuadro() expects series as a list
        df = siete.cuadro(
            series=[series_id],
            desde=start_date,
            hasta=end_date
        )
        
        if df is None or df.empty:
            logger.warning("bde_empty_response", series=series_name)
            return pd.DataFrame(columns=["date", "value", "series_id"])
        
        # cuadro returns df with index=date, column=series_id
        df = df.reset_index()
        df.columns = ["date", "value"]
        df["series_id"] = series_id
        df["date"] = pd.to_datetime(df["date"])
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df = df.dropna(subset=["value"])
        
        logger.info("bde_series_fetched", series=series_name, rows=len(df))
        
        return df
        
    except Exception as e:
        logger.error("bde_fetch_failed", series=series_name, error=str(e))
        raise DataFetchError(source="BDE", reason=str(e))


def _fetch_via_requests(
    series_id: str,
    start_date: str,
    end_date: str,
    series_name: str,
    user: str,
    password: str
) -> pd.DataFrame:
    """Fallback: Fetch using requests if bcchapi not available."""
    import requests
    
    base_url = "https://si3.bcentral.cl/SieteRestWS/SieteRestWS.ashx"
    
    params = {
        "user": user,
        "pass": password,
        "firstdate": start_date,
        "lastdate": end_date,
        "timeseries": series_id,
        "function": "GetSeries"
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if "Series" not in data or not data["Series"]:
            return pd.DataFrame(columns=["date", "value", "series_id"])
        
        series = data["Series"][0]
        obs = series.get("Obs", [])
        
        records = []
        for ob in obs:
            records.append({
                "date": ob.get("indexDateString"),
                "value": float(ob.get("value", 0)),
                "series_id": series_id
            })
        
        df = pd.DataFrame(records)
        df["date"] = pd.to_datetime(df["date"])
        
        logger.info("bde_series_fetched_requests", series=series_name, rows=len(df))
        
        return df
        
    except Exception as e:
        logger.error("bde_requests_failed", series=series_name, error=str(e))
        raise DataFetchError(source="BDE", reason=str(e))


def _aggregate_to_monthly(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate daily data to monthly (last value of month)."""
    df = df.copy()
    df["month"] = df["date"].dt.to_period("M")
    
    df_monthly = df.groupby("month").agg({
        "value": "last",
        "series_id": "first"
    }).reset_index()
    
    df_monthly["date"] = df_monthly["month"].dt.to_timestamp()
    df_monthly = df_monthly.drop(columns=["month"])
    
    return df_monthly[["date", "value", "series_id"]]


def test_connection() -> dict:
    """Test BDE connection with a minimal query."""
    try:
        df = fetch_usdclp(start_date="2024-01-01", aggregate_monthly=False)
        return {
            "status": "ok",
            "rows": len(df),
            "latest_date": str(df["date"].max()) if len(df) > 0 else None,
            "latest_value": float(df["value"].iloc[-1]) if len(df) > 0 else None
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
