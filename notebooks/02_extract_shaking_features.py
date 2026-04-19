import marimo

__generated_with = "0.23.1"
app = marimo.App()


@app.cell
def _():
    import marimo as mo
    import numpy as np
    import pandas as pd
    import sys
    from pathlib import Path
    ROOT = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(ROOT))
    from src.seismic.features import extract_features

    return ROOT, extract_features, mo, np


@app.cell
def _(mo):
    mo.md("""
    ## 02 -- Extract PGV / PGA from Seismograms
    """)
    return


@app.cell
def _(ROOT, extract_features, np):
    seismograms = np.load(ROOT / "data/raw/scripps/seismos_16_receivers.npy", mmap_mode="r")
    print(f"Shape: {seismograms.shape} -- extracting features...")
    features_df = extract_features(seismograms, dt=0.1)
    print(features_df.describe())
    return (features_df,)


@app.cell
def _(ROOT, features_df):
    out = ROOT / "data/processed/pgv_pga_matrix.parquet"
    features_df.to_parquet(out, index=False)
    print(f"Saved {len(features_df)} rows to {out}")
    return


if __name__ == "__main__":
    app.run()
