"""Task routing rules for Scloda model and tool selection."""

from __future__ import annotations

from typing import Any

PRIMARY_MODEL = "openai/gpt-5-mini"
NUMERIC_MODEL = "google/gemini-2.5-flash"
RESEARCH_MODEL = "anthropic/claude-sonnet-4.6"
FAST_MODEL = "openai/gpt-5-mini"
REVIEW_MODEL = "openai/gpt-5-mini"

TASK_MODEL_MAP = {
    "market_live_data": (NUMERIC_MODEL, [FAST_MODEL, RESEARCH_MODEL]),
    "real_estate_research": (RESEARCH_MODEL, [PRIMARY_MODEL, FAST_MODEL]),
    "news_analysis": (RESEARCH_MODEL, [PRIMARY_MODEL, FAST_MODEL]),
    "portfolio_coaching": (PRIMARY_MODEL, [FAST_MODEL, RESEARCH_MODEL]),
    "quantum_lab": (RESEARCH_MODEL, [PRIMARY_MODEL]),
    "general_explanation": (PRIMARY_MODEL, [FAST_MODEL, RESEARCH_MODEL]),
}

TASK_TOOL_ALLOWLIST = {
    "market_live_data": {
        "get_uf_data",
        "get_usdclp_data",
        "get_commodity_data",
        "get_crypto_data",
        "get_market_summary",
        "get_markov_predictions",
        "get_model_info",
        "explain_indicator",
    },
    "real_estate_research": {
        "get_uf_data",
        "get_usdclp_data",
        "get_market_summary",
        "get_markov_predictions",
        "explain_indicator",
    },
    "news_analysis": {
        "get_uf_data",
        "get_usdclp_data",
        "get_commodity_data",
        "get_crypto_data",
        "get_market_summary",
        "explain_indicator",
    },
    "portfolio_coaching": {
        "get_market_summary",
        "get_commodity_data",
        "get_crypto_data",
        "get_usdclp_data",
        "explain_indicator",
    },
    "quantum_lab": {"explain_indicator", "get_model_info", "get_markov_predictions"},
    "general_explanation": {
        "get_market_summary",
        "get_uf_data",
        "get_usdclp_data",
        "explain_indicator",
    },
}

LIVE_DATA_HINTS = (
    "uf",
    "usd/clp",
    "usdclp",
    "dollar",
    "gold",
    "copper",
    "oil",
    "btc",
    "eth",
    "bitcoin",
    "ethereum",
    "current price",
    "current value",
    "valor actual",
)


def route_task(classification: dict[str, Any], user_message: str) -> dict[str, Any]:
    """Select task type, primary model, fallbacks, and tool constraints."""
    task_type = classification.get("task_type", "general_explanation")
    lowered = (user_message or "").lower()

    if any(hint in lowered for hint in LIVE_DATA_HINTS):
        task_type = "market_live_data"

    if classification.get("task_confidence", 0) < 0.45:
        task_type = "general_explanation"
        if any(hint in lowered for hint in LIVE_DATA_HINTS):
            task_type = "market_live_data"

    primary_model, fallback_models = TASK_MODEL_MAP.get(
        task_type, TASK_MODEL_MAP["general_explanation"]
    )

    return {
        "task_type": task_type,
        "primary_model": primary_model,
        "fallback_models": fallback_models,
        "allowed_tools": sorted(TASK_TOOL_ALLOWLIST.get(task_type, set())),
        "judge_model": REVIEW_MODEL,
        "route_reason": f"task:{task_type}",
    }
