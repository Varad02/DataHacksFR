# Submission Results

## Scenario Test Results

| scenario | n_tracts | mean_expected_loss | median_expected_loss | p95_expected_loss | max_expected_loss | mean_damage_ratio | max_pga_g |
|---|---|---|---|---|---|---|---|
| dummy_next_7y | 2498 | 38676.70511180133 | 18154.670211460838 | 131374.77278657237 | 1102371.8945529936 | 0.04679001953520613 | 0.48 |
| northridge_1994 | 2498 | 77717.67682878471 | 48501.95391386187 | 261286.72246291925 | 1419445.4307872436 | 0.09466224604895516 | 0.65 |

## Visuals

### Mean Expected Loss by Scenario
![Mean Expected Loss by Scenario](figures/mean_expected_loss_by_scenario.png)
Comparison of average expected losses across the two earthquake scenarios (dummy_next_7y and northridge_1994).

### Expected Loss Distribution (Boxplot)
![Expected Loss Boxplot by Scenario](figures/expected_loss_boxplot_by_scenario.png)
Distribution of expected losses across all tracts for each scenario, showing median, quartiles, and outliers.

### Northridge Top 10 Affected Tracts
![Northridge Top 10 Tracts](figures/northridge_top10_tracts.png)
Map visualization of the 10 census tracts with the highest expected losses from the Northridge 1994 earthquake.

### Damage Ratio by Building Era
![Northridge Damage Ratio by Era](figures/northridge_damage_ratio_by_era.png)
Analysis of damage severity across different building eras during the Northridge earthquake scenario.

## Model Training Smoke Metrics

- MAE: 0.01567
- R2: 0.90189
- Training seconds: 0.04
- Runtime: {'tree_method': 'hist', 'device': 'cpu'}

## Test Command

```bash
source venv/bin/activate
python -m unittest discover -s tests -p "test_*.py" -v
```