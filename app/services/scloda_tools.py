"""
Scloda Tools - Function calling tools for market data queries.

These tools are exposed to the LLM via OpenRouter's function calling mechanism.
Each tool queries internal APIs and returns structured data for Scloda to explain.
"""

from datetime import date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from app.services.scloda_circuit_breakers import (
    allow_tool,
    record_tool_failure,
    record_tool_success,
)

MARKET_TIMEZONE = ZoneInfo("America/Santiago")

MAX_LOOKBACK_DAYS = 3650
FALLBACK_EXPLANATIONS = {
    "UF": "UF is Chile's inflation-linked unit used in mortgages, rents, and long-term contracts.",
    "USD/CLP": "USD/CLP reflects the Chilean peso exchange rate and is often shaped by copper, Fed rates, and local risk sentiment.",
    "Gold (USD/oz)": "Gold is commonly treated as a defensive asset and a barometer of inflation or geopolitical stress.",
    "Copper (USD/lb)": "Copper is one of Chile's most important macro signals because it links directly to export revenues and global industrial demand.",
    "Oil WTI (USD/bbl)": "Oil prices influence transport, inflation, and imported energy costs across the economy.",
    "Silver (USD/oz)": "Silver combines precious-metal behavior with industrial demand exposure, so it can move with both risk and manufacturing cycles.",
    "BTC": "Bitcoin is a high-volatility digital asset whose price is often influenced by global liquidity and risk appetite.",
    "ETH": "Ethereum combines crypto market beta with smart-contract ecosystem exposure, making it highly volatile and narrative-sensitive.",
}

TOOL_VALIDATORS = {
    "get_uf_data": {"days": {"type": int, "min": 1, "max": MAX_LOOKBACK_DAYS}},
    "get_usdclp_data": {"days": {"type": int, "min": 1, "max": MAX_LOOKBACK_DAYS}},
    "get_commodity_data": {
        "commodity": {"type": str, "enum": {"gold", "copper", "oil", "silver"}},
        "days": {"type": int, "min": 1, "max": MAX_LOOKBACK_DAYS},
    },
    "get_crypto_data": {"crypto": {"type": str, "enum": {"btc", "eth"}}},
    "get_model_info": {
        "asset": {"type": str, "enum": {"GOLD", "COPPER", "OIL", "USDCLP", "UF", "BTC", "ETH"}},
    },
    "get_markov_predictions": {"target": {"type": str, "max_length": 32}},
    "explain_indicator": {
        "indicator": {
            "type": str,
            "enum": {"uf", "usdclp", "gold", "copper", "oil", "cpi", "treasury_10y", "btc", "eth"},
        }
    },
}


def _market_now() -> datetime:
    """Return current datetime in Chile's market timezone."""
    return datetime.now(MARKET_TIMEZONE)


def _normalize_tool_date(value: Any) -> date:
    """Normalize pandas/datetime/string values to a market date."""
    if hasattr(value, "to_pydatetime"):
        value = value.to_pydatetime()
    if isinstance(value, datetime):
        return value.date()

    raw = str(value).split(" ")[0]
    try:
        return datetime.fromisoformat(raw).date()
    except ValueError:
        return _market_now().date()


def _with_market_date_context(payload: dict[str, Any], value: Any) -> dict[str, Any]:
    """Attach explicit date context so the LLM can avoid ambiguous date phrasing."""
    as_of_date = _normalize_tool_date(value)
    market_today = _market_now().date()
    freshness = "live" if as_of_date == market_today else "delayed"
    payload.update(
        {
            "current_date": as_of_date.isoformat(),
            "as_of_label": f"{as_of_date.strftime('%B')} {as_of_date.day}, {as_of_date.year}",
            "market_today": market_today.isoformat(),
            "market_timezone": "America/Santiago",
            "is_current_for_market_day": as_of_date == market_today,
            "freshness": freshness,
        }
    )
    return payload


def _build_no_live_data_payload(
    *,
    label: str,
    source: str,
    fallback_context: str,
    error_message: str | None = None,
) -> dict[str, Any]:
    """Standardized payload when live data is unavailable but contextual help is still possible."""
    return {
        "status": "no_live_data",
        "error": error_message or "No live data available",
        "indicator": label,
        "source": source,
        "fallback_context": fallback_context,
        "market_today": _market_now().date().isoformat(),
        "market_timezone": "America/Santiago",
        "historical_guidance_allowed": True,
        "response_instruction": (
            "State clearly that current live data is unavailable. "
            "You may still explain the indicator using historical behavior or domain context, "
            "but do not invent a current quote."
        ),
    }


