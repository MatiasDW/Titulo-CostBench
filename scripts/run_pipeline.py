"""
Script to run the Entrega 1+2 Data Pipeline.
Step 1: Normalization
"""
import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine
from datetime import datetime

load_dotenv() # Load environment variables from .env
from app.services.normalize import canon_cta, canon_uf

def run_step_1_normalization():
    print(">>> Step 1: Normalization")
    
    # Ensure output dir exists
    os.makedirs('data/canon', exist_ok=True)
    
    # --- CMF ---
    try:
        raw_cmf_path = 'data/cta_cuentavista_cmf.parquet'
        if os.path.exists(raw_cmf_path):
            print(f"Reading {raw_cmf_path}...")
            df_cmf = pd.read_parquet(raw_cmf_path)
            canon_df_cmf = canon_cta(df_cmf)
            out_cmf_path = 'data/canon/cta_cuentavista.parquet'
            canon_df_cmf.to_parquet(out_cmf_path)
            print(f"Saved {out_cmf_path} (rows={len(canon_df_cmf)})")
            print(canon_df_cmf.head(2))
        else:
            print(f"WARNING: {raw_cmf_path} not found.")
    except Exception as e:
        print(f"ERROR normalizing CMF: {e}")

    # --- UF ---
    try:
        raw_uf_path = 'data/indicadores_uf.parquet'
        if os.path.exists(raw_uf_path):
            print(f"Reading {raw_uf_path}...")
            df_uf = pd.read_parquet(raw_uf_path)
            canon_df_uf = canon_uf(df_uf)
            out_uf_path = 'data/canon/uf.parquet'
            canon_df_uf.to_parquet(out_uf_path)
            print(f"Saved {out_uf_path} (rows={len(canon_df_uf)})")
            print(canon_df_uf.head(2))
        else:
            print(f"WARNING: {raw_uf_path} not found.")
    except Exception as e:
        print(f"ERROR normalizing UF: {e}")

from app.services.atc import compute_atc, rank_topn

def run_step_2_metrics():
    print("\n>>> Step 2: ATC & Ranking")
    
    os.makedirs('data/metrics', exist_ok=True)
    
    try:
        canon_path = 'data/canon/cta_cuentavista.parquet'
        if os.path.exists(canon_path):
            print(f"Reading {canon_path}...")
            df = pd.read_parquet(canon_path)
            
            # Compute ATC
            df_atc = compute_atc(df)
            
            # Rank Top-N (Let's say ALL for the parquet, filter later?)
            # User said: "persist Top-N ranking". 
            # If I persist only top 10, I lose data for "listing".
            # Better to rank ALL and sort, so "Top-N" is just head(N).
            # But "Ranking Parquets exist with expected sorting" is the requirement.
            
            df_ranked = rank_topn(df_atc, n=1000) # Rank all
            
            out_path = 'data/metrics/atc_ranking.parquet'
            df_ranked.to_parquet(out_path)
            print(f"Saved {out_path} (rows={len(df_ranked)})")
            print(df_ranked[['institucion', 'producto', 'cta_anual_clp']].head(5))
        else:
            print(f"WARNING: {canon_path} not found. Run Step 1 first.")
    except Exception as e:
        print(f"ERROR computing metrics: {e}")

from app.services.ufx import attach_uf
from app.services.fx import attach_usd, fetch_usd_bde

def run_step_3_multicurrency():
    print("\n>>> Step 3: Multi-Currency")
    
    try:
        metrics_path = 'data/metrics/atc_ranking.parquet'
        uf_path = 'data/canon/uf.parquet'
        
        if os.path.exists(metrics_path) and os.path.exists(uf_path):
            df_metrics = pd.read_parquet(metrics_path)
            df_uf = pd.read_parquet(uf_path)
            
            # Attach UF
            df_multi = attach_uf(df_metrics, df_uf)
            
            # Get USD (Mock or Fetch)
            print("Fetching/Mocking USD data...")
            try:
                # Try fetching - commented out to avoid error without creds in test env
                # df_usd = fetch_usd_bde() 
                raise ValueError("Skipping BDE fetch")
            except Exception:
                # Mock USD
                import numpy as np
                dates = pd.date_range(start='2024-01-01', end='2025-12-31', freq='D')
                df_usd = pd.DataFrame({
                    'fecha': dates,
                    'valor': [950.0] * len(dates) # Flat 950 for test
                })
            
            # Attach USD
            df_multi = attach_usd(df_multi, df_usd)
            
            out_path = 'data/metrics/atc_ranking_multi.parquet'
            df_multi.to_parquet(out_path)
            print(f"Saved {out_path} (rows={len(df_multi)})")
            print(df_multi[['institucion', 'cta_anual_clp', 'cta_anual_uf', 'cta_anual_usd']].head(3))
            
        else:
            print("Missing input files for Step 3.")
            
    except Exception as e:
        print(f"ERROR step 3: {e}")

from app.services.fred import fetch_fred_series
from app.services.crypto import fetch_buda_series
from populate_analytics import run_analytics_step # Import Analytics
from populate_analytics import run_analytics_step # Import Analytics

