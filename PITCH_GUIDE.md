# Pitch Guide — Seismic Risk Atlas
### Everything you need to understand and present this project confidently

---

## The one-sentence version

> "We combined physics-based earthquake simulations from Scripps with Zillow home values to produce a neighborhood-level dollar loss map for LA County -- something no public tool has done before."

---

## Why this problem matters (start every conversation here)

LA is overdue for a major earthquake. The 1994 Northridge quake caused $44 billion in damage. The 1987 Whittier Narrows quake hit $360 million. But when you look at public tools -- USGS ShakeMap, FEMA flood maps -- they show you shaking intensity at the county level. They do not answer the question a homeowner, insurer, or city planner actually cares about:

**"How many dollars will my neighborhood lose?"**

That is the gap. That is what we fill.

---

## The data we used (and why each one matters)

### 1. Scripps Seismic Simulations (the core)
- **What it is:** Scripps Institution of Oceanography ran 500 physics-based earthquake simulations on the Whittier Narrows fault in East LA -- the same fault that caused the 1987 quake.
- **What we get from it:** For each simulation, ground shaking was recorded at 8181 sensor locations across a 50km x 40km grid. The file is a 3D array: 8181 sensors x 600 time-steps x 500 simulations.
- **Why it's better than alternatives:** Most risk tools use historical averages or rough USGS hazard zones. Physics-based simulation captures how shaking varies block by block based on actual geology -- which neighborhoods sit on soft sediment, which on bedrock, how fault geometry affects propagation. That spatial variation is the whole point.
- **The honest caveat:** The Scripps dataset uses reduced-order Green's functions (near-unit seismic moments). We scale them up 11,019x to match a realistic M6.7 scenario. The *spatial pattern* -- which neighborhoods shake more than others -- is real and accurate. The *absolute values* are scenario-scaled, not measured.

### 2. Zillow ZHVI (home values)
- **What it is:** Zillow's Home Value Index -- median estimated home value by ZIP code, updated monthly.
- **Why we use it:** We need home values at the neighborhood level to translate damage ratios into dollar losses. Census ACS has home value estimates but they are 5-year averages and coarser. Zillow is fresher and more granular.
- **How we join it:** Census tracts don't have ZIP codes natively. We find the geographic center (centroid) of each tract, find the nearest ZIP code centroid using a KD-tree spatial search, and pull the ZHVI for that ZIP. We got 82.6% coverage -- the remaining 17.4% fall back to Census ACS estimates.

### 3. Census ACS (income + building age)
- **What it is:** American Community Survey 5-year estimates. We pull median household income and median year built for every census tract in LA County.
- **Why building age matters:** FEMA's damage curves are split by construction era -- homes built before 1970 are more vulnerable than post-Northridge (1994) construction. Building age is the single biggest predictor of damage after shaking intensity.
- **Why income matters:** The distributional story. Wealthier neighborhoods lose more dollars (higher home values). Lower-income neighborhoods with older housing lose a higher *fraction* of what they own.

---

## The five steps of the pipeline

### Step 1: Extract shaking metrics from seismograms
**File:** `notebooks/02_extract_shaking_features.py` → calls `src/seismic/features.py`

Each simulation gives us a time series of ground velocity at each sensor. We convert this to three numbers:

- **PGV (Peak Ground Velocity):** The maximum speed the ground moves. Measured in m/s. Correlates with how much a building sways.
- **PGA (Peak Ground Acceleration):** The maximum rate of change of velocity -- how hard the ground jerks. This is what snaps load-bearing structures. Measured in m/s².
- **Arias Intensity:** The total energy in the shaking. Captures duration as well as peak.

How we get PGA from velocity: the seismogram records *velocity*. We take the numerical derivative (rate of change) to get acceleration, then take the maximum absolute value. That's PGA.

We do this for all 8181 sensors × 500 simulations = 4,090,500 (sensor, scenario) pairs. Saved as `pgv_pga_matrix.parquet`.

### Step 2: Connect every neighborhood to a sensor
**File:** `notebooks/04_spatial_join.py` → calls `src/seismic/interpolation.py`

We have 8181 sensor locations and 2498 census tracts. For each tract we find its geographic center (centroid), then find the nearest sensor using a KD-tree (an efficient spatial search structure). Now each tract has a sensor ID, and through that sensor ID, PGA values for all 500 scenarios.

Why KD-tree and not a simple loop? With 2498 tracts × 8181 sensors, a brute-force distance calculation is 20 million comparisons. A KD-tree does it in milliseconds by organizing the sensor locations into a binary search tree.

One subtlety: we compute tract centroids in California Albers projection (EPSG:3310) -- a flat coordinate system optimized for California -- before converting back to lat/lon. Computing centroids on a curved globe gives slightly wrong answers; flat projection fixes that.

