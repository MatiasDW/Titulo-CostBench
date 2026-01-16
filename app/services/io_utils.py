"""Parquet I/O utilities."""
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional
import json


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
    Read Parquet file into DataFrame.
    
    Args:
        filepath: Path to Parquet file
    
    Returns:
        DataFrame
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Parquet file not found: {filepath}")
    
    return pd.read_parquet(filepath, engine='pyarrow')


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
