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
    return """Eres Scloda, un experto multidisciplinario en finanzas, tecnología y análisis de datos.

Tienes expertise en: Data Science, FinOps, Software Engineering, Inversiones, y Economía Macro/Micro.

REGLAS:
1. Usa lenguaje simple pero preciso
2. Da ejemplos prácticos
3. Conecta datos con correlaciones
4. Advierte sobre riesgos claramente
5. Siempre: "Esto es informativo, NO asesoría financiera"

Responde en el idioma del usuario. Usa las herramientas para obtener datos reales."""

# System prompt for Scloda
SYSTEM_PROMPT = """Eres Scloda, un experto multidisciplinario en finanzas, tecnología y análisis de datos.

## TU PERFIL PROFESIONAL

**Data Scientist & ML Engineer:**
- Experto en series de tiempo (ARIMA, Theta, ETS, Prophet)
- Entiendes métricas de error (MAE, RMSE, MAPE) y sabes explicarlas en términos simples
- Puedes interpretar resultados de modelos y explicar su confiabilidad

**FinOps & Finance Expert:**
- Conoces productos financieros chilenos: créditos hipotecarios, CAE, seguros, AFPs
- Entiendes la UF, IPC, y cómo afectan a las personas comunes
- Sabes analizar costos bancarios y encontrar las mejores opciones

**Software Engineer:**
- Entiendes APIs, datos en tiempo real, y cómo funcionan las integraciones
- Puedes explicar conceptos técnicos de forma accesible

**Businessman & Investor:**
- Conoces estrategias de inversión: diversificación, riesgo/retorno, horizontes de tiempo
- Entiendes correlaciones entre activos (oro vs dólar, cobre vs peso chileno)
- Sabes cuándo un activo es refugio seguro y cuándo es especulativo

**Economista Macro & Micro:**
- Entiendes cómo las tasas de la Fed afectan a Chile
- Conoces el impacto del cobre en la economía chilena
- Sabes explicar inflación, política monetaria, y ciclos económicos

## TU PERSONALIDAD

- Cercano y profesional, como un mentor que sabe de finanzas
- Usas español neutro latinoamericano, accesible para todos
- Eres optimista pero SIEMPRE adviertes sobre los riesgos
- Explicas conceptos complejos con analogías cotidianas

## REGLAS DE COMUNICACIÓN

1. **Simplifica sin perder precisión** - Usa lenguaje cotidiano pero correcto
2. **Da ejemplos prácticos** - "Si la UF sube 1%, tu dividendo sube $5.000 aprox"
3. **Conecta los datos** - Explica correlaciones ("El dólar baja porque el cobre subió")
4. **Contextualiza siempre** - "Esto es alto/bajo/normal comparado con..."
5. **Advierte riesgos** - Si algo es volátil o especulativo, dilo claramente
6. **Disclaimer siempre** - Los datos son informativos, NO asesoría financiera

## SOBRE LOS MODELOS ML

Cuando expliques modelos, usa este framework:
- **MAPE < 2%**: "El modelo tiene alta precisión, muy confiable para este activo"
- **MAPE 2-5%**: "Predicciones útiles, pero considera un margen de ±X%"
- **MAPE > 5%**: "Activo muy volátil. Las predicciones son orientativas, no apuestas"

Explica cada modelo así:
- **ARIMA**: "Mira patrones pasados para predecir el futuro"
- **Theta**: "Suaviza la volatilidad para encontrar la tendencia real"
- **ETS**: "Detecta temporadas y ciclos repetitivos"
- **Naive**: "Asume que mañana será igual a hoy (sorprendentemente útil para algunos activos)"

## DATOS DISPONIBLES

Usa las herramientas para consultar:
- UF y USD/CLP (Banco Central de Chile)
- Oro, Cobre, Petróleo, Plata (commodities globales)
- Bitcoin, Ethereum (criptomonedas)
- CPI USA, Treasury 10Y (indicadores globales)
- Información de modelos ML y sus métricas

## IMPORTANTE

- Si no tienes datos actualizados, dilo honestamente
- NUNCA inventes números o estadísticas
- Si la pregunta está fuera de tu conocimiento, recomienda consultar un profesional
- Responde en el idioma que use el usuario (español o inglés)

Responde de forma concisa pero completa. Usa emojis con moderación (📊💡⚠️) para hacer la conversación más amigable."""


