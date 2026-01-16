"""Data parsers for various sources."""
from bs4 import BeautifulSoup
import pandas as pd
from typing import Optional, Dict, Any
import re
import json


def parse_cmf_simulador(data: Any) -> pd.DataFrame:
    """
    Parse CMF simulador response (could be JSON or HTML).
    
    Args:
        data: Response data from CMF simulador
    
    Returns:
        DataFrame with checking account data
    """
    # Si es JSON
    if isinstance(data, dict) or isinstance(data, list):
        df = pd.DataFrame(data) if isinstance(data, list) else pd.DataFrame([data])
    else:
        # Si es HTML, intentar parsear
        soup = BeautifulSoup(str(data), 'lxml')
        tables = soup.find_all('table')
        
        if not tables:
            raise ValueError("No tables found in CMF response")
        
        dfs = []
        for table in tables:
            try:
                table_df = pd.read_html(str(table))[0]
                if len(table_df) > 0:
                    dfs.append(table_df)
            except Exception:
                continue
        
        if not dfs:
            raise ValueError("Could not parse any tables from CMF")
        
        df = max(dfs, key=len)
    
    # Add metadata
    df['source'] = 'CMF_SIMULADOR'
    df['extraction_date'] = pd.Timestamp.now()
    
    return df


def parse_sernac_cards(html_content: str) -> pd.DataFrame:
    """
    Parse SERNAC credit cards comparison table.
    
    Args:
        html_content: HTML content from SERNAC page
    
    Returns:
        DataFrame with credit card data
    """
    soup = BeautifulSoup(html_content, 'lxml')
    tables = soup.find_all('table')
    
    if not tables:
        raise ValueError("No tables found in SERNAC HTML content")
    
    dfs = []
    for table in tables:
        try:
            df = pd.read_html(str(table))[0]
            if len(df) > 0:
                dfs.append(df)
        except Exception:
            continue
    
    if not dfs:
        raise ValueError("Could not parse any tables from SERNAC HTML")
    
    result_df = max(dfs, key=len)
    
    # Add metadata
    result_df['source'] = 'SERNAC'
    result_df['extraction_date'] = pd.Timestamp.now()
    
    return result_df


def parse_bde_api_response(json_data: Dict[str, Any], indicator_name: str = 'UF') -> pd.DataFrame:
    """
    Parse Banco Central API JSON response.
    
    Args:
        json_data: JSON response from BDE API
        indicator_name: Name of the indicator (UF, IPC, etc.)
    
    Returns:
        DataFrame with indicator values
    """
    # La estructura del API del Banco Central puede variar
    # Intentar diferentes estructuras comunes
    
    df = None
    
    # Intentar estructura con 'Series'
    if 'Series' in json_data:
        series_data = json_data['Series']
        if isinstance(series_data, dict) and 'Obs' in series_data:
            df = pd.DataFrame(series_data['Obs'])
        elif isinstance(series_data, list) and len(series_data) > 0:
            if 'Obs' in series_data[0]:
                df = pd.DataFrame(series_data[0]['Obs'])
    
    # Intentar estructura directa con datos
    elif isinstance(json_data, list):
        df = pd.DataFrame(json_data)
    elif isinstance(json_data, dict) and 'data' in json_data:
        df = pd.DataFrame(json_data['data'])
    
    if df is None:
        raise ValueError(f"Unexpected JSON structure from BDE API: {list(json_data.keys())}")
    
    # Add metadata
    df['indicator'] = indicator_name
    df['source'] = 'BDE_API'
    df['extraction_date'] = pd.Timestamp.now()
    
    return df


def clean_currency_string(value: str) -> Optional[float]:
    """
    Clean currency strings and convert to float.
    
    Args:
        value: String like '$1.234' or '1.234,56'
    
    Returns:
        Float value or None
    """
    if pd.isna(value) or value == '':
        return None
    
    # Remove currency symbols and whitespace
    cleaned = re.sub(r'[$\s]', '', str(value))
    
    # Handle Chilean format (1.234,56) vs US format (1,234.56)
    if ',' in cleaned and '.' in cleaned:
        # Determine which is decimal separator
        last_comma = cleaned.rfind(',')
        last_dot = cleaned.rfind('.')
        
        if last_comma > last_dot:
            # Chilean format: 1.234,56
            cleaned = cleaned.replace('.', '').replace(',', '.')
        else:
            # US format: 1,234.56
            cleaned = cleaned.replace(',', '')
    elif ',' in cleaned:
        # Assume comma is decimal separator
        cleaned = cleaned.replace(',', '.')
    
    try:
        return float(cleaned)
    except ValueError:
        return None
