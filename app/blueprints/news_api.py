"""
News API Blueprint — endpoints for GNews integration.

Endpoints:
- GET  /api/v1/news/chile   — Cached Chile economy news
- GET  /api/v1/news/world   — Cached World business headlines
- POST /api/v1/news/analyze — Scloda analysis of a single article
- GET  /api/v1/news/health  — Service status
"""

import logging
from flask import Blueprint, jsonify, request

from app.services.gnews_service import (
    fetch_chile_news,
    fetch_world_news,
    analyze_article_with_scloda,
)

logger = logging.getLogger(__name__)

news_bp = Blueprint("news", __name__, url_prefix="/api/v1/news")


@news_bp.route("/chile", methods=["GET"])
def get_chile_news():
    """Return cached Chile economy/finance news."""
    try:
        result = fetch_chile_news()
        if "error" in result:
            return jsonify(result), 503
        return jsonify(result)
    except Exception as exc:
        logger.error("chile_news_error: %s", exc)
        return jsonify({"error": "Internal server error", "articles": []}), 500


@news_bp.route("/world", methods=["GET"])
def get_world_news():
    """Return cached World business top-headlines."""
    try:
        result = fetch_world_news()
        if "error" in result:
            return jsonify(result), 503
        return jsonify(result)
    except Exception as exc:
        logger.error("world_news_error: %s", exc)
        return jsonify({"error": "Internal server error", "articles": []}), 500


@news_bp.route("/analyze", methods=["POST"])
def analyze_article():
    """Send an article to Scloda for UF/pocket impact analysis.

    Request body:
        {
            "article": {
                "title": "...",
                "description": "...",
                "source": {"name": "..."},
                "publishedAt": "...",
                "url": "..."
            }
        }
    """
    try:
        data = request.get_json()
        if not data or "article" not in data:
            return jsonify({"error": "article is required in request body"}), 400

        article = data["article"]
        if not article.get("title"):
            return jsonify({"error": "Article must have a title"}), 400

        result = analyze_article_with_scloda(article)
        return jsonify(result)

    except Exception as exc:
        logger.error("analyze_article_error: %s", exc)
        return jsonify({
            "error": "Internal server error",
            "analysis": "Analysis unavailable.",
        }), 500


@news_bp.route("/health", methods=["GET"])
def news_health():
    """Check GNews service status."""
    import os
    key = os.getenv("GNEWS_API_KEY", "")
    return jsonify({
        "status": "ok" if key else "warning",
        "api_configured": bool(key),
        "message": None if key else "GNEWS_API_KEY not configured",
    })
