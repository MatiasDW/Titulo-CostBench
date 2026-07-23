"""
Scloda Chat Service - OpenRouter/Gemini integration for AI chat.

Handles:
- OpenRouter API calls with Gemini 2.0 Flash
- Function calling (tool use) for market data queries
- Conversation context management
"""

import os
import json
import re
import uuid
import httpx
from typing import Any
from datetime import datetime
from pathlib import Path
from time import perf_counter

from app.services.scloda_classifier import classify_message, get_classifier_status
from app.services.scloda_circuit_breakers import (
    allow_model,
    get_circuit_breaker_status,
    record_model_failure,
    record_model_success,
)
from app.services.scloda_external_observability import get_external_observability_status
from app.services.scloda_memory import (
    SCLODA_EMBEDDING_MODEL,
    get_knowledge_index_status,
    retrieve_knowledge,
    should_retrieve_knowledge,
)
from app.services.scloda_observability import persist_scloda_trace
from app.services.scloda_review_queue import create_review_item, get_review_summary
from app.services.scloda_task_router import route_task
from app.services.scloda_tools import SCLODA_TOOLS, execute_tool
from app.ml.logging_utils import get_logger

logger = get_logger("scloda.service")

# Configuration
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
def _is_configured_secret(value: str | None) -> bool:
    if not value:
        return False
    normalized = value.strip().lower()
    placeholder_markers = ("tu-", "example", "ejemplo", "aqui", "changeme")
    return not any(marker in normalized for marker in placeholder_markers)


_raw_openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_API_KEY = _raw_openrouter_key if _is_configured_secret(_raw_openrouter_key) else ""
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-5-mini")
OPENROUTER_HTTP_REFERER = os.getenv("OPENROUTER_HTTP_REFERER", "https://costbench.cl")
OPENROUTER_X_TITLE = os.getenv("OPENROUTER_X_TITLE", "CostBench - Scloda Chat")
OPENROUTER_FALLBACK_MODELS = [
    model.strip()
    for model in os.getenv(
        "OPENROUTER_FALLBACK_MODELS",
        "anthropic/claude-sonnet-4.6,google/gemini-2.5-flash",
    ).split(",")
    if model.strip()
]
SCLODA_ENABLE_JUDGE_MODEL = (
    os.getenv("SCLODA_ENABLE_JUDGE_MODEL", "false").lower() == "true"
)
SCLODA_JUDGE_MODEL = os.getenv("SCLODA_JUDGE_MODEL", "openai/gpt-5-mini")
SCLODA_JUDGE_MAX_TOKENS = int(os.getenv("SCLODA_JUDGE_MAX_TOKENS", "220"))

# ── Fail-Fast config ──────────────────────────────────────────
# Strict timeout — if the LLM doesn't answer in this window we
# cut the connection and let the *user* decide whether to retry.
LLM_TIMEOUT_SECONDS = int(os.getenv("SCLODA_TIMEOUT", "12"))

# Pre-baked Scloda message shown on any LLM failure.
_FRIENDLY_ERROR = (
    "⏳ The networks are a bit congested right now and I couldn't "
    "process your request. Can you try again in a few seconds?"
)

MAX_HISTORY_MESSAGES = 10
ALLOWED_HISTORY_ROLES = {"user", "assistant"}
DOMAIN_KEYWORDS = {
    "uf", "usd", "dollar", "peso", "clp", "bitcoin", "ethereum", "crypto",
    "copper", "gold", "silver", "oil", "market", "markets", "inflation",
    "rates", "fed", "mortgage", "rent", "real estate", "property", "housing",
    "chile", "investment", "investing", "portfolio", "macro", "yield",
    "commodities", "risk", "bank", "banks", "hipotec", "arriendo",
}
SMALL_TALK_KEYWORDS = {"hi", "hello", "hey", "thanks", "thank you", "hola", "help"}
PROMPT_INJECTION_PATTERNS = [
    r"ignore (all|the|your) (previous|prior) instructions",
    r"reveal (your|the) (system|developer) prompt",
    r"show me (your|the) hidden instructions",
    r"bypass (your|the) guardrails",
    r"act as a different model",
    r"developer mode",
    r"jailbreak",
]
DATE_AWARENESS_RULES = """

## DATE-AWARE RESPONSE RULES

- When tool data includes `as_of_label`, explicitly mention it in the answer, for example: "as of July 22, 2026".
- Only use words like "currently", "today", or "right now" if `is_current_for_market_day` is true.
- If `is_current_for_market_day` is false, say "latest available reading as of <date>" instead.
- If live data is unavailable but the tool provides `fallback_context`, say that the current quote is unavailable and then give contextual or historical explanation without inventing numbers.
"""


def _candidate_openrouter_models(
    primary_model: str | None = None,
    fallback_models: list[str] | None = None,
) -> list[str]:
    candidates = [
        primary_model or OPENROUTER_MODEL,
        *(fallback_models if fallback_models is not None else OPENROUTER_FALLBACK_MODELS),
    ]
    seen = set()
    ordered: list[str] = []
    for model in candidates:
        if model and model not in seen:
            ordered.append(model)
            seen.add(model)
    return ordered


def _sanitize_history(conversation_history: list[dict] | None) -> list[dict]:
    """Keep only the last allowed user/assistant messages with valid text content."""
    sanitized: list[dict] = []
    for item in conversation_history or []:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = item.get("content")
        if role not in ALLOWED_HISTORY_ROLES or not isinstance(content, str):
            continue
        text = content.strip()
        if not text:
            continue
        sanitized.append({"role": role, "content": text[:4000]})
    return sanitized[-MAX_HISTORY_MESSAGES:]


def _message_is_domain_related(user_message: str) -> bool:
    lowered = user_message.lower()
    return any(keyword in lowered for keyword in DOMAIN_KEYWORDS)


