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
import logging
import html
import re
from datetime import datetime
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree

import httpx

from app.services.cache import cache_get, cache_set

logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY", "")
GNEWS_BASE_URL = "https://gnews.io/api/v4"
CACHE_TTL = 60 * 60 * 12  # 12 hours; GNews free plan refreshes slowly
LAST_GOOD_SUFFIX = ":last_good"
COOLDOWN_SUFFIX = ":cooldown"
COOLDOWN_TTL = 60 * 60 * 6  # 6 hours
MEDIA_NS = {"media": "http://search.yahoo.com/mrss/"}


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


def _clean_text(value: str | None) -> str:
    """Decode entities, strip tags, and collapse whitespace."""
    if not value:
        return ""
    text = html.unescape(value).replace("\xa0", " ")
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _extract_image_from_rss(item: ElementTree.Element, description_html: str) -> str | None:
    """Try to resolve an image URL from RSS media tags or embedded markup."""
    media_content = item.find("media:content", MEDIA_NS)
    if media_content is not None:
        url = (media_content.attrib.get("url") or "").strip()
        if url:
            return url

    media_thumbnail = item.find("media:thumbnail", MEDIA_NS)
    if media_thumbnail is not None:
        url = (media_thumbnail.attrib.get("url") or "").strip()
        if url:
            return url

    enclosure = item.find("enclosure")
    if enclosure is not None:
        url = (enclosure.attrib.get("url") or "").strip()
        if url:
            return url

    match = re.search(r'<img[^>]+src="([^"]+)"', description_html or "", re.IGNORECASE)
    if match:
        return html.unescape(match.group(1)).strip()

    return None


def _clean_rss_description(description_html: str, *, title: str, source_name: str) -> str:
    """Convert RSS description HTML into a plain snippet."""
    description = _clean_text(description_html)
    if not description:
        return ""

    lower_description = description.lower()
    title_lower = title.lower()
    source_lower = source_name.lower()

    if lower_description.startswith(title_lower):
        description = description[len(title):].strip(" -:|")

    source_index = description.lower().find(source_lower)
    if source_index > 0:
        description = description[:source_index].strip(" -:|")

    # Google News RSS descriptions are often only the linked title + source.
    if not description or description.lower() in {title_lower, source_lower}:
        return ""

    return description


def _normalize_articles(articles: list[dict], *, max_items: int) -> list[dict]:
    """Deduplicate and trim headline lists while keeping stable order."""
    normalized: list[dict] = []
    seen: set[str] = set()

    for article in articles or []:
        url = (article.get("url") or "").strip()
        title = _clean_text(article.get("title"))
        article["title"] = title
        article["description"] = _clean_text(article.get("description"))
        fingerprint = (url or title).lower()
        if not fingerprint or fingerprint in seen:
            continue
        seen.add(fingerprint)
        normalized.append(article)
        if len(normalized) >= max_items:
            break

    return normalized


def _build_payload(
    articles: list[dict],
    *,
    total: int | None = None,
    fetched_at: str | None = None,
    stale: bool = False,
    source_status: str = "live",
    warning: str | None = None,
) -> dict:
    return {
        "articles": articles,
        "toon": compress_articles_toon(articles),
        "total": total if total is not None else len(articles),
        "fetched_at": fetched_at or datetime.utcnow().isoformat(),
        "stale": stale,
        "source_status": source_status,
        "warning": warning,
    }


def _set_last_good(cache_key: str, payload: dict) -> None:
    cache_set(f"{cache_key}{LAST_GOOD_SUFFIX}", payload, ttl=60 * 60 * 24 * 14)


def _get_last_good(cache_key: str) -> dict | None:
    return cache_get(f"{cache_key}{LAST_GOOD_SUFFIX}") or cache_get(cache_key)


def _set_cooldown(cache_key: str, reason: str) -> None:
    cache_set(
        f"{cache_key}{COOLDOWN_SUFFIX}",
        {"reason": reason, "until": datetime.utcnow().isoformat()},
        ttl=COOLDOWN_TTL,
    )


def _cooldown_active(cache_key: str) -> bool:
    return cache_get(f"{cache_key}{COOLDOWN_SUFFIX}") is not None


def _stale_fallback(cache_key: str, error_message: str) -> dict:
    stale_payload = _get_last_good(cache_key)
    if stale_payload:
        return _build_payload(
            stale_payload.get("articles", []),
            total=stale_payload.get("total"),
            fetched_at=stale_payload.get("fetched_at"),
            stale=True,
            source_status="stale_cache",
            warning=error_message,
        )
    return {"error": error_message, "articles": []}


def _rss_datetime(value: str) -> str:
    try:
        return parsedate_to_datetime(value).isoformat()
    except Exception:
        return datetime.utcnow().isoformat()


