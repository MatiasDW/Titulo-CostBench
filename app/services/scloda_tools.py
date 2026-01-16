"""
Scloda Tools - Function calling tools for market data queries.

These tools are exposed to the LLM via OpenRouter's function calling mechanism.
Each tool queries internal APIs and returns structured data for Scloda to explain.
"""
import os
from datetime import datetime, timedelta
from typing import Any

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
                        "description": "Cantidad de días hacia atrás para obtener historial. Default: 30"
                    }
                }
            }
        }
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
                        "description": "Cantidad de días hacia atrás para obtener historial. Default: 30"
                    }
                }
            }
        }
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
                        "description": "El commodity a consultar"
                    },
                    "days": {
                        "type": "integer",
                        "description": "Cantidad de días de historial. Default: 30"
                    }
                },
                "required": ["commodity"]
            }
        }
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
                        "description": "La criptomoneda a consultar"
                    }
                },
                "required": ["crypto"]
            }
        }
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
                        "description": "El activo del cual obtener info del modelo"
                    }
                },
                "required": ["asset"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_market_summary",
            "description": "Obtiene un resumen completo del mercado: UF, dólar, oro, cobre, petróleo, Bitcoin. Útil para dar un panorama general.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
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
                        "enum": ["uf", "usdclp", "gold", "copper", "oil", "cpi", "treasury_10y", "btc", "eth"],
                        "description": "El indicador a explicar"
                    }
                },
                "required": ["indicator"]
            }
        }
    }
]

# Indicator explanations (static knowledge)
INDICATOR_EXPLANATIONS = {
    "uf": {
        "name": "UF (Unidad de Fomento)",
        "what": "Es una unidad de cuenta que se ajusta diariamente según la inflación en Chile.",
        "use": "Se usa para créditos hipotecarios, arriendos y algunos contratos para proteger el valor del dinero.",
        "impact": "Cuando la inflación sube, la UF sube. Si tienes un crédito en UF, tu dividendo aumenta.",
        "tip": "Si la UF sube muy rápido, significa que hay inflación alta en Chile."
    },
    "usdclp": {
        "name": "Dólar Observado (USD/CLP)",
        "what": "Es el precio del dólar estadounidense en pesos chilenos.",
        "use": "Afecta el precio de todo lo importado: tecnología, autos, combustibles.",
        "impact": "Dólar alto = importaciones más caras, pero exportaciones más competitivas.",
        "tip": "El cobre y el dólar suelen moverse en direcciones opuestas."
    },
    "gold": {
        "name": "Oro",
        "what": "Metal precioso considerado 'refugio seguro' en tiempos de incertidumbre.",
        "use": "Los inversionistas compran oro cuando hay miedo en los mercados.",
        "impact": "Sube cuando hay crisis o inflación alta. Baja cuando hay confianza económica.",
        "tip": "Si el oro sube mucho, puede indicar que los mercados están nerviosos."
    },
    "copper": {
        "name": "Cobre",
        "what": "Chile es el mayor productor mundial. Se usa en construcción, electrónica y energía verde.",
        "use": "Es un indicador de la salud económica global (le dicen 'Dr. Copper').",
        "impact": "Cobre alto = más dólares entran a Chile = peso más fuerte. Cobre bajo = peso se debilita.",
        "tip": "El precio del cobre depende mucho de la economía de China."
    },
    "oil": {
        "name": "Petróleo (WTI)",
        "what": "El petróleo West Texas Intermediate es la referencia para el precio del crudo en América.",
        "use": "Determina el precio de la bencina y muchos productos derivados.",
        "impact": "Petróleo alto = inflación por combustibles. Afecta el costo de transporte y producción.",
        "tip": "Los conflictos en Medio Oriente suelen hacer subir el petróleo."
    },
    "cpi": {
        "name": "CPI USA (Inflación EEUU)",
        "what": "Índice de Precios al Consumidor de Estados Unidos. Mide la inflación gringa.",
        "use": "La Fed usa este dato para decidir si sube o baja las tasas de interés.",
        "impact": "CPI alto = la Fed sube tasas = dólar se fortalece = afecta a Chile.",
        "tip": "Es uno de los datos más importantes para los mercados globales."
    },
    "treasury_10y": {
        "name": "Bono del Tesoro 10 años",
        "what": "Tasa de interés que paga el gobierno de EEUU por préstamos a 10 años.",
        "use": "Es la 'tasa libre de riesgo' de referencia mundial.",
        "impact": "Tasas altas atraen dinero a EEUU, presionando monedas emergentes como el peso chileno.",
        "tip": "Cuando esta tasa sube mucho, los mercados emergentes sufren."
    },
    "btc": {
        "name": "Bitcoin",
        "what": "Primera y más conocida criptomoneda. Suministro limitado a 21 millones de unidades.",
        "use": "Algunos lo ven como 'oro digital', otros como inversión especulativa.",
        "impact": "Muy volátil. Puede subir o bajar 10% en un día.",
        "tip": "No inviertas dinero que no puedas perder. Es de alto riesgo."
    },
    "eth": {
        "name": "Ethereum",
        "what": "Plataforma de contratos inteligentes. Segunda cripto más grande después de Bitcoin.",
        "use": "Base de aplicaciones DeFi (finanzas descentralizadas) y NFTs.",
        "impact": "Tiende a moverse con Bitcoin pero con mayor volatilidad.",
        "tip": "Es más que una moneda: es una plataforma tecnológica."
    }
}


