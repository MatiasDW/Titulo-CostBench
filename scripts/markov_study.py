import pandas as pd
import numpy as np
import yfinance as yf
import statsmodels.api as sm
from statsmodels.tsa.stattools import grangercausalitytests, ccf
from scipy import stats


def run_markov_study():
    print("Downloading historical data...")
    # Fetch data (5 years for a good statistical sample)
    data = yf.download(
        ["USDCLP=X", "HG=F"], start="2019-01-01", end="2024-01-01", progress=False
    )

    # Extract Close prices
    df = data["Close"].copy()
    df.columns = ["COPPER", "USDCLP"]  # HG=F is Copper, USDCLP=X is USDCLP

    # Forward fill missing weekends/holidays so dates align perfectly
    merged = df.ffill().dropna()

    # Calculate returns
    merged["USD_ret"] = merged["USDCLP"].pct_change()
    merged["COP_ret"] = merged["COPPER"].pct_change()
    merged = merged.dropna()

    print("=== FINAL DATASET SHAPE ===")
    print(merged.shape)

    # ---------------------------------------------------------
    # FASE 1: Análisis de Correlación y Causalidad
    # ---------------------------------------------------------
    print("\n\n" + "=" * 50)
    print("FASE 1: TEST DE CAUSALIDAD DE GRANGER (Copper -> USDCLP)")
    print("=" * 50)
    print("¿El Cobre (pasado) predice el USD/CLP (futuro)?")
    # Granger expects 2D array: [target, predictor] -> [USD_ret, COP_ret]
    # H0: time series in the second column does NOT Granger cause the time series in the first column
    data_granger = merged[["USD_ret", "COP_ret"]].values
    gc_res = grangercausalitytests(data_granger, maxlag=5, verbose=False)
    for lag in range(1, 6):
        p_val = gc_res[lag][0]["ssr_ftest"][1]
        print(
            f"Lag {lag}: p-value = {p_val:.4f} {'(Significativo < 0.05)' if p_val < 0.05 else ''}"
        )

    print("\n" + "=" * 50)
    print("FASE 1: CORRELACIÓN CRUZADA (Cross-Correlation)")
    print("=" * 50)
    # ccf(x, y) order: cross correlation of x(t+k) and y(t)
    # We want to see correlation of COP_ret(t-k) and USD_ret(t)
    # So we use ccf(USD_ret, COP_ret) which gives corr(USD(t), COP(t-k)) for k>=0
    cc = ccf(merged["USD_ret"], merged["COP_ret"], adjusted=False)
    print("Correlación contemporánea (Lag 0):", round(cc[0], 4))
    for lag in range(1, 6):
        print(
            f"Correlación Lag {lag} (Copper hace {lag} días vs USD hoy): {round(cc[lag], 4)}"
        )

    # ---------------------------------------------------------
    # FASE 2: Discretización (Estados Z-Score)
    # ---------------------------------------------------------
    print("\n\n" + "=" * 50)
    print("FASE 2: DISCRETIZACIÓN DE ESTADOS (Z-SCORE)")
    print("=" * 50)
    merged["USD_z"] = stats.zscore(merged["USD_ret"])
    merged["COP_z"] = stats.zscore(merged["COP_ret"])

    def categorize_state(z):
        if z < -1.0:
            return "Bear"
        elif z > 1.0:
            return "Bull"
        else:
            return "Sideways"

    merged["USD_state"] = merged["USD_z"].apply(categorize_state)
    merged["COP_state"] = merged["COP_z"].apply(categorize_state)

    print("Distribución de Estados Dólar (USD/CLP):")
    print(merged["USD_state"].value_counts(normalize=True).round(3))
    print("\nDistribución de Estados Cobre:")
    print(merged["COP_state"].value_counts(normalize=True).round(3))

    # ---------------------------------------------------------
    # FASE 3: Matriz de Transición Empírica
    # ---------------------------------------------------------
    print("\n\n" + "=" * 50)
    print("FASE 3: MATRIZ DE TRANSICIÓN EMPÍRICA")
    print("=" * 50)
    # COP state at t-1 vs USD state at t
    merged["COP_state_lag1"] = merged["COP_state"].shift(1)
    df_trans = merged.dropna(subset=["COP_state_lag1"])

    # Crosstab (rows = COP t-1, cols = USD t)
    transition_counts = pd.crosstab(df_trans["COP_state_lag1"], df_trans["USD_state"])
    transition_matrix = transition_counts.div(transition_counts.sum(axis=1), axis=0)

    print("\nMatriz de Probabilidades P(USD[t] | COP[t-1]):")
    print("Filas: Estado Cobre Día Anterior | Columnas: Estado Dólar Día Actual")
    print("-" * 70)
    print(transition_matrix.round(3))


if __name__ == "__main__":
    run_markov_study()
