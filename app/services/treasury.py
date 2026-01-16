"""
Service to fetch US Treasury Yields (DGS10).
Source: US Treasury Fiscal Data API (public).
Dataset: daily_treasury_yield_curve
"""
import requests
import pandas as pd
from datetime import datetime

TREASURY_API_URL = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/daily_treasury_yield_curve"

def fetch_treasury_yields(start_date='2023-01-01'):
    """
    Fetches 10-Year Treasury Yields (DGS10 equivalent).
    """
    params = {
        'fields': 'record_date,tc_10year',
        'filter': f'record_date:gte:{start_date}',
        'page[size]': 10000
    }
    
    try:
        response = requests.get(TREASURY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        json_data = response.json()
        
        data = json_data['data']
        df = pd.DataFrame(data)
        
        # Parse
        df['date'] = pd.to_datetime(df['record_date'])
        df['value'] = pd.to_numeric(df['tc_10year'])
        df['series_id'] = 'DGS10'
        df['source'] = 'TREASURY'
        df = df.dropna(subset=['value'])
        
        # Aggregate to monthly? Brief says: "yields diarios agregados a promedio mensual"
        df.set_index('date', inplace=True)
        monthly = df['value'].resample('ME').mean().reset_index() # 'M' is deprecated, 'ME' for month end
        
        monthly['series_id'] = 'DGS10'
        monthly['source'] = 'TREASURY'
        
        return monthly[['date', 'value', 'series_id', 'source']]
        
    except Exception as e:
        print(f"Failed to fetch Treasury: {e}")
        # Mock
        print("Returning MOCK Treasury data")
        dates = pd.date_range(start=start_date, end=datetime.now(), freq='ME')
        return pd.DataFrame({
            'date': dates,
            'value': [4.0] * len(dates),
            'series_id': 'DGS10_MOCK',
            'source': 'TREASURY_MOCK'
        })