def chat_completion(
    user_message: str,
    conversation_history: list[dict] | None = None
) -> dict[str, Any]:
    """
    Process a chat message and return Scloda's response.
    
    Args:
        user_message: The user's message
        conversation_history: Previous messages in the conversation
        
    Returns:
        dict with 'response' (text) and 'tokens_used'
    """
    if not OPENROUTER_API_KEY:
        return {
            "response": "⚠️ API no configurada. Agrega OPENROUTER_API_KEY al archivo .env",
            "tokens_used": 0,
            "error": "no_api_key"
        }
    
    # Build messages - load prompt from file
    system_prompt = _load_system_prompt()
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
                tool_results.append({
                    "tool_call_id": tool_call["id"],
                    "role": "tool",
                    "content": json.dumps(result, ensure_ascii=False)
                })
            
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
                "tools_used": [tc["function"]["name"] for tc in assistant_message["tool_calls"]]
            }
        
        # No tool calls, return direct response
        return {
            "response": assistant_message.get("content", ""),
            "tokens_used": tokens_used
        }
        
    except Exception as e:
        logger.error("chat_error", error=str(e))
        return {
            "response": f"😅 Ups, tuve un problema técnico. Intenta de nuevo en un momento.",
            "tokens_used": 0,
            "error": str(e)
        }


def _call_openrouter(messages: list[dict], tools: list[dict] | None = None) -> dict:
    """Make an API call to OpenRouter."""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://costbench.cl",
        "X-Title": "CostBench - Scloda Chat"
    }
    
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1024
    }
    
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                OPENROUTER_API_URL,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
            
    except httpx.TimeoutException:
        return {"error": "timeout", "response": "La consulta tardó demasiado. Intenta de nuevo."}
    except httpx.HTTPStatusError as e:
        logger.error("openrouter_error", status=e.response.status_code, body=e.response.text)
        return {"error": "api_error", "response": f"Error de API: {e.response.status_code}"}
    except Exception as e:
        return {"error": str(e)}


def get_service_status() -> dict:
    """Check if the Scloda service is configured correctly."""
    return {
        "api_configured": bool(OPENROUTER_API_KEY),
        "model": OPENROUTER_MODEL,
        "timestamp": datetime.now().isoformat()
    }


# Asset context for insight generation
ASSET_CONTEXT = {
    "gold": {
        "name": "Oro",
        "unit": "USD/oz",
        "context": "Safe-haven asset, inversely correlated with risk appetite and USD. Central banks are major buyers."
    },
    "copper": {
        "name": "Cobre",
        "unit": "USD/lb",
        "context": "Chile's main export. Indicator of global industrial demand. China is the largest consumer."
    },
    "oil": {
        "name": "Petróleo WTI",
        "unit": "USD/bbl",
        "context": "Energy benchmark. Affects transportation and production costs globally."
    },
    "btc": {
        "name": "Bitcoin",
        "unit": "CLP",
        "context": "Digital asset, high volatility. Increasingly correlated with tech stocks and risk sentiment."
    },
    "eth": {
        "name": "Ethereum",
        "unit": "CLP",
        "context": "Smart contract platform. Tracks Bitcoin with higher volatility. DeFi exposure."
    },
    "cpi": {
        "name": "CPI USA",
        "unit": "Index",
        "context": "US inflation measure. Key driver of Fed policy and global interest rates."
    },
    "yields": {
        "name": "Treasury 10Y",
        "unit": "Yield %",
        "context": "Risk-free rate benchmark. Higher yields pressure emerging market currencies."
    },
    "usdclp": {
        "name": "USD/CLP",
        "unit": "CLP",
        "context": "Chilean peso exchange rate. Affected by copper prices, Fed policy, and local politics."
    },
    "uf": {
        "name": "UF",
        "unit": "CLP",
        "context": "Chilean inflation-indexed unit. Used for mortgages, rent, and contracts."
    }
}


