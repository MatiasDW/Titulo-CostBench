import os
import sys
from dotenv import load_dotenv
import pandas as pd

# Load env
load_dotenv()

# Add project root to path
sys.path.append(os.path.abspath('.'))

from app.services.fred import fetch_fred_series
from app.services.crypto import fetch_crypto_price

def verify_apis():
    print("🔎 Verifying API Connections...\n")

    # 1. FRED Verification
    fred_key = os.getenv('FRED_API_KEY')
    print(f"🇺🇸 FRED API Key found: {'Yes' if fred_key else 'No'}")
    
    fred_series = ['CPIAUCSL', 'GOLDAMGBD228NLBM', 'PCOPPUSDM', 'DCOILWTICO']
    for sid in fred_series:
        try:
            df = fetch_fred_series(sid)
            latest = df.iloc[-1] if not df.empty else None
            val = latest['value'] if latest is not None else 'N/A'
            src = latest['source'] if latest is not None else 'N/A'
            print(f"   - {sid}: {val} (Source: {src})")
        except Exception as e:
            print(f"   - {sid}: ❌ Error ({e})")

    print("\n--------------------------------\n")

    # 2. Buda.com Verification (Crypto)
    print("🇨🇱 Buda.com API (Public)...")
    crypto_pairs = ['btc-clp', 'eth-clp', 'xrp-clp', 'sol-clp']
    
    for pair in crypto_pairs:
        try:
            data = fetch_crypto_price(pair)
            if data:
                print(f"   - {pair}: ${data['value']:,.0f} CLP (Source: {data['source']})")
            else:
                print(f"   - {pair}: ⚠️ No Data / Not Supported natively (Will use Mock)")
        except Exception as e:
            print(f"   - {pair}: ❌ Error ({e})")

if __name__ == "__main__":
    verify_apis()
