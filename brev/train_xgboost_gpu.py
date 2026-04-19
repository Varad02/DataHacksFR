"""Train XGBoost for damage ratio on Brev GPU (with CPU fallback).

Example usage on Brev:
    python brev/train_xgboost_gpu.py \
      --input data/processed/property_risk_joined.parquet \
      --output-dir artifacts
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split


ERA_MAP = {"pre_1970": 0, "code_1973": 1, "code_1994": 2}
TARGET = "damage_ratio"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train XGBoost damage model on Brev GPU")
    parser.add_argument("--input", type=Path, required=True, help="Parquet input file")
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts"), help="Output directory")
    parser.add_argument("--test-size", type=float, default=0.2, help="Test split ratio")
    parser.add_argument("--random-state", type=int, default=42, help="Random state")
    parser.add_argument("--n-estimators", type=int, default=500, help="Number of boosting rounds")
    parser.add_argument("--max-depth", type=int, default=6, help="Tree max depth")
    parser.add_argument("--learning-rate", type=float, default=0.05, help="Learning rate")
    parser.add_argument("--subsample", type=float, default=0.8, help="Row subsample")
    parser.add_argument("--colsample-bytree", type=float, default=0.8, help="Feature subsample")
    parser.add_argument(
        "--prefer-gpu",
        action="store_true",
        help="Prefer CUDA training when GPU-enabled XGBoost is available",
    )
    parser.add_argument(
        "--scale-factor",
        type=float,
        default=11019.0,
        help="Scale factor for pga_g = (pga/9.81) * scale_factor",
    )
    return parser.parse_args()


def build_features(df: pd.DataFrame, scale_factor: float) -> tuple[np.ndarray, np.ndarray, list[str]]:
    era_series = df.get("era", pd.Series(["code_1973"] * len(df)))
    df = df.copy()
    df["era_code"] = era_series.map(ERA_MAP).fillna(1).astype(np.float32)
    df["pga_g"] = (df["pga"] / 9.81) * scale_factor

    features = ["pga_g", "pgv", "era_code"]
    missing = [c for c in features + [TARGET] if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    clean = df.dropna(subset=features + [TARGET])
    x = clean[features].values.astype(np.float32)
    y = clean[TARGET].values.astype(np.float32)
    return x, y, features


def choose_xgb_runtime(prefer_gpu: bool) -> dict:
    if prefer_gpu:
        # For XGBoost>=2.0, device='cuda' is the preferred path.
        return {"tree_method": "hist", "device": "cuda"}
    return {"tree_method": "hist", "device": "cpu"}


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading input: {args.input}")
    df = pd.read_parquet(args.input)
    print(f"Loaded rows: {len(df)}")

    x, y, features = build_features(df, scale_factor=args.scale_factor)
    print(f"Feature matrix: {x.shape}")
    print(f"Target range: {y.min():.4f} -- {y.max():.4f}")

    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=args.test_size,
        random_state=args.random_state,
    )

    runtime = choose_xgb_runtime(prefer_gpu=args.prefer_gpu)
    print(f"Training runtime: {runtime}")

    model = xgb.XGBRegressor(
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
        learning_rate=args.learning_rate,
        subsample=args.subsample,
        colsample_bytree=args.colsample_bytree,
        objective="reg:squarederror",
        eval_metric="rmse",
        early_stopping_rounds=20,
        **runtime,
    )

    t0 = time.time()
    model.fit(
        x_train,
        y_train,
        eval_set=[(x_test, y_test)],
        verbose=False,
    )
    elapsed = time.time() - t0

    y_pred = model.predict(x_test)
    mae = float(mean_absolute_error(y_test, y_pred))
    r2 = float(r2_score(y_test, y_pred))

    print(f"Training time: {elapsed:.2f}s")
    print(f"Test MAE: {mae:.5f}")
    print(f"Test R2:  {r2:.5f}")

    model_path = args.output_dir / "xgb_damage_model.json"
    model.save_model(model_path)

    metrics = {
        "rows": int(len(df)),
        "train_rows": int(len(x_train)),
        "test_rows": int(len(x_test)),
        "mae": mae,
        "r2": r2,
        "train_seconds": elapsed,
        "features": features,
        "runtime": runtime,
        "feature_importances": {
            feat: float(imp) for feat, imp in zip(features, model.feature_importances_)
        },
        "model_path": str(model_path),
    }

    metrics_path = args.output_dir / "xgb_metrics.json"
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"Saved model: {model_path}")
    print(f"Saved metrics: {metrics_path}")


if __name__ == "__main__":
    main()
