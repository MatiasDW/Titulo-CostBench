"""
Scloda Chat Blueprint - API endpoints for AI chat.

Endpoints:
- POST /api/v1/scloda/message - Send a message and get response
- POST /api/v1/scloda/insight - Generate insight for a chart
- GET /api/v1/scloda/health - Check service status
"""

from flask import Blueprint, g, jsonify, request
from app.blueprints.auth import require_admin, require_auth
from app.services.scloda_service import (
    chat_completion,
    get_service_status,
    generate_chart_insight,
)
from app.services.scloda_memory import (
    get_knowledge_index_status,
    rebuild_knowledge_index,
)
from app.services.scloda_observability import get_trace_summary, list_recent_traces
from app.services.scloda_review_queue import (
    assign_review_item,
    claim_review_item,
    get_capability_tree,
    get_review_summary,
    list_review_items,
    resolve_review_item,
)
from app.services.scloda_rate_limits import (
    check_chat_limit,
    check_insight_limit,
    check_model_analysis_limit,
)
from app.ml.logging_utils import get_logger

logger = get_logger("scloda.api")

scloda_bp = Blueprint("scloda", __name__, url_prefix="/api/v1/scloda")


def _rate_limit_subject() -> str:
    user = getattr(g, "current_user", None)
    if user is not None:
        return f"user:{user.id}"
    forwarded = request.headers.get("X-Forwarded-For", "")
    client_ip = (forwarded.split(",")[0].strip() if forwarded else "") or request.remote_addr
    return f"ip:{client_ip or 'unknown'}"


def _rate_limit_response(limit_state: dict, message: str):
    response = jsonify(
        {
            "error": "rate_limited",
            "message": message,
            "retry_after_seconds": limit_state["reset_in_seconds"],
            "limit": limit_state["limit"],
            "window_seconds": limit_state["window_seconds"],
        }
    )
    response.status_code = 429
    response.headers["Retry-After"] = str(limit_state["reset_in_seconds"])
    response.headers["X-RateLimit-Limit"] = str(limit_state["limit"])
    response.headers["X-RateLimit-Remaining"] = str(limit_state["remaining"])
    return response


@scloda_bp.route("/message", methods=["POST"])
@require_auth
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
        limit_state = check_chat_limit(_rate_limit_subject())
        if not limit_state["allowed"]:
            return _rate_limit_response(
                limit_state,
                "Too many Scloda chat requests. Please wait a moment and try again.",
            )

        data = request.get_json()

        if not data or "message" not in data:
            return jsonify({"error": "Message is required"}), 400

        user_message = data["message"].strip()
        if not user_message:
            return jsonify({"error": "Message cannot be empty"}), 400

        if len(user_message) > 2000:
            return jsonify({"error": "Message too long (max 2000 chars)"}), 400

        history = data.get("history", [])

        # Build user profile from authenticated user ("Modo Sniper")
        user = g.current_user
        user_profile = {
            "id": user.id,
            "risk_profile": user.risk_profile,
            "interests": user.interests or [],
            "email": user.email,
        }

        logger.info(
            "chat_request",
            message_length=len(user_message),
            risk=user_profile["risk_profile"],
        )

        result = chat_completion(
            user_message=user_message,
            conversation_history=history,
            user_profile=user_profile,
        )

        logger.info(
            "chat_response",
            tokens=result.get("tokens_used", 0),
            tools=result.get("tools_used", []),
        )

        return jsonify(result)

    except Exception as e:
        logger.error("chat_endpoint_error", error=str(e))
        return (
            jsonify(
                {
                    "error": "Internal server error",
                    "response": "😅 Something went wrong. Please try again.",
                }
            ),
            500,
        )


@scloda_bp.route("/insight", methods=["POST"])
def get_insight():
    """
    POST /api/v1/scloda/insight

    Generate a dynamic insight for a chart based on current data.
    """
    try:
        limit_state = check_insight_limit(_rate_limit_subject())
        if not limit_state["allowed"]:
            return _rate_limit_response(
                limit_state,
                "Too many insight requests. Please wait a moment and try again.",
            )

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
            trend=trend,
        )

        return jsonify(result)

    except Exception as e:
        logger.error("insight_endpoint_error", error=str(e))
        return (
            jsonify(
                {"error": "Internal server error", "insight": "Analysis unavailable."}
            ),
            500,
        )


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
        limit_state = check_model_analysis_limit(_rate_limit_subject())
        if not limit_state["allowed"]:
            return _rate_limit_response(
                limit_state,
                "Too many model analysis requests. Please wait a moment and try again.",
            )

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
        return (
            jsonify(
                {
                    "selection_reason": "Analysis unavailable.",
                    "confidence_note": "Please refer to standard metrics.",
                }
            ),
            500,
        )


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

    return jsonify(
        {
            "status": "ok" if status["api_configured"] else "warning",
            "api_configured": status["api_configured"],
            "model": status["model"],
            "fallback_models": status["fallback_models"],
            "embedding_model": status["embedding_model"],
            "judge_enabled": status["judge_enabled"],
            "judge_model": status["judge_model"],
            "message": (
                "API key not configured" if not status["api_configured"] else None
            ),
        }
    )


