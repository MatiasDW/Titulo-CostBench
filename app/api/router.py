# Central router to mount all blueprints under /api/v1
from flask import Blueprint
from ..blueprints.indicators import bp as indicators_bp
from ..blueprints.cmf_cta import bp as cmf_cta_bp
from ..blueprints.sernac_cards import bp as sernac_bp

def build_api_v1() -> Blueprint:
    api = Blueprint("api_v1", __name__)
    api.register_blueprint(indicators_bp, url_prefix="/download")
    api.register_blueprint(cmf_cta_bp, url_prefix="/download")
    api.register_blueprint(sernac_bp, url_prefix="/download")
    return api
