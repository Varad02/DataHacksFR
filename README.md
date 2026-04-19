# Seismic Risk Atlas

Block-level expected earthquake loss estimates for Los Angeles County using physics-based ground-motion simulations, housing value data, and census demographics.

Built at DataHacks 2026.

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi&logoColor=white)
![Leaflet](https://img.shields.io/badge/Leaflet-Map-199900?logo=leaflet&logoColor=white)
![License](https://img.shields.io/badge/Data-Source--specific-lightgrey)

## Table of Contents

- [Overview](#overview)
- [Key Outputs](#key-outputs)
- [Methodology](#methodology)
- [Assumptions and Caveats](#assumptions-and-caveats)
- [Pipeline](#pipeline)
- [Repository Guide](#repository-guide)
- [Project Layout](#project-layout)
- [Tech Stack](#tech-stack)
- [Quickstart](#quickstart)
- [Environment Variables](#environment-variables)
- [Run the Pipeline](#run-the-pipeline)
- [Run the App and API](#run-the-app-and-api)
- [Marimo Entry Points](#marimo-entry-points)
- [Data Sources](#data-sources)

## Overview

Most earthquake tools focus on shaking intensity. This project estimates expected household dollar loss and highlights who is most exposed.

For each of 2,498 census tracts in LA County, the atlas computes:

- Expected structural dollar loss per household under an M6.7 scenario
- Damage ratio by building construction era
- Distributional breakdown by income decile

The output is an interactive choropleth map where each tract includes a plain-English summary generated via OpenAI.

## Key Outputs

- `app/risk_data.geojson`: simplified tract-level map layer for the web app
- `mc_tract_summary.parquet`: tract-level expected loss and uncertainty statistics
- Interactive map in `app/index.html` + `app/main.js`
- Optional explanation API in `api/explain.py`

## Methodology

### 1) Shaking data extraction

Scripps generated 500 physics-based earthquake simulations for the Whittier Narrows fault. For each scenario, ground velocity is recorded on a receiver grid. The pipeline extracts peak metrics including PGA and PGV.

### 2) Spatial assignment

Each census tract centroid is mapped to its nearest receiver using a KD-tree lookup. This gives every tract a full scenario-by-scenario shaking profile.

### 3) Damage estimation

FEMA HAZUS fragility curves map shaking to expected structural damage ratio. The model accounts for building code eras (for example pre-1970 vs newer stock).

### 4) Economic loss estimation

Expected damage ratio is multiplied by tract-level housing value estimates. Zillow ZHVI is used where available, with ACS-based fallback features.

### 5) Monte Carlo aggregation

Loss is computed per scenario and then averaged over all 500 scenarios. This preserves nonlinearity in the damage function and avoids bias from averaging shaking first.

## Assumptions and Caveats

The prototype data uses reduced-order seismic moments for methodology demonstration. Results are scaled to an M6.7 reference scenario (comparable to major historical Southern California events). Spatial patterns are informative; absolute loss magnitudes remain scenario-dependent.

## Pipeline

```text
seismos_16_receivers.npy (Scripps prototype)
    -> notebooks/02_extract_shaking_features.py
    -> notebooks/04_spatial_join.py
    -> notebooks/05_damage_model.py
    -> notebooks/06_loss_aggregation.py
    -> notebooks/08_zillow_join.py
    -> notebooks/09_monte_carlo.py
    -> notebooks/07_export_map_geojson.py
    -> app/risk_data.geojson
```

Runtime flow:

1. Pipeline writes `app/risk_data.geojson`.
2. Frontend (`app/index.html`, `app/main.js`) renders the choropleth.
3. On tract click, frontend calls `POST /api/explain`.
4. API (`api/explain.py`) returns a 2-3 sentence summary.

## Repository Guide

| Path | Purpose |
|---|---|
| `notebooks/` | End-to-end pipeline scripts and analysis steps |
| `src/` | Reusable project modules |
| `app/` | Frontend map UI (Leaflet) and data layer |
| `api/` | FastAPI endpoint for tract-level natural-language summaries |
| `docs/` | Sphinx documentation sources |

## Project Layout

```text
DataHacksFR/
├── README.md
├── PROJECT_PLAN.md
├── requirements.txt
├── demo_marimo.py
├── api/
│   └── explain.py
├── app/
│   ├── index.html
│   ├── main.js
│   └── risk_data.geojson
├── notebooks/
│   ├── 01_explore_seismograms.py
│   ├── 02_extract_shaking_features.py
│   ├── 03_fetch_property_data.py
│   ├── 04_spatial_join.py
│   ├── 05_damage_model.py
│   ├── 06_loss_aggregation.py
│   ├── 07_export_map_geojson.py
│   ├── 08_zillow_join.py
│   ├── 09_monte_carlo.py
│   └── __marimo__/
├── src/
│   ├── damage/
│   ├── economic/
│   ├── models/
│   └── seismic/
├── docs/
│   ├── conf.py
│   ├── index.rst
│   ├── damage.rst
│   ├── economic.rst
│   ├── models.rst
│   └── seismic.rst
├── databricks/
├── brev/
└── venv/
```

## Tech Stack

| Tool | Use |
|---|---|
| Marimo | Reactive Python notebook workflow with version-controllable `.py` files |
| Databricks Serverless | Distributed extraction on large-volume seismic data |
| Nvidia Brev.dev (L40s) | GPU acceleration for model training experiments |
| OpenAI gpt-4o-mini | Plain-English tract summaries |
| Leaflet.js | Interactive choropleth frontend |
| FastAPI | Lightweight summary API |
| Sphinx | Auto-generated technical documentation |

## Quickstart

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Windows (PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Windows (CMD)

```bat
py -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
```

## Environment Variables

Create `.env` from `.env.example`.

macOS / Linux:

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Set required values:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

What is required:

- `OPENAI_API_KEY`: OpenAI API key used by `api/explain.py`.

How to populate:

1. Open `.env`.
2. Replace `your_openai_api_key_here` with your real key.
3. Save the file.

## Run the Pipeline

```bash
python notebooks/02_extract_shaking_features.py
python notebooks/04_spatial_join.py
python notebooks/05_damage_model.py
python notebooks/06_loss_aggregation.py
python notebooks/08_zillow_join.py
python notebooks/09_monte_carlo.py
python notebooks/07_export_map_geojson.py
```

## Run the App and API

Start the API:

```bash
uvicorn api.explain:app --reload
```

Serve the frontend map:

```bash
cd app
python -m http.server 3000
```

Then open `http://localhost:3000`.

## Marimo Entry Points

```bash
python demo_marimo.py
python demo_marimo.py --step 05
```

## Data Sources

| Dataset | Source | License |
|---|---|---|
| Scripps ground motion simulations | [Zenodo 12520845](https://zenodo.org/records/12520845) | CC-BY 4.0 |
| Zillow Home Value Index | [Zillow Research](https://www.zillow.com/research/data/) | Public |
| Census ACS 5-year estimates | [Census Bureau API](https://www.census.gov/data/developers.html) | Public domain |
| TIGER tract boundaries | [Census TIGER](https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html) | Public domain |
| FEMA HAZUS fragility curves | [FEMA HAZUS](https://www.fema.gov/flood-maps/tools-resources/flood-map-products/hazus) | Public |
