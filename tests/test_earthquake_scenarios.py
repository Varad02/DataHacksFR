import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.models.scenario_cases import SCENARIOS, simulate_scenario


class ScenarioTests(unittest.TestCase):
    def setUp(self) -> None:
        # Synthetic tract sample spanning vulnerable to modern stock.
        self.df = pd.DataFrame(
            {
                "tract": ["A", "B", "C", "D"],
                "era": ["pre_1970", "code_1973", "code_1994", "pre_1970"],
                "pga_g_raw": [0.10, 0.22, 0.30, 0.45],
                "home_value": [380_000, 520_000, 740_000, 460_000],
            }
        )

    def test_northridge_1994_conditions(self) -> None:
        result = simulate_scenario(self.df, SCENARIOS["northridge_1994"])

        self.assertTrue((result["pga_g"] >= 0).all())
        self.assertLessEqual(float(result["pga_g"].max()), 0.65 + 1e-9)
        self.assertTrue((result["expected_loss"] > 0).all())

        # Older stock should generally show higher fragility for similar shaking.
        pre_code = result[result["era"] == "pre_1970"]["damage_ratio"].mean()
        modern = result[result["era"] == "code_1994"]["damage_ratio"].mean()
        self.assertGreater(pre_code, modern)

    def test_dummy_next_7_year_scenario(self) -> None:
        result = simulate_scenario(self.df, SCENARIOS["dummy_next_7y"])

        self.assertLessEqual(float(result["pga_g"].max()), 0.48 + 1e-9)
        self.assertTrue((result["expected_loss"] > 0).all())

        # Retrofit multiplier should suppress raw damage ratio impact.
        baseline = simulate_scenario(self.df, SCENARIOS["northridge_1994"])
        self.assertLess(result["damage_ratio"].mean(), baseline["damage_ratio"].mean())



if __name__ == "__main__":
    unittest.main()
