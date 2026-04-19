"""Generate submission-ready results and visuals for scenario tests."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src.models.scenario_cases import SCENARIOS, simulate_scenario

DATA_PATH = ROOT / "data/processed/property_risk_joined.parquet"
ARTIFACTS = ROOT / "artifacts"
FIG_DIR = ARTIFACTS / "figures"
METRICS_PATH = ARTIFACTS / "xgb_metrics.json"
REPORT_PATH = ARTIFACTS / "SUBMISSION_RESULTS.md"


def _prepare_base_dataframe() -> pd.DataFrame:
    df = pd.read_parquet(DATA_PATH)
    out = pd.DataFrame()
    out["tract"] = df["tract"].astype(str)
    out["era"] = df["era"].fillna("code_1973")
    out["pga_g_raw"] = pd.to_numeric(df["pga_g_raw"], errors="coerce")
    out["home_value"] = pd.to_numeric(df["home_value_final"], errors="coerce")

    if "median_home_value_acs" in df.columns:
        fallback = pd.to_numeric(df["median_home_value_acs"], errors="coerce")
        out["home_value"] = out["home_value"].fillna(fallback)

    out["home_value"] = out["home_value"].fillna(500_000)
    out["pga_g_raw"] = out["pga_g_raw"].fillna(out["pga_g_raw"].median())
    return out.dropna(subset=["era", "pga_g_raw", "home_value"])


def _run_scenarios(base_df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    scenario_outputs: dict[str, pd.DataFrame] = {}
    summary_rows = []

    for name, profile in SCENARIOS.items():
        result = simulate_scenario(base_df, profile)
        scenario_outputs[name] = result
        summary_rows.append(
            {
                "scenario": name,
                "n_tracts": int(len(result)),
                "mean_expected_loss": float(result["expected_loss"].mean()),
                "median_expected_loss": float(result["expected_loss"].median()),
                "p95_expected_loss": float(result["expected_loss"].quantile(0.95)),
                "max_expected_loss": float(result["expected_loss"].max()),
                "mean_damage_ratio": float(result["damage_ratio"].mean()),
                "max_pga_g": float(result["pga_g"].max()),
            }
        )

    summary_df = pd.DataFrame(summary_rows).sort_values("scenario")
    return summary_df, scenario_outputs


def _save_visuals(summary_df: pd.DataFrame, scenario_outputs: dict[str, pd.DataFrame]) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    # 1) Mean expected loss by scenario
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(summary_df["scenario"], summary_df["mean_expected_loss"])
    ax.set_title("Mean Expected Loss by Scenario")
    ax.set_xlabel("Scenario")
    ax.set_ylabel("Expected Loss per Household (USD)")
    ax.tick_params(axis="x", rotation=15)
    plt.tight_layout()
    plt.savefig(FIG_DIR / "mean_expected_loss_by_scenario.png", dpi=160)
    plt.close(fig)

    # 2) Distribution (boxplot) of expected loss across scenarios
    fig, ax = plt.subplots(figsize=(8, 5))
    data = [scenario_outputs[k]["expected_loss"].values for k in sorted(scenario_outputs.keys())]
    labels = sorted(scenario_outputs.keys())
    ax.boxplot(data, tick_labels=labels, showfliers=False)
    ax.set_title("Expected Loss Distribution by Scenario")
    ax.set_ylabel("Expected Loss per Household (USD)")
    ax.tick_params(axis="x", rotation=15)
    plt.tight_layout()
    plt.savefig(FIG_DIR / "expected_loss_boxplot_by_scenario.png", dpi=160)
    plt.close(fig)

    # 3) Northridge top 10 tracts
    northridge = scenario_outputs["northridge_1994"].copy()
    top10 = northridge.nlargest(10, "expected_loss")[ ["tract", "expected_loss"] ]
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(top10["tract"], top10["expected_loss"])
    ax.invert_yaxis()
    ax.set_title("Top 10 Tracts by Expected Loss (Northridge Scenario)")
    ax.set_xlabel("Expected Loss per Household (USD)")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "northridge_top10_tracts.png", dpi=160)
    plt.close(fig)

    # 4) Damage ratio by era in Northridge scenario
    era_summary = (
        northridge.groupby("era", as_index=False)["damage_ratio"]
        .mean()
        .sort_values("damage_ratio", ascending=False)
    )
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.bar(era_summary["era"], era_summary["damage_ratio"])
    ax.set_title("Mean Damage Ratio by Building Era (Northridge)")
    ax.set_xlabel("Era")
    ax.set_ylabel("Mean Damage Ratio")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "northridge_damage_ratio_by_era.png", dpi=160)
    plt.close(fig)


def _load_metrics() -> dict:
    if METRICS_PATH.exists():
        return json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    return {}


def _write_report(summary_df: pd.DataFrame, metrics: dict) -> None:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    summary_csv = ARTIFACTS / "scenario_test_summary.csv"
    summary_df.to_csv(summary_csv, index=False)

    lines = []
    lines.append("# Submission Results")
    lines.append("")
    lines.append("## Scenario Test Results")
    lines.append("")
    headers = list(summary_df.columns)
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("|" + "|".join(["---"] * len(headers)) + "|")
    for _, row in summary_df.iterrows():
        vals = [str(row[h]) for h in headers]
        lines.append("| " + " | ".join(vals) + " |")
    lines.append("")

    lines.append("## Visuals")
    lines.append("")
    lines.append("- figures/mean_expected_loss_by_scenario.png")
    lines.append("- figures/expected_loss_boxplot_by_scenario.png")
    lines.append("- figures/northridge_top10_tracts.png")
    lines.append("- figures/northridge_damage_ratio_by_era.png")
    lines.append("")

    lines.append("## Model Training Smoke Metrics")
    lines.append("")
    if metrics:
        lines.append(f"- MAE: {metrics.get('mae'):.5f}")
        lines.append(f"- R2: {metrics.get('r2'):.5f}")
        lines.append(f"- Training seconds: {metrics.get('train_seconds'):.2f}")
        lines.append(f"- Runtime: {metrics.get('runtime')}")
    else:
        lines.append("- xgb_metrics.json not found. Run brev/train_xgboost_gpu.py first.")

    lines.append("")
    lines.append("## Test Command")
    lines.append("")
    lines.append("```bash")
    lines.append("source venv/bin/activate")
    lines.append("python -m unittest discover -s tests -p \"test_*.py\" -v")
    lines.append("```")

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    base = _prepare_base_dataframe()
    summary_df, outputs = _run_scenarios(base)
    _save_visuals(summary_df, outputs)
    metrics = _load_metrics()
    _write_report(summary_df, metrics)
    print(f"Wrote report: {REPORT_PATH}")
    print(f"Wrote figures: {FIG_DIR}")


if __name__ == "__main__":
    main()
