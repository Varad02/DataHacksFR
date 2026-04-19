"""Spatial interpolation of shaking metrics from receivers to arbitrary coordinates."""

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree


def nearest_receiver(
    query_lats: np.ndarray,
    query_lons: np.ndarray,
    receiver_lats: np.ndarray,
    receiver_lons: np.ndarray,
    receiver_ids=None,
) -> pd.DataFrame:
    """
    Assign each query point (property/tract centroid) its nearest receiver.

    Returns DataFrame with columns: query_idx, receiver_id, distance_km
    """
    # Simple Euclidean distance in lat/lon degrees (sufficient for SoCal scale)
    receiver_coords = np.column_stack([receiver_lats, receiver_lons])
    query_coords = np.column_stack([query_lats, query_lons])

    tree = cKDTree(receiver_coords)
    distances, indices = tree.query(query_coords)

    if receiver_ids is None:
        receiver_ids = np.arange(len(receiver_lats))

    return pd.DataFrame({
        "query_idx": np.arange(len(query_lats)),
        "receiver_id": np.array(receiver_ids)[indices],
        "distance_deg": distances,
    })
