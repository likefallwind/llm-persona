# Human preference calibration of the planned semantic judges

The calibration set contains 482 expert-labelled positive/negative teacher-response pairs, each shown in both A/B orders (964 items). These data predate the semantic study and require no new API calls.

## Agreement with expert preference

| judge_or_ensemble         |   agreement |   cluster_bootstrap_ci_low |   cluster_bootstrap_ci_high |
|:--------------------------|------------:|---------------------------:|----------------------------:|
| MiniMax-M3                |       0.844 |                      0.815 |                       0.872 |
| glm-5.2                   |       0.839 |                      0.808 |                       0.869 |
| deepseek-v4-pro           |       0.817 |                      0.784 |                       0.849 |
| majority                  |       0.835 |                      0.804 |                       0.865 |
| majority_minus_MiniMax-M3 |      -0.009 |                     -0.027 |                       0.007 |

Intervals resample the 482 underlying preference pairs and preserve both presentation orders.

## Position robustness

| judge           |   complete_pairs |   position_consistency |   positive_both_orders |   negative_both_orders |
|:----------------|-----------------:|-----------------------:|-----------------------:|-----------------------:|
| MiniMax-M3      |              482 |                  0.900 |                  0.795 |                  0.106 |
| deepseek-v4-pro |              482 |                  0.913 |                  0.774 |                  0.139 |
| glm-5.2         |              482 |                  0.919 |                  0.799 |                  0.120 |

## Pairwise judge agreement

| judge_left   | judge_right     |   raw_agreement |   cohen_kappa |
|:-------------|:----------------|----------------:|--------------:|
| MiniMax-M3   | glm-5.2         |           0.897 |         0.614 |
| MiniMax-M3   | deepseek-v4-pro |           0.892 |         0.617 |
| glm-5.2      | deepseek-v4-pro |           0.920 |         0.719 |

## Error overlap

|   expert_pair_order_items |   all_three_correct |   exactly_two_correct |   exactly_one_correct |   all_three_wrong |
|--------------------------:|--------------------:|----------------------:|----------------------:|------------------:|
|                       964 |                 733 |                    72 |                    68 |                91 |

## Interpretation boundary

This establishes that the three models are competent and reasonably position-stable on human pedagogical preference pairs. It does not validate the eight descriptive semantic dimensions, eliminate shared LLM variance, or turn majority vote into human ground truth.
