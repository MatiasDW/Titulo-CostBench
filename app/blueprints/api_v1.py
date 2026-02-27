"""
API v1 Blueprint.
Endpoints for Entrega 2: ATC Ranking, Market Context, Data List.
"""
from flask import Blueprint, request, jsonify, current_app
import logging
import pandas as pd
import os

bp = Blueprint('api_v1', __name__, url_prefix='/api/v1')

logger = logging.getLogger(__name__)

DATA_DIR = os.path.abspath('data')

def load_parquet(rel_path):
    """Read a Parquet file with resilient retry (see ``io_utils``).

    Returns ``None`` when the file is missing **or** when all retries are
    exhausted, so every caller's existing ``if df is None`` guard keeps
    working and the user never gets a raw 500.
    """
    path = os.path.join(DATA_DIR, rel_path)
    if not os.path.exists(path):
        return None
    try:
        from pathlib import Path as _P
        from app.services.io_utils import read_parquet as _read
        return _read(_P(path))
    except Exception:
        logger.exception("Failed to read Parquet after retries: %s", rel_path)
        return None

@bp.route('/atc/ranking', methods=['GET'])
def get_atc_ranking():
    """
    GET /api/v1/atc/ranking?top=10&denom=clp|uf|usd
    """
    top = request.args.get('top', default=10, type=int)
    denom = request.args.get('denom', default='clp').lower()
    
    df = load_parquet('metrics/atc_ranking_multi.parquet')
    if df is None:
        # Fallback to basic ranking if multi not found
        df = load_parquet('metrics/atc_ranking.parquet')
    
    if df is None:
        return jsonify({'error': 'Ranking data not available'}), 404
        
    # Sort
    if 'cta_anual_clp' in df.columns:
        df = df.sort_values('cta_anual_clp', ascending=True)
    
    # Select denomination column
    col_map = {
        'clp': 'cta_anual_clp',
        'uf': 'cta_anual_uf',
        'usd': 'cta_anual_usd'
    }
    
    target_col = col_map.get(denom)
    if not target_col or target_col not in df.columns:
        # If USD/UF requested but not available (e.g. only basic parquet), warn or fallback?
        # Return error if strict
        if denom != 'clp':
             return jsonify({'error': f'Denomination {denom} not available'}), 400
        target_col = 'cta_anual_clp'
    
    # Prepare result
    res = df.head(top).copy()
    
    # Format
    items = []
    for _, row in res.iterrows():
        items.append({
            'institution': row['institucion'],
            'product': row.get('producto', ''),
            'cost': float(row[target_col]) if pd.notnull(row[target_col]) else None,
            'denom': denom.upper()
        })
        
    return jsonify({
        'meta': {'top': top, 'denom': denom.upper()},
        'items': items
    })

@bp.route('/market/indices', methods=['GET'])
def get_market_indices():
    """
    GET /api/v1/market/indices
    Returns available macro series from parquet.
    """
    df = load_parquet('market/macro_indicators.parquet')
    if df is None:
        return jsonify({'items': []})
    
    # Unique series
    series = df[['series_id', 'source']].drop_duplicates()
    items = series.to_dict('records')
    return jsonify({'items': items})

@bp.route('/market/history', methods=['GET'])
def get_market_history():
    """
    GET /api/v1/market/history?series_id=...
    """
    sid = request.args.get('series_id')
    if not sid:
        return jsonify({'error': 'Missing series_id'}), 400
        
    df = load_parquet('market/macro_indicators.parquet')
    if df is None:
         return jsonify({'error': 'No market data'}), 404
         
    # Filter
    df_filtered = df[df['series_id'] == sid].copy()
    
    # Format
    df_filtered['date'] = df_filtered['date'].dt.strftime('%Y-%m-%d')
    obs = df_filtered[['date', 'value']].to_dict('records')
    
    return jsonify({
        'series_id': sid,
        'observations': obs
    })

# Series metadata — currency & unit for every indicator
SERIES_META = {
    'CPIAUCSL':         {'unit': 'Index',    'currency': '',     'label': 'US CPI'},
    'DGS10':            {'unit': '%',        'currency': '',     'label': 'Treasury 10Y'},
    'GOLDAMGBD228NLBM': {'unit': 'USD/oz',   'currency': 'USD',  'label': 'Gold (BCCh)'},
    'PCOPPUSDM':        {'unit': 'USD/lb',   'currency': 'USD',  'label': 'Copper (BCCh)'},
    'DCOILWTICO':       {'unit': 'USD/bbl',  'currency': 'USD',  'label': 'Oil WTI'},
    'SLVPRUSD':         {'unit': 'USD/oz',   'currency': 'USD',  'label': 'Silver'},
    'BTC-CLP':          {'unit': 'CLP',      'currency': 'CLP',  'label': 'Bitcoin'},
    'ETH-CLP':          {'unit': 'CLP',      'currency': 'CLP',  'label': 'Ethereum'},
    'XRP-CLP':          {'unit': 'CLP',      'currency': 'CLP',  'label': 'XRP'},
    'SOL-CLP':          {'unit': 'CLP',      'currency': 'CLP',  'label': 'Solana'},
    'USDCLP':           {'unit': 'CLP/USD',  'currency': 'CLP',  'label': 'USD/CLP'},
    'UF':               {'unit': 'CLP',      'currency': 'CLP',  'label': 'UF'},
}


@bp.route('/market/latest', methods=['GET'])
def get_market_latest():
    """
    GET /api/v1/market/latest
    Returns the latest value + percentage change for ALL series in one shot.
    Each item includes unit/currency metadata for clear UI display.
    """
    df = load_parquet('market/macro_indicators.parquet')
    if df is None:
        return jsonify({'items': []}), 200

    results = []
    for sid, group in df.groupby('series_id'):
        group_sorted = group.sort_values('date')
        if group_sorted.empty:
            continue

        latest = group_sorted.iloc[-1]
        latest_val = float(latest['value'])

        # Calculate change_pct from previous observation
        change_pct = 0.0
        if len(group_sorted) >= 2:
            prev_val = float(group_sorted.iloc[-2]['value'])
            if prev_val != 0:
                change_pct = round(((latest_val - prev_val) / prev_val) * 100, 2)

        meta = SERIES_META.get(sid, {'unit': '', 'currency': '', 'label': sid})
        source = latest.get('source', '')

        results.append({
            'series_id': sid,
            'label': meta['label'],
            'value': latest_val,
            'change_pct': change_pct,
            'unit': meta['unit'],
            'currency': meta['currency'],
            'source': source,
            'is_mock': 'MOCK' in str(source).upper(),
            'date': latest['date'].strftime('%Y-%m-%d') if hasattr(latest['date'], 'strftime') else str(latest['date']),
        })

    return jsonify({'items': results})


@bp.route('/data/list', methods=['GET'])
def list_data():
    """Debug endpoint to list data files."""
    files = []
    for root, dirs, filenames in os.walk(DATA_DIR):
        for f in filenames:
            if f.endswith('.parquet'):
                full = os.path.join(root, f)
                rel = os.path.relpath(full, DATA_DIR)
                files.append(rel)
    return jsonify({'files': files})
