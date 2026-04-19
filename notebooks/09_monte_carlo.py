import marimo

__generated_with = "0.10.0"
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
    from src.damage.hazus import damage_ratio, year_built_to_era
    from src.economic.loss import expected_loss_per_property
    return ROOT, mo, pd, np, damage_ratio, year_built_to_era, expected_loss_per_property


@app.cell
def _(mo):
    mo.md("""
    ## 09 -- Monte Carlo Expected Loss

    Instead of averaging PGA across 500 sources before applying HAZUS (wrong -- nonlinear),
    apply HAZUS to each of the 500 scenarios separately, then average the losses.
    Weight = 1/500 (uniform -- UCERF3 noted as future improvement).
    """)


@app.cell
def _(ROOT, pd):
    # Load all 8000 (receiver, source) shaking features
    features_df = pd.read_parquet(ROOT / "data/processed/pgv_pga_matrix.parquet")

    # Load tract data with receiver assignment, building era, home value
    tracts_df = pd.read_parquet(ROOT / "data/processed/property_risk_joined.parquet")

    print(f"Features: {len(features_df)} rows ({features_df['source_id'].nunique()} sources x {features_df['receiver_id'].nunique()} receivers)")
    print(f"Tracts: {len(tracts_df)}")
    return (features_df, tracts_df)


@app.cell
def _(features_df, tracts_df, pd, np, damage_ratio, year_built_to_era, expected_loss_per_property):
    # Scenario scale factor (same as notebook 05 -- target max PGA = 0.5g)
    TARGET_MAX_PGA_G = 0.5
    scale = TARGET_MAX_PGA_G / (features_df["pga"].max() / 9.81)

    # For each tract, cross-join with all 500 source scenarios via its receiver
    # tracts_df has receiver_id; features_df has (receiver_id, source_id, pga)
    tract_cols = ["tract", "receiver_id", "median_year_built", "home_value_final",
                  "median_income", "lat", "lon"]
    tracts_slim = tracts_df[tract_cols].copy()
    tracts_slim["home_value"] = tracts_slim["home_value_final"].fillna(500_000)
    tracts_slim["era"] = tracts_slim["median_year_built"].fillna(1980).astype(float).apply(year_built_to_era)

    # Join: each tract gets all 500 source scenarios for its receiver
    merged = tracts_slim.merge(
        features_df[["receiver_id", "source_id", "pga"]],
        on="receiver_id", how="left"
    )
    merged["pga_g"] = (merged["pga"] / 9.81) * scale

    print(f"Expanded table: {len(merged):,} rows (tracts x sources)")

    # Apply HAZUS per row
    merged["damage_ratio"] = merged.apply(
        lambda r: damage_ratio(np.array([r["pga_g"]]), r["era"])[0], axis=1
    )
    merged["loss"] = expected_loss_per_property(merged["damage_ratio"].values, merged["home_value"].values)

    return (merged, scale)


@app.cell
def _(merged, pd):
    # Monte Carlo aggregate: mean loss across all 500 scenarios per tract (uniform weights)
    N_SOURCES = 500

    mc_summary = (
        merged.groupby("tract")
        .agg(
            expected_loss=("loss", "mean"),          # E[loss] over scenarios
            std_loss=("loss", "std"),                 # uncertainty
            max_loss=("loss", "max"),                 # worst-case scenario
            damage_ratio_mean=("damage_ratio", "mean"),
            home_value=("home_value", "first"),
            median_income=("median_income", "first"),
            lat=("lat", "first"),
            lon=("lon", "first"),
        )
        .reset_index()
    )
    mc_summary["cv"] = mc_summary["std_loss"] / mc_summary["expected_loss"]  # coefficient of variation

    print("Top 10 tracts by Monte Carlo expected loss:")
    print(mc_summary.nlargest(10, "expected_loss")[
        ["tract", "expected_loss", "std_loss", "max_loss", "damage_ratio_mean"]
    ].to_string())
    return (mc_summary,)


@app.cell
def _(mc_summary, pd):
    # Income decile breakdown
    CENSUS_NULL = -666666666
    mc_summary["income"] = pd.to_numeric(mc_summary["median_income"], errors="coerce").replace(CENSUS_NULL, float("nan")).fillna(70_000)
    mc_summary["income_decile"] = pd.qcut(mc_summary["income"], q=10, labels=False)

    decile_summary = (
        mc_summary.groupby("income_decile")
        .agg(mean_expected_loss=("expected_loss", "mean"), n=("expected_loss", "count"))
        .reset_index()
    )
    print("\nMonte Carlo loss by income decile:")
    print(decile_summary.to_string())


@app.cell
def _(ROOT, mc_summary):
    out = ROOT / "data/processed/mc_tract_summary.parquet"
    mc_summary.to_parquet(out, index=False)
    print(f"Saved Monte Carlo summary: {len(mc_summary)} tracts to {out}")


if __name__ == "__main__":
    app.run()
