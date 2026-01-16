"""
Service for UF (Unidad de Fomento) conversion.
"""
import pandas as pd

def attach_uf(df_metrics: pd.DataFrame, df_uf: pd.DataFrame) -> pd.DataFrame:
    """
    Attaches UF value to metrics dataframe based on date.
    
    Args:
        df_metrics: DF with 'date' and 'cta_anual_clp'
        df_uf: DF with 'fecha' and 'valor'
    Returns:
        DF with 'cta_anual_uf' and 'uf_valor_used'
    """
    out = df_metrics.copy()
    
    # Ensure types to nanosecond precision
    out['date'] = pd.to_datetime(out['date']).astype('datetime64[ns]')
    df_uf['fecha'] = pd.to_datetime(df_uf['fecha']).astype('datetime64[ns]')
    
    # Sort UF by date
    df_uf = df_uf.sort_values('fecha')
    
    # Merge asof to get nearest UF (or exact)
    # direction='backward' means if exact match not found, take previous valid UF.
    # tolerance? 
    # For 'fecha_captura', we want the UF of that day.
    
    merged = pd.merge_asof(
        out.sort_values('date'),
        df_uf[['fecha', 'valor']],
        left_on='date',
        right_on='fecha',
        direction='backward'
    )
    
    # Rename
    merged = merged.rename(columns={'valor': 'uf_val_used'})
    
    # Compute
    merged['cta_anual_uf'] = merged['cta_anual_clp'] / merged['uf_val_used']
    
    # Drop temp cols if needed
    
    return merged