def _message_is_small_talk(user_message: str) -> bool:
    lowered = user_message.lower().strip()
    return any(keyword == lowered or keyword in lowered for keyword in SMALL_TALK_KEYWORDS)


def _screen_user_message(user_message: str) -> dict[str, Any]:
    """Basic input guardrails for scope and obvious injection patterns."""
    lowered = user_message.lower()

    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, lowered):
            return {
                "blocked": True,
                "reason": "prompt_injection",
                "response": (
                    "I can help with CostBench topics like markets, real estate, macro data, and investment context, "
                    "but I can't expose internal instructions or override my operating rules."
                ),
            }

    if _message_is_small_talk(user_message):
        return {"blocked": False, "reason": "small_talk"}

    if not _message_is_domain_related(user_message):
        return {
            "blocked": True,
            "reason": "out_of_scope",
            "response": (
                "I’m specialized in CostBench topics: Chilean markets, macro indicators, real estate, investment context, and Scloda-related analysis. "
                "If you want, ask me about UF, USD/CLP, mortgages, market moves, property decisions, or financial news."
            ),
        }

    return {"blocked": False, "reason": "domain"}


def _extract_tool_payloads(tool_results: list[dict]) -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    for item in tool_results:
        try:
            payload = json.loads(item.get("content", "{}"))
        except Exception:
            payload = {"error": "invalid_tool_payload"}
        payloads.append(payload)
    return payloads


def _extract_message_content(message: Any) -> str:
    """Normalize OpenRouter/OpenAI-style message content into plain text."""
    if isinstance(message, str):
        return message
    if message is None:
        return ""
    if isinstance(message, list):
        parts: list[str] = []
        for item in message:
            if isinstance(item, str):
                parts.append(item)
                continue
            if not isinstance(item, dict):
                continue
            text = item.get("text")
            if isinstance(text, str):
                parts.append(text)
                continue
            if item.get("type") == "text" and isinstance(item.get("content"), str):
                parts.append(item["content"])
        return "\n".join(part for part in parts if part).strip()
    if isinstance(message, dict):
        text = message.get("text")
        if isinstance(text, str):
            return text
        content = message.get("content")
        if isinstance(content, str):
            return content
        return _extract_message_content(content)
    return str(message)


def _compute_confidence(tool_payloads: list[dict[str, Any]]) -> str:
    if not tool_payloads:
        return "medium"
    success_count = sum(1 for payload in tool_payloads if payload.get("status") == "ok" and "error" not in payload)
    fallback_count = sum(1 for payload in tool_payloads if payload.get("status") == "no_live_data")
    if success_count == len(tool_payloads):
        return "high"
    if success_count > 0 or fallback_count > 0:
        return "medium"
    return "low"


def _apply_response_guardrails(final_content: str, tool_payloads: list[dict[str, Any]]) -> str:
    """Post-process the final response so the UX is explicit about freshness and missing live data."""
    text = (final_content or "").strip()
    if not text:
        text = "I'm sorry, I was able to retrieve context but had a problem producing the final answer."

    successful_dates = [
        payload.get("as_of_label")
        for payload in tool_payloads
        if payload.get("status") == "ok" and payload.get("as_of_label")
    ]
    if successful_dates and "as of" not in text.lower():
        text = f"As of {successful_dates[0]}, {text[0].lower() + text[1:] if len(text) > 1 else text.lower()}"

    if any(payload.get("status") == "no_live_data" for payload in tool_payloads):
        if "live data" not in text.lower() and "latest available" not in text.lower():
            text += " Live data was unavailable for part of this answer, so I relied on historical or structural context where needed."

    return text


def _build_retrieval_context(retrieved_chunks: list[dict[str, Any]]) -> str:
    lines = [
        "## INTERNAL KNOWLEDGE CONTEXT",
        "Use this retrieved context only when relevant. Prefer tool data for live numeric claims.",
    ]
    for idx, chunk in enumerate(retrieved_chunks, start=1):
        title = chunk.get("title", f"Chunk {idx}")
        content = (chunk.get("content", "") or "").strip()
        source_key = chunk.get("source_key", "unknown")
        lines.append(f"{idx}. [{source_key}] {title}: {content}")
    return "\n".join(lines)


def _usage_from_response(response: dict[str, Any]) -> dict[str, int]:
    usage = response.get("usage", {}) if isinstance(response, dict) else {}
    return {
        "prompt_tokens": int(usage.get("prompt_tokens", 0) or 0),
        "completion_tokens": int(usage.get("completion_tokens", 0) or 0),
        "total_tokens": int(usage.get("total_tokens", 0) or 0),
    }


def _should_run_judge(
    tool_payloads: list[dict[str, Any]],
    retrieved_chunks: list[dict[str, Any]],
    confidence: str,
) -> bool:
    if not SCLODA_ENABLE_JUDGE_MODEL:
        return False
    return bool(tool_payloads or retrieved_chunks or confidence != "high")