def _coerce_int(value: Any) -> int:
    if isinstance(value, bool):
        raise ValueError("Boolean is not valid here")
    return int(value)


def validate_tool_request(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize model-provided tool arguments."""
    if not isinstance(arguments, dict):
        raise ValueError("Tool arguments must be a JSON object")

    spec = TOOL_VALIDATORS.get(tool_name)
    if not spec:
        return arguments

    normalized = dict(arguments)
    for field, rules in spec.items():
        if field not in normalized:
            continue

        value = normalized[field]
        expected_type = rules.get("type")
        if expected_type is int:
            value = _coerce_int(value)
        elif expected_type is str:
            value = str(value).strip()

        enum_values = rules.get("enum")
        if enum_values is not None:
            compare_value = value.upper() if field == "asset" else value.lower()
            compare_set = {item.upper() if field == "asset" else item.lower() for item in enum_values}
            if compare_value not in compare_set:
                raise ValueError(f"Invalid value for {field}: {value}")
            if field != "asset":
                value = value.lower()
            else:
                value = value.upper()

        if isinstance(value, int):
            if "min" in rules and value < rules["min"]:
                raise ValueError(f"{field} must be >= {rules['min']}")
            if "max" in rules and value > rules["max"]:
                raise ValueError(f"{field} must be <= {rules['max']}")

        if isinstance(value, str) and "max_length" in rules and len(value) > rules["max_length"]:
            raise ValueError(f"{field} too long")

        normalized[field] = value

    return normalized

# Tool definitions for OpenRouter function calling
SCLODA_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_uf_data",
            "description": "Obtiene el valor actual e histórico de la UF (Unidad de Fomento) desde el Banco Central de Chile. La UF es una unidad de cuenta indexada a la inflación, usada para créditos hipotecarios y arriendos.",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Cantidad de días hacia atrás para obtener historial. Default: 30",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_usdclp_data",
            "description": "Obtiene el tipo de cambio USD/CLP (dólar observado) desde el Banco Central de Chile.",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Cantidad de días hacia atrás para obtener historial. Default: 30",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_commodity_data",
            "description": "Obtiene datos de commodities: oro (gold), cobre (copper), petróleo (oil), plata (silver).",
            "parameters": {
                "type": "object",
                "properties": {
                    "commodity": {
                        "type": "string",
                        "enum": ["gold", "copper", "oil", "silver"],
                        "description": "El commodity a consultar",
                    },
                    "days": {
                        "type": "integer",
                        "description": "Cantidad de días de historial. Default: 30",
                    },
                },
                "required": ["commodity"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_crypto_data",
            "description": "Obtiene datos de criptomonedas: Bitcoin (BTC) o Ethereum (ETH) en pesos chilenos.",
            "parameters": {
                "type": "object",
                "properties": {
                    "crypto": {
                        "type": "string",
                        "enum": ["btc", "eth"],
                        "description": "La criptomoneda a consultar",
                    }
                },
                "required": ["crypto"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_model_info",
            "description": "Obtiene información sobre el modelo de Machine Learning usado para predecir un activo específico. Incluye métricas de precisión (MAE, RMSE, MAPE) y el tipo de modelo (ARIMA, Theta, ETS, etc.).",
            "parameters": {
                "type": "object",
                "properties": {
                    "asset": {
                        "type": "string",
                        "enum": ["GOLD", "COPPER", "OIL", "USDCLP", "UF", "BTC", "ETH"],
                        "description": "El activo del cual obtener info del modelo",
                    }
                },
                "required": ["asset"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_market_summary",
            "description": "Obtiene un resumen completo del mercado: UF, dólar, oro, cobre, petróleo, Bitcoin. Útil para dar un panorama general.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_markov_predictions",
            "description": "Obtiene las probabilidades estadísticas actuales del mercado mediante la Cadena de Markov calculada. Entrega una matriz empírica que dice, por ejemplo, si el Cobre bajó ayer, cuál es la probabilidad real de que el Dólar o el IPSA suban hoy.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "Opcional. El activo que queremos predecir (ej. 'USD-CLP', 'HG=F'). Si no se indica, devuelve las matrices más significativas.",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "explain_indicator",
            "description": "Explica qué es un indicador financiero y cómo afecta a la economía chilena.",
            "parameters": {
                "type": "object",
                "properties": {
                    "indicator": {
                        "type": "string",
                        "enum": [
                            "uf",
                            "usdclp",
                            "gold",
                            "copper",
                            "oil",
                            "cpi",
                            "treasury_10y",
                            "btc",
                            "eth",
                        ],
                        "description": "El indicador a explicar",
                    }
                },
                "required": ["indicator"],
            },
        },
    },
]

# Indicator explanations (static knowledge)
INDICATOR_EXPLANATIONS = {
    "uf": {
        "name": "UF (Unidad de Fomento)",
        "what": "Es una unidad de cuenta que se ajusta diariamente según la inflación en Chile.",
        "use": "Se usa para créditos hipotecarios, arriendos y algunos contratos para proteger el valor del dinero.",
        "impact": "Cuando la inflación sube, la UF sube. Si tienes un crédito en UF, tu dividendo aumenta.",
        "tip": "Si la UF sube muy rápido, significa que hay inflación alta en Chile.",
    },
    "usdclp": {
        "name": "Dólar Observado (USD/CLP)",
        "what": "Es el precio del dólar estadounidense en pesos chilenos.",
        "use": "Afecta el precio de todo lo importado: tecnología, autos, combustibles.",
        "impact": "Dólar alto = importaciones más caras, pero exportaciones más competitivas.",
        "tip": "El cobre y el dólar suelen moverse en direcciones opuestas.",
    },
    "gold": {
        "name": "Oro",
        "what": "Metal precioso considerado 'refugio seguro' en tiempos de incertidumbre.",
        "use": "Los inversionistas compran oro cuando hay miedo en los mercados.",
        "impact": "Sube cuando hay crisis o inflación alta. Baja cuando hay confianza económica.",
        "tip": "Si el oro sube mucho, puede indicar que los mercados están nerviosos.",
    },
    "copper": {
        "name": "Cobre",
        "what": "Chile es el mayor productor mundial. Se usa en construcción, electrónica y energía verde.",
        "use": "Es un indicador de la salud económica global (le dicen 'Dr. Copper').",
        "impact": "Cobre alto = más dólares entran a Chile = peso más fuerte. Cobre bajo = peso se debilita.",
        "tip": "El precio del cobre depende mucho de la economía de China.",
    },
    "oil": {
        "name": "Petróleo (WTI)",
        "what": "El petróleo West Texas Intermediate es la referencia para el precio del crudo en América.",
        "use": "Determina el precio de la bencina y muchos productos derivados.",
        "impact": "Petróleo alto = inflación por combustibles. Afecta el costo de transporte y producción.",
        "tip": "Los conflictos en Medio Oriente suelen hacer subir el petróleo.",
    },
    "cpi": {
        "name": "CPI USA (Inflación EEUU)",
        "what": "Índice de Precios al Consumidor de Estados Unidos. Mide la inflación gringa.",
        "use": "La Fed usa este dato para decidir si sube o baja las tasas de interés.",
        "impact": "CPI alto = la Fed sube tasas = dólar se fortalece = afecta a Chile.",
        "tip": "Es uno de los datos más importantes para los mercados globales.",
    },
    "treasury_10y": {
        "name": "Bono del Tesoro 10 años",
        "what": "Tasa de interés que paga el gobierno de EEUU por préstamos a 10 años.",
        "use": "Es la 'tasa libre de riesgo' de referencia mundial.",
        "impact": "Tasas altas atraen dinero a EEUU, presionando monedas emergentes como el peso chileno.",
        "tip": "Cuando esta tasa sube mucho, los mercados emergentes sufren.",
    },
    "btc": {
        "name": "Bitcoin",
        "what": "Primera y más conocida criptomoneda. Suministro limitado a 21 millones de unidades.",
        "use": "Algunos lo ven como 'oro digital', otros como inversión especulativa.",
        "impact": "Muy volátil. Puede subir o bajar 10% en un día.",
        "tip": "No inviertas dinero que no puedas perder. Es de alto riesgo.",
    },
    "eth": {
        "name": "Ethereum",
        "what": "Plataforma de contratos inteligentes. Segunda cripto más grande después de Bitcoin.",
        "use": "Base de aplicaciones DeFi (finanzas descentralizadas) y NFTs.",
        "impact": "Tiende a moverse con Bitcoin pero con mayor volatilidad.",
        "tip": "Es más que una moneda: es una plataforma tecnológica.",
    },
}


def execute_tool(tool_name: str, arguments: dict) -> dict[str, Any]:
    """
    Execute a tool and return its result.
    This is called by the chat service when the LLM requests a function call.
    """
    try:
        allowed, reason = allow_tool(tool_name)
        if not allowed:
            return {
                "error": "Tool temporarily unavailable after repeated failures",
                "tool": tool_name,
                "status": "circuit_open",
                "response_instruction": "Explain that this live data source is temporarily unavailable and provide only non-numeric contextual guidance if relevant.",
                "circuit_reason": reason,
            }

        arguments = validate_tool_request(tool_name, arguments or {})
        if tool_name == "get_uf_data":
            result = _get_uf_data(arguments.get("days", 30))
        elif tool_name == "get_usdclp_data":
            result = _get_usdclp_data(arguments.get("days", 30))
        elif tool_name == "get_commodity_data":
            result = _get_commodity_data(
                arguments["commodity"], arguments.get("days", 30)
            )
        elif tool_name == "get_crypto_data":
            result = _get_crypto_data(arguments["crypto"])
        elif tool_name == "get_model_info":
            result = _get_model_info(arguments["asset"])
        elif tool_name == "get_market_summary":
            result = _get_market_summary()
        elif tool_name == "get_markov_predictions":
            result = _get_markov_predictions(arguments.get("target"))
        elif tool_name == "explain_indicator":
            result = _explain_indicator(arguments["indicator"])
        else:
            result = {"error": f"Unknown tool: {tool_name}"}

        if isinstance(result, dict) and result.get("error") and result.get("status") not in {"ok", "no_live_data"}:
            record_tool_failure(tool_name)
        else:
            record_tool_success(tool_name)
        return result
    except Exception as e:
        record_tool_failure(tool_name)
        return {
            "error": str(e),
            "tool": tool_name,
            "status": "validation_error",
            "response_instruction": "Explain that the requested operation could not be validated, and ask the user to rephrase more specifically.",
        }


def _get_uf_data(days: int = 30) -> dict:
    """Fetch UF data from internal API."""
    try:
        from app.ml.ingest.bde_client import fetch_uf

        now = _market_now()
        end = now.strftime("%Y-%m-%d")
        start = (now - timedelta(days=days)).strftime("%Y-%m-%d")
        df = fetch_uf(start_date=start, end_date=end, aggregate_monthly=False)

        if df.empty:
            return _build_no_live_data_payload(
                label="UF",
                source="Banco Central de Chile",
                fallback_context=FALLBACK_EXPLANATIONS["UF"],
            )

        latest = df.iloc[-1]
        first = df.iloc[0]
        latest_val = float(latest["value"])
        first_val = float(first["value"])
        change_pct = ((latest_val - first_val) / first_val) * 100

        return _with_market_date_context({
            "indicator": "UF",
            "current_value": round(latest_val, 2),
            "change_percent": round(float(change_pct), 2),
            "period_days": days,
            "trend": "up" if change_pct > 0 else "down",
            "source": "Banco Central de Chile",
            "status": "ok",
        }, latest["date"])
    except Exception as e:
        return _build_no_live_data_payload(
            label="UF",
            source="Banco Central de Chile",
            fallback_context=FALLBACK_EXPLANATIONS["UF"],
            error_message=str(e),
        )


def _get_usdclp_data(days: int = 30) -> dict:
    """Fetch USD/CLP data from internal API."""
    try:
        from app.ml.ingest.bde_client import fetch_usdclp

        now = _market_now()
        end = now.strftime("%Y-%m-%d")
        start = (now - timedelta(days=days)).strftime("%Y-%m-%d")
        df = fetch_usdclp(start_date=start, end_date=end, aggregate_monthly=False)

        if df.empty:
            return _build_no_live_data_payload(
                label="USD/CLP",
                source="Banco Central de Chile",
                fallback_context=FALLBACK_EXPLANATIONS["USD/CLP"],
            )

        latest = df.iloc[-1]
        first = df.iloc[0]
        latest_val = float(latest["value"])
        first_val = float(first["value"])
        change_pct = ((latest_val - first_val) / first_val) * 100

        return _with_market_date_context({
            "indicator": "USD/CLP",
            "current_value": round(latest_val, 2),
            "change_percent": round(float(change_pct), 2),
            "period_days": days,
            "trend": "up" if change_pct > 0 else "down",
            "source": "Banco Central de Chile",
            "status": "ok",
        }, latest["date"])
    except Exception as e:
        return _build_no_live_data_payload(
            label="USD/CLP",
            source="Banco Central de Chile",
            fallback_context=FALLBACK_EXPLANATIONS["USD/CLP"],
            error_message=str(e),
        )


def _get_commodity_data(commodity: str, days: int = 30) -> dict:
    """Fetch commodity data from FRED."""
    # FRED series IDs for commodities
    series_map = {
        "gold": "GOLDAMGBD228NLBM",
        "copper": "PCOPPUSDM",
        "oil": "DCOILWTICO",
        "silver": "SLVPRUSD",
    }

    commodity_names = {
        "gold": "Gold (USD/oz)",
        "copper": "Copper (USD/lb)",
        "oil": "Oil WTI (USD/bbl)",
        "silver": "Silver (USD/oz)",
    }

    try:
        from app.services.fred import fetch_fred_series
        import pandas as pd

        series_id = series_map.get(commodity)
        if not series_id:
            return {"error": f"Unknown commodity: {commodity}"}

        df = fetch_fred_series(series_id)

        if df.empty:
            return {"error": "No data available", "commodity": commodity}

        # Filter to the requested time window
        cutoff = _market_now().replace(tzinfo=None) - timedelta(days=days)
        df = df[df["date"] >= pd.Timestamp(cutoff)]

        if df.empty:
            return _build_no_live_data_payload(
                label=commodity_names.get(commodity, commodity),
                source="FRED (Federal Reserve)",
                fallback_context=FALLBACK_EXPLANATIONS.get(commodity_names.get(commodity, commodity), "Historical context is available, but no current live quote was returned."),
            )

        latest = df.iloc[-1]
        first = df.iloc[0]
        latest_val = float(latest["value"])
        first_val = float(first["value"])
        change_pct = ((latest_val - first_val) / first_val) * 100

        return _with_market_date_context({
            "commodity": commodity_names.get(commodity, commodity),
            "current_value": round(latest_val, 2),
            "change_percent": round(float(change_pct), 2),
            "period_days": days,
            "trend": "up" if change_pct > 0 else "down",
            "source": "FRED (Federal Reserve)",
            "status": "ok",
        }, latest["date"])
    except Exception as e:
        label = commodity_names.get(commodity, commodity)
        return _build_no_live_data_payload(
            label=label,
            source="FRED (Federal Reserve)",
            fallback_context=FALLBACK_EXPLANATIONS.get(label, "Historical context is available, but no current live quote was returned."),
            error_message=str(e),
        )


def _get_crypto_data(crypto: str) -> dict:
    """Fetch crypto data from Buda API."""
    try:
        from app.services.crypto import get_buda_ticker

        market = f"{crypto.upper()}-CLP"
        data = get_buda_ticker(market)

        if not data:
            return _build_no_live_data_payload(
                label=crypto.upper(),
                source="Buda.com",
                fallback_context=FALLBACK_EXPLANATIONS[crypto.upper()],
            )

        return _with_market_date_context({
            "crypto": crypto.upper(),
            "price_clp": data.get("last_price"),
            "volume_24h": data.get("volume"),
            "source": "Buda.com",
            "status": "ok",
        }, _market_now())
    except Exception as e:
        return _build_no_live_data_payload(
            label=crypto.upper(),
            source="Buda.com",
            fallback_context=FALLBACK_EXPLANATIONS.get(crypto.upper(), "Historical crypto context is available, but no current live quote was returned."),
            error_message=str(e),
        )


def _get_model_info(asset: str) -> dict:
    """Get ML model info for an asset."""
    # Demo data - in production would query model registry
    model_data = {
        "GOLD": {
            "model": "Auto ARIMA",
            "mae": 12.5,
            "rmse": 15.2,
            "mape": 0.65,
            "confidence": "excellent",
        },
        "COPPER": {
            "model": "Theta",
            "mae": 180,
            "rmse": 220,
            "mape": 6.14,
            "confidence": "volatile",
        },
        "OIL": {
            "model": "Naive",
            "mae": 1.2,
            "rmse": 1.8,
            "mape": 1.92,
            "confidence": "excellent",
        },
        "USDCLP": {
            "model": "Auto ARIMA",
            "mae": 8.5,
            "rmse": 12.3,
            "mape": 4.22,
            "confidence": "good",
        },
        "UF": {
            "model": "ARIMA(0,2,2)",
            "mae": 250,
            "rmse": 253,
            "mape": 0.63,
            "confidence": "excellent",
        },
        "BTC": {
            "model": "Auto ARIMA",
            "mae": 2500,
            "rmse": 3200,
            "mape": 8.5,
            "confidence": "volatile",
        },
        "ETH": {
            "model": "Auto ARIMA",
            "mae": 180,
            "rmse": 240,
            "mape": 9.2,
            "confidence": "volatile",
        },
    }

    info = model_data.get(asset.upper())
    if not info:
        return {"error": f"No model for {asset}"}

    # Model explanations
    model_explanations = {
        "Auto ARIMA": "Modelo que automáticamente encuentra la mejor combinación de valores pasados para predecir el futuro.",
        "Theta": "Método que descompone y suaviza la serie. Bueno para activos volátiles.",
        "Naive": "Usa el último valor como predicción. Sorprendentemente efectivo para algunos activos.",
        "ARIMA(0,2,2)": "Modelo ARIMA específico para series con tendencia fuerte y predecible.",
    }

    return {
        "asset": asset.upper(),
        "model_name": info["model"],
        "model_explanation": model_explanations.get(
            info["model"], "Modelo de series de tiempo"
        ),
        "metrics": {"mae": info["mae"], "rmse": info["rmse"], "mape": info["mape"]},
        "confidence": info["confidence"],
        "confidence_meaning": {
            "excellent": "Alta confiabilidad. El modelo predice muy bien este activo.",
            "good": "Buena confiabilidad. Predicciones útiles pero con margen de error.",
            "volatile": "Activo muy volátil. Las predicciones son orientativas, no definitivas.",
        }.get(info["confidence"]),
    }


def _get_market_summary() -> dict:
    """Get a summary of all market data."""
    summary = {
        "timestamp": _market_now().isoformat(),
        "indicators": [],
        "status": "ok",
        "market_timezone": "America/Santiago",
    }

    # Get each indicator
    uf = _get_uf_data(7)
    if "error" not in uf:
        summary["indicators"].append(uf)

    usdclp = _get_usdclp_data(7)
    if "error" not in usdclp:
        summary["indicators"].append(usdclp)

    for commodity in ["gold", "copper", "oil"]:
        data = _get_commodity_data(commodity, 7)
        if "error" not in data:
            summary["indicators"].append(data)

    if not summary["indicators"]:
        summary["status"] = "no_live_data"
        summary["response_instruction"] = (
            "Explain that a live market snapshot is unavailable. You may still explain the role of these indicators using historical context, but do not invent fresh quotes."
        )

    return summary


def _explain_indicator(indicator: str) -> dict:
    """Return static explanation for an indicator."""
    explanation = INDICATOR_EXPLANATIONS.get(indicator.lower())
    if not explanation:
        return {"error": f"Unknown indicator: {indicator}"}
    return explanation


def _get_markov_predictions(target: str = None) -> dict:
    """Read the latest statistical Markov transition matrices from the database."""
    try:
        from app.models.ml import MarkovCombination
        from app.extensiones import db
        from sqlalchemy import desc

        query = MarkovCombination.query.order_by(
            desc(MarkovCombination.run_date), desc(MarkovCombination.id)
        )

        if target:
            # Simple soft match (handles 'USD-CLP' vs 'USDCLP=X')
            query = query.filter(MarkovCombination.target.ilike(f"%{target[:3]}%"))

        results = query.limit(3).all()

        if not results:
            return {
                "error": "No Markov transition matrices found in the database. Call get_market_summary instead."
            }

        insights = []
        for res in results:
            insights.append(
                {
                    "predictor": res.predictor,
                    "predicts_target": res.target,
                    "statistical_significance_p_value": float(res.p_value),
                    "lag_correlation": float(res.lag1_correlation),
                    "transition_matrix_probabilities": res.transition_matrix,
                    "calculated_on": str(res.run_date),
                }
            )

        return {
            "concept": "Markov Chain empirical probabilities based on Granger causality (P-Value < 0.05).",
            "interpretation_guide": "The matrix shows P(Target_State_Today | Predictor_State_Yesterday). 'Bull'=Up, 'Bear'=Down, 'Sideways'=Flat.",
            "top_predictive_relationships": insights,
        }
    except Exception as e:
        return {"error": str(e), "tool": "get_markov_predictions"}
