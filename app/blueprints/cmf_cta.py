"""CMF checking accounts blueprint."""
from flask import Blueprint, jsonify, current_app
from app.services.http import HTTPClient
from app.services.parsers import parse_cmf_simulador
from app.services.io_utils import write_parquet, profile_parquet
from pathlib import Path

bp = Blueprint('cmf', __name__)


@bp.route('/cuentavista/download', methods=['GET'])
def download_checking_accounts():
    """Download CMF checking accounts data and save to Parquet."""
    try:
        # Get configuration
        url = current_app.config['CMF_SIMULADOR_URL']
        data_dir = Path(current_app.config['DATA_DIR'])
        api_key = current_app.config.get('CMF_API_KEY')
        
        # Download data
        client = HTTPClient(api_key=api_key if api_key else None)
        response = client.get(url)
        
        # Try to parse as JSON first, then HTML
        try:
            data = response.json()
        except:
            data = response.text
        
        # Parse to DataFrame
        df = parse_cmf_simulador(data)
        
        # Save to Parquet
        output_path = data_dir / 'cta_cuentavista_cmf.parquet'
        metadata = write_parquet(df, output_path)
        
        client.close()
        
        return jsonify({
            'status': 'success',
            'message': 'CMF checking accounts data downloaded successfully',
            'metadata': metadata,
            'columns': df.columns.tolist(),
            'sample_row': df.head(1).to_dict(orient='records')[0] if len(df) > 0 else None
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'type': type(e).__name__
        }), 500


@bp.route('/cuentavista/profile', methods=['GET'])
def profile_checking_accounts():
    """Profile the CMF checking accounts Parquet file."""
    try:
        data_dir = Path(current_app.config['DATA_DIR'])
        filepath = data_dir / 'cta_cuentavista_cmf.parquet'
        
        profile = profile_parquet(filepath)
        
        return jsonify({
            'status': 'success',
            'profile': profile
        })
        
    except FileNotFoundError as e:
        return jsonify({
            'status': 'error',
            'message': 'Data file not found. Please run /download first.',
            'error': str(e)
        }), 404
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'type': type(e).__name__
        }), 500