Output: `property_risk_joined.parquet` -- one row per census tract with its PGA, PGV, home value, income, building age, and lat/lon.

### Step 3: Convert shaking to damage
**File:** `notebooks/05_damage_model.py` → calls `src/damage/hazus.py`

We use FEMA HAZUS fragility curves. Here is the concept:

Imagine a graph where the x-axis is PGA (in units of g -- multiples of gravitational acceleration) and the y-axis is the probability that a building reaches a given damage state. The curve is S-shaped (lognormal CDF). A pre-1970 home has a steeper, left-shifted curve -- it reaches 50% damage at 0.30g. A post-1994 home reaches 50% damage at 0.60g. Same shaking, half the damage.

The three building eras:
- **pre_1970:** Built before any seismic code. Most vulnerable. 50% damage at 0.30g.
- **code_1973:** Post-1971 Sylmar earthquake reforms. Medium vulnerability. 50% damage at 0.45g.
- **code_1994:** Post-Northridge. Modern seismic code. 50% damage at 0.60g.

We determine each tract's era from Census median year built. The output is a damage ratio between 0 and 1 -- what fraction of the building's structure is expected to be destroyed.

**The scaling step:** The raw Scripps PGA values are tiny (roughly 0.00001g) because it's a reduced-order model. We scale them up by 11,019x to target a maximum PGA of 0.5g -- consistent with a M6.7 scenario. We derived this factor as: `0.5g / max_raw_PGA_in_g`. The spatial variation is preserved; only the absolute level changes.

### Step 4: Dollar loss
**File:** `notebooks/06_loss_aggregation.py` → calls `src/economic/loss.py`

Simple formula:

```
dollar_loss = damage_ratio × home_value × 0.85
```

The 0.85 factor: HAZUS says about 85% of a home's value is structural (walls, roof, foundation). The remaining 15% is land, which earthquakes don't destroy. This is the standard HAZUS assumption for Southern California urban residential.

We also compute loss by income decile -- divide all tracts into 10 equal groups by median income and compute the mean loss per household in each group. This is the distributional story for the pitch.

### Step 5: Monte Carlo over 500 scenarios
**File:** `notebooks/09_monte_carlo.py`

The naive approach would be: average PGA across all 500 scenarios, then run HAZUS once. That is mathematically wrong because HAZUS is nonlinear. The damage curve is S-shaped -- averaging PGA before the curve gives a different (lower) answer than applying the curve to each scenario and then averaging.

The correct approach: for each of the 2498 tracts × 500 scenarios = 1,249,000 combinations, apply HAZUS individually. Then average the 500 loss values per tract. That is the true expected loss E[loss].

We also compute standard deviation across scenarios (uncertainty) and the worst-case scenario loss. These go into the map tooltip.

---

## The map
**Files:** `app/index.html`, `app/main.js`

Built with Leaflet.js -- a JavaScript library for interactive maps. The data is a GeoJSON file (a standard geographic data format) where each polygon is a census tract boundary and the properties include expected loss, damage ratio, home value, income.

The color scale goes from yellow (low loss) to dark red (high loss). When you click a tract, a sidebar appears with the stats and an AI-generated plain-English summary via OpenAI.

The GeoJSON polygons are simplified (geometry compressed) so the file loads fast in a browser. The full-resolution boundaries would be 100MB+; simplified is about 15MB.

---

## The AI summary
**File:** `api/explain.py`

FastAPI (a Python web framework) serves a single endpoint: `POST /api/explain`. When you click a tract on the map, the JavaScript sends the tract's stats to this endpoint. The endpoint calls OpenAI's `gpt-4o-mini` with a prompt that includes loss, damage ratio, home value, and income, and asks for a 2-3 sentence plain-English explanation for a homeowner. The response appears in the sidebar within 1-2 seconds.

---

## The cloud infrastructure

### Databricks (notebooks in `databricks/`)
The prototype uses 16 sensor locations (38MB). The full Scripps dataset has 8181 sensors (176GB). That doesn't run on a laptop. We wrote Databricks notebooks that run on Serverless compute:

- `01_pgv_extraction.py`: Loads the full seismogram array, extracts PGV/PGA/Arias for all (sensor, scenario) pairs using NumPy, saves to a Delta table in Unity Catalog.
- `02_spatial_join_spark.py`: Joins 8181 sensors to 2498 tracts using distributed Spark SQL. The cross-join (8181 × 2498 = 20 million rows) that would kill a laptop runs in minutes on a cluster.

