import marimo

__generated_with = "0.10.0"
app = marimo.App()


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import geopandas as gpd
    import json
    from pathlib import Path
    ROOT = Path(__file__).resolve().parent.parent
    return ROOT, mo, pd, gpd, json


@app.cell
def _(mo):
    mo.md("## 07 -- Export GeoJSON for Leaflet Map")


@app.cell
def _(ROOT, pd, gpd):
    # Load TIGER tract polygons
    tracts = gpd.read_file(ROOT / "data/raw/census/la_tracts.gpkg")
    tracts["tract"] = tracts["GEOID"]

    # Use Monte Carlo summary if available, else fall back to single-scenario
    mc_path = ROOT / "data/processed/mc_tract_summary.parquet"
    single_path = ROOT / "data/processed/tract_loss_summary.parquet"
    if mc_path.exists():
        summary = pd.read_parquet(mc_path).rename(columns={
            "expected_loss": "mean_loss_per_household",
            "home_value": "median_home_value",
        })
        summary["total_expected_loss"] = summary["mean_loss_per_household"]
        print("Using Monte Carlo summary")
    else:
        summary = pd.read_parquet(single_path)
        print("Using single-scenario summary")

    # Load joined parquet for extra columns (damage_ratio, median_income, era)
    joined = pd.read_parquet(ROOT / "data/processed/property_risk_joined.parquet")
    extra = joined[["tract", "damage_ratio", "median_income", "median_year_built", "pga_g"]].copy()
    extra["median_income"] = pd.to_numeric(extra["median_income"], errors="coerce").replace(-666666666, float("nan")).fillna(70_000)

    # Merge everything onto tract polygons
    gdf = tracts.merge(summary, on="tract", how="inner")

    # Only merge extra columns not already in summary
    extra_cols = [c for c in ["damage_ratio", "median_income", "median_year_built", "pga_g"]
                  if c not in gdf.columns]
    if extra_cols:
        gdf = gdf.merge(extra[["tract"] + extra_cols], on="tract", how="left")

    # Keep only columns that exist
    want = ["tract", "NAME", "geometry", "total_expected_loss", "mean_loss_per_household",
            "median_home_value", "damage_ratio", "median_income", "median_year_built", "pga_g"]
    gdf = gdf[[c for c in want if c in gdf.columns]].copy()

    # Simplify geometries -- project to metres, simplify, reproject to WGS84
    gdf = gdf.to_crs("EPSG:3310")
    gdf["geometry"] = gdf["geometry"].simplify(tolerance=100, preserve_topology=True)
    gdf = gdf.to_crs("EPSG:4326")

    # Round floats for smaller file size
    float_cols = ["total_expected_loss", "mean_loss_per_household", "median_home_value",
                  "damage_ratio", "median_income", "pga_g"]
    for col in float_cols:
        if col in gdf.columns:
            gdf[col] = gdf[col].round(2)

    print(f"GeoDataFrame: {len(gdf)} tracts")
    gdf.head()
    return (gdf,)


@app.cell
def _(ROOT, gdf):
    out = ROOT / "app/risk_data.geojson"
    gdf.to_file(out, driver="GeoJSON")
    print(f"Saved {len(gdf)} features to {out}")
    size_mb = out.stat().st_size / 1e6
    print(f"File size: {size_mb:.1f} MB")


if __name__ == "__main__":
    app.run()
