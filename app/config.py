"""Application configuration."""
import os
from pathlib import Path


class Config:
    """Base configuration."""
    
    # Application
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Paths
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / 'data'
    
    # CMF - Comisión para el Mercado Financiero
    CMF_SIMULADOR_URL = os.getenv(
        'CMF_SIMULADOR_URL',
        'https://servicios.cmfchile.cl/simuladorcuentavista/simulacionpromedio'
    )
    CMF_API_BASE_URL = os.getenv('CMF_API_BASE_URL', 'https://api.cmfchile.cl')
    CMF_API_KEY = os.getenv('CMF_API_KEY', '')
    
    # SERNAC
    SERNAC_CARDS_URL = 'https://www.sernac.cl/comparador-tarjetas-credito/'
    
    # Banco Central de Chile - Credenciales para bcchapi
    BDE_USER = os.getenv('BDE_USER', '')
    BDE_PASS = os.getenv('BDE_PASS', '')
    
    # HTTP settings
    REQUEST_TIMEOUT = 30
    USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    
    @classmethod
    def init_app(cls, app):
        """Initialize application with this config."""
        # Create data directory if it doesn't exist
        cls.DATA_DIR.mkdir(exist_ok=True)


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """Testing configuration."""
    DEBUG = True
    TESTING = True


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
