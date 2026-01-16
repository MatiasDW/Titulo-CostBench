"""
Series Classification Configuration
Defines which series are trainable vs context-only
"""

# ============================================
# TRAINABLE SERIES (ML Enabled)
# ============================================
TRAINABLE_SERIES = {
    # FX - Primary currency pairs
    "USDCLP": {
        "source": "BDE",
        "frequency": "daily",
        "model_candidates": ["auto_arima", "theta", "naive"],
        "confidence_default": "good",
        "description": "USD/CLP exchange rate (Banco Central)",
        "trainable": True
    },
    "GBPCLP": {
        "source": "BDE", 
        "frequency": "daily",
        "model_candidates": ["auto_arima", "theta"],
        "confidence_default": "good",
        "description": "GBP/CLP exchange rate",
        "trainable": True
    },
    
    # Indexed series (semi-deterministic)
    "UF": {
        "source": "BDE",
        "frequency": "daily",
        "model_candidates": ["auto_arima"],
        "confidence_default": "good",
        "is_rule_based": True,
        "rule_note": "UF is indexed to inflation. Forecasts are short-term statistical approximations, not inflation predictions.",
        "academic_note": "Although UF is derived from inflation, its daily path can still be statistically modeled for short horizons. Results are compared against a rule-based baseline.",
        "description": "Unidad de Fomento (inflation-indexed)",
        "trainable": True
    },
    
    # Commodities
    "GOLD": {
        "source": "FRED/Market",
        "frequency": "daily",
        "model_candidates": ["auto_arima", "theta", "naive"],
        "confidence_default": "good",
        "description": "Gold price (USD/oz)",
        "trainable": True
    },
    "COPPER": {
        "source": "FRED/Market",
        "frequency": "daily", 
        "model_candidates": ["theta", "auto_arima", "naive"],
        "confidence_default": "good",
        "description": "Copper price (USD/ton)",
        "trainable": True
    },
    "OIL": {
        "source": "FRED/Market",
        "frequency": "daily",
        "model_candidates": ["naive", "auto_arima"],
        "confidence_default": "good",
        "description": "WTI Crude Oil (USD/barrel)",
        "trainable": True
    },
    
    # Crypto (high volatility warning)
    "BTC": {
        "source": "Exchange",
        "frequency": "daily",
        "model_candidates": ["auto_arima", "naive"],
        "confidence_default": "low",
        "is_high_volatility": True,
        "volatility_note": "High volatility asset. Forecast accuracy is structurally limited due to regime changes and exogenous shocks.",
        "description": "Bitcoin (USD)",
        "trainable": True
    },
    "ETH": {
        "source": "Exchange",
        "frequency": "daily",
        "model_candidates": ["auto_arima", "naive"],
        "confidence_default": "low",
        "is_high_volatility": True,
        "volatility_note": "High volatility asset. Forecast accuracy is structurally limited due to regime changes and exogenous shocks.",
        "description": "Ethereum (USD)",
        "trainable": True
    }
}


# ============================================
# CONTEXT-ONLY SERIES (No Training)
# ============================================
CONTEXT_SERIES = {
    "CPI_USA": {
        "source": "BLS",
        "series_id": "CUUR0000SA0",
        "frequency": "monthly",
        "description": "Consumer Price Index - All Urban Consumers",
        "use": "Global inflation context",
        "trainable": False,
        "license_note": "Used for contextual analysis only. Not trained due to licensing restrictions."
    },
    "UST_10Y": {
        "source": "Treasury",
        "frequency": "daily",
        "description": "10-Year Treasury Yield",
        "use": "Interest rate context",
        "trainable": False,
        "license_note": "Contextual macro indicator. No forecast endpoint available."
    }
}


# ============================================
# CONFIDENCE LEVELS
# ============================================
CONFIDENCE_LEVELS = {
    "excellent": {
        "label": "Excellent",
        "color": "#38a169",  # Green
        "emoji": "🟢",
        "mape_threshold": 2.0,
        "description": "Predictions typically within 2% of actual values"
    },
    "good": {
        "label": "Good", 
        "color": "#ecc94b",  # Yellow
        "emoji": "🟡",
        "mape_threshold": 5.0,
        "description": "Predictions typically within 5% of actual values"
    },
    "volatile": {
        "label": "Volatile",
        "color": "#ed8936",  # Orange
        "emoji": "🟠",
        "mape_threshold": 10.0,
        "description": "Higher variability expected due to market conditions"
    },
    "experimental": {
        "label": "Experimental",
        "color": "#e53e3e",  # Red
        "emoji": "🔴",
        "mape_threshold": float("inf"),
        "description": "Limited predictability - use with caution"
    }
}


def get_confidence_from_mape(mape: float) -> str:
    """Determine confidence level from MAPE."""
    if mape < 2.0:
        return "excellent"
    elif mape < 5.0:
        return "good"
    elif mape < 10.0:
        return "volatile"
    else:
        return "experimental"


def is_trainable(series: str) -> bool:
    """Check if a series is trainable."""
    return series.upper() in TRAINABLE_SERIES


def get_series_config(series: str) -> dict:
    """Get configuration for a series."""
    series_upper = series.upper()
    if series_upper in TRAINABLE_SERIES:
        return TRAINABLE_SERIES[series_upper]
    elif series_upper in CONTEXT_SERIES:
        return CONTEXT_SERIES[series_upper]
    return None


def get_all_trainable():
    """Get list of all trainable series."""
    return list(TRAINABLE_SERIES.keys())


def get_all_context():
    """Get list of context-only series."""
    return list(CONTEXT_SERIES.keys())
