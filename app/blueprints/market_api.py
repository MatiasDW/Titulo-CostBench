"""
Market Data API
Endpoints for external market data: BDE (Chile), BLS (USA), Treasury (USA)
"""
from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
import os

from app.ml.logging_utils import get_logger
from app.ml.ingest.bde_client import fetch_usdclp, fetch_uf, BCCHAPI_AVAILABLE

logger = get_logger("api.market")

market_api = Blueprint("market_api", __name__, url_prefix="/api/v1/market")


# ============================================
# BDE (Banco Central de Chile) Endpoints
# ============================================

@market_api.route("/bde/uf", methods=["GET"])
def get_uf():
    """
    GET /api/v1/market/bde/uf
    
    Fetch UF (Unidad de Fomento) from Banco Central.
    
    Query params:
        start: Start date (YYYY-MM-DD), default: 1 year ago
        end: End date (YYYY-MM-DD), default: today
        monthly: If true, aggregate to monthly (default: true)
        
    Note: UF is a rule-based index derived from CPI Chile.
    """
    try:
        start = request.args.get("start", (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"))
        end = request.args.get("end", datetime.now().strftime("%Y-%m-%d"))
        monthly = request.args.get("monthly", "true").lower() == "true"
        
        df = fetch_uf(start_date=start, end_date=end, aggregate_monthly=monthly)
        
        data = df.to_dict(orient="records")
        
        return jsonify({
            "status": "ok",
            "series": "UF",
            "source": "BDE (Banco Central de Chile)",
            "note": "UF is a rule-based index calculated from CPI Chile using geometric interpolation (days 10→9 each month)",
            "count": len(data),
            "start": start,
            "end": end,
            "data": data
        })
        
    except Exception as e:
        logger.error("uf_fetch_failed", error=str(e))
        return jsonify({
            "status": "error",
            "error": str(e),
            "hint": "Check BDE_USER and BDE_PASS environment variables"
        }), 500


@market_api.route("/bde/usdclp", methods=["GET"])
def get_usdclp():
    """
    GET /api/v1/market/bde/usdclp
    
    Fetch USD/CLP exchange rate from Banco Central.
    
    Query params:
        start: Start date (YYYY-MM-DD), default: 1 year ago
        end: End date (YYYY-MM-DD), default: today
        monthly: If true, aggregate to monthly (default: true)
    """
    try:
        start = request.args.get("start", (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"))
        end = request.args.get("end", datetime.now().strftime("%Y-%m-%d"))
        monthly = request.args.get("monthly", "true").lower() == "true"
        
        df = fetch_usdclp(start_date=start, end_date=end, aggregate_monthly=monthly)
        
        data = df.to_dict(orient="records")
        
        return jsonify({
            "status": "ok",
            "series": "USD/CLP",
            "source": "BDE (Banco Central de Chile)",
            "description": "Tipo de cambio observado USD/CLP",
            "count": len(data),
            "data": data
        })
        
    except Exception as e:
        logger.error("usdclp_fetch_failed", error=str(e))
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


# ============================================
# BLS (Bureau of Labor Statistics) Endpoints
# ============================================

@market_api.route("/bls/cpi", methods=["GET"])
def get_bls_cpi():
    """
    GET /api/v1/market/bls/cpi
    
    Fetch CPI (Consumer Price Index) from BLS.
    
    Query params:
        series: BLS series ID (default: CUUR0000SA0 - All items, not seasonally adjusted)
        start_year: Start year (default: current year - 5)
        end_year: End year (default: current year)
    """
    try:
        from app.ml.ingest.bls_client import BLSClient
        
        series = request.args.get("series", "CUUR0000SA0")
        end_year = int(request.args.get("end_year", datetime.now().year))
        start_year = int(request.args.get("start_year", end_year - 5))
        
        client = BLSClient()
        df = client.fetch_series(series, start_year, end_year)
        
        data = df.to_dict(orient="records")
        
        return jsonify({
            "status": "ok",
            "series": series,
            "source": "BLS (Bureau of Labor Statistics)",
            "description": "Consumer Price Index - All Urban Consumers",
            "frequency": "monthly",
            "count": len(data),
            "data": data
        })
        
    except Exception as e:
        logger.error("bls_cpi_failed", error=str(e))
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


# ============================================
# Treasury Endpoints
# ============================================

@market_api.route("/treasury/yields", methods=["GET"])
def get_treasury_yields():
    """
    GET /api/v1/market/treasury/yields
    
    Fetch Treasury yields from US Treasury Fiscal Data API.
    
    Query params:
        maturity: Yield maturity (default: 10y)
        start: Start date (YYYY-MM-DD)
        end: End date (YYYY-MM-DD)
    """
    try:
        from app.ml.ingest.treasury_client import TreasuryClient
        
        maturity = request.args.get("maturity", "10y")
        start = request.args.get("start", (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"))
        end = request.args.get("end", datetime.now().strftime("%Y-%m-%d"))
        
        client = TreasuryClient()
        df = client.fetch_yields(start_date=start, end_date=end)
        
        data = df.to_dict(orient="records")
        
        return jsonify({
            "status": "ok",
            "series": f"Treasury {maturity}",
            "source": "U.S. Treasury Fiscal Data API",
            "description": "Average Interest Rates on U.S. Treasury Securities",
            "count": len(data),
            "data": data
        })
        
    except Exception as e:
        logger.error("treasury_yields_failed", error=str(e))
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


# ============================================
# Status Endpoint
# ============================================

@market_api.route("/status", methods=["GET"])
def market_status():
    """
    GET /api/v1/market/status
    
    Check status of all market data sources.
    """
    status = {
        "bde": {
            "available": BCCHAPI_AVAILABLE,
            "credentials": bool(os.getenv("BDE_USER") and os.getenv("BDE_PASS")),
            "series": ["UF", "USD/CLP"]
        },
        "bls": {
            "available": True,
            "series": ["CPI (CUUR0000SA0)"]
        },
        "treasury": {
            "available": True,
            "series": ["10Y Yield"]
        }
    }
    
    return jsonify({
        "status": "ok",
        "sources": status,
        "documentation": {
            "bde": "https://si3.bcentral.cl/sieterest/",
            "bls": "https://www.bls.gov/developers/",
            "treasury": "https://fiscaldata.treasury.gov/api-documentation/"
        }
    })
