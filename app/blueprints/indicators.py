"""Economic indicators blueprint usando bcchapi."""
from flask import Blueprint, jsonify, current_app, request
from app.services.io_utils import write_parquet, profile_parquet
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

bp = Blueprint('indicators', __name__)


@bp.route('/uf', methods=['GET'])
def download_uf():
    """Download UF (Unidad de Fomento) values usando bcchapi."""
    try:
        # Importar bcchapi
        try:
            import bcchapi
        except ImportError:
            return jsonify({
                'status': 'error',
                'message': 'bcchapi no está instalado. Ejecuta: pip install bcchapi',
                'type': 'ImportError'
            }), 500
        
        # Get configuration
        data_dir = Path(current_app.config['DATA_DIR'])
        bde_user = current_app.config.get('BDE_USER')
        bde_pass = current_app.config.get('BDE_PASS')
        
        if not bde_user or not bde_pass:
            return jsonify({
                'status': 'error',
                'message': 'Credenciales del Banco Central no configuradas. Agrega BDE_USER y BDE_PASS en .env',
                'type': 'ConfigurationError'
            }), 500
        
        # Get date range from query params or use defaults (last 365 days)
        days = request.args.get('days', 365, type=int)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Format dates (YYYY-MM-DD)
        fecha_inicio = start_date.strftime('%Y-%m-%d')
        fecha_fin = end_date.strftime('%Y-%m-%d')
        
        # Inicializar cliente bcchapi
        siete = bcchapi.Siete(bde_user, bde_pass)
        
        # Código de serie para UF diaria
        # F073.UFF.PRE.Z.D = UF, Frecuencia Diaria
        serie_uf = "F073.UFF.PRE.Z.D"
        
        # Obtener datos usando cuadro()
        df = siete.cuadro(
            series=[serie_uf],
            nombres=["uf_valor"],
            desde=fecha_inicio,
            hasta=fecha_fin
        )
        
        # Reset index para tener la fecha como columna
        df = df.reset_index()
        df.columns = ['fecha', 'valor_uf']
        
        # Add metadata
        df['source'] = 'BDE_API'
        df['serie_id'] = serie_uf
        df['extraction_date'] = pd.Timestamp.now()
        
        # Save to Parquet
        output_path = data_dir / 'indicadores_uf.parquet'
        from app.services.io_utils import write_parquet
        metadata = write_parquet(df, output_path)
        
        return jsonify({
            'status': 'success',
            'message': 'UF indicators downloaded successfully usando bcchapi',
            'metadata': metadata,
            'date_range': {
                'start': fecha_inicio,
                'end': fecha_fin
            },
            'columns': df.columns.tolist(),
            'sample_row': df.head(1).to_dict(orient='records')[0] if len(df) > 0 else None
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'type': type(e).__name__,
            'hint': 'Verifica que BDE_USER y BDE_PASS estén configurados en .env'
        }), 500


@bp.route('/buscar', methods=['GET'])
def buscar_series():
    """Buscar series disponibles en el Banco Central."""
    try:
        import bcchapi
        
        # Get configuration
        bde_user = current_app.config.get('BDE_USER')
        bde_pass = current_app.config.get('BDE_PASS')
        
        if not bde_user or not bde_pass:
            return jsonify({
                'status': 'error',
                'message': 'Credenciales del Banco Central no configuradas',
                'type': 'ConfigurationError'
            }), 500
        
        # Get search term
        termino = request.args.get('termino', 'uf')
        
        # Inicializar cliente
        siete = bcchapi.Siete(bde_user, bde_pass)
        
        # Buscar series
        resultados = siete.buscar(termino)
        
        # Convertir a dict para JSON
        resultados_dict = resultados.to_dict(orient='records')
        
        return jsonify({
            'status': 'success',
            'termino_busqueda': termino,
            'total_resultados': len(resultados_dict),
            'resultados': resultados_dict[:50]  # Limitar a 50 resultados
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'type': type(e).__name__
        }), 500


@bp.route('/profile', methods=['GET'])
def profile_indicators():
    """Profile the indicators Parquet file."""
    try:
        data_dir = Path(current_app.config['DATA_DIR'])
        filepath = data_dir / 'indicadores_uf.parquet'
        
        profile = profile_parquet(filepath)
        
        return jsonify({
            'status': 'success',
            'profile': profile
        })
        
    except FileNotFoundError as e:
        return jsonify({
            'status': 'error',
            'message': 'Data file not found. Please run /uf first.',
            'error': str(e)
        }), 404
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'type': type(e).__name__
        }), 500