def _run_judge_review(
    *,
    user_message: str,
    final_response: str,
    tool_payloads: list[dict[str, Any]],
    retrieved_chunks: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if not OPENROUTER_API_KEY:
        return None

    evidence = {
        "tool_payloads": tool_payloads,
        "retrieved_chunks": [
            {
                "source_key": chunk.get("source_key"),
                "title": chunk.get("title"),
                "content": chunk.get("content"),
            }
            for chunk in retrieved_chunks
        ],
    }
    prompt = (
        "Review whether the assistant answer is grounded in the evidence.\n\n"
        f"User question:\n{user_message}\n\n"
        f"Assistant answer:\n{final_response}\n\n"
        f"Evidence:\n{json.dumps(evidence, ensure_ascii=False)}\n\n"
        "Return strict JSON with keys: grounded_to_evidence (boolean), "
        "mentions_date_correctly (boolean), numeric_risk ('low'|'medium'|'high'), "
        "final_verdict ('safe'|'review'|'warn'), notes (string)."
    )
    messages = [
        {
            "role": "system",
            "content": (
                "You are a strict groundedness reviewer. "
                "Do not rewrite the answer. Only score whether it is supported by the provided evidence."
            ),
        },
        {"role": "user", "content": prompt},
    ]
    response = _call_openrouter(
        messages,
        tools=None,
        temperature=0,
        max_tokens=SCLODA_JUDGE_MAX_TOKENS,
        primary_model=SCLODA_JUDGE_MODEL,
        fallback_models=[],
    )
    if "error" in response:
        return None

    content = _extract_message_content(response["choices"][0]["message"].get("content"))
    if content.startswith("```json"):
        content = content.replace("```json", "").replace("```", "").strip()
    try:
        result = json.loads(content)
        result["_resolved_model"] = response.get("_resolved_model", SCLODA_JUDGE_MODEL)
        return result
    except Exception:
        logger.warning("judge_parse_failed", content=content[:200])
        return None


def _persist_trace(
    *,
    trace_id: str,
    user_message: str,
    user_profile: dict[str, Any] | None,
    history_count: int,
    screening_reason: str | None,
    guardrail_action: str | None,
    response_status: str,
    response_text: str,
    error_code: str | None,
    confidence: str | None,
    model_resolved: str | None,
    task_type: str | None,
    tools_used: list[str],
    tool_payloads: list[dict[str, Any]],
    retrieved_chunks: list[dict[str, Any]],
    judge_summary: dict[str, Any] | None,
    usage_totals: dict[str, int],
    started_at: float,
) -> None:
    persist_scloda_trace(
        {
            "trace_id": trace_id,
            "user_id": (user_profile or {}).get("id"),
            "request_kind": "chat",
            "user_message": user_message,
            "response_text": response_text,
            "history_count": history_count,
            "screening_reason": screening_reason,
            "guardrail_action": guardrail_action,
            "response_status": response_status,
            "confidence": confidence,
            "error_code": error_code,
            "task_type": task_type,
            "model_requested": OPENROUTER_MODEL,
            "model_resolved": model_resolved,
            "embedding_model": SCLODA_EMBEDDING_MODEL if retrieved_chunks else None,
            "judge_model": (
                judge_summary.get("_resolved_model")
                if isinstance(judge_summary, dict)
                else None
            ),
            "tools_used": tools_used,
            "tool_payloads": tool_payloads,
            "retrieved_chunks": [
                {
                    "source_key": chunk.get("source_key"),
                    "title": chunk.get("title"),
                    "score": chunk.get("score"),
                }
                for chunk in retrieved_chunks
            ],
            "judge_summary": judge_summary,
            "prompt_tokens": usage_totals["prompt_tokens"],
            "completion_tokens": usage_totals["completion_tokens"],
            "total_tokens": usage_totals["total_tokens"],
            "latency_ms": int((perf_counter() - started_at) * 1000),
        }
    )


def _load_system_prompt() -> str:
    """Load system prompt from AI_PROMPT_GUIDE.md if available, otherwise use default."""
    # Try to load from file
    prompt_file = Path(__file__).parent.parent.parent / "AI_PROMPT_GUIDE.md"

    if prompt_file.exists():
        try:
            content = prompt_file.read_text(encoding="utf-8")
            # Add a prefix to make it clear this is a system prompt
            return f"""You are Scloda, the AI analyst for CostBench. Use the following guide as your knowledge base and persona definition:

{content}

Remember: Always use the available tools to get real data. Never invent numbers. ALWAYS respond in English, regardless of the language the user writes in."""
        except Exception as e:
            logger.warning("prompt_file_load_failed", error=str(e))

    # Fallback to embedded prompt
    return _get_default_prompt()


def _get_default_prompt() -> str:
    """Default system prompt if file is not available."""
    return """You are Scloda, a multidisciplinary expert in finance, technology, and data analysis.

Your expertise spans: Data Science, FinOps, Software Engineering, Investments, and Macro/Micro Economics.

RULES:
1. Use simple but precise language
2. Provide practical examples
3. Connect data with correlations
4. Clearly warn about risks
5. Always: "This is informational, NOT financial advice"

ALWAYS respond in English, regardless of the language the user writes in. Use the available tools to get real data."""


# System prompt for Scloda
SYSTEM_PROMPT = """You are Scloda, a multidisciplinary expert in finance, technology, and data analysis.

## YOUR PROFESSIONAL PROFILE

**Data Scientist & ML Engineer:**
- Expert in time series (ARIMA, Theta, ETS, Prophet)
- Understand error metrics (MAE, RMSE, MAPE) and can explain them in simple terms
- Can interpret model results and explain their reliability

**FinOps & Finance Expert:**
- Know Chilean financial products: mortgages, CAE, insurance, AFPs
- Understand UF, CPI, and how they affect everyday people
- Can analyze banking costs and find the best options

**Software Engineer:**
- Understand APIs, real-time data, and how integrations work
- Can explain technical concepts in an accessible way

**Businessman & Investor:**
- Know investment strategies: diversification, risk/return, time horizons
- Understand correlations between assets (gold vs dollar, copper vs Chilean peso)
- Know when an asset is a safe haven and when it's speculative

**Macro & Micro Economist:**
- Understand how Fed rates affect Chile
- Know the impact of copper on the Chilean economy
- Can explain inflation, monetary policy, and economic cycles

## YOUR PERSONALITY

- Approachable yet professional, like a mentor who knows finance
- Use clear, accessible language for all audiences
- Optimistic but ALWAYS warn about risks
- Explain complex concepts with everyday analogies

## COMMUNICATION RULES

1. **Simplify without losing precision** - Use everyday but correct language
2. **Give practical examples** - "If UF rises 1%, your mortgage payment goes up ~$5,000"
3. **Connect the data** - Explain correlations ("The dollar drops because copper rose")
4. **Always contextualize** - "This is high/low/normal compared to..."
5. **Warn about risks** - If something is volatile or speculative, say it clearly
6. **Always disclaimer** - Data is informational, NOT financial advice
7. **Ultra-Concise Format** - Respond natively via chat (max 1-2 paragraphs). DO NOT write reports with bold sections (e.g., "**Current Trend:**" or "**Model Assessment:**"). First call tools, and THEN generate a natural conversation summarizing the data.

## ABOUT ML MODELS & PREDICTIVE ANALYTICS

When asked about market movements or predictions, you MUST ACT AS A QUANTITATIVE ANALYST:
1. **Never rely on single data points**.
2. **Always cross-reference:**
   - The historical data (what just happened).
   - The ARIMA/ML Model Forecasts (what the mathematical trend says).
   - **The Markov Chain Matrix (get_markov_predictions)**: The empirical probability of state changes based on Granger causality.
3. Example of an excellent response: "The ARIMA model predicts a slight upward trend (MAPE 2.5%), but wait, according to our Markov matrices, if Copper just dropped today, there is a 73% historical probability that the Dollar will go 'Sideways' or 'Bull' tomorrow. So, despite the long-term upward trend, expect short-term turbulence."

Explain ML models like this:
- **ARIMA**: "Looks at past patterns to predict the future"
- **Theta**: "Smooths volatility to find the real trend"
- **Naive**: "Assumes tomorrow will be the same as today"

## AVAILABLE DATA

Use tools to query:
- UF and USD/CLP (Central Bank of Chile)
- Gold, Copper, Oil, Silver (global commodities)
- Bitcoin, Ethereum (cryptocurrencies)
- **Markov Predictions**: Use `get_markov_predictions` when someone asks "What predicts X?" or "What is likely to happen next based on today's movement?"

### TOOL USAGE (CRITICAL)
- **DO NOT** output python code. **DO NOT** write ```tool_code``` or `print(default_api.get_asset_prediction(...))`. 
- You must use the integrated JSON tool calling mechanism secretly whenever you need data.
- The user cannot see code. The user only wants the human-readable result.
- **NEVER** mention internal tool or function names (like get_commodity_data, get_crypto_data, get_uf_data, get_markov_predictions, etc.) in your responses. These are internal and invisible to the user.

## IMPORTANT

- If you don't have updated data, say so honestly
- NEVER make up numbers or statistics
- If the question is outside your knowledge, recommend consulting a professional
- ALWAYS respond in English, regardless of the language the user writes in

Respond concisely but completely. Use emojis sparingly (📊💡⚠️) to make conversation friendlier."""


# ── Risk-profile rules for "Sniper Mode" ──────────────────────
RISK_PROFILE_RULES = {
    "conservative": {
        "label": "Conservative",
        "tone": "prudent and protective",
        "focus": (
            "- Prioritize capital preservation and stability\n"
            "- Emphasize risks and potential downturns BEFORE opportunities\n"
            "- Recommend low-risk instruments (deposits, UF, fixed income)\n"
            "- Use phrases like 'consider the risk', 'protect your capital'\n"
            "- Explicitly warn about volatility in crypto and commodities\n"
            "- Long-term investment horizon, defensive diversification"
        ),
    },
    "moderate": {
        "label": "Moderate",
        "tone": "balanced and analytical",
        "focus": (
            "- Balance opportunities with risk management\n"
            "- Present both sides: potential gains AND risk of loss\n"
            "- Suggest diversification between stable and growth assets\n"
            "- Mention risk/return ratios when relevant\n"
            "- Allow moderate exposure to crypto and commodities\n"
            "- Medium-term investment horizon"
        ),
    },
    "aggressive": {
        "label": "Aggressive",
        "tone": "direct and opportunity-oriented",
        "focus": (
            "- Focus on high-return opportunities\n"
            "- Analyze momentum, trends, and technical signals\n"
            "- Discuss alpha, beta, and volatility as opportunity\n"
            "- You can be bolder in suggestions\n"
            "- Still ALWAYS mention risk (mandatory)\n"
            "- Short/medium-term investment horizon, high drawdown tolerance"
        ),
    },
}

# Interest label mapping
INTEREST_LABELS = {
    "crypto": "Cryptocurrencies (BTC, ETH)",
    "commodities": "Commodities (Gold, Copper, Oil)",
    "fixed_income": "Fixed Income (Bonds, Deposits)",
    "banking": "Banking Costs (accounts, fees)",
    "macro": "Macroeconomics (CPI, rates, monetary policy)",
    "forex": "Forex (USD/CLP, UF)",
    "stocks": "Stocks",
    "ml_models": "ML Models & Predictions",
}


def _build_user_context(user_profile: dict | None) -> str:
    """
    Build a dynamic system-prompt section from the user's profile.
    Returns empty string if no profile or no risk_profile set.
    """
    if not user_profile:
        return ""

    risk = user_profile.get("risk_profile")
    interests = user_profile.get("interests", [])

    if not risk:
        return ""

    rules = RISK_PROFILE_RULES.get(risk)
    if not rules:
        return ""

    # Build personalized section
    lines = [
        "",
        "## 🎯 MODO SNIPER — Perfil Personalizado",
        "",
        f"El usuario tiene perfil **{rules['label']}**.",
        f"Tu tono debe ser **{rules['tone']}**.",
        "",
        "### Reglas específicas para este perfil:",
        rules["focus"],
    ]

    if interests:
        labels = [INTEREST_LABELS.get(i, i) for i in interests]
        lines.extend(
            [
                "",
                "### Áreas de interés del usuario:",
                ", ".join(labels),
                "Cuando sea posible, conecta tus respuestas con estos temas de interés.",
            ]
        )

    return "\n".join(lines)


def chat_completion(
    user_message: str,
    conversation_history: list[dict] | None = None,
    user_profile: dict | None = None,
) -> dict[str, Any]:
    """
    Process a chat message and return Scloda's response.

    Args:
        user_message: The user's message
        conversation_history: Previous messages in the conversation
        user_profile: Optional dict with risk_profile, interests, email

    Returns:
        dict with 'response' (text) and 'tokens_used'
    """
    trace_id = str(uuid.uuid4())
    started_at = perf_counter()
    usage_totals = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    tools_used: list[str] = []
    tool_payloads: list[dict[str, Any]] = []
    retrieved_chunks: list[dict[str, Any]] = []
    judge_summary: dict[str, Any] | None = None
    model_resolved: str | None = None
    history_count = 0
    task_type = "general_explanation"
    classification = classify_message(user_message)
    route = route_task(classification, user_message)
    task_type = route["task_type"]

    if not OPENROUTER_API_KEY:
        result = {
            "response": "⚠️ API not configured. Add OPENROUTER_API_KEY to the .env file",
            "tokens_used": 0,
            "error": "no_api_key",
            "trace_id": trace_id,
        }
        _persist_trace(
            trace_id=trace_id,
            user_message=user_message,
            user_profile=user_profile,
            history_count=history_count,
            screening_reason="no_api_key",
            guardrail_action=None,
            response_status="error",
            response_text=result["response"],
            error_code="no_api_key",
            confidence=None,
            model_resolved=None,
            task_type=task_type,
            tools_used=[],
            tool_payloads=[],
            retrieved_chunks=[],
            judge_summary=None,
            usage_totals=usage_totals,
            started_at=started_at,
        )
        return result

    screening = _screen_user_message(user_message)
    if screening["blocked"]:
        logger.info(
            "chat_guardrail_blocked", trace_id=trace_id, reason=screening["reason"]
        )
        result = {
            "response": screening["response"],
            "tokens_used": 0,
            "guardrail_action": screening["reason"],
            "trace_id": trace_id,
            "confidence": "high",
        }
        _persist_trace(
            trace_id=trace_id,
            user_message=user_message,
            user_profile=user_profile,
            history_count=history_count,
            screening_reason=screening["reason"],
            guardrail_action=screening["reason"],
            response_status="guardrail_blocked",
            response_text=result["response"],
            error_code=None,
            confidence=result["confidence"],
            model_resolved=None,
            task_type=task_type,
            tools_used=[],
            tool_payloads=[],
            retrieved_chunks=[],
            judge_summary=None,
            usage_totals=usage_totals,
            started_at=started_at,
        )
        return result

    system_prompt = _load_system_prompt()
    system_prompt += DATE_AWARENESS_RULES
    system_prompt += (
        f"\n\n## TASK ROUTING\n- Current task type: {task_type}\n"
        f"- Use only tools relevant to this task. Allowed tools: {', '.join(route['allowed_tools']) or 'none'}.\n"
        "- If the user asks for unsupported live numbers, say so clearly instead of improvising."
    )
    user_context = _build_user_context(user_profile)
    if user_context:
        system_prompt += user_context
    messages = [{"role": "system", "content": system_prompt}]

    sanitized_history = _sanitize_history(conversation_history)
    history_count = len(sanitized_history)
    if sanitized_history:
        messages.extend(sanitized_history)

    if should_retrieve_knowledge(user_message):
        try:
            retrieved_chunks = retrieve_knowledge(user_message)
        except Exception as exc:
            logger.warning(
                "knowledge_retrieval_failed", trace_id=trace_id, error=str(exc)
            )
            retrieved_chunks = []
        if retrieved_chunks:
            messages.append(
                {"role": "system", "content": _build_retrieval_context(retrieved_chunks)}
            )

    messages.append({"role": "user", "content": user_message})

    try:
        routed_tools = [
            tool
            for tool in SCLODA_TOOLS
            if tool.get("function", {}).get("name") in set(route["allowed_tools"])
        ]
        response = _call_openrouter(
            messages,
            tools=routed_tools,
            primary_model=route["primary_model"],
            fallback_models=route["fallback_models"],
        )
        first_usage = _usage_from_response(response)
        for key in usage_totals:
            usage_totals[key] += first_usage[key]
        model_resolved = response.get("_resolved_model", model_resolved)

        if "error" in response:
            response["trace_id"] = trace_id
            _persist_trace(
                trace_id=trace_id,
                user_message=user_message,
                user_profile=user_profile,
                history_count=history_count,
                screening_reason=screening["reason"],
                guardrail_action=None,
                response_status="error",
                response_text=response.get("response", _FRIENDLY_ERROR),
                error_code=response.get("error"),
                confidence=None,
                model_resolved=model_resolved,
                task_type=task_type,
                tools_used=tools_used,
                tool_payloads=tool_payloads,
                retrieved_chunks=retrieved_chunks,
                judge_summary=None,
                usage_totals=usage_totals,
                started_at=started_at,
            )
            return response

        assistant_message = response["choices"][0]["message"]

        if assistant_message.get("tool_calls"):
            tool_results = []
            for tool_call in assistant_message["tool_calls"]:
                function_name = tool_call["function"]["name"]
                arguments = json.loads(tool_call["function"]["arguments"])
                logger.info("tool_call", tool=function_name, args=arguments)
                result = execute_tool(function_name, arguments)
                tools_used.append(function_name)
                tool_results.append(
                    {
                        "tool_call_id": tool_call["id"],
                        "role": "tool",
                        "content": json.dumps(result, ensure_ascii=False),
                    }
                )

            messages.append(assistant_message)
            messages.extend(tool_results)

            final_response = _call_openrouter(
                messages,
                tools=None,
                primary_model=route["primary_model"],
                fallback_models=route["fallback_models"],
            )
            second_usage = _usage_from_response(final_response)
            for key in usage_totals:
                usage_totals[key] += second_usage[key]
            model_resolved = final_response.get("_resolved_model", model_resolved)

            if "error" in final_response:
                final_response["trace_id"] = trace_id
                _persist_trace(
                    trace_id=trace_id,
                    user_message=user_message,
                    user_profile=user_profile,
                    history_count=history_count,
                    screening_reason=screening["reason"],
                    guardrail_action=None,
                    response_status="error",
                    response_text=final_response.get("response", _FRIENDLY_ERROR),
                    error_code=final_response.get("error"),
                    confidence=None,
                    model_resolved=model_resolved,
                    task_type=task_type,
                    tools_used=tools_used,
                    tool_payloads=tool_payloads,
                    retrieved_chunks=retrieved_chunks,
                    judge_summary=None,
                    usage_totals=usage_totals,
                    started_at=started_at,
                )
                return final_response

            final_content = _extract_message_content(
                final_response["choices"][0]["message"].get("content")
            )
            if not final_content or not final_content.strip():
                final_content = (
                    "I'm sorry, I was able to retrieve the data but had a problem "
                    "processing the final response. Please try asking in a different way."
                )

            tool_payloads = _extract_tool_payloads(tool_results)
            final_content = _apply_response_guardrails(final_content, tool_payloads)
            confidence = _compute_confidence(tool_payloads)
            if _should_run_judge(tool_payloads, retrieved_chunks, confidence):
                judge_summary = _run_judge_review(
                    user_message=user_message,
                    final_response=final_content,
                    tool_payloads=tool_payloads,
                    retrieved_chunks=retrieved_chunks,
                )
                if judge_summary:
                    verdict = judge_summary.get("final_verdict")
                    if verdict == "warn":
                        confidence = "low"
                        final_content += (
                            " I could not fully verify every claim against the "
                            "available evidence, so treat this as contextual guidance."
                        )
                    elif verdict == "review" and confidence == "high":
                        confidence = "medium"

            if confidence == "low" or (judge_summary and judge_summary.get("final_verdict") in {"warn", "review"}):
                create_review_item(
                    trace_id=trace_id,
                    user_id=(user_profile or {}).get("id"),
                    task_type=task_type,
                    reason=(judge_summary or {}).get("final_verdict", "low_confidence"),
                    priority="high" if confidence == "low" else "medium",
                    model_resolved=model_resolved,
                    user_message=user_message,
                    agent_response=final_content,
                )

            result = {
                "response": final_content,
                "tokens_used": usage_totals["total_tokens"],
                "tools_used": tools_used,
                "confidence": confidence,
                "task_type": task_type,
                "trace_id": trace_id,
            }
            _persist_trace(
                trace_id=trace_id,
                user_message=user_message,
                user_profile=user_profile,
                history_count=history_count,
                screening_reason=screening["reason"],
                guardrail_action=None,
                response_status="ok",
                response_text=result["response"],
                error_code=None,
                confidence=result["confidence"],
                model_resolved=model_resolved,
                task_type=task_type,
                tools_used=tools_used,
                tool_payloads=tool_payloads,
                retrieved_chunks=retrieved_chunks,
                judge_summary=judge_summary,
                usage_totals=usage_totals,
                started_at=started_at,
            )
            return result

        content = _extract_message_content(assistant_message.get("content"))
        if not content or not content.strip():
            content = "I'm sorry, I had a problem generating the response. Please try again."
        content = content.strip()
        confidence = "medium"

        if _should_run_judge([], retrieved_chunks, confidence):
            judge_summary = _run_judge_review(
                user_message=user_message,
                final_response=content,
                tool_payloads=[],
                retrieved_chunks=retrieved_chunks,
            )
            if judge_summary:
                verdict = judge_summary.get("final_verdict")
                if verdict == "warn":
                    confidence = "low"
                    content += " I could not fully verify this against the available evidence."

        if confidence == "low" or (judge_summary and judge_summary.get("final_verdict") in {"warn", "review"}):
            create_review_item(
                trace_id=trace_id,
                user_id=(user_profile or {}).get("id"),
                task_type=task_type,
                reason=(judge_summary or {}).get("final_verdict", "low_confidence"),
                priority="high" if confidence == "low" else "medium",
                model_resolved=model_resolved,
                user_message=user_message,
                agent_response=content,
            )

        result = {
            "response": content,
            "tokens_used": usage_totals["total_tokens"],
            "confidence": confidence,
            "task_type": task_type,
            "trace_id": trace_id,
        }
        _persist_trace(
            trace_id=trace_id,
            user_message=user_message,
            user_profile=user_profile,
            history_count=history_count,
            screening_reason=screening["reason"],
            guardrail_action=None,
            response_status="ok",
            response_text=result["response"],
            error_code=None,
            confidence=result["confidence"],
            model_resolved=model_resolved,
            task_type=task_type,
            tools_used=tools_used,
            tool_payloads=tool_payloads,
            retrieved_chunks=retrieved_chunks,
            judge_summary=judge_summary,
            usage_totals=usage_totals,
            started_at=started_at,
        )
        return result

    except httpx.TimeoutException:
        logger.warning("chat_timeout", timeout=LLM_TIMEOUT_SECONDS, trace_id=trace_id)
        result = {
            "response": _FRIENDLY_ERROR,
            "tokens_used": 0,
            "error": "timeout",
            "trace_id": trace_id,
        }
        _persist_trace(
            trace_id=trace_id,
            user_message=user_message,
            user_profile=user_profile,
            history_count=history_count,
            screening_reason=screening["reason"],
            guardrail_action=None,
            response_status="error",
            response_text=result["response"],
            error_code="timeout",
            confidence=None,
            model_resolved=model_resolved,
            task_type=task_type,
            tools_used=tools_used,
            tool_payloads=tool_payloads,
            retrieved_chunks=retrieved_chunks,
            judge_summary=judge_summary,
            usage_totals=usage_totals,
            started_at=started_at,
        )
        return result
    except Exception as e:
        logger.error("chat_error", error=str(e), trace_id=trace_id)
        result = {
            "response": _FRIENDLY_ERROR,
            "tokens_used": 0,
            "error": str(e),
            "trace_id": trace_id,
        }
        _persist_trace(
            trace_id=trace_id,
            user_message=user_message,
            user_profile=user_profile,
            history_count=history_count,
            screening_reason=screening["reason"],
            guardrail_action=None,
            response_status="error",
            response_text=result["response"],
            error_code=str(e),
            confidence=None,
            model_resolved=model_resolved,
            task_type=task_type,
            tools_used=tools_used,
            tool_payloads=tool_payloads,
            retrieved_chunks=retrieved_chunks,
            judge_summary=judge_summary,
            usage_totals=usage_totals,
            started_at=started_at,
        )
        return result


def _call_openrouter(
    messages: list[dict],
    tools: list[dict] | None = None,
    *,
    temperature: float | int | None = None,
    max_tokens: int = 1024,
    primary_model: str | None = None,
    fallback_models: list[str] | None = None,
) -> dict:
    """Make an API call to OpenRouter with a strict fail-fast timeout.

    If the LLM doesn't respond within ``LLM_TIMEOUT_SECONDS`` the
    connection is severed immediately — no retries, no extra cost.
    The caller surfaces a friendly Scloda message so the user can
    press Send again at "human speed".
    """
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": OPENROUTER_HTTP_REFERER,
        "X-Title": OPENROUTER_X_TITLE,
    }

    timeout = httpx.Timeout(LLM_TIMEOUT_SECONDS, connect=5.0)
    last_error: dict[str, Any] | None = None

    try:
        with httpx.Client(timeout=timeout) as client:
            for model_name in _candidate_openrouter_models(primary_model, fallback_models):
                allowed, reason = allow_model(model_name)
                if not allowed:
                    logger.warning("model_circuit_open", model=model_name, reason=reason)
                    last_error = {"error": reason, "response": _FRIENDLY_ERROR}
                    continue

                payload = {
                    "model": model_name,
                    "messages": messages,
                    "temperature": (
                        temperature if temperature is not None else (0.35 if tools else 0.45)
                    ),
                    "max_tokens": max_tokens,
                }

                if tools:
                    payload["tools"] = tools
                    payload["tool_choice"] = "auto"

                try:
                    response = client.post(OPENROUTER_API_URL, headers=headers, json=payload)
                    response.raise_for_status()
                    data = response.json()
                    data["_resolved_model"] = model_name
                    record_model_success(model_name)
                    return data
                except httpx.TimeoutException:
                    last_error = {"error": "timeout", "response": _FRIENDLY_ERROR}
                    record_model_failure(model_name)
                    logger.warning("openrouter_timeout", timeout_s=LLM_TIMEOUT_SECONDS, model=model_name)
                except httpx.HTTPStatusError as e:
                    last_error = {"error": "api_error", "response": _FRIENDLY_ERROR}
                    record_model_failure(model_name)
                    logger.error(
                        "openrouter_http_error",
                        status=e.response.status_code,
                        body=e.response.text[:200],
                        model=model_name,
                    )
                except Exception as e:
                    last_error = {"error": str(e), "response": _FRIENDLY_ERROR}
                    record_model_failure(model_name)
                    logger.error("openrouter_unexpected", error=str(e), model=model_name)
    except Exception as e:
        logger.error("openrouter_client_unexpected", error=str(e))
        return {"error": str(e), "response": _FRIENDLY_ERROR}

    return last_error or {"error": "model_fallbacks_exhausted", "response": _FRIENDLY_ERROR}


