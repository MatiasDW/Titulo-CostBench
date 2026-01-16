"""SERNAC credit cards blueprint."""
from flask import Blueprint, jsonify, current_app
from app.services.http import HTTPClient
from app.services.parsers import parse_sernac_cards
from app.services.io_utils import write_parquet, profile_parquet
from pathlib import Path

bp = Blueprint('sernac', __name__)


@bp.route('/tarjetas/download', methods=['GET'])
def download_credit_cards():
    """Download SERNAC credit cards data and save to Parquet."""
    try:
        # Get configuration
        url = current_app.config['SERNAC_CARDS_URL']
        data_dir = Path(current_app.config['DATA_DIR'])
        
        # Download data
        client = HTTPClient()
        response = client.get(url)
        
        # Parse HTML to DataFrame
        df = parse_sernac_cards(response.text)
        
        # Save to Parquet
        output_path = data_dir / 'tarjetas_sernac.parquet'
        metadata = write_parquet(df, output_path)
        
        client.close()
        
        return jsonify({
            'status': 'success',
            'message': 'SERNAC credit cards data downloaded successfully',
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


@bp.route('/tarjetas/profile', methods=['GET'])
def profile_credit_cards():
    """Profile the SERNAC credit cards Parquet file."""
    try:
        data_dir = Path(current_app.config['DATA_DIR'])
        filepath = data_dir / 'tarjetas_sernac.parquet'
        
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
