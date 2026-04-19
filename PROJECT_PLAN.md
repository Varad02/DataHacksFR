# Seismic Risk × Property Value Atlas

DataHacks 2026 project. Physics-based earthquake shaking maps combined with property and census data to produce neighborhood-level expected economic loss estimates for Southern California.

---

## The pitch in one paragraph

Published seismic risk tools rely on coarse USGS hazard maps. We combine high-resolution physics-based earthquake simulations from Scripps (500 source locations, 8181 receivers across Southern California) with Zillow home values and Census income data to produce a block-level expected-loss atlas. Output: for any neighborhood in SoCal, the expected dollar loss per household under a realistic earthquake scenario, plus a distributional breakdown showing who bears the risk. This is Scripps-eligible, economically concrete, and visually striking.

---

## Why this wins

1. No one has combined physics-based simulation output with granular property data at the neighborhood level. Published work stops at the county level using USGS zones.
2. The economic framing is sharp and quotable: expected dollar loss per household, layered by income.
3. Data is genuinely accessible (no credentialing, no scraping).
4. Strong demo potential: a shaded interactive map of San Diego is inherently shareable.
5. Eligible for the Scripps Challenge ($1500 prize pool).

---

## Datasets

### Primary (Scripps, required for the $1500 challenge)

**Scripps Ground Velocity Simulation Data**
- Source: https://zenodo.org/records/12520845
- License: CC-BY 4.0
- Format: NumPy binary (`velocity_time_series.npy`, 176.7 GB) + CSV source locations
- Structure: 60-second, three-component velocity seismograms for 500 source locations × 8181 receivers
- Smaller version available: `seismos_16_receivers.npy` (38.4 MB) with 16 evenly-spaced receivers for prototyping
- Associated paper: Rekoske et al. 2025, "Reduced-order modelling for complex three-dimensional seismic wave propagation"
- What we extract: peak ground velocity (PGV) and peak ground acceleration (PGA) at each receiver for each source, which is the standard input to damage functions.

**Scripps Physics-Based Ground Motion Data (secondary)**
- Rekoske et al. 2023 instantaneous physics-based ground motion maps
- Use as validation for our PGV/PGA estimates from the time-series data.

### External (free, no credentialing)

**Zillow Research Home Value Index (ZHVI)**
- Source: https://www.zillow.com/research/data/
- Format: CSV by ZIP code, updated monthly
- Features we use: median home value by ZIP, time series from 2000-present

**US Census American Community Survey (ACS) 5-year estimates**
- Source: https://www.census.gov/data/developers/data-sets/acs-5year.html (free API key)
- Granularity: census tract (smaller than ZIP)
- Features we use: median household income, population, housing units, year structure built

**FEMA HAZUS damage functions (for converting shaking to damage)**
- Source: publicly documented empirical fragility curves
- Use: map PGA/PGV to expected % structural damage, then multiply by property value

### Optional stretch datasets

**USGS ShakeMap archive** for validation against known historical events.
**California Earthquake Authority policy data** for insurance market comparison if we want an extension.

---

## ML/Modeling approach

### Core pipeline

1. **Feature extraction from seismograms** (Scripps data)
   - For each (source, receiver) pair, extract PGV, PGA, spectral acceleration at key periods, and Arias intensity
   - Output: a 500 × 8181 matrix of shaking metrics per source event

2. **Spatial interpolation to property coordinates**
   - Receivers form a grid; property addresses (from Zillow ZIP centroids or Census tract centroids) do not coincide with receivers
   - Use ordinary kriging or a GNN over the receiver graph to interpolate shaking at arbitrary coordinates
   - Fallback: nearest-neighbor receiver (simpler baseline)

3. **Damage function**
   - Apply HAZUS fragility curves to convert PGA to expected damage ratio by building type
   - Use Census `year structure built` as a proxy for building code era (pre-1970, 1970-1994, post-1994)

4. **Economic loss aggregation**
   - Expected loss per household = damage ratio × home value
   - Aggregate by census tract, ZIP, and city
   - Per capita and per income decile for distributional view

5. **Monte Carlo over sources**
   - The 500 source locations represent possible earthquake scenarios
   - Weight scenarios by historical recurrence rates (USGS UCERF3 gives these)
   - Compute expected annualized loss per neighborhood

### Specific models to try

- **Baseline**: gradient boosted trees (XGBoost) predicting damage ratio from shaking features + building features
- **Spatial**: Graph Neural Network on the receiver grid, with property locations as query nodes
- **Uncertainty**: quantile regression to give a confidence interval on loss estimates

---

## Prize stacking strategy

We target 5-6 prize categories. Each integration is scoped to add no more than one day of combined team effort.

| Prize | Prize value | Integration needed | Owner |
|---|---|---|---|
| Scripps Challenge / Best Use of [X] Data | $1500 + DJI Neo Drone | Core project already qualifies | Whole team |
| Best Use of Databricks | ~$500 | Load 176GB seismogram array into Databricks, run distributed PGV extraction | 1 person, ~4 hrs |
| Best Use of Marimo/Sphinx | $200 gift card | Write notebooks in Marimo, auto-generate docs with Sphinx | 1 person, ~3 hrs |
| Best Use of Nvidia Brev.dev | Sennheiser Headphones | Train GNN / XGBoost on Brev.dev GPU instance, document the workflow | 1 person, ~2 hrs |
| Most Innovative Build With AI / Best Use of Gemini | Google merch + MLH swag | Gemini-powered explainer: click a neighborhood, get a plain-English risk summary | 1 person, ~4 hrs |
| Most Innovative Idea (The Basement) | $25 gift card + swag | Default-eligible, no extra work | Whole team |
| Most Viral Idea (SDx) | JBL Go 3 + Escape Game Ticket | Publish interactive map publicly, tweet it | 1 person, ~1 hr |

