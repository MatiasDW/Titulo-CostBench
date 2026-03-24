"""
GNews Service — fetches news from GNews API with caching and TOON compression.

Free Plan constraints:
- 100 requests/day
- News refreshes every 12 hours
- No CORS (must call from backend)

Endpoints used:
- Search: Chile financial news (Spanish)
- Top Headlines: World business news (English)
"""

import os
import json
import hashlib
import logging
from datetime import datetime

import httpx

from app.services.cache import cache_get, cache_set

logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY", "")
GNEWS_BASE_URL = "https://gnews.io/api/v4"
CACHE_TTL = 43200  # 12 hours in seconds


# ── TOON Compression ─────────────────────────────────────────
def _try_import_toon():
    """Lazy import toon_format — returns encode function or None."""
    try:
        from toon_format import encode
        return encode
    except ImportError:
        logger.warning("toon_format not installed, using fallback compressor")
        return None


def compress_articles_toon(articles: list[dict]) -> str:
    """Compress a list of GNews articles using TOON format.

    Falls back to pipe-delimited format if toon_format is unavailable.
    """
    encode = _try_import_toon()

    # Build a minimal list of dicts for compression
    compact = []
    for i, art in enumerate(articles):
        compact.append({
            "id": i + 1,
            "t": art.get("title", ""),
            "d": (art.get("description") or "")[:120],
            "s": art.get("source", {}).get("name", ""),
            "f": _format_date(art.get("publishedAt", "")),
            "u": art.get("url", ""),
        })

    if encode:
        try:
            return encode(compact)
        except Exception as exc:
            logger.warning("TOON encode failed, using fallback: %s", exc)

    return _compress_fallback(compact)


def _compress_fallback(compact: list[dict]) -> str:
    """Pipe-delimited fallback compressor."""
    lines = []
    for item in compact:
        lines.append(
            f"[ID:{item['id']} | T:{item['t']} | "
            f"D:{item['d']} | S:{item['s']} | F:{item['f']}]"
        )
    return "\n".join(lines)


def compress_single_article(article: dict) -> str:
    """Compress a single article for Scloda analysis."""
    return compress_articles_toon([article])


def _format_date(iso_str: str) -> str:
    """Convert ISO date to compact format."""
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except (ValueError, AttributeError):
        return iso_str[:16] if iso_str else ""


# ── GNews API Calls ──────────────────────────────────────────
def _gnews_request(endpoint: str, params: dict) -> dict:
    """Make a request to the GNews API with error handling."""
    if not GNEWS_API_KEY:
        return {"error": "GNEWS_API_KEY not configured", "articles": []}

    params["apikey"] = GNEWS_API_KEY
    url = f"{GNEWS_BASE_URL}/{endpoint}"

    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(url, params=params)

            if resp.status_code == 403:
                logger.error("GNews 403: API key invalid or quota exceeded")
                return {
                    "error": "API quota exceeded (Free plan: 100 req/day)",
                    "articles": [],
                }

            if resp.status_code == 429:
                logger.error("GNews 429: rate limited")
                return {
                    "error": "Rate limited — please try again later",
                    "articles": [],
                }

            resp.raise_for_status()
            return resp.json()

    except httpx.TimeoutException:
        logger.error("GNews timeout")
        return {"error": "GNews API timeout", "articles": []}
    except Exception as exc:
        logger.error("GNews request failed: %s", exc)
        return {"error": str(exc), "articles": []}


def fetch_chile_news() -> dict:
    """Fetch Chile economy/finance/real-estate news (cached 12h).

    Search query: Chile AND (economía OR finanzas OR inmobiliario)
    """
    cache_key = "gnews:chile"
    cached = cache_get(cache_key)
    if cached:
        logger.info("gnews_chile_cache_hit")
        return cached

    result = _gnews_request("search", {
        "q": "Chile AND (economía OR finanzas OR inmobiliario)",
        "lang": "es",
        "country": "cl",
        "max": 10,
    })

    if "error" not in result:
        articles = result.get("articles", [])
        payload = {
            "articles": articles,
            "toon": compress_articles_toon(articles),
            "total": result.get("totalArticles", len(articles)),
            "fetched_at": datetime.utcnow().isoformat(),
        }
        cache_set(cache_key, payload, ttl=CACHE_TTL)
        return payload

    return result


def fetch_world_news() -> dict:
    """Fetch world business top-headlines (cached 12h)."""
    cache_key = "gnews:world"
    cached = cache_get(cache_key)
    if cached:
        logger.info("gnews_world_cache_hit")
        return cached

    result = _gnews_request("top-headlines", {
        "category": "business",
        "lang": "en",
        "max": 5,
    })

    if "error" not in result:
        articles = result.get("articles", [])
        payload = {
            "articles": articles,
            "toon": compress_articles_toon(articles),
            "total": result.get("totalArticles", len(articles)),
            "fetched_at": datetime.utcnow().isoformat(),
        }
        cache_set(cache_key, payload, ttl=CACHE_TTL)
        return payload

    return result


# ── Scloda RAG Analysis ──────────────────────────────────────
def analyze_article_with_scloda(article: dict) -> dict:
    """Send a compressed article snippet to Scloda for analysis.

    Asks: 'How does this affect your pocket or the UF?'
    Returns dict with 'analysis' and 'tokens_used'.
    """
    snippet = compress_single_article(article)

    prompt = (
        "You are Scloda, the financial analyst for CostBench.\n\n"
        "A user clicked 'Analyze with Scloda' on this news article. "
        "Read the compressed snippet below and answer:\n"
        "**How does this news affect the average Chilean's pocket or the UF?**\n\n"
        "Be concise (2-3 sentences), practical, and mention specific financial "
        "impacts when possible (mortgage rates, purchasing power, UF movement).\n\n"
        f"Article snippet:\n{snippet}\n\n"
        "ALWAYS respond in English. Add the disclaimer that this is informational, "
        "not financial advice."
    )

    try:
        from app.services.scloda_service import _call_openrouter
        messages = [
            {"role": "system", "content": "You are Scloda, senior financial analyst."},
            {"role": "user", "content": prompt},
        ]
        response = _call_openrouter(messages, tools=None)

        if "error" in response:
            return {
                "analysis": "⏳ Analysis temporarily unavailable. Try again shortly.",
                "tokens_used": 0,
            }

        return {
            "analysis": response["choices"][0]["message"]["content"].strip(),
            "tokens_used": response.get("usage", {}).get("total_tokens", 0),
        }

    except Exception as exc:
        logger.error("analyze_article error: %s", exc)
        return {
            "analysis": "⚠️ Could not analyze this article right now.",
            "tokens_used": 0,
        }
