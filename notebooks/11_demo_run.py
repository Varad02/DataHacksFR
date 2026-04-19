import marimo

__generated_with = "0.23.1"
app = marimo.App()


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import matplotlib.pyplot as plt
    import sys
    from pathlib import Path

    ROOT = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(ROOT))

    from src.models.scenario_cases import SCENARIOS, simulate_scenario

    plt.style.use("seaborn-v0_8-whitegrid")
    return ROOT, SCENARIOS, mo, pd, plt, simulate_scenario


@app.cell
def _(mo):
    mo.md("""
    # DataHacksFR Demo Run

    This notebook is the fastest way to understand the project in one place.

    It shows:
    - a real past earthquake stress test (`northridge_1994`)
    - a dummy forward-looking case (`dummy_next_7y`)
    - summary charts from the processed tract-level data

    Run it with:
    ```bash
    python demo_marimo.py --step 11
    ```
    """)
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
            "median_year_built": pd.to_numeric(df["median_year_built"], errors="coerce"),
        }
    )
    base["home_value"] = base["home_value"].fillna(500000)
    base["pga_g_raw"] = base["pga_g_raw"].fillna(base["pga_g_raw"].median())
    base["median_income"] = base["median_income"].fillna(base["median_income"].median())
    base["median_year_built"] = base["median_year_built"].fillna(base["median_year_built"].median())
    base = base.dropna(subset=["era", "pga_g_raw", "home_value"])

    base.head(8)
    return (base,)


@app.cell
def _(SCENARIOS, base, pd, simulate_scenario):
    outputs = {}
    rows = []

    for scenario_name in ["northridge_1994", "dummy_next_7y"]:
        profile = SCENARIOS[scenario_name]
        out = simulate_scenario(base, profile)
        outputs[scenario_name] = out
        rows.append(
            {
                "scenario": scenario_name,
                "n_tracts": int(len(out)),
                "mean_expected_loss": float(out["expected_loss"].mean()),
                "median_expected_loss": float(out["expected_loss"].median()),
                "p95_expected_loss": float(out["expected_loss"].quantile(0.95)),
                "mean_damage_ratio": float(out["damage_ratio"].mean()),
                "max_pga_g": float(out["pga_g"].max()),
            }
        )

    summary = pd.DataFrame(rows)
    summary
    return outputs, summary


@app.cell
def _(plt, summary):
    def _():
        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.bar(summary["scenario"], summary["mean_expected_loss"], color=["#BD0026", "#E31A1C"])
        ax.set_title("Mean Expected Loss by Demo Scenario")
        ax.set_ylabel("USD per household")
        ax.tick_params(axis="x", rotation=15)
        plt.tight_layout()
        return fig


    _()
    return


@app.cell
def _(outputs, plt):
    def _():
        labels = ["northridge_1994", "dummy_next_7y"]
        data = [outputs[label]["expected_loss"].values for label in labels]

        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.boxplot(data, tick_labels=labels, showfliers=False)
        ax.set_title("Expected Loss Distribution by Demo Scenario")
        ax.set_ylabel("USD per household")
        ax.tick_params(axis="x", rotation=15)
        plt.tight_layout()
        return fig


    _()
    return


@app.cell
def _(outputs, plt):
    northridge = outputs["northridge_1994"].copy()
    top = northridge.nlargest(10, "expected_loss")[ ["tract", "expected_loss"] ]

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh(top["tract"], top["expected_loss"], color="#800026")
    ax.invert_yaxis()
    ax.set_title("Top 10 Tracts by Expected Loss (Northridge)")
    ax.set_xlabel("USD per household")
    plt.tight_layout()
    fig
    return


@app.cell
def _(ROOT, mo):
    map_path = ROOT / "app/risk_data.geojson"
    api_path = ROOT / "api/explain.py"
    docs_path = ROOT / "docs/index.rst"

    mo.md(
        f"""
        ## Where to see the implementation

        - Frontend map: `app/index.html` and `app/main.js`
        - API summary service: `api/explain.py`
        - Scenario math: `src/models/scenario_cases.py`
        - Sphinx docs: `docs/index.rst`
        - Demo map data: `{map_path}`

        ## Status check

        - Map data exists: {'yes' if map_path.exists() else 'no'}
        - API exists: {'yes' if api_path.exists() else 'no'}
        - Docs exist: {'yes' if docs_path.exists() else 'no'}
        """
    )
    return


if __name__ == "__main__":
    app.run()
