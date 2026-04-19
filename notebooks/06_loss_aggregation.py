import marimo

__generated_with = "0.23.1"
app = marimo.App()


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import numpy as np
    import sys
    from pathlib import Path
    ROOT = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(ROOT))
    from src.economic.loss import expected_loss_per_property, aggregate_by_geography, loss_by_income_decile

    return (
        ROOT,
        aggregate_by_geography,
        expected_loss_per_property,
        loss_by_income_decile,
        mo,
        pd,
    )


@app.cell
def _(mo):
    mo.md("""
    ## 06 -- Expected Dollar Loss per Household
    """)
    return


@app.cell
def _(ROOT, expected_loss_per_property, pd):
    df = pd.read_parquet(ROOT / "data/processed/property_risk_joined.parquet")

    CENSUS_NULL = -666666666

    # Use home_value_final (ZHVI where available, ACS fallback) set by notebook 08
    # Fall back to ACS if notebook 08 hasn't run yet
    if "home_value_final" in df.columns:
        df["home_value"] = df["home_value_final"]
    else:
        df["home_value"] = (
            pd.to_numeric(df["median_home_value_acs"], errors="coerce")
            .replace(CENSUS_NULL, float("nan"))
            .fillna(500_000)
        )
    df["median_income"] = (
        pd.to_numeric(df["median_income"], errors="coerce")
        .replace(CENSUS_NULL, float("nan"))
        .fillna(70_000)
    )

    df["expected_loss"] = expected_loss_per_property(df["damage_ratio"].values, df["home_value"].values)
    return (df,)


@app.cell
def _(aggregate_by_geography, df):
    tract_summary = aggregate_by_geography(df, "tract")
    print("Top 10 tracts by expected loss:")
    print(tract_summary.nlargest(10, "total_expected_loss")[["tract", "total_expected_loss", "mean_loss_per_household"]])
    return (tract_summary,)


@app.cell
def _(df, loss_by_income_decile):
    income_summary = loss_by_income_decile(df)
    print("Loss by income decile:")
    print(income_summary)
    return


@app.cell
def _(ROOT, tract_summary):
    out = ROOT / "data/processed/tract_loss_summary.parquet"
    tract_summary.to_parquet(out, index=False)
    print(f"Saved tract summary to {out}")
    return


if __name__ == "__main__":
    app.run()
