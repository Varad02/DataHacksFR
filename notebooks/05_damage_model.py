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
    from src.damage.hazus import damage_ratio, year_built_to_era

    return ROOT, damage_ratio, mo, np, pd, year_built_to_era


@app.cell
def _(mo):
    mo.md("""
    ## 05 -- Apply HAZUS Damage Functions
    """)
    return


@app.cell
def _(ROOT, damage_ratio, np, pd, year_built_to_era):
    df = pd.read_parquet(ROOT / "data/processed/property_risk_joined.parquet")

    # PGA from seismograms is in m/s^2 -- convert to g
    df["pga_g_raw"] = df["pga"] / 9.81

    # The ROM dataset uses near-unit seismic moments (Mw ~1.3 Green's functions).
    # Scale to a M6.7 scenario (Whittier Narrows / Northridge equivalent):
    # target max PGA = 0.5g in the near-fault zone.
    TARGET_MAX_PGA_G = 0.5
    scale = TARGET_MAX_PGA_G / df["pga_g_raw"].max()
    df["pga_g"] = df["pga_g_raw"] * scale
    print(f"Scenario scale factor: {scale:.1f}x  (targeting max PGA = {TARGET_MAX_PGA_G}g)")
    print(f"Scaled PGA range: {df['pga_g'].min():.4f}g -- {df['pga_g'].max():.4f}g")

    df["era"] = df["median_year_built"].fillna(1980).astype(float).apply(year_built_to_era)
    df["damage_ratio"] = df.apply(
        lambda r: damage_ratio(np.array([r["pga_g"]]), r["era"])[0], axis=1
    )

    print(df[["pga_g", "era", "damage_ratio"]].describe())
    return (df,)


@app.cell
def _(ROOT, df):
    out = ROOT / "data/processed/property_risk_joined.parquet"
    df.to_parquet(out, index=False)
    print(f"Updated {len(df)} rows with damage_ratio, saved to {out}")
    df[["tract", "pga_g", "era", "damage_ratio"]].head()
    return


if __name__ == "__main__":
    app.run()
