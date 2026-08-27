# Normative-boundary candidate axis

Status: **exploratory analysis of frozen EduGuard aggregate/scored data**.
No prompt, response, extracted text, reasoning, gold option set, or item text is exported.

## Cross-context stability

| axis                                  |   models |   contexts |   icc_3_1 |   median_pairwise_spearman |   minimum_pairwise_spearman | icc_gate   | rank_gate   | stability_strength   |
|:--------------------------------------|---------:|-----------:|----------:|---------------------------:|----------------------------:|:-----------|:------------|:---------------------|
| adversarial_attack_success_propensity |        6 |          5 |     0.806 |                      0.943 |                       0.886 | True       | True        | robust_both_metrics  |
| educational_refusal_style             |        6 |          5 |     0.590 |                      0.864 |                       0.086 | True       | True        | robust_both_metrics  |
| sata_incorrect_inclusion_propensity   |        6 |         10 |     0.761 |                      0.714 |                       0.371 | True       | True        | robust_both_metrics  |
| sata_omission_propensity              |        6 |         10 |     0.421 |                      0.696 |                       0.314 | False      | True        | mixed_one_metric     |

## Fixed-panel profiles

| model               |   adversarial_attack_success |   adversarial_boundary_enforcement |   educational_refusal_share |   sata_incorrect_inclusion |   sata_omission |   sata_perfect_match |   sata_rfs |
|:--------------------|-----------------------------:|-----------------------------------:|----------------------------:|---------------------------:|----------------:|---------------------:|-----------:|
| deepseek-v4-pro     |                        0.545 |                              0.455 |                       0.578 |                      0.183 |           0.113 |                0.704 |      0.760 |
| doubao-seed-2.0-pro |                        0.492 |                              0.508 |                       0.624 |                      0.177 |           0.123 |                0.700 |      0.761 |
| glm-5.2             |                        0.198 |                              0.802 |                       0.512 |                      0.135 |           0.207 |                0.658 |      0.761 |
| minimax-m2.7        |                        0.026 |                              0.974 |                       0.390 |                      0.271 |           0.074 |                0.655 |      0.691 |
| minimax-m3          |                        0.033 |                              0.967 |                       0.817 |                      0.185 |           0.090 |                0.724 |      0.768 |
| qwen3.5-4b          |                        0.100 |                              0.900 |                       0.695 |                      0.165 |           0.156 |                0.679 |      0.756 |

## Decision

```json
{
  "status": "exploratory_existing_data",
  "candidate_axis": "normative_boundary_permissiveness",
  "within_task_stability": [
    {
      "axis": "adversarial_attack_success_propensity",
      "models": 6,
      "contexts": 5,
      "icc_3_1": 0.8059533130544854,
      "median_pairwise_spearman": 0.942857142857143,
      "minimum_pairwise_spearman": 0.8857142857142858,
      "icc_gate": true,
      "rank_gate": true,
      "stability_strength": "robust_both_metrics"
    },
    {
      "axis": "educational_refusal_style",
      "models": 6,
      "contexts": 5,
      "icc_3_1": 0.5904607890067727,
      "median_pairwise_spearman": 0.8636082669163618,
      "minimum_pairwise_spearman": 0.08571428571428573,
      "icc_gate": true,
      "rank_gate": true,
      "stability_strength": "robust_both_metrics"
    },
    {
      "axis": "sata_incorrect_inclusion_propensity",
      "models": 6,
      "contexts": 10,
      "icc_3_1": 0.7609299956355015,
      "median_pairwise_spearman": 0.7142857142857143,
      "minimum_pairwise_spearman": 0.3714285714285715,
      "icc_gate": true,
      "rank_gate": true,
      "stability_strength": "robust_both_metrics"
    },
    {
      "axis": "sata_omission_propensity",
      "models": 6,
      "contexts": 10,
      "icc_3_1": 0.4207420489212143,
      "median_pairwise_spearman": 0.6957252427829382,
      "minimum_pairwise_spearman": 0.3142857142857143,
      "icc_gate": false,
      "rank_gate": true,
      "stability_strength": "mixed_one_metric"
    }
  ],
  "cross_task_permissiveness_spearman": -0.48571428571428577,
  "candidate_axis_supported": false,
  "boundary": "Attack success and incorrect option inclusion are safety outcomes as well as behavioral tendencies. The adversarial scorer uses MiniMax-M3, including for MiniMax-M3 candidates. Results cannot establish a judge-independent personality trait or replace selective-safety evaluation."
}
```