def execute_tool(tool_name: str, arguments: dict) -> dict[str, Any]:
    """
    Execute a tool and return its result.
    This is called by the chat service when the LLM requests a function call.
    """
    try:
        if tool_name == "get_uf_data":
            return _get_uf_data(arguments.get("days", 30))
        elif tool_name == "get_usdclp_data":
            return _get_usdclp_data(arguments.get("days", 30))
        elif tool_name == "get_commodity_data":
            return _get_commodity_data(arguments["commodity"], arguments.get("days", 30))
        elif tool_name == "get_crypto_data":
            return _get_crypto_data(arguments["crypto"])
        elif tool_name == "get_model_info":
            return _get_model_info(arguments["asset"])
        elif tool_name == "get_market_summary":
            return _get_market_summary()
        elif tool_name == "explain_indicator":
            return _explain_indicator(arguments["indicator"])
        else:
            return {"error": f"Unknown tool: {tool_name}"}
    except Exception as e:
        return {"error": str(e)}


def _get_uf_data(days: int = 30) -> dict:
    """Fetch UF data from internal API."""
    try:
        from app.ml.ingest.bde_client import fetch_uf
        end = datetime.now().strftime("%Y-%m-%d")
        start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        df = fetch_uf(start_date=start, end_date=end, aggregate_monthly=False)
        
        if df.empty:
            return {"error": "No data available"}
        
        latest = df.iloc[-1]
        first = df.iloc[0]
        change_pct = ((latest["value"] - first["value"]) / first["value"]) * 100
        
        return {
            "indicator": "UF",
            "current_value": round(latest["value"], 2),
            "current_date": str(latest["date"]),
            "change_percent": round(change_pct, 2),
            "period_days": days,
            "trend": "up" if change_pct > 0 else "down",
            "source": "Banco Central de Chile"
        }
    except Exception as e:
        return {"error": str(e), "indicator": "UF"}


def _get_usdclp_data(days: int = 30) -> dict:
    """Fetch USD/CLP data from internal API."""
    try:
        from app.ml.ingest.bde_client import fetch_usdclp
        end = datetime.now().strftime("%Y-%m-%d")
        start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        df = fetch_usdclp(start_date=start, end_date=end, aggregate_monthly=False)
        
        if df.empty:
            return {"error": "No data available"}
        
        latest = df.iloc[-1]
        first = df.iloc[0]
        change_pct = ((latest["value"] - first["value"]) / first["value"]) * 100
        
        return {
            "indicator": "USD/CLP",
            "current_value": round(latest["value"], 2),
            "current_date": str(latest["date"]),
            "change_percent": round(change_pct, 2),
            "period_days": days,
            "trend": "up" if change_pct > 0 else "down",
            "source": "Banco Central de Chile"
        }
    except Exception as e:
        return {"error": str(e), "indicator": "USD/CLP"}


