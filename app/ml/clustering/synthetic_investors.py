"""
Synthetic Investor Data Generator
Generates labeled dataset for clustering validation.
"""
from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd

from app.ml.config import CLUSTER_CONFIG


def generate_synthetic_investors(
    n: int = 1000,
    seed: int = None
) -> pd.DataFrame:
    """
    Generate labeled investor dataset for clustering validation.
    
    Features:
        - investment_horizon_years: Uniform(1, 30)
        - loss_capacity_pct: Beta(2, 5) * 50 (skewed low)
        - risk_tolerance_1_10: Normal(5, 2), clipped [1, 10]
        - experience_years: Exponential(λ=0.2), clipped [0, 40]
        
    Labels (for validation only):
        - profile: Derived from rules (conservative, moderate, aggressive)
        
    Args:
        n: Number of synthetic investors
        seed: Random seed for reproducibility
        
    Returns:
        DataFrame with features and derived labels
    """
    seed = seed or CLUSTER_CONFIG.random_seed
    np.random.seed(seed)
    
    # Generate features with different distributions
    data = {
        'investment_horizon_years': np.random.uniform(1, 30, n),
        'loss_capacity_pct': np.random.beta(2, 5, n) * 50,  # Skewed towards low
        'risk_tolerance_1_10': np.clip(np.random.normal(5, 2, n), 1, 10),
        'experience_years': np.clip(np.random.exponential(5, n), 0, 40)
    }
    
    df = pd.DataFrame(data)
    
    # Derive profile labels based on rules
    df['profile'] = df.apply(_derive_profile, axis=1)
    
    # Add some noise to make clustering more realistic
    # Slightly correlate features
    df['investment_horizon_years'] = df['investment_horizon_years'] + \
        0.3 * (df['risk_tolerance_1_10'] - 5)  # Higher risk tolerance -> longer horizon
    df['investment_horizon_years'] = df['investment_horizon_years'].clip(1, 35)
    
    df['loss_capacity_pct'] = df['loss_capacity_pct'] + \
        0.5 * df['experience_years']  # More experience -> can handle more loss
    df['loss_capacity_pct'] = df['loss_capacity_pct'].clip(0, 50)
    
    return df


def _derive_profile(row: pd.Series) -> str:
    """
    Derive investor profile from feature values.
    
    Rules:
        - Conservative: Low risk tolerance OR short horizon AND low loss capacity
        - Aggressive: High risk tolerance AND long horizon AND high loss capacity
        - Moderate: Everything else
    """
    horizon = row['investment_horizon_years']
    loss_cap = row['loss_capacity_pct']
    risk_tol = row['risk_tolerance_1_10']
    experience = row['experience_years']
    
    # Conservative criteria
    if risk_tol < 4 or (horizon < 5 and loss_cap < 10):
        return 'conservative'
    
    # Aggressive criteria
    if risk_tol > 7 and horizon > 15 and loss_cap > 25:
        return 'aggressive'
    
    # Moderate is default
    return 'moderate'


def get_feature_statistics(df: pd.DataFrame) -> dict:
    """
    Get summary statistics for clustering features.
    
    Args:
        df: DataFrame with investor features
        
    Returns:
        Dict with mean, std, min, max per feature
    """
    features = list(CLUSTER_CONFIG.features)
    stats = {}
    
    for feature in features:
        if feature in df.columns:
            stats[feature] = {
                'mean': df[feature].mean(),
                'std': df[feature].std(),
                'min': df[feature].min(),
                'max': df[feature].max(),
                'median': df[feature].median()
            }
    
    return stats


def validate_profile_distribution(df: pd.DataFrame) -> dict:
    """
    Check distribution of derived profiles.
    
    Returns:
        Dict with profile counts and percentages
    """
    if 'profile' not in df.columns:
        return {}
    
    counts = df['profile'].value_counts()
    total = len(df)
    
    return {
        profile: {
            'count': count,
            'percentage': round(count / total * 100, 1)
        }
        for profile, count in counts.items()
    }