def run_step_4_macro():
    print("\n>>> Step 4: Macro Context")
    os.makedirs('data/market', exist_ok=True)
    
    try:
        # 1. CPI (Inflation)
        print("Fetching CPI (CPIAUCSL) from FRED...")
        cpi_df = fetch_fred_series('CPIAUCSL')
        print(f"   -> CPI records: {len(cpi_df)}")
        
        # 2. 10Y Treasury Yield
        print("Fetching 10Y Treasury Yield (DGS10) from FRED...")
        yield_df = fetch_fred_series('DGS10')
        print(f"   -> 10Y Yield records: {len(yield_df)}")

        # 3. Commodities (Gold, Copper, Oil, Silver)
        print("Fetching Commodities (Gold, Copper, Oil, Silver) from FRED...")
        gold_df = fetch_fred_series('GOLDAMGBD228NLBM') 
        copper_df = fetch_fred_series('PCOPPUSDM') 
        oil_df = fetch_fred_series('DCOILWTICO') 
        silver_df = fetch_fred_series('SLVPRUSD') # Silver Price: London Fix

        # 4. Crypto (Buda)
        print("Fetching Crypto (BTC, ETH, XRP, SOL) from Buda.com...")
        btc_df = fetch_buda_series('btc-clp')
        eth_df = fetch_buda_series('eth-clp')
        xrp_df = fetch_buda_series('xrp-clp') # Mocked
        sol_df = fetch_buda_series('sol-clp') # Mocked
        
        # Combine
        macro_df = pd.concat([cpi_df, yield_df, gold_df, copper_df, oil_df, silver_df, btc_df, eth_df, xrp_df, sol_df], ignore_index=True)
        
        # Save
        macro_path = os.path.join('data', "market", "macro_indicators.parquet")
        macro_df.to_parquet(macro_path, index=False)
        print(f"   -> Macro data saved: {macro_path} ({len(macro_df)} records)")
        
    except Exception as e:
        print(f"ERROR step 4: {e}")

def save_to_db(ranking_df, macro_df):
    print("\n>>> Step 5: Save to Database (Postgres)")
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("   -> No DATABASE_URL found. Skipping DB save.")
        return

    try:
        engine = create_engine(db_url)
        
        # 1. Ranking
        # Add process_date if not exists (it was added in Step 2? No, let's ensure it)
        if 'process_date' not in ranking_df.columns:
            ranking_df['process_date'] = datetime.today().date()
            
        # Rename columns to match DB schema
        # DF has: institucion, producto, cta_anual_clp, cta_anual_uf, cta_anual_usd
        # DB has: institution, product, cost_clp, cost_uf, cost_usd
        ranking_db = ranking_df.rename(columns={
            'institucion': 'institution',
            'producto': 'product',
            'cta_anual_clp': 'cost_clp',
            'cta_anual_uf': 'cost_uf',
            'cta_anual_usd': 'cost_usd'
        })[['process_date', 'institution', 'product', 'cost_clp', 'cost_uf', 'cost_usd']]
        
        # Clear entries for today before inserting to avoid duplicates
        from sqlalchemy import text
        today_str = datetime.today().strftime('%Y-%m-%d')
        with engine.connect() as con:
            con.execute(text(f"DELETE FROM ranking WHERE process_date = '{today_str}'"))
            con.commit()
            
        ranking_db.to_sql('ranking', engine, if_exists='append', index=False)
        print(f"   -> Saved {len(ranking_db)} rows to 'ranking' table.")

        # 2. Macro Indicators
        # DF has: date, value, series_id, source
        # DB has same columns.
        
        # For macro, simpler to replace widely or upsert.
        # Given it fetches *all* history each time for now, 'replace' is acceptable for this prototype.
        macro_df.to_sql('macro_indicators', engine, if_exists='replace', index=False)
        print(f"   -> Saved {len(macro_df)} rows to 'macro_indicators' table.")

    except Exception as e:
        print(f"   -> Error saving to DB: {e}")

if __name__ == "__main__":
    # Step 1
    run_step_1_normalization()
    
    # Step 2
    # We load from disk, so no need to pass df
    df_rank = run_step_2_metrics() 
    
    # Step 3
    # Step 2 returns None? Let's check.
    # Actually, let's just run them sequentially and rely on file existence checks inside them.
    run_step_3_multicurrency()
    
    # Step 4
    run_step_4_macro()
    
    # Analytics
    run_analytics_step()
    
    # Save to DB
    print("\n>>> Saving to Database...")
    try:
        # Load necessary data for DB
        df_multi_path = 'metrics/atc_ranking_multi.parquet'
        macro_path = 'market/macro_indicators.parquet'
        
        # We need to construct absolute paths or use the load_parquet logic from valid steps
        # Simpler: just use pandas directly
        mp = os.path.join('data', 'metrics', 'atc_ranking_multi.parquet')
        macp = os.path.join('data', 'market', 'macro_indicators.parquet')
        
        if os.path.exists(mp) and os.path.exists(macp):
            df_multi = pd.read_parquet(mp)
            macro_df = pd.read_parquet(macp)
            save_to_db(df_multi, macro_df)
        else:
            print(f"Skipping DB save: Missing {mp} or {macp}")
            
    except Exception as e:
        print(f"Could not load data for DB save: {e}")
