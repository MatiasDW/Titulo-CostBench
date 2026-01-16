"""Flask application factory."""
from flask import Flask, jsonify
from flask_cors import CORS
from app.config import config


def create_app(config_name='default'):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Configure Logging
    import logging
    import sys
    import os
    
    env = os.getenv('FLASK_ENV', 'production')
    
    if env == 'development':
        # Human-readable text format for development
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
        )
    else:
        # JSON format for production (Docker/Cloud)
        import json
        class JsonFormatter(logging.Formatter):
            def format(self, record):
                log_record = {
                    "timestamp": self.formatTime(record),
                    "level": record.levelname,
                    "message": record.getMessage(),
                    "module": record.module,
                    "func": record.funcName
                }
                if record.exc_info:
                    log_record["exception"] = self.formatException(record.exc_info)
                return json.dumps(log_record)
        formatter = JsonFormatter()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    
    # Avoid duplicate handlers
    if not app.logger.handlers:
        app.logger.addHandler(handler)
    
    app.logger.setLevel(logging.DEBUG if env == 'development' else logging.INFO)
    
    # Enable CORS
    CORS(app)
    
    # Register blueprints
    from app.blueprints.cmf_cta import bp as cmf_bp
    from app.blueprints.sernac_cards import bp as sernac_bp
    from app.blueprints.indicators import bp as indicators_bp
    from app.blueprints.api_v1 import bp as api_v1_bp
    from app.blueprints.web import bp as web_bp
    from app.blueprints.ml_api import bp as ml_bp  # ML endpoints
    from app.blueprints.market_api import market_api  # Market data endpoints
    
    app.register_blueprint(cmf_bp, url_prefix='/api/v1/cmf')
    app.register_blueprint(sernac_bp, url_prefix='/api/v1/sernac')
    app.register_blueprint(indicators_bp, url_prefix='/api/v1/indicators')
    app.register_blueprint(api_v1_bp) # uses prefix defined in bp
    app.register_blueprint(web_bp)    # uses prefix defined in bp (none, root)
    app.register_blueprint(ml_bp)     # ML API: /api/v1/models/*
    app.register_blueprint(market_api) # Market data: /api/v1/market/*

    
    # Health check endpoint
    @app.route('/health')
    def health():
        return jsonify({
            'status': 'healthy',
            'service': 'cost-benchmark-api',
            'version': '0.1.0'
        })
    
    # Root endpoint
    @app.route('/')
    def index():
        return jsonify({
            'service': 'Chilean Bank Cost Benchmark API',
            'version': '0.1.0',
            'endpoints': {
                'health': '/health',
                'cmf_checking_accounts': {
                    'download': '/api/v1/cmf/cuentavista/download',
                    'profile': '/api/v1/cmf/cuentavista/profile'
                },
                'sernac_cards': {
                    'download': '/api/v1/sernac/tarjetas/download',
                    'profile': '/api/v1/sernac/tarjetas/profile'
                },
                'indicators': {
                    'uf': '/api/v1/indicators/uf',
                    'profile': '/api/v1/indicators/profile'
                }
            }
        })
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    return app
