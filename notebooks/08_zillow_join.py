import marimo

__generated_with = "0.10.0"
app = marimo.App()


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    from pathlib import Path
    ROOT = Path(__file__).resolve().parent.parent
    return ROOT, mo, pd


@app.cell
def _(mo):
    mo.md("## 08 -- Join Zillow ZHVI Home Values to Census Tracts")


@app.cell
def _(ROOT, pd):
    zhvi_raw = pd.read_csv(ROOT / "data/raw/zillow/zhvi_zip.csv")
    date_cols = [c for c in zhvi_raw.columns if c.startswith("20")]
    latest_col = date_cols[-1]
    print(f"Using ZHVI column: {latest_col}")

    zhvi_lookup = (
        zhvi_raw[["RegionName", latest_col]]
        .rename(columns={"RegionName": "zip", latest_col: "zhvi_value"})
        .dropna(subset=["zhvi_value"])
    )
    zhvi_lookup["zip"] = zhvi_lookup["zip"].astype(str).str.zfill(5)
    print(f"ZIPs with ZHVI values: {len(zhvi_lookup)}")
    return (zhvi_lookup,)


@app.cell
def _(ROOT, pd, zhvi_lookup):
    import pgeocode
    from scipy.spatial import cKDTree

    tracts_df = pd.read_parquet(ROOT / "data/processed/property_risk_joined.parquet")

    # Build KD-tree over all US ZIP centroids from pgeocode
    nomi = pgeocode.Nominatim("us")
    zip_centroids = nomi._data[["postal_code", "latitude", "longitude"]].dropna()
    zip_centroids = zip_centroids.rename(columns={"postal_code": "zip"})

    tree = cKDTree(zip_centroids[["latitude", "longitude"]].values)
    tract_coords = tracts_df[["lat", "lon"]].values
    _, indices = tree.query(tract_coords)
    tracts_df["zip"] = zip_centroids["zip"].iloc[indices].values

    print(f"ZIP assigned to all {len(tracts_df)} tracts via nearest-centroid KD-tree")

    # Join ZHVI
    joined_df = tracts_df.merge(zhvi_lookup, on="zip", how="left")

    # Use ZHVI where available, fall back to ACS median home value
    acs_num = pd.to_numeric(joined_df["median_home_value_acs"], errors="coerce").replace(-666666666, float("nan"))
    joined_df["home_value_final"] = joined_df["zhvi_value"].combine_first(acs_num).fillna(500_000)

    zhvi_coverage = joined_df["zhvi_value"].notna().sum()
    print(f"ZHVI coverage: {zhvi_coverage}/{len(joined_df)} tracts ({zhvi_coverage/len(joined_df):.1%})")
    print(f"Home value range: ${joined_df['home_value_final'].min():,.0f} -- ${joined_df['home_value_final'].max():,.0f}")
    print(f"Median home value: ${joined_df['home_value_final'].median():,.0f}")

    out = ROOT / "data/processed/property_risk_joined.parquet"
    joined_df.to_parquet(out, index=False)
    print(f"Saved to {out}")


if __name__ == "__main__":
    app.run()