def get_service_status() -> dict:
    """Check if the Scloda service is configured correctly."""
    return {
        "api_configured": bool(OPENROUTER_API_KEY),
        "model": OPENROUTER_MODEL,
        "fallback_models": OPENROUTER_FALLBACK_MODELS,
        "embedding_model": SCLODA_EMBEDDING_MODEL,
        "judge_enabled": SCLODA_ENABLE_JUDGE_MODEL,
        "judge_model": SCLODA_JUDGE_MODEL,
        "classifier": get_classifier_status(),
        "review_queue": get_review_summary(),
        "knowledge_index": get_knowledge_index_status(),
        "external_observability": get_external_observability_status(),
        "circuit_breakers": get_circuit_breaker_status(),
        "timestamp": datetime.now().isoformat(),
    }


# Asset context for insight generation
ASSET_CONTEXT = {
    "gold": {
        "name": "Gold",
        "unit": "USD/oz",
        "context": "Safe-haven asset, inversely correlated with risk appetite and USD. Central banks are major buyers.",
    },
    "copper": {
        "name": "Copper",
        "unit": "USD/lb",
        "context": "Chile's main export. Indicator of global industrial demand. China is the largest consumer.",
    },
    "oil": {
        "name": "Oil WTI",
        "unit": "USD/bbl",
        "context": "Energy benchmark. Affects transportation and production costs globally.",
    },
    "btc": {
        "name": "Bitcoin",
        "unit": "CLP",
        "context": "Digital asset, high volatility. Increasingly correlated with tech stocks and risk sentiment.",
    },
    "eth": {
        "name": "Ethereum",
        "unit": "CLP",
        "context": "Smart contract platform. Tracks Bitcoin with higher volatility. DeFi exposure.",
    },
    "cpi": {
        "name": "US CPI",
        "unit": "Index",
        "context": "US inflation measure. Key driver of Fed policy and global interest rates.",
    },
    "yields": {
        "name": "Treasury 10Y",
        "unit": "Yield %",
        "context": "Risk-free rate benchmark. Higher yields pressure emerging market currencies.",
    },
    "usdclp": {
        "name": "USD/CLP",
        "unit": "CLP",
        "context": "Chilean peso exchange rate. Affected by copper prices, Fed policy, and local politics.",
    },
    "uf": {
        "name": "UF",
        "unit": "CLP",
        "context": "Chilean inflation-indexed unit. Used for mortgages, rent, and contracts.",
    },
}


