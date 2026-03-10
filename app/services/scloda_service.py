"""
Scloda Chat Service - OpenRouter/Gemini integration for AI chat.

Handles:
- OpenRouter API calls with Gemini 2.0 Flash
- Function calling (tool use) for market data queries
- Conversation context management
"""

import os
import json
import httpx
from typing import Any
from datetime import datetime
from pathlib import Path

from app.services.scloda_tools import SCLODA_TOOLS, execute_tool
from app.ml.logging_utils import get_logger

logger = get_logger("scloda.service")

# Configuration
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-001")

# ── Fail-Fast config ──────────────────────────────────────────
# Strict timeout — if the LLM doesn't answer in this window we
# cut the connection and let the *user* decide whether to retry.
LLM_TIMEOUT_SECONDS = int(os.getenv("SCLODA_TIMEOUT", "12"))

# Pre-baked Scloda message shown on any LLM failure.
_FRIENDLY_ERROR = (
    "⏳ Las redes están un poco saturadas en este momento y no pude "
    "procesar tu consulta. ¿Puedes intentarlo de nuevo en unos segundos?"
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

Remember: Always use the available tools to get real data. Never invent numbers. Respond in the user's language."""
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

Respond in the user's language. Use the available tools to get real data."""


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
- US CPI, Treasury 10Y (global indicators)
- ML model information (ARIMA, etc)
- **Markov Predictions**: Use `get_markov_predictions` when someone asks "What predicts X?" or "What is likely to happen next based on today's movement?"

## IMPORTANT

- If you don't have updated data, say so honestly
- NEVER make up numbers or statistics
- If the question is outside your knowledge, recommend consulting a professional
- Respond in the language the user uses (Spanish or English)

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
    if not OPENROUTER_API_KEY:
        return {
            "response": "⚠️ API no configurada. Agrega OPENROUTER_API_KEY al archivo .env",
            "tokens_used": 0,
            "error": "no_api_key",
        }

    # Build messages — base prompt + dynamic user context
    system_prompt = _load_system_prompt()
    user_context = _build_user_context(user_profile)
    if user_context:
        system_prompt += user_context
    messages = [{"role": "system", "content": system_prompt}]

    # Add conversation history (last 10 messages max)
    if conversation_history:
        messages.extend(conversation_history[-10:])

    # Add current user message
    messages.append({"role": "user", "content": user_message})

    try:
        # First API call
        response = _call_openrouter(messages, tools=SCLODA_TOOLS)

        if "error" in response:
            return response

        assistant_message = response["choices"][0]["message"]
        tokens_used = response.get("usage", {}).get("total_tokens", 0)

        # Check for tool calls
        if assistant_message.get("tool_calls"):
            # Execute tools and get results
            tool_results = []
            for tool_call in assistant_message["tool_calls"]:
                function_name = tool_call["function"]["name"]
                arguments = json.loads(tool_call["function"]["arguments"])

                logger.info("tool_call", tool=function_name, args=arguments)

                result = execute_tool(function_name, arguments)
                tool_results.append(
                    {
                        "tool_call_id": tool_call["id"],
                        "role": "tool",
                        "content": json.dumps(result, ensure_ascii=False),
                    }
                )

            # Add assistant message with tool calls
            messages.append(assistant_message)

            # Add tool results
            messages.extend(tool_results)

            # Second API call with tool results
            final_response = _call_openrouter(messages, tools=None)

            if "error" in final_response:
                return final_response

            final_content = final_response["choices"][0]["message"]["content"]
            tokens_used += final_response.get("usage", {}).get("total_tokens", 0)

            return {
                "response": final_content,
                "tokens_used": tokens_used,
                "tools_used": [
                    tc["function"]["name"] for tc in assistant_message["tool_calls"]
                ],
            }

        # No tool calls, return direct response
        return {
            "response": assistant_message.get("content", ""),
            "tokens_used": tokens_used,
        }

    except httpx.TimeoutException:
        logger.warning("chat_timeout", timeout=LLM_TIMEOUT_SECONDS)
        return {"response": _FRIENDLY_ERROR, "tokens_used": 0, "error": "timeout"}
    except Exception as e:
        logger.error("chat_error", error=str(e))
        return {"response": _FRIENDLY_ERROR, "tokens_used": 0, "error": str(e)}


def _call_openrouter(messages: list[dict], tools: list[dict] | None = None) -> dict:
    """Make an API call to OpenRouter with a strict fail-fast timeout.

    If the LLM doesn't respond within ``LLM_TIMEOUT_SECONDS`` the
    connection is severed immediately — no retries, no extra cost.
    The caller surfaces a friendly Scloda message so the user can
    press Send again at "human speed".
    """
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://costbench.cl",
        "X-Title": "CostBench - Scloda Chat",
    }

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1024,
    }

    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

    # Strict timeout — fail fast, let the user retry.
    timeout = httpx.Timeout(LLM_TIMEOUT_SECONDS, connect=5.0)

    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(OPENROUTER_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()

    except httpx.TimeoutException:
        logger.warning("openrouter_timeout", timeout_s=LLM_TIMEOUT_SECONDS)
        return {"error": "timeout", "response": _FRIENDLY_ERROR}
    except httpx.HTTPStatusError as e:
        logger.error(
            "openrouter_http_error",
            status=e.response.status_code,
            body=e.response.text[:200],
        )
        return {"error": "api_error", "response": _FRIENDLY_ERROR}
    except Exception as e:
        logger.error("openrouter_unexpected", error=str(e))
        return {"error": str(e), "response": _FRIENDLY_ERROR}


def get_service_status() -> dict:
    """Check if the Scloda service is configured correctly."""
    return {
        "api_configured": bool(OPENROUTER_API_KEY),
        "model": OPENROUTER_MODEL,
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
            "insight": response["choices"][0]["message"]["content"].strip(),
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

        content = response["choices"][0]["message"]["content"].strip()

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