### Brev GPU (script in `brev/`)
`train_xgboost_gpu.py` trains an XGBoost model on the damage ratio data using a Brev L40s GPU instance (48GB VRAM). The `tree_method="gpu_hist"` flag tells XGBoost to use the GPU instead of CPU. Training time drops from ~60 seconds to ~2 seconds. The model learns to predict damage ratio from PGA, PGV, and building era -- useful as a fast inference model once deployed.

---

## The notebooks tool (Marimo)
The pipeline notebooks are written in Marimo instead of Jupyter. Two reasons:

1. **Reactive execution:** In Jupyter, cells run in whatever order you click them. Hidden state accumulates and notebooks break silently. In Marimo, cells declare their inputs and outputs explicitly. If you change cell A, all cells that depend on A automatically rerun. It's like a spreadsheet -- no stale state.

2. **Plain .py files:** Jupyter notebooks are JSON files with embedded outputs -- hard to read in a diff, hard to version control. Marimo notebooks are plain Python files. You can read them, grep them, and see exactly what changed in git.

---

## The documentation (Sphinx)
`docs/` contains a Sphinx configuration that auto-generates an HTML documentation site from the docstrings in `src/`. Run `cd docs && make html` and it builds a searchable site at `docs/_build/html/index.html`. Every function's parameters, return values, and description are pulled automatically. This is how production scientific Python packages (NumPy, pandas, scikit-learn) document themselves.

---

## The three things that make this different

**1. Physics-based simulation, not historical averages.**
USGS hazard maps average centuries of earthquakes. Scripps simulated the specific fault that is most likely to rupture next, with modern ground motion physics. The neighborhood-level variation comes from real geology -- soil type, basin depth, fault geometry.

**2. Census tract resolution, not county averages.**
Every published tool gives you county-level or ZIP-level risk. We give you census tract -- about 4,000 residents per polygon. That is neighborhood-level. You can see the difference between one side of a hill and the other.

**3. Dollar loss framing, not shaking intensity.**
Shaking maps answer "how hard?" We answer "how much?" Those are completely different questions for different audiences. Shaking maps are for engineers. Dollar loss maps are for homeowners, insurers, city planners, and banks that hold mortgages on those properties.

---

## Common questions and honest answers

**"Isn't 11,000x scaling unrealistic?"**
The scaling factor is not arbitrary -- it is derived from the target scenario (M6.7, same as Northridge). The reduced-order model preserves the physics of wave propagation; we are just adjusting the amplitude. The spatial pattern -- which neighborhoods experience more shaking relative to others -- is the real scientific output. The absolute dollar numbers should be treated as scenario estimates, not predictions.

**"How do you know HAZUS curves are accurate?"**
HAZUS is the FEMA standard used for post-disaster damage assessments and insurance pricing. It has been validated against actual earthquake damage data (Northridge, Loma Prieta, Christchurch). We use the wood-frame residential curves, which is the dominant housing type in our domain. It is the best publicly available model for this purpose.

**"What about aftershocks?"**
This model covers the mainshock only. Aftershock sequences (which can cause as much cumulative damage as the mainshock) are a known gap. Future work would use USGS ETAS (Epidemic-Type Aftershock Sequence) models.

**"Why not use actual property-level data instead of tract medians?"**
We don't have parcel-level records. County assessor data is public but requires a separate scraping pipeline. The census tract approach is the best available at this resolution using open data. Each tract has ~4,000 residents and ~1,500 households -- more than fine enough for neighborhood-level policy analysis.

**"What's the most vulnerable neighborhood?"**
Tracts near the Whittier Narrows epicentral zone with pre-1970 housing. Look for dark red polygons in the 34.0°N, -118.0°W area on the map.

---

## How to run the demo

```bash
# Terminal 1: Start the map server
cd app && python -m http.server 3000

# Terminal 2: Start the AI API
uvicorn api.explain:app --reload

# Terminal 3: Open a Marimo notebook (optional, for showing the pipeline)
python demo_marimo.py --step 05
```

Then open http://localhost:3000. Click a dark red tract near the center of the map.

---

## One-liners for each tech stack component

| Component | One-liner |
|---|---|
| Marimo | "Reactive Python notebooks -- like Jupyter but cells can't lie to you" |
| Databricks | "Distributed processing for the 176GB full dataset -- runs in minutes instead of days" |
| Brev L40s | "GPU-accelerated model training -- 30x faster than CPU for XGBoost" |
| OpenAI | "Turns a row of numbers into a sentence a homeowner can actually understand" |
| Leaflet.js | "The map library used by Wikipedia, OpenStreetMap, and half the web" |
| HAZUS | "FEMA's own damage model -- the same curves insurance companies use to price earthquake policies" |
| KD-tree | "Finds the nearest sensor to each neighborhood in milliseconds instead of minutes" |
| Sphinx | "Auto-generates documentation from code -- never out of date because it reads the source" |
