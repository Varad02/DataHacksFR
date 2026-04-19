"""
GPU-accelerated XGBoost damage ratio model -- run on Brev L40s instance
Uses cuML for GPU acceleration (drop-in replacement for scikit-learn)

Setup on Brev instance:
    pip install cuml-cu12 xgboost --extra-index-url https://pypi.nvidia.com
    pip install pandas pyarrow scikit-learn matplotlib

Upload data:
    Copy property_risk_joined.parquet to the instance via JupyterLab file upload
"""

import pandas as pd
import numpy as np
import time

# ── Load data ──────────────────────────────────────────────────────────────
df = pd.read_parquet("property_risk_joined.parquet")
print(f"Loaded {len(df)} rows")

FEATURES = ["pgv", "pga", "arias_intensity"] if "arias_intensity" in df.columns else ["pgv", "pga"]
ERA_MAP = {"pre_1970": 0, "code_1973": 1, "code_1994": 2}

df["era_code"] = df.get("era", pd.Series(["code_1973"] * len(df))).map(ERA_MAP).fillna(1)
df["pga_g"] = df["pga"] / 9.81 * 11019  # scenario scaling

FEATURES = ["pga_g", "pgv", "era_code"]
TARGET = "damage_ratio"

df = df.dropna(subset=FEATURES + [TARGET])
X = df[FEATURES].values.astype(np.float32)
y = df[TARGET].values.astype(np.float32)

print(f"Feature matrix: {X.shape}")
print(f"Target range: {y.min():.4f} -- {y.max():.4f}")

# ── Train/test split ────────────────────────────────────────────────────────
from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# ── GPU XGBoost via cuML ────────────────────────────────────────────────────
print("\nTraining XGBoost on GPU...")
import xgboost as xgb

t0 = time.time()
model = xgb.XGBRegressor(
    n_estimators=500,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    tree_method="gpu_hist",   # GPU acceleration
    device="cuda",
    objective="reg:squarederror",
    eval_metric="rmse",
    early_stopping_rounds=20,
)
model.fit(
    X_train, y_train,
    eval_set=[(X_test, y_test)],
    verbose=50,
)
elapsed = time.time() - t0
print(f"\nTraining time: {elapsed:.1f}s")

# ── Evaluate ────────────────────────────────────────────────────────────────
from sklearn.metrics import mean_absolute_error, r2_score

y_pred = model.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print(f"\nTest MAE:  {mae:.4f}")
print(f"Test R2:   {r2:.4f}")
print(f"\nFeature importances:")
for feat, imp in zip(FEATURES, model.feature_importances_):
    print(f"  {feat}: {imp:.3f}")

# ── Save model ──────────────────────────────────────────────────────────────
model.save_model("xgb_damage_model.json")
print("\nSaved model to xgb_damage_model.json")

# ── Plot predictions vs actual ──────────────────────────────────────────────
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(6, 6))
ax.scatter(y_test, y_pred, alpha=0.3, s=10)
ax.plot([0, 1], [0, 1], "r--", lw=1)
ax.set_xlabel("Actual damage ratio")
ax.set_ylabel("Predicted damage ratio")
ax.set_title(f"XGBoost (GPU) -- R2={r2:.3f}, MAE={mae:.4f}")
plt.tight_layout()
plt.savefig("xgb_predictions.png", dpi=150)
print("Saved plot to xgb_predictions.png")
