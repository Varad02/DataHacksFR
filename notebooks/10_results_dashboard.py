import marimo

__generated_with = "0.23.1"
app = marimo.App()


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import matplotlib.pyplot as plt
    import seaborn as sns
    from pathlib import Path
    import sys

    ROOT = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(ROOT))

    from src.models.scenario_cases import SCENARIOS, simulate_scenario

    sns.set_theme(style="whitegrid")
    return ROOT, SCENARIOS, mo, pd, plt, simulate_scenario


@app.cell
def _(mo):
    mo.md(
        """
        # Results and Test Dashboard

        Submission-oriented dashboard for:
        - Scenario comparison (Northridge, +7y dummy)
        - Training metrics snapshot
        - Test status from artifacts
        """
    )
    return


@app.cell
def _(ROOT, pd):
    data_path = ROOT / "data/processed/property_risk_joined.parquet"
    df = pd.read_parquet(data_path)

    base = pd.DataFrame(
        {
            "tract": df["tract"].astype(str),
            "era": df["era"].fillna("code_1973"),
            "pga_g_raw": pd.to_numeric(df["pga_g_raw"], errors="coerce"),
            "home_value": pd.to_numeric(df["home_value_final"], errors="coerce"),
            "median_income": pd.to_numeric(df["median_income"], errors="coerce"),
        }
    )
    base["home_value"] = base["home_value"].fillna(500000)
    base["pga_g_raw"] = base["pga_g_raw"].fillna(base["pga_g_raw"].median())
    base["median_income"] = base["median_income"].fillna(base["median_income"].median())
    base = base.dropna(subset=["era", "pga_g_raw", "home_value"])
    base.head()
    return (base,)


@app.cell
def _(SCENARIOS, base, pd, simulate_scenario):
    outputs = {}
    rows = []

    for name, profile in SCENARIOS.items():
        out = simulate_scenario(base, profile)
        outputs[name] = out
        rows.append(
            {
                "scenario": name,
                "n_tracts": int(len(out)),
                "mean_expected_loss": float(out["expected_loss"].mean()),
                "median_expected_loss": float(out["expected_loss"].median()),
                "p95_expected_loss": float(out["expected_loss"].quantile(0.95)),
                "mean_damage_ratio": float(out["damage_ratio"].mean()),
                "max_pga_g": float(out["pga_g"].max()),
            }
        )

    summary = pd.DataFrame(rows).sort_values("scenario")
    summary
    return outputs, summary


@app.cell
def _(plt, summary):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(summary["scenario"], summary["mean_expected_loss"], color="#E31A1C")
    ax.set_title("Mean Expected Loss by Scenario")
    ax.set_ylabel("USD per household")
    ax.tick_params(axis="x", rotation=15)
    plt.tight_layout()
    fig
    return


@app.cell
def _(outputs, plt):
    keys = sorted(outputs.keys())
    data = [outputs[k]["expected_loss"].values for k in keys]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.boxplot(data, tick_labels=keys, showfliers=False)
    ax.set_title("Expected Loss Distribution by Scenario")
    ax.set_ylabel("USD per household")
    ax.tick_params(axis="x", rotation=15)
    plt.tight_layout()
    fig
    return


@app.cell
def _(outputs, plt):
    northridge = outputs["northridge_1994"].copy()
    top = northridge.nlargest(10, "expected_loss")[["tract", "expected_loss"]]

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh(top["tract"], top["expected_loss"], color="#BD0026")
    ax.invert_yaxis()
    ax.set_title("Top 10 Tracts by Expected Loss (Northridge)")
    ax.set_xlabel("USD per household")
    plt.tight_layout()
    fig
    return


@app.cell
def _(ROOT, mo, pd):
    metrics_path = ROOT / "artifacts/xgb_metrics.json"
    tests_path = ROOT / "artifacts/test_results.txt"

    metrics = {}
    if metrics_path.exists():
        import json

        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))

    tests_text = tests_path.read_text(encoding="utf-8") if tests_path.exists() else "test_results.txt not found"

    md = f"""
    ## Runtime Status

    - Model metrics file: {'found' if metrics_path.exists() else 'missing'}
    - Test log file: {'found' if tests_path.exists() else 'missing'}
    - MAE: {metrics.get('mae', 'N/A')}
    - R2: {metrics.get('r2', 'N/A')}
    - Runtime: {metrics.get('runtime', 'N/A')}

    ### Test Log (first lines)

    ```text
    {chr(10).join(tests_text.splitlines()[:20])}
    ```
    """
    mo.md(md)
    return


if __name__ == "__main__":
    app.run()