@scloda_bp.route("/observability/summary", methods=["GET"])
@require_admin
def observability_summary():
    """GET /api/v1/scloda/observability/summary – aggregated Scloda trace metrics."""
    days = request.args.get("days", default=7, type=int)
    return jsonify(
        {
            "summary": get_trace_summary(days=days),
            "review_queue": get_review_summary(),
        }
    )


@scloda_bp.route("/observability/traces", methods=["GET"])
@require_admin
def observability_traces():
    """GET /api/v1/scloda/observability/traces – recent Scloda traces for admin review."""
    limit = request.args.get("limit", default=25, type=int)
    status = request.args.get("status", default=None, type=str)
    return jsonify({"traces": list_recent_traces(limit=limit, status=status)})


@scloda_bp.route("/knowledge/status", methods=["GET"])
@require_admin
def knowledge_status():
    """GET /api/v1/scloda/knowledge/status – retrieval cache state."""
    return jsonify(get_knowledge_index_status())


@scloda_bp.route("/knowledge/rebuild", methods=["POST"])
@require_admin
def knowledge_rebuild():
    """POST /api/v1/scloda/knowledge/rebuild – rebuild the retrieval cache from current DB state."""
    return jsonify(rebuild_knowledge_index(force=True))


@scloda_bp.route("/review-queue", methods=["GET"])
@require_admin
def review_queue_list():
    """GET /api/v1/scloda/review-queue – pending/resolved human review items."""
    status = request.args.get("status", default=None, type=str)
    limit = request.args.get("limit", default=50, type=int)
    assignee_user_id = request.args.get("assignee_user_id", default=None, type=int)
    return jsonify(
        {
            "items": list_review_items(
                status=status,
                limit=limit,
                assignee_user_id=assignee_user_id,
            )
        }
    )


@scloda_bp.route("/review-queue/mine", methods=["GET"])
@require_admin
def review_queue_mine():
    """GET /api/v1/scloda/review-queue/mine – review items assigned to the current admin."""
    limit = request.args.get("limit", default=25, type=int)
    return jsonify(
        {"items": list_review_items(limit=limit, assignee_user_id=g.current_user.id)}
    )


@scloda_bp.route("/review-queue/<int:item_id>/claim", methods=["POST"])
@require_admin
def review_queue_claim(item_id: int):
    """POST /api/v1/scloda/review-queue/<id>/claim – assign the item to the current admin."""
    result = claim_review_item(item_id, reviewer_user_id=g.current_user.id)
    if result is None:
        return jsonify({"error": "Review item or assignee not found"}), 404
    return jsonify(result)


@scloda_bp.route("/review-queue/<int:item_id>/assign", methods=["POST"])
@require_admin
def review_queue_assign(item_id: int):
    """POST /api/v1/scloda/review-queue/<id>/assign – assign the item to a specific admin."""
    data = request.get_json(silent=True) or {}
    result = assign_review_item(
        item_id,
        assignee_user_id=data.get("assignee_user_id"),
        assignment_note=(data.get("assignment_note") or "").strip(),
    )
    if result is None:
        return jsonify({"error": "Review item or assignee not found"}), 404
    return jsonify(result)


@scloda_bp.route("/review-queue/<int:item_id>/resolve", methods=["POST"])
@require_admin
def review_queue_resolve(item_id: int):
    """POST /api/v1/scloda/review-queue/<id>/resolve – resolve or dismiss a review item."""
    data = request.get_json(silent=True) or {}
    result = resolve_review_item(
        item_id,
        reviewer_notes=(data.get("reviewer_notes") or "").strip(),
        resolution_summary=(data.get("resolution_summary") or "").strip(),
        status=(data.get("status") or "resolved").strip(),
    )
    if result is None:
        return jsonify({"error": "Review item not found"}), 404
    return jsonify(result)


@scloda_bp.route("/capabilities", methods=["GET"])
@require_auth
def capabilities():
    """GET /api/v1/scloda/capabilities – capability tree for Quantum Lab / roadmap."""
    return jsonify({"nodes": get_capability_tree()})
