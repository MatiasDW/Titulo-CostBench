"""Parquet I/O utilities with resilient read (retry-on-write-collision)."""
import logging
import time

import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional
import json

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Retry config – protects against scheduler overwriting a .parquet file at
# the exact millisecond a user request tries to read it.
# ---------------------------------------------------------------------------
_READ_MAX_RETRIES = 3
_READ_BACKOFF_BASE = 0.05  # 50 ms → 150 ms → 450 ms


def write_parquet(df: pd.DataFrame, filepath: Path, compression: str = 'snappy') -> Dict[str, Any]:
    """
    Write DataFrame to Parquet file.
    
    Args:
        df: DataFrame to write
        filepath: Path to output file
        compression: Compression algorithm (snappy, gzip, brotli)
    
    Returns:
        Metadata about the written file
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_parquet(
        filepath,
        engine='pyarrow',
        compression=compression,
        index=False
    )
    
    return {
        'filepath': str(filepath),
        'rows': len(df),
        'columns': len(df.columns),
        'size_bytes': filepath.stat().st_size
    }


def read_parquet(filepath: Path) -> pd.DataFrame:
    """
    Read Parquet file into DataFrame **with retry logic**.

    If the file is being overwritten by the scheduler at the exact moment
    a user request arrives, the underlying I/O call may raise ``OSError``
    or ``pyarrow.lib.ArrowInvalid``.  This wrapper retries up to
    ``_READ_MAX_RETRIES`` times with exponential back-off before
    propagating the exception.

    Args:
        filepath: Path to Parquet file

    Returns:
        DataFrame

    Raises:
        FileNotFoundError: if the file does not exist at all.
        Exception: after exhausting all retries.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Parquet file not found: {filepath}")

    last_exc: Exception | None = None

    for attempt in range(_READ_MAX_RETRIES + 1):
        try:
            return pd.read_parquet(filepath, engine='pyarrow')
        except (OSError, Exception) as exc:
            # Only retry on I/O-level or Arrow corruption errors.
            exc_name = type(exc).__name__
            is_retryable = (
                isinstance(exc, OSError)
                or 'Arrow' in exc_name
                or 'Parquet' in exc_name
            )
            if not is_retryable:
                raise

            last_exc = exc
            if attempt < _READ_MAX_RETRIES:
                wait = _READ_BACKOFF_BASE * (3 ** attempt)
                logger.warning(
                    "Parquet read failed (attempt %d/%d, retrying in %.0f ms): %s – %s",
                    attempt + 1, _READ_MAX_RETRIES + 1, wait * 1000,
                    filepath.name, exc,
                )
                time.sleep(wait)
            else:
                logger.error(
                    "Parquet read exhausted retries for %s: %s",
                    filepath.name, exc,
                )

    # Should not reach here, but satisfy the type checker
    raise last_exc  # type: ignore[misc]


def profile_parquet(filepath: Path, sample_rows: int = 5) -> Dict[str, Any]:
    """
    Profile a Parquet file to understand its structure.
    
    Args:
        filepath: Path to Parquet file
        sample_rows: Number of sample rows to include
    
    Returns:
        Profile information including columns, dtypes, stats, and sample data
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Parquet file not found: {filepath}")
    
    df = read_parquet(filepath)
    
    # Column information
    columns_info = []
    for col in df.columns:
        col_info = {
            'name': col,
            'dtype': str(df[col].dtype),
            'null_count': int(df[col].isnull().sum()),
            'null_percentage': float(df[col].isnull().sum() / len(df) * 100) if len(df) > 0 else 0
        }
        
        # Add basic stats for numeric columns
        if pd.api.types.is_numeric_dtype(df[col]):
            col_info['min'] = float(df[col].min()) if not df[col].isnull().all() else None
            col_info['max'] = float(df[col].max()) if not df[col].isnull().all() else None
            col_info['mean'] = float(df[col].mean()) if not df[col].isnull().all() else None
        
        # Add unique count for object/string columns
        if pd.api.types.is_object_dtype(df[col]) or pd.api.types.is_string_dtype(df[col]):
            col_info['unique_count'] = int(df[col].nunique())
            col_info['sample_values'] = df[col].dropna().unique()[:5].tolist()
        
        columns_info.append(col_info)
    
    # Sample data
    sample_data = df.head(sample_rows).to_dict(orient='records')
    
    # Convert any non-JSON-serializable types
    for record in sample_data:
        for key, value in record.items():
            if pd.isna(value):
                record[key] = None
            elif isinstance(value, (pd.Timestamp, pd.DatetimeTZDtype)):
                record[key] = str(value)
    
    return {
        'filepath': str(filepath),
        'file_size_bytes': filepath.stat().st_size,
        'total_rows': len(df),
        'total_columns': len(df.columns),
        'columns': columns_info,
        'sample_data': sample_data,
        'memory_usage_bytes': int(df.memory_usage(deep=True).sum())
    }


def list_parquet_files(data_dir: Path) -> list:
    """
    List all Parquet files in the data directory.
    
    Args:
        data_dir: Path to data directory
    
    Returns:
        List of Parquet file paths
    """
    if not data_dir.exists():
        return []
    
    return [str(f.relative_to(data_dir)) for f in data_dir.rglob('*.parquet')]
