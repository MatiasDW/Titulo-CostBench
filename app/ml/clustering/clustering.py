"""
Investor Clustering Module
K-Means clustering with optimal K selection via silhouette analysis.
"""
import json
import pickle
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from app.ml.config import CLUSTER_CONFIG
from app.ml.logging_utils import get_logger

logger = get_logger("ml.clustering")

# Scikit-learn imports
try:
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import silhouette_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("sklearn_not_available", message="Install scikit-learn for clustering")


@dataclass
class ClusteringResult:
    """Result of K-Means clustering."""
    n_clusters: int
    inertia: float
    silhouette_score: float
    centroids: list  # np.ndarray converted to list for serialization
    labels: list     # np.ndarray converted to list
    mapping: dict    # {cluster_id: profile_name}
    feature_names: list
    scaler_params: dict  # mean_ and scale_ from StandardScaler
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "ClusteringResult":
        return cls(**data)


def fit_investor_clusters(
    df: pd.DataFrame,
    k_range: tuple = None,
    features: list = None,
    random_seed: int = None
) -> ClusteringResult:
    """
    Fit K-Means with optimal K selection.
    
    Process:
        1. StandardScaler on features
        2. Fit K-Means for each k in k_range
        3. Compute inertia and silhouette for each
        4. Select k with best silhouette (or elbow)
        5. Map clusters to profiles by centroid analysis
        
    Args:
        df: DataFrame with investor features
        k_range: Range of k values to try
        features: Feature columns to use
        random_seed: Random seed for reproducibility
        
    Returns:
        ClusteringResult with model info and mappings
    """
    if not SKLEARN_AVAILABLE:
        raise ImportError("scikit-learn required for clustering")
    
    k_range = k_range or CLUSTER_CONFIG.k_range
    features = features or list(CLUSTER_CONFIG.features)
    random_seed = random_seed or CLUSTER_CONFIG.random_seed
    
    # Extract feature matrix
    X = df[features].values
    
    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Find optimal k
    best_k = 3  # Default
    best_silhouette = -1
    k_results = []
    
    for k in k_range:
        if k < 2 or k > len(X) - 1:
            continue
            
        kmeans = KMeans(n_clusters=k, random_state=random_seed, n_init=10)
        labels = kmeans.fit_predict(X_scaled)
        
        inertia = kmeans.inertia_
        sil_score = silhouette_score(X_scaled, labels)
        
        k_results.append({
            'k': k,
            'inertia': inertia,
            'silhouette': sil_score
        })
        
        logger.info(
            "k_evaluation",
            k=k,
            inertia=round(inertia, 2),
            silhouette=round(sil_score, 4)
        )
        
        if sil_score > best_silhouette:
            best_silhouette = sil_score
            best_k = k
    
    # Fit final model with best k
    final_kmeans = KMeans(n_clusters=best_k, random_state=random_seed, n_init=10)
    final_labels = final_kmeans.fit_predict(X_scaled)
    
    # Map clusters to profiles
    mapping = _map_clusters_to_profiles(
        final_kmeans.cluster_centers_,
        features,
        scaler
    )
    
    result = ClusteringResult(
        n_clusters=best_k,
        inertia=float(final_kmeans.inertia_),
        silhouette_score=float(best_silhouette),
        centroids=final_kmeans.cluster_centers_.tolist(),
        labels=final_labels.tolist(),
        mapping=mapping,
        feature_names=features,
        scaler_params={
            'mean': scaler.mean_.tolist(),
            'scale': scaler.scale_.tolist()
        }
    )
    
    logger.info(
        "clustering_complete",
        best_k=best_k,
        silhouette=round(best_silhouette, 4),
        mapping=mapping
    )
    
    return result


def _map_clusters_to_profiles(
    centroids: np.ndarray,
    features: list,
    scaler: StandardScaler
) -> dict:
    """
    Map cluster IDs to profile names based on centroid analysis.
    
    Logic:
        - Cluster with highest risk_tolerance -> aggressive
        - Cluster with lowest risk_tolerance -> conservative
        - Middle cluster(s) -> moderate
    """
    # Inverse transform centroids to original scale
    centroids_original = scaler.inverse_transform(centroids)
    
    # Find risk tolerance index
    try:
        risk_idx = features.index('risk_tolerance_1_10')
    except ValueError:
        # Fallback: use first feature
        risk_idx = 0
    
    # Get risk tolerance values for each centroid
    risk_values = centroids_original[:, risk_idx]
    
    # Sort clusters by risk tolerance
    sorted_clusters = np.argsort(risk_values)
    
    n_clusters = len(centroids)
    mapping = {}
    
    if n_clusters == 2:
        mapping[int(sorted_clusters[0])] = 'conservative'
        mapping[int(sorted_clusters[1])] = 'aggressive'
    elif n_clusters == 3:
        mapping[int(sorted_clusters[0])] = 'conservative'
        mapping[int(sorted_clusters[1])] = 'moderate'
        mapping[int(sorted_clusters[2])] = 'aggressive'
    else:
        # For more clusters, split into thirds
        third = n_clusters // 3
        for i, cluster_id in enumerate(sorted_clusters):
            if i < third:
                mapping[int(cluster_id)] = 'conservative'
            elif i < 2 * third:
                mapping[int(cluster_id)] = 'moderate'
            else:
                mapping[int(cluster_id)] = 'aggressive'
    
    return mapping


def predict_investor_profile(
    investor: dict,
    result: ClusteringResult
) -> dict:
    """
    Predict profile for a new investor.
    
    Args:
        investor: Dict with feature values
        result: ClusteringResult with centroids and scaler
        
    Returns:
        Dict with cluster_id and profile
    """
    if not SKLEARN_AVAILABLE:
        raise ImportError("scikit-learn required")
    
    # Extract features in correct order
    features = result.feature_names
    X = np.array([[investor.get(f, 0) for f in features]])
    
    # Scale using saved parameters
    scaler = StandardScaler()
    scaler.mean_ = np.array(result.scaler_params['mean'])
    scaler.scale_ = np.array(result.scaler_params['scale'])
    X_scaled = scaler.transform(X)
    
    # Find nearest centroid
    centroids = np.array(result.centroids)
    distances = np.linalg.norm(X_scaled - centroids, axis=1)
    cluster_id = int(np.argmin(distances))
    
    return {
        'cluster_id': cluster_id,
        'profile': result.mapping.get(cluster_id, 'moderate'),
        'distance_to_centroid': float(distances[cluster_id])
    }


def save_clustering_result(
    result: ClusteringResult,
    path: Path = Path("models/clustering/investor_clusters.json")
) -> None:
    """Save clustering result to JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(result.to_dict(), f, indent=2)
    
    logger.info("clustering_result_saved", path=str(path))


def load_clustering_result(
    path: Path = Path("models/clustering/investor_clusters.json")
) -> ClusteringResult:
    """Load clustering result from JSON file."""
    with open(path, 'r') as f:
        data = json.load(f)
    
    return ClusteringResult.from_dict(data)
