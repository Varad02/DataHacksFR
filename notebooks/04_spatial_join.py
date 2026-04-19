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
    from src.seismic.interpolation import nearest_receiver

    return ROOT, mo, nearest_receiver, pd


@app.cell
def _(mo):
    mo.md("""
    ## 04 -- Spatial Join: Properties to Receivers
    """)
    return


@app.cell
def _(ROOT):
    import geopandas as gpd
    import pygris

    tiger_path = ROOT / "data/raw/census/la_tracts.gpkg"

    if not tiger_path.exists():
        print("Downloading LA County TIGER tract shapefile via pygris...")
        tracts = pygris.tracts(state="CA", county="Los Angeles", year=2022)
        tracts = tracts.to_crs("EPSG:4326")
        tracts.to_file(tiger_path, driver="GPKG")
        print(f"Saved {len(tracts)} tracts to {tiger_path}")
    else:
        tracts = gpd.read_file(tiger_path)
        print(f"Loaded {len(tracts)} tracts from cache")

    # Project to California Albers for accurate centroids, then back to WGS84
    centroids = tracts.to_crs("EPSG:3310").geometry.centroid.to_crs("EPSG:4326")
    tracts["lat"] = centroids.y
    tracts["lon"] = centroids.x
    tracts["tract"] = tracts["GEOID"]
    tracts[["tract", "lat", "lon"]].head()
    return (tracts,)


@app.cell
def _(ROOT, nearest_receiver, pd, tracts):
    features_df = pd.read_parquet(ROOT / "data/processed/pgv_pga_matrix.parquet")
    receivers_meta = pd.read_csv(ROOT / "data/raw/scripps/receiver_locations.csv")

    # Prototype dataset only has 16 receivers -- filter to those receiver_ids
    prototype_ids = sorted(features_df["receiver_id"].unique())
    receivers_meta = receivers_meta[receivers_meta["receiver_id"].isin(prototype_ids)].reset_index(drop=True)
    print(f"Using {len(receivers_meta)} prototype receivers")

    acs_df = pd.read_csv(ROOT / "data/raw/census/la_county_acs.csv")
    acs_df["tract"] = "06037" + acs_df["tract"].astype(str).str.zfill(6)
    acs_df = acs_df.merge(tracts[["tract", "lat", "lon"]], on="tract", how="inner")
    print(f"Tracts with centroids: {len(acs_df)}")

    assignment = nearest_receiver(
        query_lats=acs_df["lat"].values,
        query_lons=acs_df["lon"].values,
        receiver_lats=receivers_meta["lat"].values,
        receiver_lons=receivers_meta["lon"].values,
        receiver_ids=receivers_meta["receiver_id"].values,
    )

    mean_shaking = features_df.groupby("receiver_id")[["pgv", "pga"]].mean().reset_index()
    joined = (
        acs_df.reset_index()
        .merge(assignment, left_index=True, right_on="query_idx")
        .merge(mean_shaking, on="receiver_id")
    )
    out = ROOT / "data/processed/property_risk_joined.parquet"
    joined.to_parquet(out, index=False)
    print(f"Joined {len(joined)} tract-receiver pairs, saved to {out}")
    joined.head()
    return


if __name__ == "__main__":
    app.run()
