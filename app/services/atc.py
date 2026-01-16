"""
Service for ATC (Annual Total Cost) Metrics and Ranking.
"""
import pandas as pd

def compute_atc(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes Annual Total Cost (ATC) from monthly fees.
    
    Formula: cta_anual_clp = cta_mensual_clp * 12
    
    Args:
        df: Dataframe with 'cta_mensual_clp'
    Returns:
        Dataframe with added 'cta_anual_clp' column.
        Rows with NaN monthly cost are dropped or handled? 
        We should probably keep them as NaN.
    """
    out = df.copy()
    if 'cta_mensual_clp' not in out.columns:
        raise ValueError("Missing 'cta_mensual_clp' column")
        
    out['cta_anual_clp'] = out['cta_mensual_clp'] * 12
    return out

def rank_topn(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """
    Ranks products by Annual Cost (Cheapest first).
    
    Args:
        df: Dataframe with 'cta_anual_clp'
        n: Return top N rows
    Returns:
        Top N dataframe sorted by cost ascending.
    """
    if 'cta_anual_clp' not in df.columns:
        raise ValueError("Missing 'cta_anual_clp' column")
    
    # Filter out NaNs for ranking? 
    # Or put them at end? default 'na_position=last'
    
    # Sort
    ranked = df.sort_values(by='cta_anual_clp', ascending=True)
    
    # Reset index for clean Top 1..N
    ranked = ranked.reset_index(drop=True)
    
    # Add 'rank' column? Or just implicit index.
    # User asked for 'persist Top-N ranking', so maybe saving them is enough.
    
    return ranked.head(n)
