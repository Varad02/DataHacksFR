"""Extract PGV, PGA, and Arias intensity from Scripps seismograms.

Data shape: (n_receivers, n_timesteps, n_sources)
  - east-component velocity in m/s
  - 10 Hz sampling (dt = 0.1 s), 600 timesteps = 60 s
  - 500 source locations (fault-plane coords in source_locations.csv)
"""

import numpy as np
import pandas as pd

DT = 0.1  # seconds, 10 Hz sampling


def compute_pgv(velocity: np.ndarray) -> float:
    return float(np.max(np.abs(velocity)))


def compute_pga(velocity: np.ndarray, dt: float = DT) -> float:
    acceleration = np.gradient(velocity, dt)
    return float(np.max(np.abs(acceleration)))


def compute_arias_intensity(velocity: np.ndarray, dt: float = DT) -> float:
    g = 9.81
    acceleration = np.gradient(velocity, dt)
    return float((np.pi / (2 * g)) * np.trapezoid(acceleration**2, dx=dt))


def extract_features(
    seismograms: np.ndarray,
    dt: float = DT,
) -> pd.DataFrame:
    """
    Extract PGV, PGA, Arias intensity for all (receiver, source) pairs.

    Parameters
    ----------
    seismograms : np.ndarray, shape (n_receivers, n_timesteps, n_sources)

    Returns
    -------
    DataFrame with columns: receiver_id, source_id, pgv, pga, arias_intensity
    """
    n_receivers, n_timesteps, n_sources = seismograms.shape
    records = []

    for r in range(n_receivers):
        for s in range(n_sources):
            trace = seismograms[r, :, s]
            records.append({
                "receiver_id": r,
                "source_id": s,
                "pgv": compute_pgv(trace),
                "pga": compute_pga(trace, dt),
                "arias_intensity": compute_arias_intensity(trace, dt),
            })

    return pd.DataFrame(records)
