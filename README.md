# Seismic Risk Atlas

Block-level expected earthquake loss estimates for LA County, built on physics-based ground motion simulations from Scripps Institution of Oceanography combined with Zillow home values and Census income data.

Built at DataHacks 2026.

---

## What it does

Existing earthquake risk tools tell you how hard the ground shakes. We tell you how many dollars your neighborhood stands to lose -- and who bears the most risk.

For each of 2498 census tracts in LA County we compute:
- Expected structural dollar loss per household under a M6.7 scenario
- Damage ratio by building construction era
- Distributional breakdown by income decile

The result is an interactive choropleth map -- click any neighborhood, get a plain-English risk summary powered by OpenAI.

---

## How it works

**Step 1 -- Shaking data**
Scripps ran 500 physics-based earthquake simulations on the Whittier Narrows fault. For each simulation they recorded ground velocity at 8181 locations across a 50km x 40km grid covering East LA and the San Gabriel Valley. We extract Peak Ground Acceleration (PGA) and Peak Ground Velocity (PGV) from those recordings.

**Step 2 -- Spatial join**
Every census tract centroid is assigned to its nearest measurement point via KD-tree. Each of the 2498 tracts now has PGA values for all 500 scenarios.

**Step 3 -- Damage model**
FEMA HAZUS lognormal fragility curves convert PGA into a structural damage ratio, accounting for building era (pre-1970, post-1973, post-1994 seismic codes). Older buildings take higher damage at the same shaking level.

**Step 4 -- Dollar loss**
Damage ratio x home value = expected dollar loss. Home values come from Zillow ZHVI (82.6% coverage) with Census ACS as fallback.

**Step 5 -- Monte Carlo**
We apply HAZUS to all 500 source scenarios independently and average the resulting losses -- correct treatment of the nonlinear damage function.

### The one caveat
The Scripps dataset uses near-unit seismic moments (reduced-order model for methodology demonstration). We scale to M6.7 -- same magnitude as the 1987 Whittier Narrows and 1994 Northridge earthquakes. The spatial pattern of which neighborhoods shake more is real; the absolute magnitude is scenario-dependent.

---

## Pipeline

```
seismos_16_receivers.npy  (Scripps, 38MB prototype)
        |
        v
01_explore_seismograms.py       -- sanity check, plot receiver grid
02_extract_shaking_features.py  -- PGV, PGA, Arias intensity
        |
        v  pgv_pga_matrix.parquet
        |
03_fetch_property_data.py       -- Zillow ZHVI + Census ACS
04_spatial_join.py              -- TIGER centroids + KD-tree nearest receiver
        |
        v  property_risk_joined.parquet
        |
05_damage_model.py              -- HAZUS fragility curves + M6.7 scaling
06_loss_aggregation.py          -- dollar loss + income deciles
08_zillow_join.py               -- ZHVI home values (82.6% coverage)
09_monte_carlo.py               -- E[loss] over 500 scenarios
        |
        v  mc_tract_summary.parquet
        |
07_export_map_geojson.py        -- simplified GeoJSON for the map
        |
        v  app/risk_data.geojson
        |
app/index.html + main.js        -- Leaflet choropleth map
api/explain.py                  -- OpenAI plain-English summaries
```

---

## Tech stack

| Tool | Use |
|---|---|
| Marimo | Reactive Python notebooks (plain .py, version-controllable) |
| Databricks Serverless | Distributed PGV extraction on full 176GB dataset |
| Nvidia Brev.dev (L40s) | GPU-accelerated XGBoost damage ratio model |
| OpenAI gpt-4o-mini | Neighborhood risk summaries |
| Leaflet.js | Interactive choropleth map |
| FastAPI | REST endpoint for AI summaries |
| Sphinx | Auto-generated pipeline documentation |

---

## Setup

```bash
conda activate myenv
pip install -r requirements.txt
```

Add your OpenAI key to `.env`:
```
OPENAI_API_KEY=sk-...
```

Run the pipeline in order:

```bash
python notebooks/02_extract_shaking_features.py
python notebooks/04_spatial_join.py
python notebooks/05_damage_model.py
python notebooks/06_loss_aggregation.py
python notebooks/08_zillow_join.py
python notebooks/09_monte_carlo.py
python notebooks/07_export_map_geojson.py
```

Launch notebooks in Marimo UI:

```bash
python demo_marimo.py           # opens all key notebooks
python demo_marimo.py --step 05 # opens only the damage model
```

Start the API:

```bash
uvicorn api.explain:app --reload
```

Open the map:

```bash
cd app && python -m http.server 3000
# open http://localhost:3000
```

---

## Demo script

**Total time: 3-5 minutes**

---

**Opening (30 seconds)**

> "Every few decades, a major earthquake hits Los Angeles. The 1994 Northridge quake caused $44 billion in damage. The 1987 Whittier Narrows quake -- $360 million. But here's the thing: we have never been able to answer the question at the neighborhood level -- which specific streets bear the most financial risk, and who lives there?
>
> That is what we built."

---

**The data (45 seconds)**

> "Scripps Institution of Oceanography ran 500 physics-based earthquake simulations on the Whittier Narrows fault -- the same fault that ruptured in 1987. For each simulation, they recorded ground shaking at 8181 measurement points across a 50-kilometer grid covering East LA and the San Gabriel Valley.
>
> We took that data, combined it with Zillow home values and Census income data, and built a block-level expected loss atlas for LA County.
>
> No one has done this at this resolution before. Published tools stop at the county level."

