"""Translate damage ratios and property values into dollar loss estimates."""

import numpy as np
import pandas as pd


def expected_loss_per_property(
    damage_ratio: np.ndarray,
    home_value: np.ndarray,
    structural_fraction: float = 0.85,
) -> np.ndarray:
    """
    Expected dollar loss = damage_ratio * structural_value.

    structural_fraction: portion of home value that is structural (vs. land).
    HAZUS default for SoCal urban is ~0.85.
    """
    return damage_ratio * home_value * structural_fraction


def aggregate_by_geography(df: pd.DataFrame, geo_col: str) -> pd.DataFrame:
    """
    Aggregate expected loss to tract or ZIP level.

    df must have columns: [geo_col, expected_loss, home_value, income_decile]
    """
    return (
        df.groupby(geo_col)
        .agg(
            total_expected_loss=("expected_loss", "sum"),
            mean_loss_per_household=("expected_loss", "mean"),
            median_home_value=("home_value", "median"),
            n_properties=("expected_loss", "count"),
        )
        .reset_index()
    )


def loss_by_income_decile(df: pd.DataFrame) -> pd.DataFrame:
    """Distributional view: mean loss per household by income decile."""
    df = df.copy()
    df["income_decile"] = pd.qcut(df["median_income"], q=10, labels=False)
    return (
        df.groupby("income_decile")
        .agg(mean_loss=("expected_loss", "mean"), n=("expected_loss", "count"))
        .reset_index()
    )