def _rss_fallback(feed_url: str, *, max_items: int) -> list[dict]:
    try:
        with httpx.Client(timeout=10.0, follow_redirects=True) as client:
            response = client.get(feed_url)
            response.raise_for_status()
        root = ElementTree.fromstring(response.text)
    except Exception as exc:
        logger.warning("rss_fallback_failed: %s", exc)
        return []

    articles: list[dict] = []
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        url = (item.findtext("link") or "").strip()
        published_at = _rss_datetime(item.findtext("pubDate") or "")
        description_html = item.findtext("description") or ""
        if not title or not url:
            continue
        source_name = _clean_text(item.findtext("source") or "") or "RSS fallback"
        if " - " in title:
            title_parts = title.rsplit(" - ", 1)
            if len(title_parts) == 2 and title_parts[1].strip():
                title = title_parts[0].strip()
                if source_name == "RSS fallback":
                    source_name = title_parts[1].strip()
        articles.append(
            {
                "title": _clean_text(title),
                "description": _clean_rss_description(
                    description_html,
                    title=title,
                    source_name=source_name,
                ),
                "url": url,
                "publishedAt": published_at,
                "image": _extract_image_from_rss(item, description_html),
                "source": {"name": source_name},
            }
        )
        if len(articles) >= max_items:
            break

    return _normalize_articles(articles, max_items=max_items)


def _rss_payload(feed_url: str, *, max_items: int, warning: str) -> dict | None:
    articles = _rss_fallback(feed_url, max_items=max_items)
    if not articles:
        return None
    return _build_payload(
        articles,
        total=len(articles),
        stale=False,
        source_status="rss_fallback",
        warning=warning,
    )


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
    cache_key = "gnews:v2:chile"
    cached = cache_get(cache_key)
    if cached:
        logger.info("gnews_chile_cache_hit")
        return {**cached, "source_status": cached.get("source_status", "cache")}

    if _cooldown_active(cache_key):
        return _stale_fallback(
            cache_key,
            "Using cached Chile headlines while the upstream provider cools down.",
        )

    result = _gnews_request("search", {
        "q": '"Chile" AND (economía OR finanzas OR inmobiliario OR hipotecario OR UF OR "Banco Central")',
        "lang": "es",
        "country": "cl",
        "max": 12,
        "sortby": "publishedAt",
    })

    if "error" not in result:
        articles = _normalize_articles(result.get("articles", []), max_items=12)
        payload = _build_payload(
            articles,
            total=result.get("totalArticles", len(articles)),
            source_status="live",
        )
        cache_set(cache_key, payload, ttl=CACHE_TTL)
        _set_last_good(cache_key, payload)
        return payload

    _set_cooldown(cache_key, result["error"])
    rss_payload = _rss_payload(
        "https://news.google.com/rss/search?q=Chile+econom%C3%ADa+OR+Chile+finanzas+OR+Chile+inmobiliario&hl=es-419&gl=CL&ceid=CL:es-419",
        max_items=12,
        warning="GNews is rate limited, using RSS backup headlines.",
    )
    if rss_payload:
        cache_set(cache_key, rss_payload, ttl=CACHE_TTL)
        _set_last_good(cache_key, rss_payload)
        return rss_payload
    return _stale_fallback(cache_key, result["error"])


def fetch_world_news() -> dict:
    """Fetch world business top-headlines (cached 12h)."""
    cache_key = "gnews:v2:world"
    cached = cache_get(cache_key)
    if cached:
        logger.info("gnews_world_cache_hit")
        return {**cached, "source_status": cached.get("source_status", "cache")}

    if _cooldown_active(cache_key):
        return _stale_fallback(
            cache_key,
            "Using cached world headlines while the upstream provider cools down.",
        )

    result = _gnews_request("top-headlines", {
        "category": "business",
        "lang": "en",
        "max": 8,
    })

    if "error" not in result:
        articles = _normalize_articles(result.get("articles", []), max_items=8)
        payload = _build_payload(
            articles,
            total=result.get("totalArticles", len(articles)),
            source_status="live",
        )
        cache_set(cache_key, payload, ttl=CACHE_TTL)
        _set_last_good(cache_key, payload)
        return payload

    _set_cooldown(cache_key, result["error"])
    rss_payload = _rss_payload(
        "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=en-US&gl=US&ceid=US:en",
        max_items=8,
        warning="GNews is rate limited, using RSS backup headlines.",
    )
    if rss_payload:
        cache_set(cache_key, rss_payload, ttl=CACHE_TTL)
        _set_last_good(cache_key, rss_payload)
        return rss_payload
    return _stale_fallback(cache_key, result["error"])


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
