"""Scenario utilities for deterministic earthquake stress tests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd

from src.damage.hazus import damage_ratio
from src.economic.loss import expected_loss_per_property


@dataclass(frozen=True)
class ScenarioProfile:
    """Named scenario controls for tract-level stress testing."""

    name: str
    max_pga_g: float
    retrofit_multiplier: float
    home_value_multiplier: float


SCENARIOS: dict[str, ScenarioProfile] = {
    "northridge_1994": ScenarioProfile(
        name="northridge_1994",
        max_pga_g=0.65,
        retrofit_multiplier=1.0,
        home_value_multiplier=1.0,
    ),
    "dummy_next_7y": ScenarioProfile(
        name="dummy_next_7y",
        max_pga_g=0.48,
        retrofit_multiplier=0.90,
        home_value_multiplier=1.12,
    ),
}


def _scaled_pga(base_pga_g: Iterable[float], max_target: float) -> np.ndarray:
    values = np.asarray(base_pga_g, dtype=float)
    max_raw = max(values.max(), 1e-6)
    return (values / max_raw) * max_target


def simulate_scenario(
    df: pd.DataFrame,
    profile: ScenarioProfile,
    structural_fraction: float = 0.85,
) -> pd.DataFrame:
    """Return tract-level losses under a scenario profile.

    Required columns: tract, era, pga_g_raw, home_value
    """
    required = {"tract", "era", "pga_g_raw", "home_value"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    out = df.copy()
    out["pga_g"] = _scaled_pga(out["pga_g_raw"].values, profile.max_pga_g)
    out["damage_ratio"] = out.apply(
        lambda r: float(damage_ratio(np.array([r["pga_g"]]), str(r["era"]))[0]),
        axis=1,
    )

    adjusted_damage = out["damage_ratio"].values * profile.retrofit_multiplier
    adjusted_damage = np.clip(adjusted_damage, 0.0, 1.0)
    adjusted_home_value = out["home_value"].values * profile.home_value_multiplier

    out["expected_loss"] = expected_loss_per_property(
        adjusted_damage,
        adjusted_home_value,
        structural_fraction=structural_fraction,
    )

    return out
