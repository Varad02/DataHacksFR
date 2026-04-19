"""
HAZUS-style fragility curves mapping PGA to expected damage ratio.

Building classes mapped by construction era (from Census year_built):
  - pre_1970: pre-code, most vulnerable
  - code_1973: post-1971 Sylmar, partial code
  - code_1994: post-Northridge, modern code
"""

import numpy as np

# Median PGA (g) at which each building class reaches 50% damage
# Values derived from HAZUS-MH technical manual Table 5.9 (wood-frame residential)
FRAGILITY_PARAMS = {
    "pre_1970":   {"median": 0.30, "beta": 0.64},
    "code_1973":  {"median": 0.45, "beta": 0.64},
    "code_1994":  {"median": 0.60, "beta": 0.64},
}

ERA_MAP = {
    "pre_1970":   (0, 1970),
    "code_1973":  (1970, 1994),
    "code_1994":  (1994, 9999),
}


def year_built_to_era(year_built: float) -> str:
    for era, (low, high) in ERA_MAP.items():
        if low <= year_built < high:
            return era
    return "code_1994"


def lognormal_cdf(x: np.ndarray, median: float, beta: float) -> np.ndarray:
    from scipy.stats import norm
    return norm.cdf(np.log(x / median) / beta)


def damage_ratio(pga_g: np.ndarray, era: str) -> np.ndarray:
    """
    Expected structural damage ratio (0-1) for given PGA and building era.

    pga_g : PGA in units of g
    """
    params = FRAGILITY_PARAMS[era]
    pga_g = np.clip(pga_g, 1e-6, None)
    return lognormal_cdf(pga_g, params["median"], params["beta"])
