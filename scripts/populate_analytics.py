import os
import sys
import pandas as pd
import json
from datetime import datetime

# Setup
os.makedirs('data/analytics', exist_ok=True)

def run_analytics_step():
    print("\n>>> Running Analytics Calculation Step...")
    
    # 1. Load Ranking Data
    ranking_path = 'data/metrics/atc_ranking.parquet'
    if not os.path.exists(ranking_path):
        print("   ⚠️ Ranking data not found. Skipping.")
        return

    df = pd.read_parquet(ranking_path)
    print(f"   -> Loaded {len(df)} records from {ranking_path}")

    # 2. Market Composition (Pie Chart Data)
    # Group by Institution Type (inferred from name or manually mapped)
    # Simple Logic: Map known banks to 'Bank', others to 'Cooperative' or 'Retail'
    
    def classify_inst(name):
        name = name.upper()
        if 'BANCO' in name or 'BICE' in name or 'SCOTIABANK' in name:
            return 'Traditional Bank'
        if 'COO' in name or 'COOPERATIVA' in name:
            return 'Cooperative'
        return 'Retail / Modern'

    df['type'] = df['institucion'].apply(classify_inst)
    
    # Composition by Type
    comp = df['type'].value_counts().reset_index()
    comp.columns = ['type', 'count']
    
    # Save as JSON for frontend
    comp_data = comp.to_dict('records')
    
    # 3. Cost Efficiency by Type (Avg Cost by Type)
    # Assuming 'cta_anual_clp' exists
    if 'cta_anual_clp' in df.columns:
        efficiency = df.groupby('type')['cta_anual_clp'].mean().reset_index()
        efficiency.columns = ['type', 'avg_cost']
        eff_data = efficiency.to_dict('records')
    else:
        eff_data = []

    analytics_payload = {
        'generated_at': datetime.now().isoformat(),
        'market_composition': comp_data,
        'cost_efficiency': eff_data
    }
    
    out_path = 'data/analytics/dashboard_insights.json'
    with open(out_path, 'w') as f:
        json.dump(analytics_payload, f, indent=2)
    
    print(f"   -> Analytics saved to {out_path}")

if __name__ == "__main__":
    run_analytics_step()
