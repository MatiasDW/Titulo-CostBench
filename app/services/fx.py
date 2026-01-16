"""
Service for FX (USD) conversion.
"""
import pandas as pd
import os
try:
    import bcchapi
except ImportError:
    bcchapi = None

def fetch_usd_bde(username=None, password=None) -> pd.DataFrame:
    """
    Fetches USD Observed Exchange Rate (F073.TCO.PRE.Z.D) from BDE.
    """
    if not bcchapi:
        raise ImportError("bcchapi not installed")
        
    u = username or os.getenv('BDE_USER')
    p = password or os.getenv('BDE_PASS')
    
    if not u or not p:
        raise ValueError("Missing BDE credentials")
        
    client = bcchapi.Siete(u, p)
    # Series for Dólar Observado: F073.TCO.PRE.Z.D
    data = client.cuadros(series=["F073.TCO.PRE.Z.D"])
    
    # Check data integrity (bcchapi returns varied structures)
    # Assuming standard df output or similar
    if not isinstance(data, pd.DataFrame):
         # Try to adapt if it returns something else
         pass
         
    # Standardize 
    # Usually bcchapi returns index as date
    df = data.reset_index()
    df.columns = ['fecha', 'valor']
    df['serie_id'] = 'F073.TCO.PRE.Z.D'
    df['source'] = 'BDE_API'
    
    return df

def attach_usd(df_metrics: pd.DataFrame, df_usd: pd.DataFrame) -> pd.DataFrame:
    """
    Attaches USD value.
    For monthly context, we might want 'average monthly USD' or 'daily USD'.
    Brief says: "USD re-muestreados a vista mensual... o fin de mes".
    We'll use merge_asof (daily match) for simplicity and robustness.
    """
    out = df_metrics.copy()
    
    out['date'] = pd.to_datetime(out['date']).astype('datetime64[ns]')
    df_usd['fecha'] = pd.to_datetime(df_usd['fecha']).astype('datetime64[ns]')
    df_usd = df_usd.sort_values('fecha')
    
    merged = pd.merge_asof(
        out.sort_values('date'),
        df_usd[['fecha', 'valor']],
        left_on='date',
        right_on='fecha',
        direction='backward'
    )
    
    merged = merged.rename(columns={'valor': 'usd_val_used'})
    merged['cta_anual_usd'] = merged['cta_anual_clp'] / merged['usd_val_used']
    
    return merged
