"""XGBoost baseline: predict damage ratio from shaking + building features."""

import numpy as np
import pandas as pd


FEATURES = ["pgv", "pga", "arias_intensity", "year_built", "distance_to_fault_km"]
TARGET = "damage_ratio"


def build_feature_matrix(df: pd.DataFrame) -> tuple[np.ndarray, list[str]]:
    cols = [c for c in FEATURES if c in df.columns]
    return df[cols].values, cols


def train(df: pd.DataFrame):
    try:
        import xgboost as xgb
    except ImportError:
        raise ImportError("pip install xgboost")

    X, feature_cols = build_feature_matrix(df)
    y = df[TARGET].values

    model = xgb.XGBRegressor(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="reg:squarederror",
        n_jobs=-1,
    )
    model.fit(X, y)
    return model, feature_cols


def predict(model, df: pd.DataFrame, feature_cols: list[str]) -> np.ndarray:
    return model.predict(df[feature_cols].values)
