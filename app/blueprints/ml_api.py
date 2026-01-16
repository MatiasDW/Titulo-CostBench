"""
ML API Blueprint
Read-only endpoints for model champion metadata and forecasts.
"""
from flask import Blueprint, jsonify, request
from datetime import datetime

bp = Blueprint('ml_api', __name__, url_prefix='/api/v1')


# BLS CPI Endpoint
@bp.route('/market/bls/cpi', methods=['GET'])
def get_bls_cpi():
    """
    Fetch CPI data from BLS API.
    
    Query params:
        series: str = "CUUR0000SA0"
        years: int = 5
        
    Returns:
        {observations: [{date, value, yoy_pct}], metadata: {source, fetched_at}}
    """
    series = request.args.get('series', 'CUUR0000SA0')
    years = int(request.args.get('years', 5))
    
    try:
        from app.ml.ingest.bls_client import fetch_cpi_series
        
        end_year = datetime.now().year
        start_year = end_year - years
        
        df = fetch_cpi_series(
            series_id=series,
            start_year=start_year,
            end_year=end_year
        )
        
        observations = df.to_dict(orient='records')
        # Convert dates to ISO format
        for obs in observations:
            if 'date' in obs:
                obs['date'] = obs['date'].isoformat() if hasattr(obs['date'], 'isoformat') else str(obs['date'])
        
        return jsonify({
            'observations': observations,
            'metadata': {
                'source': 'BLS',
                'series_id': series,
                'fetched_at': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Treasury Yields Endpoint  
@bp.route('/market/treasury/yields', methods=['GET'])
def get_treasury_yields():
    """
    Fetch Treasury yields.
    
    Query params:
        maturity: str = "10-Year"
        months: int = 60
        
    Returns:
        {observations: [{date, yield_pct}], metadata: {...}}
    """
    maturity = request.args.get('maturity', '10-Year')
    months = int(request.args.get('months', 60))
    
    try:
        from app.ml.ingest.treasury_client import fetch_treasury_yields
        
        df = fetch_treasury_yields(maturity=maturity, months=months)
        
        observations = df.to_dict(orient='records')
        for obs in observations:
            if 'date' in obs:
                obs['date'] = obs['date'].isoformat() if hasattr(obs['date'], 'isoformat') else str(obs['date'])
        
        return jsonify({
            'observations': observations,
            'metadata': {
                'source': 'Treasury Fiscal Data',
                'maturity': maturity,
                'fetched_at': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Model Champion Endpoint
@bp.route('/models/<asset>/best', methods=['GET'])
def get_best_model(asset: str):
    """
    Get champion model metadata for an asset.
    
    Returns:
        {
            model_id, model_name, horizon, 
            metrics: {mae, rmse, mape},
            trained_until, data_version
        }
    """
    try:
        from app.ml.registry.model_registry import get_latest_champion
        
        entry = get_latest_champion(asset.upper())
        
        return jsonify({
            'model_id': entry.id,
            'asset': entry.asset,
            'model_name': entry.model_name,
            'horizon': entry.horizon,
            'metrics': entry.metrics,
            'trained_until': entry.trained_until,
            'data_version': entry.data_version,
            'library': entry.library,
            'library_version': entry.library_version,
            'created_at': entry.created_at
        })
        
    except Exception as e:
        return jsonify({'error': str(e), 'asset': asset}), 404


# Forecast Endpoint
@bp.route('/models/<asset>/forecast', methods=['GET'])
def get_forecast(asset: str):
    """
    Get forecast from champion model.
    
    Query params:
        h: int = 1 (forecast horizon, max 3)
        
    Returns:
        {
            asset, horizon, model_id,
            forecasts: [{date, predicted_price}],
            generated_at
        }
    """
    h = min(int(request.args.get('h', 1)), 3)  # Max horizon = 3
    
    try:
        from app.ml.registry.model_registry import get_latest_champion, load_champion_model
        
        # Get champion
        entry = get_latest_champion(asset.upper())
        
        # Load model
        model = load_champion_model(entry)
        
        # Generate forecast
        # Note: In production, would use PyCaret's predict method
        # For now, return placeholder
        forecasts = []
        base_date = datetime.now()
        for i in range(h):
            forecasts.append({
                'date': (base_date.replace(day=1)).isoformat(),
                'predicted_price': None,  # Would be actual prediction
                'month_offset': i + 1
            })
        
        return jsonify({
            'asset': entry.asset,
            'horizon': h,
            'model_id': entry.id,
            'model_name': entry.model_name,
            'forecasts': forecasts,
            'generated_at': datetime.now().isoformat(),
            'note': 'Forecast generation requires trained model. This is metadata only.'
        })
        
    except Exception as e:
        return jsonify({'error': str(e), 'asset': asset}), 404


# List Models Endpoint
@bp.route('/models', methods=['GET'])
def list_models():
    """
    List all models in registry.
    
    Query params:
        asset: str = None (filter by asset)
        
    Returns:
        {models: [...]}
    """
    asset = request.args.get('asset')
    
    try:
        from app.ml.registry.model_registry import list_models
        
        entries = list_models(asset=asset.upper() if asset else None)
        
        return jsonify({
            'models': [e.to_dict() for e in entries],
            'count': len(entries)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Health check for ML module
@bp.route('/ml/health', methods=['GET'])
def ml_health():
    """ML module health check."""
    health = {
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'components': {}
    }
    
    # Check PyCaret availability
    try:
        import pycaret
        health['components']['pycaret'] = {
            'status': 'available',
            'version': pycaret.__version__
        }
    except ImportError:
        health['components']['pycaret'] = {
            'status': 'unavailable',
            'message': 'Install with: pip install pycaret[time_series]'
        }
    
    # Check models directory
    from pathlib import Path
    models_dir = Path('models')
    health['components']['models_dir'] = {
        'status': 'exists' if models_dir.exists() else 'missing',
        'path': str(models_dir.absolute())
    }
    
    return jsonify(health)
