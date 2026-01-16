"""
Scloda Chat Blueprint - API endpoints for AI chat.

Endpoints:
- POST /api/v1/scloda/message - Send a message and get response
- POST /api/v1/scloda/insight - Generate insight for a chart
- GET /api/v1/scloda/health - Check service status
"""
from flask import Blueprint, jsonify, request
from app.services.scloda_service import chat_completion, get_service_status, generate_chart_insight
from app.ml.logging_utils import get_logger

logger = get_logger("scloda.api")

scloda_bp = Blueprint("scloda", __name__, url_prefix="/api/v1/scloda")


@scloda_bp.route("/message", methods=["POST"])
def send_message():
    """
    POST /api/v1/scloda/message
    
    Send a message to Scloda and receive a response.
    
    Request body:
        {
            "message": "¿Cuánto vale la UF hoy?",
            "history": [  # optional
                {"role": "user", "content": "..."},
                {"role": "assistant", "content": "..."}
            ]
        }
    
    Response:
        {
            "response": "La UF hoy está en...",
            "tokens_used": 150,
            "tools_used": ["get_uf_data"]  # optional
        }
    """
    try:
        data = request.get_json()
        
        if not data or "message" not in data:
            return jsonify({"error": "Message is required"}), 400
        
        user_message = data["message"].strip()
        if not user_message:
            return jsonify({"error": "Message cannot be empty"}), 400
        
        if len(user_message) > 2000:
            return jsonify({"error": "Message too long (max 2000 chars)"}), 400
        
        history = data.get("history", [])
        
        logger.info("chat_request", message_length=len(user_message))
        
        result = chat_completion(
            user_message=user_message,
            conversation_history=history
        )
        
        logger.info("chat_response", 
                   tokens=result.get("tokens_used", 0),
                   tools=result.get("tools_used", []))
        
        return jsonify(result)
        
    except Exception as e:
        logger.error("chat_endpoint_error", error=str(e))
        return jsonify({
            "error": "Internal server error",
            "response": "😅 Algo salió mal. Intenta de nuevo."
        }), 500


@scloda_bp.route("/insight", methods=["POST"])
def get_insight():
    """
    POST /api/v1/scloda/insight
    
    Generate a dynamic insight for a chart based on current data.
    """
    try:
        data = request.get_json()
        
        if not data or "asset" not in data:
            return jsonify({"error": "Asset is required"}), 400
        
        asset = data["asset"]
        current_value = data.get("current_value")
        change_percent = data.get("change_percent", 0)
        trend = data.get("trend", "stable")
        
        logger.info("insight_request", asset=asset, change=change_percent)
        
        result = generate_chart_insight(
            asset=asset,
            current_value=current_value,
            change_percent=change_percent,
            trend=trend
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error("insight_endpoint_error", error=str(e))
        return jsonify({
            "error": "Internal server error",
            "insight": "Analysis unavailable."
        }), 500


@scloda_bp.route("/model-analysis", methods=["POST"])
def get_model_analysis():
    """
    POST /api/v1/scloda/model-analysis
    
    Generate a detailed analysis of ML model selection.
    
    Request body:
        {
            "asset": "Gold",
            "model_name": "Auto ARIMA",
            "metrics": {"mape": 0.65, "mae": 12.5}
        }
    """
    try:
        data = request.get_json()
        
        if not data or "asset" not in data or "model_name" not in data:
            return jsonify({"error": "Asset and model_name are required"}), 400
        
        asset = data["asset"]
        model_name = data["model_name"]
        metrics = data.get("metrics", {})
        
        logger.info("model_analysis_request", asset=asset, model=model_name)
        
        from app.services.scloda_service import generate_model_analysis
        result = generate_model_analysis(asset, model_name, metrics)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error("model_analysis_endpoint_error", error=str(e))
        return jsonify({
            "selection_reason": "Análisis no disponible.",
            "confidence_note": "Consulte métricas estándar."
        }), 500


@scloda_bp.route("/health", methods=["GET"])
def health():
    """
    GET /api/v1/scloda/health
    
    Check Scloda service status.
    
    Response:
        {
            "status": "ok",
            "api_configured": true,
            "model": "google/gemini-2.0-flash-001"
        }
    """
    status = get_service_status()
    
    return jsonify({
        "status": "ok" if status["api_configured"] else "warning",
        "api_configured": status["api_configured"],
        "model": status["model"],
        "message": "API key not configured" if not status["api_configured"] else None
    })
