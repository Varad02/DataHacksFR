# Why This Project Matters

---

## Is this real or academic?

**It's real, and it's a known gap.**

The components individually are all production-grade:
- **FEMA HAZUS** -- used by every US county for disaster planning and FEMA grant allocation. Real government decisions are made with it today.
- **USGS ShakeMap** -- deployed within minutes of every earthquake. Emergency managers use it to dispatch resources.
- **Physics-based simulation** -- what makes Scripps's dataset cutting-edge. Most deployed tools use statistical equations (GMPEs). Physics-based is more accurate near faults and is where the research frontier is.

The gap we fill is real. Companies like RMS, AIR Worldwide, and CoreLogic do proprietary versions of exactly this for insurance pricing -- and charge millions for it. There is no free, open, neighborhood-level version. That is the actual hole in the market.

---

## How often do major earthquakes happen in LA?

From USGS UCERF3 (the authoritative forecast):

| Scenario | Probability in next 30 years |
|---|---|
| M6.7+ anywhere in California | ~99% |
| M6.7+ in Southern California | ~60% |
| M7.8+ "Big One" on San Andreas | ~60% |
| Another Northridge-equivalent in LA | Roughly every 15-30 years |

The last major LA earthquake was Northridge in **1994 -- 30 years ago.** Statistically, another one is not decades away. It could be tomorrow.

Small earthquakes (M3-4) happen several times a year in LA. M5+ happen every few years. The question is not whether -- it is when.

---

## How to justify it before the next earthquake

You do not need the earthquake to happen for this to be useful. The value is generated now, in decisions made before it hits.

**1. Insurance pricing -- happens every single year**
The California Earthquake Authority prices policies right now based on coarse USGS zones. A neighborhood-level model would let them price more accurately. That is billions of dollars of market impact annually, no earthquake required.

**2. Retrofit prioritization**
After Northridge, LA spent 25 years retrofitting ~15,000 soft-story apartment buildings. A tool like this would have told them exactly which neighborhoods to prioritize on day one. LA still has unreinforced masonry buildings that need retrofitting -- this tells you where.

**3. Real estate and lending**
Banks assess earthquake risk in mortgage portfolios today. Buyers want neighborhood-level risk before purchasing. Zillow already shows flood risk scores per listing -- earthquake loss is the missing layer.

**4. City planning and building codes**
Cities use risk maps to decide where to require stronger construction. Census tract resolution is exactly the granularity planners need.

**5. Emergency pre-positioning**
Hospitals, fire stations, and supply caches need to be placed before the earthquake. Knowing which tracts face $800k average losses tells you where demand will be highest.

---

## The one-line justification

> "You do not buy fire insurance after your house burns down. This is the earthquake equivalent of knowing your fire risk before you need it -- at the neighborhood level, for free, for the first time."

---

## Why this project specifically is defensible

The Scripps simulation models the **Whittier Narrows fault**, which already ruptured in 1987 (M5.9, $360M damage). The 500 scenarios in the dataset are physically realistic ruptures on a real fault that is capable of a larger event. This is not a made-up scenario -- it is a well-studied fault with documented history sitting under one of the most densely populated and valuable real estate markets in the world.

The combination of physics-based simulation + granular property data + income distribution at census tract level is research-frontier. It exists in proprietary form at companies like RMS and AIR Worldwide. It does not exist as a free, open, reproducible tool. That is what we built.
