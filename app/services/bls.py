"""
Service to fetch US CPI from BLS.
Series: CPIAUCSL (Consumer Price Index for All Urban Consumers: All Items in U.S. City Average)
"""
import logging
import os

import pandas as pd
import requests

logger = logging.getLogger(__name__)

BLS_API_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"


def fetch_cpi_bls(start_year='2023', end_year='2025', api_key=None):
    """
    Fetches CPI data from BLS.
    """
    key = api_key or os.getenv('BLS_API_KEY')

    headers = {'Content-type': 'application/json'}
    payload = {
        "seriesid": ["CUSR0000SA0"],
        "startyear": start_year,
        "endyear": end_year
    }

    if key:
        payload["registrationkey"] = key

    try:
        response = requests.post(BLS_API_URL, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        json_data = response.json()

        if json_data['status'] == 'REQUEST_NOT_PROCESSED':
            raise ValueError(f"BLS Error: {json_data['message']}")

        # Parse
        series = json_data['Results']['series'][0]
        data = series['data']

        # To DF
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['year'] + '-' + df['period'].str.replace('M', '') + '-01')
        df['value'] = pd.to_numeric(df['value'])
        df['series_id'] = 'CPIAUCSL'
        df['source'] = 'BLS'

        # Sort
        df = df.sort_values('date')

        return df[['date', 'value', 'series_id', 'source']]

    except Exception as e:
        logger.error("bls_fetch_failed: %s", e, exc_info=True)
        logger.warning("bls_falling_back_to_mock_data")
        dates = pd.date_range(start=f'{start_year}-01-01', end=f'{end_year}-12-01', freq='MS')
        return pd.DataFrame({
            'date': dates,
            'value': [300.0 + i for i in range(len(dates))],
            'series_id': 'CPIAUCSL_MOCK',
            'source': 'BLS_MOCK'
        })
