import pandas as pd
import yfinance as yf
from statsmodels.tsa.stattools import grangercausalitytests, ccf
from scipy import stats
import warnings

# Suppress statsmodels warnings for cleaner output
warnings.filterwarnings("ignore")

# Define the assets we want to test across our app ecosystem
ASSETS = {
    "USDCLP=X": "USD/CLP",
    "HG=F": "Copper",
    "GC=F": "Gold",
    "CL=F": "Oil (WTI)",
    "BTC-USD": "Bitcoin",
    "ETH-USD": "Ethereum",
    "^TNX": "Treasury 10Y Yield",
    "^GSPC": "S&P 500",
}


def fetch_data():
    print("Downloading 5 years of historical data for all assets...")
    tickers = list(ASSETS.keys())
    # Download data
    data = yf.download(tickers, start="2019-01-01", end="2024-01-01", progress=False)[
        "Close"
    ]

    # Forward fill missing data to align trading days
    data = data.ffill().dropna()

    # Calculate daily percent returns
    returns = data.pct_change().dropna()

    # Calculate Z-Scores mapping
    z_scores = returns.copy()
    states = returns.copy()

    for ticker in tickers:
        z = stats.zscore(returns[ticker])
        z_scores[ticker] = z
        # Discretize into Bull, Bear, Sideways
        states[ticker] = (
            pd.Series(z)
            .apply(
                lambda x: "Bear" if x < -1.0 else ("Bull" if x > 1.0 else "Sideways")
            )
            .values
        )

    return returns, states


def test_granger_causality(returns_df, predictor, target, maxlag=5):
    """
    Tests if `predictor` causes `target`.
    H0: Predictor does NOT Granger cause Target.
    Returns the minimum p-value across the lags.
    """
    data = returns_df[[target, predictor]].values
    try:
        gc_res = grangercausalitytests(data, maxlag=maxlag, verbose=False)
        p_values = [gc_res[lag][0]["ssr_ftest"][1] for lag in range(1, maxlag + 1)]
        return min(p_values), p_values
    except Exception:
        return 1.0, []


def get_transition_matrix(states_df, predictor, target):
    """
    Returns the transition probabilities P(Target(t) | Predictor(t-1))
    """
    # Shift predictor by 1 day
    pred_lag1 = states_df[predictor].shift(1)
    targ_t = states_df[target]

    df_trans = pd.DataFrame({"Pred_t_minus_1": pred_lag1, "Target_t": targ_t}).dropna()

    # Cross tabulation
    transition_counts = pd.crosstab(df_trans["Pred_t_minus_1"], df_trans["Target_t"])
    # Convert to percentages
    transition_matrix = (
        transition_counts.div(transition_counts.sum(axis=1), axis=0) * 100
    )

    return transition_matrix


def run_all_combinations():
    returns, states = fetch_data()
    tickers = list(ASSETS.keys())

    results = []

    print("\n--- GRANGER CAUSALITY TEST ACROSS ALL COMBINATIONS ---\n")
    for predictor in tickers:
        for target in tickers:
            if predictor == target:
                continue

            min_p, p_vals = test_granger_causality(
                returns, predictor=predictor, target=target
            )

            # If the best p-value across any of the first 5 lags is < 0.05, we found statistically significant causality
            is_significant = min_p < 0.05

            if is_significant:
                # Calculate cross correlation at lag 1 to see direction
                cc = ccf(returns[target], returns[predictor], adjusted=False)
                lag1_corr = cc[1]

                results.append(
                    {
                        "Predictor": ASSETS[predictor],
                        "Target": ASSETS[target],
                        "Min_P_Value": min_p,
                        "Lag1_Correlation": lag1_corr,
                        "Ticker_Pred": predictor,
                        "Ticker_Targ": target,
                    }
                )

    # Sort results by strongest significance (lowest p-value)
    results.sort(key=lambda x: x["Min_P_Value"])

    print("🏆 BEST SIGNIFICANT RELATIONSHIPS FOUND (p < 0.05) 🏆")
    print("-" * 80)
    for res in results:
        direction = "INVERSE (-)" if res["Lag1_Correlation"] < 0 else "DIRECT (+)"
        if abs(res["Lag1_Correlation"]) < 0.05:
            direction = "WEAK/MIXED"

        print(f"[{res['Predictor']}] predicts [{res['Target']}]")
        print(
            f"   -> p-value: {res['Min_P_Value']:.6f} | Relation: {direction} (lag-1 corr: {res['Lag1_Correlation']:.3f})"
        )

    if not results:
        print("No statistically significant relationships found.")
        return

    print("\n\n--- TRANSITION MATRICES FOR ALL SIGNIFICANT COMBINATIONS ---\n")
    for i, res in enumerate(results):
        pred_ticker = res["Ticker_Pred"]
        targ_ticker = res["Ticker_Targ"]

        # We only print the top 3 to terminal to avoid console spam, but calculate ALL for the DB
        matrix = get_transition_matrix(states, pred_ticker, targ_ticker)

        if i < 3:
            print(f"#{i+1}: {res['Predictor']} (Day T-1) -> {res['Target']} (Day T)")
            print(matrix.round(1).to_string())
            print("-" * 50 + "\n")

        # Attach the matrix dictionary to every result for DB storage
        # Pandas DataFrame to JSON-serializable dictionary format
        res["transition_matrix_json"] = matrix.to_dict(orient="index")

    return results


if __name__ == "__main__":
    run_all_combinations()
