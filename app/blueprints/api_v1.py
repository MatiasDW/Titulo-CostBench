"""
API v1 Blueprint.
Endpoints for Entrega 2: ATC Ranking, Market Context, Data List.
"""
from flask import Blueprint, request, jsonify, current_app
import pandas as pd
import os

bp = Blueprint('api_v1', __name__, url_prefix='/api/v1')

DATA_DIR = os.path.abspath('data')

def load_parquet(rel_path):
    path = os.path.join(DATA_DIR, rel_path)
    if os.path.exists(path):
        return pd.read_parquet(path)
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
