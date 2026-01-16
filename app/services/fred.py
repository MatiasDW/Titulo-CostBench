import os
import requests
import pandas as pd
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

FRED_API_URL = "https://api.stlouisfed.org/fred/series/observations"

def fetch_fred_series(series_id, api_key=None):
    """
    Fetches historical data for a given series_id from FRED API.
    Returns a DataFrame with columns ['date', 'value', 'series_id'].
    """
    if not api_key:
        api_key = os.environ.get('FRED_API_KEY')
        
    if not api_key:
        logger.warning(f"No FRED_API_KEY found. Returning mock data for {series_id}.")
        return _get_mock_data(series_id)

    params = {
        'series_id': series_id,
        'api_key': api_key,
        'file_type': 'json',
        'sort_order': 'asc'
    }

    try:
        response = requests.get(FRED_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        observations = data.get('observations', [])
        if not observations:
            logger.warning(f"No observations found for {series_id}")
            return _get_mock_data(series_id)
            
        df = pd.DataFrame(observations)
        if df.empty:
             return _get_mock_data(series_id)

        # Clean up
        df['date'] = pd.to_datetime(df['date'])
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        df['series_id'] = series_id
        df['source'] = 'FRED'
        
        # Select relevant columns
        result = df[['date', 'value', 'series_id', 'source']].sort_values('date').dropna()
        
        logger.info(f"Successfully fetched {len(result)} rows for {series_id} from FRED")
        return result

    except Exception as e:
        logger.error(f"Error fetching {series_id} from FRED: {e}")
        return _get_mock_data(series_id)

def _get_mock_data(series_id):
    """Fallback mock data if API fails or no key."""
    dates = pd.date_range(end=datetime.today(), periods=24, freq='MS')
    
    if series_id == 'CPIAUCSL':
        # Mock CPI ~300-350
        base = 300
        values = [base + i*1.5 + (i%3) for i in range(len(dates))]
    elif series_id == 'DGS10':
        # Mock Yield ~3.5-4.5%
        values = [3.5 + (i%10)/10.0 for i in range(len(dates))]
    elif series_id == 'GOLDAMGBD228NLBM':
        # Mock Gold ~2000-2500
        values = [2000 + i*20 for i in range(len(dates))]
    elif series_id == 'PCOPPUSDM':
        # Mock Copper ~8000-9000
        values = [8500 + i*50 for i in range(len(dates))]
    elif series_id == 'DCOILWTICO':
        # Mock Oil ~70-80
        values = [75 + (i%5) for i in range(len(dates))]
    else:
        values = [100 for _ in range(len(dates))]
        
    return pd.DataFrame({
        'date': dates,
        'value': values,
        'series_id': series_id,
        'source': 'FRED_MOCK'
    })
