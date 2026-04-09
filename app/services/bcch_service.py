"""
Banco Central de Chile (BCCh) Service
Fetches daily and expected macroeconomic metrics from the SIETE API for Real Estate simulations.
"""

import os
import requests
from typing import Dict, Any

from app.ml.logging_utils import get_logger

logger = get_logger("services.bcch")

# Official BDE Series IDs (Representational IDs for the EEE and Rates)
SERIES_IDS = {
    "UF": "F073.UFF.PRE.Z.D",
    # Tasa de Interés Promedio para Mutuos Hipotecarios (Endógenos)
    "MORTGAGE_RATE": "F033.TMM.11.1.2.U.D",
    # EEE: Expectativa TPM a 11 meses
    "EXP_TPM_11M": "F019.EEE.TPM.11.M",
    # EEE: Expectativa Inflacion a 11 meses
    "EXP_INFL_11M": "F019.EEE.INF.11.M",
}


class BCChService:
    def __init__(self):
        raw_user = os.getenv("BDE_USER")
        raw_password = os.getenv("BDE_PASS")
        self.user = raw_user if self._is_configured_value(raw_user) else None
        self.password = raw_password if self._is_configured_value(raw_password) else None
        self.base_url = "https://si3.bcentral.cl/SieteRestWS/SieteRestWS.ashx"
        self.timeout = 15
        self.last_source = "fallback"

    @staticmethod
    def _is_configured_value(value: str | None) -> bool:
        if not value:
            return False
        normalized = value.strip().lower()
        placeholder_markers = ("tu-", "example", "ejemplo", "aqui", "changeme")
        return not any(marker in normalized for marker in placeholder_markers)

    def _fetch_last_value(self, series_id: str, fallback_value: float) -> float:
        """Helper to fetch the latest available daily or monthly record."""
        if not self.user or not self.password:
            logger.warning("Mocking BCCh data (no credentials found)")
            self.last_source = "fallback"
            return fallback_value

        params = {
            "user": self.user,
            "pass": self.password,
            "timeseries": series_id,
            "function": "GetSeries",
        }

        try:
            response = requests.get(self.base_url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            series_block = data.get("Series")
            if series_block:
                # BCCh may return Series as dict (current behavior) or list.
                if isinstance(series_block, dict):
                    obs = series_block.get("Obs", [])
                elif isinstance(series_block, list) and series_block:
                    obs = series_block[0].get("Obs", [])
                else:
                    obs = []

                if obs:
                    # Return the chronologically last observation available.
                    latest_val = obs[-1].get("value")
                    if latest_val is not None:
                        self.last_source = "bcch_live"
                        return float(str(latest_val).replace(",", "."))

            logger.warning(f"No observations found for {series_id}")
            self.last_source = "fallback"
            return fallback_value

        except Exception as e:
            logger.error(f"Error fetching BCCh Series {series_id}: {e}")
            self.last_source = "fallback"
            return fallback_value

    def get_uf(self) -> float:
        """Returns today's UF value. Fallback: ~38000 CLP"""
        return self._fetch_last_value(SERIES_IDS["UF"], fallback_value=38000.0)

    def get_mortgage_rate(self) -> float:
        """Returns the current average mortgage interest rate (e.g. 5.1%)."""
        return self._fetch_last_value(SERIES_IDS["MORTGAGE_RATE"], fallback_value=5.1)

    def get_macro_expectations(self) -> Dict[str, float]:
        """
        Returns the Encuesta de Expectativas Económicas (EEE) for 11 months ahead.
        Used as exogenous parameters for the ARIMAX Real estate models.
        """
        tpm = self._fetch_last_value(SERIES_IDS["EXP_TPM_11M"], fallback_value=5.5)
        infl = self._fetch_last_value(SERIES_IDS["EXP_INFL_11M"], fallback_value=3.2)

        return {"expected_tpm_11m": tpm, "expected_inflation_11m": infl}