def _get_commodity_data(commodity: str, days: int = 30) -> dict:
    """Fetch commodity data from FRED."""
    # FRED series IDs for commodities
    series_map = {
        "gold": "GOLDAMGBD228NLBM",
        "copper": "PCOPPUSDM", 
        "oil": "DCOILWTICO",
        "silver": "SLVPRUSD"
    }
    
    commodity_names = {
        "gold": "Oro (USD/oz)",
        "copper": "Cobre (USD/lb)",
        "oil": "Petróleo WTI (USD/bbl)",
        "silver": "Plata (USD/oz)"
    }
    
    try:
        from app.services.fred import get_fred_series
        series_id = series_map.get(commodity)
        if not series_id:
            return {"error": f"Unknown commodity: {commodity}"}
        
        df = get_fred_series(series_id, days=days)
        
        if df.empty:
            return {"error": "No data available", "commodity": commodity}
        
        latest = df.iloc[-1]
        first = df.iloc[0]
        change_pct = ((latest["value"] - first["value"]) / first["value"]) * 100
        
        return {
            "commodity": commodity_names.get(commodity, commodity),
            "current_value": round(latest["value"], 2),
            "current_date": str(latest["date"]),
            "change_percent": round(change_pct, 2),
            "period_days": days,
            "trend": "up" if change_pct > 0 else "down",
            "source": "FRED (Federal Reserve)"
        }
    except Exception as e:
        return {"error": str(e), "commodity": commodity}


def _get_crypto_data(crypto: str) -> dict:
    """Fetch crypto data from Buda API."""
    try:
        from app.services.crypto import get_buda_ticker
        
        market = f"{crypto.upper()}-CLP"
        data = get_buda_ticker(market)
        
        if not data:
            return {"error": f"No data for {crypto}"}
        
        return {
            "crypto": crypto.upper(),
            "price_clp": data.get("last_price"),
            "volume_24h": data.get("volume"),
            "source": "Buda.com"
        }
    except Exception as e:
        return {"error": str(e), "crypto": crypto}


def _get_model_info(asset: str) -> dict:
    """Get ML model info for an asset."""
    # Demo data - in production would query model registry
    model_data = {
        "GOLD": {"model": "Auto ARIMA", "mae": 12.5, "rmse": 15.2, "mape": 0.65, "confidence": "excellent"},
        "COPPER": {"model": "Theta", "mae": 180, "rmse": 220, "mape": 6.14, "confidence": "volatile"},
        "OIL": {"model": "Naive", "mae": 1.2, "rmse": 1.8, "mape": 1.92, "confidence": "excellent"},
        "USDCLP": {"model": "Auto ARIMA", "mae": 8.5, "rmse": 12.3, "mape": 4.22, "confidence": "good"},
        "UF": {"model": "ARIMA(0,2,2)", "mae": 250, "rmse": 253, "mape": 0.63, "confidence": "excellent"},
        "BTC": {"model": "Auto ARIMA", "mae": 2500, "rmse": 3200, "mape": 8.5, "confidence": "volatile"},
        "ETH": {"model": "Auto ARIMA", "mae": 180, "rmse": 240, "mape": 9.2, "confidence": "volatile"}
    }
    
    info = model_data.get(asset.upper())
    if not info:
        return {"error": f"No model for {asset}"}
    
    # Model explanations
    model_explanations = {
        "Auto ARIMA": "Modelo que automáticamente encuentra la mejor combinación de valores pasados para predecir el futuro.",
        "Theta": "Método que descompone y suaviza la serie. Bueno para activos volátiles.",
        "Naive": "Usa el último valor como predicción. Sorprendentemente efectivo para algunos activos.",
        "ARIMA(0,2,2)": "Modelo ARIMA específico para series con tendencia fuerte y predecible."
    }
    
    return {
        "asset": asset.upper(),
        "model_name": info["model"],
        "model_explanation": model_explanations.get(info["model"], "Modelo de series de tiempo"),
        "metrics": {
            "mae": info["mae"],
            "rmse": info["rmse"],
            "mape": info["mape"]
        },
        "confidence": info["confidence"],
        "confidence_meaning": {
            "excellent": "Alta confiabilidad. El modelo predice muy bien este activo.",
            "good": "Buena confiabilidad. Predicciones útiles pero con margen de error.",
            "volatile": "Activo muy volátil. Las predicciones son orientativas, no definitivas."
        }.get(info["confidence"])
    }


def _get_market_summary() -> dict:
    """Get a summary of all market data."""
    summary = {
        "timestamp": datetime.now().isoformat(),
        "indicators": []
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
    
    return summary


def _explain_indicator(indicator: str) -> dict:
    """Return static explanation for an indicator."""
    explanation = INDICATOR_EXPLANATIONS.get(indicator.lower())
    if not explanation:
        return {"error": f"Unknown indicator: {indicator}"}
    return explanation