**Important**: confirm with organizers that stacking is allowed before final submission.

---

## Suggested repo structure

```
seismic-risk-atlas/
├── README.md                    # Project overview for judges
├── PROJECT_PLAN.md              # This file
├── data/
│   ├── raw/                     # Downloaded datasets (gitignored)
│   │   ├── scripps/            # velocity_time_series.npy, source_locations.csv
│   │   ├── zillow/             # ZHVI CSV
│   │   └── census/             # ACS extracts
│   └── processed/               # Derived features (gitignored)
│       ├── pgv_pga_matrix.parquet
│       └── property_risk_joined.parquet
├── notebooks/                   # Marimo notebooks
│   ├── 01_explore_seismograms.py
│   ├── 02_extract_shaking_features.py
│   ├── 03_fetch_property_data.py
│   ├── 04_spatial_join.py
│   ├── 05_damage_model.py
│   └── 06_loss_aggregation.py
├── src/
│   ├── seismic/
│   │   ├── features.py         # PGV/PGA extraction
│   │   └── interpolation.py    # Spatial interpolation
│   ├── damage/
│   │   └── hazus.py            # Fragility curves
│   ├── economic/
│   │   └── loss.py             # Dollar loss calculations
│   └── models/
│       ├── xgb_baseline.py
│       └── gnn_spatial.py
├── app/                         # Interactive map frontend
│   ├── index.html
│   └── main.js                 # Leaflet/Mapbox
├── api/                         # Gemini explainer backend
│   └── explain.py
├── docs/                        # Sphinx output
└── requirements.txt
```

---

## Day 1 tasks (first 8 hours)

Goal by end of day 1: a working baseline that produces one ugly but correct loss estimate for one ZIP code in San Diego.

1. **Download data** (all team, parallel, 1 hour)
   - One person: Scripps small dataset (`seismos_16_receivers.npy`, 38MB) for prototyping
   - One person: Zillow ZHVI CSV
   - One person: Census API key + pull San Diego County ACS data
   - One person: set up Databricks workspace and upload the larger Scripps dataset

2. **Seismic feature extraction** (1 person, 3 hours)
   - Load the 16-receiver version first
   - Compute PGV and PGA for each (source, receiver) pair
   - Save as a Parquet table with columns: source_id, receiver_id, receiver_lat, receiver_lon, pgv, pga

3. **Property/census data prep** (1 person, 2 hours)
   - Pull San Diego County ZIPs from Zillow (filter CSV)
   - Pull census tract median income and year built for San Diego County
   - Geocode ZIP/tract centroids

4. **First spatial join** (1 person, 2 hours)
   - For each property coordinate, find nearest receiver
   - Attach PGV/PGA for each source scenario
   - Output: one row per (property, source) with shaking and property value

5. **Baseline loss calc** (1 person, 2 hours)
   - Apply a simple linear damage function (placeholder, replace with HAZUS later)
   - Compute expected loss for one source × all San Diego properties
   - Plot a choropleth on a map to sanity check

---

## Day 2 tasks

1. Scale to full receiver dataset using Databricks
2. Replace linear damage function with proper HAZUS fragility curves
3. Train the XGBoost baseline model
4. Build interactive Leaflet/Mapbox frontend
5. Add Gemini explainer API
6. Set up Sphinx docs

## Day 3 tasks (final day)

1. Monte Carlo over all 500 sources, weighted by UCERF3 recurrence
2. Income-decile distributional analysis ("who bears the risk")
3. Polish map, write demo script
4. Final writeup and submission

---

## Open questions / things to resolve early

1. **Receiver grid coverage**: do the 8181 receivers cover San Diego densely enough for ZIP-level estimates? Check first thing by plotting receivers on a map. If coverage is sparse in our target area, pivot target city.

2. **HAZUS license**: the curves are publicly documented but check if we can redistribute the specific parameters. Worst case, hand-code from published equations.

3. **UCERF3 recurrence rates**: needed for annualized loss. If hard to parse, use uniform weighting across the 500 sources for the hackathon version and note this as a limitation.

4. **Stacking rules**: confirm multiple sponsor prizes allowed per project.

---

## Key links

- Scripps dataset: https://zenodo.org/records/12520845
- Zillow data: https://www.zillow.com/research/data/
- Census API: https://www.census.gov/data/developers.html
- USGS UCERF3: https://www.usgs.gov/programs/earthquake-hazards/science/uniform-california-earthquake-rupture-forecast-version-3-ucerf3
- HAZUS technical manual: https://www.fema.gov/flood-maps/tools-resources/flood-map-products/hazus

---

## Context for Claude Code sessions

When starting a Claude Code session on this project, the key context is:

1. This is a 3-day hackathon so optimize for "working end-to-end" over "perfect individual components"
2. The economic framing is the differentiator; don't let ML engineering overshadow the story
3. Scripps data is required for the $1500 prize
4. Always use the 16-receiver prototyping dataset first before scaling to 176GB
5. No em dashes in any user-facing output (team preference)