def generate_chart_insight(
    asset: str,
    current_value: float | None = None,
    change_percent: float = 0,
    trend: str = "stable"
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
        return {
            "insight": "API not configured.",
            "tokens_used": 0
        }
    
    # Get asset context
    asset_info = ASSET_CONTEXT.get(asset.lower(), {
        "name": asset.upper(),
        "unit": "",
        "context": "Financial asset"
    })
    
    # Build a focused prompt for short insight generation in SPANISH
    prompt = f"""Genera un insight de mercado muy breve (1-2 frases) para {asset_info['name']}.

Datos actuales:
- Valor: {current_value} {asset_info['unit']} 
- Cambio: {change_percent:+.2f}%
- Tendencia: {trend}

Contexto: {asset_info['context']}

Reglas:
- ESCRIBE EN ESPAÑOL FINANCIERO FORMAL Y ELEGANTE.
- PROHIBIDO USAR JERGA TIPO: "cachai", "al tiro", "fome", "bacan", "filete", "compipa".
- Usa un tono profesional, técnico y serio (Estilo "Diario Financiero" o "Bloomberg").
- Sé específico sobre qué significa el movimiento.
- Máximo 30 palabras.
- Si la tendencia es alza, explica implicancias alcistas (bullish).
- Si la tendencia es baja, explica implicancias bajistas (bearish).

Responde SOLO con el texto del insight."""

    try:
        messages = [
            {"role": "system", "content": "Eres Scloda, un analista financiero senior experto. Tu lenguaje es 100% formal, elegante y técnico."},
            {"role": "user", "content": prompt}
        ]
        
        response = _call_openrouter(messages, tools=None)
        
        if "error" in response:
            # Fallback to static insight
            return _get_fallback_insight(asset, change_percent, trend)
        
        return {
            "insight": response["choices"][0]["message"]["content"].strip(),
            "tokens_used": response["usage"]["total_tokens"]
        }
        
    except Exception as e:
        logger.error("insight_generation_error", error=str(e))
        return _get_fallback_insight(asset, change_percent, trend)


def _get_fallback_insight(asset: str, change_percent: float, trend: str) -> dict:
    """Return a static fallback insight if LLM fails (IN SPANISH)."""
    fallbacks = {
        "gold": "El oro mantiene su rol como activo refugio ante la incertidumbre global.",
        "copper": "La demanda de cobre sigue siendo un indicador clave de la actividad industrial.",
        "oil": "El precio del crudo refleja las tensiones en la cadena de suministro energética.",
        "btc": "Bitcoin continúa demostrando alta volatilidad correlacionada con activos de riesgo.",
        "eth": "Ethereum consolida su posición como infraestructura clave para finanzas descentralizadas.",
        "cpi": "La inflación persistente presiona a la Reserva Federal a mantener tasas altas.",
        "yields": "El rendimiento de los bonos del Tesoro impacta el costo del crédito global.",
        "usdclp": "Termómetro del peso. Sensible al precio del cobre y tasas Fed.",
        "uf": "Unidad indexada a la inflación. Referencia para créditos y arriendos."
    }
    
    base = fallbacks.get(asset.lower(), "Indicador de mercado financiero.")
    direction = "📈" if trend == "up" else "📉" if trend == "down" else "➡️"
    
    return {
        "insight": f"{direction} {base}",
        "tokens_used": 0
    }


def generate_model_analysis(
    asset: str,
    model_name: str,
    metrics: dict
) -> dict:
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
    
    mape = metrics.get('mape', 0)
    
    prompt = f"""Analiza el rendimiento del modelo ML para {asset}.

Datos:
- Modelo ganador: {model_name}
- Error porcentual (MAPE): {mape:.2f}%

Genera 2 textos breves en ESPAÑOL FINANCIERO FORMAL:
1. "selection_reason": ¿Por qué este modelo funciona mejor para este tipo de activo? (Max 25 palabras)
2. "confidence_note": Interpreta qué tan confiable es el MAPE de {mape:.2f}% para este activo. (Max 20 palabras)

Reglas:
- TONO SERIO Y PROFESIONAL.
- PROHIBIDO USAR JERGA (slang).
- Usa terminología técnica correcta (volatilidad intrínseca, estocástico, etc.).

Contexto técnico:
- ARIMA/AutoARIMA: Bueno para tendencias claras.
- Theta: Bueno para volatilidad y suavizado.
- ETS: Bueno para estacionalidad.
- Naive: Bueno para caminatas aleatorias (random walks).

Responde SOLO en formato JSON:
{{
  "selection_reason": "...",
  "confidence_note": "..."
}}"""

    try:
        messages = [
            {"role": "system", "content": "Eres Scloda, Data Scientist Senior. Responde en JSON válido con lenguaje formal."},
            {"role": "user", "content": prompt}
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
            "tokens_used": response.get("usage", {}).get("total_tokens", 0)
        }
        
    except Exception as e:
        logger.error("model_analysis_error", error=str(e))
        return _get_fallback_model_analysis(asset, model_name)


def _get_fallback_model_analysis(asset: str, model_name: str) -> dict:
    """Return static fallback analysis in Spanish."""
    return {
        "selection_reason": f"{model_name} se adaptó mejor a los patrones históricos y la volatilidad de {asset}.",
        "confidence_note": "El error está dentro de rangos aceptables para este tipo de activo financiero.",
        "tokens_used": 0
    }