---

**The live demo (90 seconds)**

*[Open http://localhost:3000 in browser]*

> "This is our interactive map. Each shaded polygon is a census tract. Darker red means higher expected dollar loss per household under a realistic M6.7 scenario -- same magnitude as Northridge."

*[Click a high-loss tract near Whittier Narrows]*

> "I'll click here -- this tract is near the epicentral zone. The summary on the right is generated live by OpenAI -- plain English, no jargon, written for a resident not an engineer."

*[Click a lower-income tract with older housing]*

> "Now I'll click over here -- lower home values, but look at the damage ratio. These homes were built pre-1970, before modern seismic codes. A higher fraction of the structure gets destroyed even though the dollar loss is lower.
>
> That is the distributional story. Wealthier neighborhoods lose more dollars. Lower-income neighborhoods with older housing lose more of what they have."

---

**The methodology (45 seconds)**

> "Five steps.
>
> One: extract peak ground acceleration from the Scripps seismograms for all 500 source scenarios.
>
> Two: assign each census tract to its nearest measurement point on the receiver grid.
>
> Three: run FEMA HAZUS fragility curves to convert shaking into a structural damage ratio, accounting for building age.
>
> Four: damage ratio times home value equals expected dollar loss.
>
> Five: Monte Carlo over all 500 scenarios -- we apply HAZUS to each scenario separately and average, which is the correct treatment of the nonlinear damage function.
>
> The full 176GB dataset runs on Databricks. The prototype runs on the 38MB version Scripps provides for exactly this purpose."

---

**The tooling (30 seconds)**

*[Run `python demo_marimo.py --step 05` and show the reactive notebook UI]*

> "The pipeline is written in Marimo -- a next-generation notebook format where cells are pure functions. Change a parameter and every downstream cell reruns automatically. Each notebook is also a plain .py file you can diff and version-control.

*[Open docs/_build/html/index.html]*

> "Documentation is auto-generated with Sphinx -- every function in the pipeline has its signature and docstring in a searchable HTML site. And the damage ratio model runs on a GPU instance via Brev -- training time drops from minutes to seconds on the L40s."

---

**The differentiators (30 seconds)**

> "Three things make this different from what is already out there.
>
> First, physics-based simulation -- not just historical averages or USGS hazard zones.
>
> Second, neighborhood resolution -- census tract level, not county level.
>
> Third, the economic framing. We are not showing you a shaking map. We are showing you a dollar map, layered by income. That is a policy tool."

---

**Closing line (15 seconds)**

> "Earthquake risk is not evenly distributed. Now you can see exactly where it falls -- and what it costs. This is the Seismic Risk Atlas."

---

**Likely judge questions**

| Question | Answer |
|---|---|
| "Why scale by 11,000x?" | The Scripps dataset is a reduced-order model -- unit Green's functions. We scale to M6.7, same magnitude as 1987 Whittier Narrows. The spatial pattern is real; the absolute magnitude is scenario-dependent. |
| "How accurate are the HAZUS curves?" | HAZUS is the FEMA standard used for insurance pricing and disaster planning nationwide. We use wood-frame residential curves, the dominant housing type in our domain. |
| "Why only 16 receivers for the prototype?" | Scripps provides a 38MB prototype with 16 evenly-spaced receivers for exactly this use case. The full 8181-receiver 176GB dataset runs on Databricks. |
| "What is the Monte Carlo piece?" | We apply HAZUS to all 500 source scenarios separately and average the resulting losses -- correct treatment because HAZUS is nonlinear. Averaging PGA before HAZUS would underestimate damage. |
| "Could this work for other cities?" | Yes -- the pipeline is generic. You need a physics-based simulation dataset and property values. San Francisco, Seattle, Tokyo -- same approach. |
| "What is the OpenAI integration?" | Click any neighborhood on the map, get a plain-English 2-sentence risk summary written for a homeowner. It reads the tract's loss, damage ratio, income, and home value and explains it without jargon. |

---

## Data sources

| Dataset | Source | License |
|---|---|---|
| Scripps ground motion simulations | [Zenodo 12520845](https://zenodo.org/records/12520845) | CC-BY 4.0 |
| Zillow Home Value Index | [Zillow Research](https://www.zillow.com/research/data/) | Public |
| Census ACS 5-year estimates | [Census Bureau API](https://www.census.gov/data/developers.html) | Public domain |
| TIGER tract boundaries | [Census TIGER](https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html) | Public domain |
| FEMA HAZUS fragility curves | [FEMA HAZUS](https://www.fema.gov/flood-maps/tools-resources/flood-map-products/hazus) | Public |

---

## Prize eligibility

- Scripps Challenge -- core project uses Scripps data as primary dataset
- Databricks -- full 176GB dataset processed via distributed PGV extraction on Serverless
- Marimo/Sphinx -- notebooks written in Marimo, docs auto-generated with Sphinx
- Nvidia Brev.dev -- XGBoost damage ratio model trained on L40s GPU instance
- Most Innovative Idea (The Basement) -- default eligible
- Most Viral (SDx) -- interactive public map