def generate_chart_insight(
    asset: str,
    current_value: float | None = None,
    change_percent: float = 0,
    trend: str = "stable",
) -> dict:
    """
    Generate a dynamic insight for a chart card.

    Args:
        asset: Asset key (e.g., 'gold', 'copper', 'btc')
        current_value: Current price/value
        change_percent: Percentage change
        trend: 'up', 'down', or 'stable'

    Returns:
        dict with 'insight' and 'tokens_used'
    """
    if not OPENROUTER_API_KEY:
        return {"insight": "API not configured.", "tokens_used": 0}

    # Get asset context
    asset_info = ASSET_CONTEXT.get(
        asset.lower(), {"name": asset.upper(), "unit": "", "context": "Financial asset"}
    )

    # Build a focused prompt for short insight generation in ENGLISH
    prompt = f"""Generate a very brief market insight (1-2 sentences) for {asset_info['name']}.

Current data:
- Value: {current_value} {asset_info['unit']} 
- Change: {change_percent:+.2f}%
- Trend: {trend}

Context: {asset_info['context']}

Rules:
- WRITE IN FORMAL FINANCIAL ENGLISH (Bloomberg / Financial Times style).
- Be specific about what the movement implies.
- Maximum 30 words.
- If trend is up, explain bullish implications.
- If trend is down, explain bearish implications.

Respond ONLY with the insight text."""

    try:
        messages = [
            {
                "role": "system",
                "content": "You are Scloda, a senior financial analyst. Your language is 100% formal, elegant, and technical.",
            },
            {"role": "user", "content": prompt},
        ]

        response = _call_openrouter(messages, tools=None)

        if "error" in response:
            # Fallback to static insight
            return _get_fallback_insight(asset, change_percent, trend)

        return {
            "insight": _extract_message_content(
                response["choices"][0]["message"].get("content")
            ).strip(),
            "tokens_used": response["usage"]["total_tokens"],
        }

    except Exception as e:
        logger.error("insight_generation_error", error=str(e))
        return _get_fallback_insight(asset, change_percent, trend)


