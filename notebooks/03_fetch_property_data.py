import marimo

__generated_with = "0.10.0"
app = marimo.App()


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import requests
    import os
    from pathlib import Path
    ROOT = Path(__file__).resolve().parent.parent
    return ROOT, mo, os, pd, requests


@app.cell
def _(mo):
    mo.md("## 03 -- Fetch Zillow ZHVI + Census ACS for LA County")


@app.cell
def _(ROOT, pd):
    # Zillow ZHVI -- single-family homes, ZIP-level
    # Domain is Whittier Narrows / LA area (33.82-34.18N, 118.31-117.77W)
    zhvi = pd.read_csv(ROOT / "data/raw/zillow/zhvi_zip.csv")
    la_zips = zhvi[
        (zhvi["StateName"] == "California") &
        (zhvi["RegionName"].astype(str).str.match(r"^9(00|01|02|03|04|05|06|07|08|09|10|11|12|13|14|15|16|17|18)"))
    ]
    print(f"LA area ZIPs in ZHVI: {len(la_zips)}")
    la_zips.head()


@app.cell
def _(ROOT, os, pd, requests):
    # Census ACS 5-year -- LA County FIPS = 06037
    key = os.environ.get("CENSUS_API_KEY", "")
    key_param = f"&key={key}" if key else ""

    url = (
        "https://api.census.gov/data/2022/acs/acs5"
        "?get=B19013_001E,B25077_001E,B25035_001E,B01003_001E,NAME"
        "&for=tract:*"
        "&in=state:06%20county:037"
        + key_param
    )
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    acs_df = pd.DataFrame(data[1:], columns=data[0]).rename(columns={
        "B19013_001E": "median_income",
        "B25077_001E": "median_home_value_acs",
        "B25035_001E": "median_year_built",
        "B01003_001E": "population",
    })
    out = ROOT / "data/raw/census/la_county_acs.csv"
    acs_df.to_csv(out, index=False)
    print(f"Saved {len(acs_df)} LA County census tracts to {out}")
    acs_df.head()


if __name__ == "__main__":
    app.run()