def _get_fallback_insight(asset: str, change_percent: float, trend: str) -> dict:
    """Return a static fallback insight if LLM fails."""
    fallbacks = {
        "gold": "Gold maintains its role as a safe-haven asset amid global uncertainty.",
        "copper": "Copper demand remains a key indicator of global industrial activity.",
        "oil": "Crude prices reflect ongoing tensions in the global energy supply chain.",
        "btc": "Bitcoin continues to demonstrate high volatility correlated with risk assets.",
        "eth": "Ethereum consolidates its position as core infrastructure for decentralized finance.",
        "cpi": "Persistent inflation pressures the Federal Reserve to maintain elevated rates.",
        "yields": "Treasury yields directly impact the cost of credit globally.",
        "usdclp": "Peso barometer. Sensitive to copper prices and Fed rate decisions.",
        "uf": "Inflation-indexed unit. Benchmark for mortgages and contracts in Chile.",
    }

    base = fallbacks.get(asset.lower(), "Financial market indicator.")
    direction = "📈" if trend == "up" else "📉" if trend == "down" else "➡️"

    return {"insight": f"{direction} {base}", "tokens_used": 0}


def generate_model_analysis(asset: str, model_name: str, metrics: dict) -> dict:
    """
    Generate a detailed analysis of why a specific ML model was selected for an asset.

    Args:
        asset: Asset name (e.g., 'Gold')
        model_name: Selected model (e.g., 'Auto ARIMA')
        metrics: Dictionary with mae, rmse, mape

    Returns:
        dict with 'selection_reason' and 'confidence_note'
    """
    if not OPENROUTER_API_KEY:
        return _get_fallback_model_analysis(asset, model_name)

    mape = metrics.get("mape", 0)

    prompt = f"""Analyze the ML model performance for {asset}.

Data:
- Winning model: {model_name}
- Percentage error (MAPE): {mape:.2f}%

Generate 2 brief texts in FORMAL FINANCIAL ENGLISH:
1. "selection_reason": Why does this model work best for this type of asset? (Max 25 words)
2. "confidence_note": Interpret how reliable a MAPE of {mape:.2f}% is for this asset. (Max 20 words)

Rules:
- SERIOUS AND PROFESSIONAL TONE.
- Use correct technical terminology (intrinsic volatility, stochastic, etc.).

Technical context:
- ARIMA/AutoARIMA: Good for clear trends.
- Theta: Good for volatility and smoothing.
- ETS: Good for seasonality.
- Naive: Good for random walks.

Respond ONLY in JSON format:
{{
  "selection_reason": "...",
  "confidence_note": "..."
}}"""

    try:
        messages = [
            {
                "role": "system",
                "content": "You are Scloda, Senior Data Scientist. Respond in valid JSON with formal language.",
            },
            {"role": "user", "content": prompt},
        ]

        response = _call_openrouter(messages, tools=None)

        if "error" in response:
            return _get_fallback_model_analysis(asset, model_name)

        content = _extract_message_content(
            response["choices"][0]["message"].get("content")
        ).strip()

        # Clean markdown code blocks if present
        if content.startswith("```json"):
            content = content.replace("```json", "").replace("```", "")

        import json

        result = json.loads(content)

        return {
            "selection_reason": result.get("selection_reason", ""),
            "confidence_note": result.get("confidence_note", ""),
            "tokens_used": response.get("usage", {}).get("total_tokens", 0),
        }

    except Exception as e:
        logger.error("model_analysis_error", error=str(e))
        return _get_fallback_model_analysis(asset, model_name)


def _get_fallback_model_analysis(asset: str, model_name: str) -> dict:
    """Return static fallback analysis in English."""
    return {
        "selection_reason": f"{model_name} best adapted to the historical patterns and volatility of {asset}.",
        "confidence_note": "The error falls within acceptable ranges for this type of financial asset.",
        "tokens_used": 0,
    }
