# Objective epistemic-character axes

Status: **outcome-aware exploratory analysis of frozen data**.
No provider response, prompt, reasoning trace, gold answer, or item text is exported.

## Cross-context stability

| axis                               |   models |   contexts |   icc_3_1 |   median_pairwise_spearman |   minimum_pairwise_spearman | icc_gate   | rank_gate   | stability_strength   |
|:-----------------------------------|---------:|-----------:|----------:|---------------------------:|----------------------------:|:-----------|:------------|:---------------------|
| revision_propensity                |        6 |          4 |     0.537 |                      0.472 |                       0.319 | True       | False       | mixed_one_metric     |
| expressed_confidence               |        6 |          4 |     0.852 |                      0.886 |                       0.657 | True       | True        | robust_both_metrics  |
| unanswerable_abstention_propensity |        6 |          5 |     0.346 |                      0.705 |                       0.087 | False      | True        | mixed_one_metric     |

## Fixed-panel profiles

| model               |   revision_propensity |   net_revision_gain |   fix_rate_given_wrong |   break_rate_given_right |   expressed_confidence |   accuracy_under_confidence_prompt |   overconfidence_gap |   brier |   answerable_abstention_rate |   unanswerable_abstention_rate |   abstention_selectivity |   overall_accuracy |   semantic_epistemic_caution |
|:--------------------|----------------------:|--------------------:|-----------------------:|-------------------------:|-----------------------:|-----------------------------------:|---------------------:|--------:|-----------------------------:|-------------------------------:|-------------------------:|-------------------:|-----------------------------:|
| deepseek-v4-pro     |                 0.084 |               0.014 |                  0.111 |                    0.038 |                  0.948 |                              0.673 |                0.275 |   0.285 |                        0.060 |                          0.872 |                    0.812 |              0.892 |                        1.240 |
| doubao-seed-2.0-pro |                 0.019 |              -0.006 |                  0.021 |                    0.015 |                  0.977 |                              0.688 |                0.289 |   0.292 |                        0.036 |                          0.832 |                    0.796 |              0.886 |                        1.088 |
| glm-5.2             |                 0.102 |               0.005 |                  0.125 |                    0.054 |                  0.948 |                              0.672 |                0.275 |   0.294 |                        0.036 |                          0.860 |                    0.824 |              0.896 |                        1.176 |
| minimax-m2.7        |                 0.101 |               0.003 |                  0.094 |                    0.062 |                  0.941 |                              0.467 |                0.473 |   0.468 |                        0.024 |                          0.748 |                    0.724 |              0.838 |                        1.157 |
| minimax-m3          |                 0.068 |               0.012 |                  0.073 |                    0.038 |                  0.878 |                              0.595 |                0.283 |   0.313 |                        0.004 |                          0.748 |                    0.744 |              0.852 |                        1.151 |
| qwen3.5-4b          |                 0.025 |              -0.009 |                  0.014 |                    0.024 |                  0.956 |                              0.547 |                0.409 |   0.409 |                        0.048 |                          0.912 |                    0.864 |              0.914 |                        1.170 |

## Cross-axis convergence checks

| left                       | right                        |   models |   spearman | status                      |
|:---------------------------|:-----------------------------|---------:|-----------:|:----------------------------|
| semantic_epistemic_caution | expressed_confidence         |        6 |     -0.029 | descriptive_only_six_models |
| semantic_epistemic_caution | unanswerable_abstention_rate |        6 |      0.638 | descriptive_only_six_models |
| semantic_epistemic_caution | revision_propensity          |        6 |      0.600 | descriptive_only_six_models |
| expressed_confidence       | unanswerable_abstention_rate |        6 |      0.638 | descriptive_only_six_models |
| revision_propensity        | net_revision_gain            |        6 |      0.486 | descriptive_only_six_models |
| overconfidence_gap         | abstention_selectivity       |        6 |     -0.314 | descriptive_only_six_models |

## Boundary

Revision propensity, expressed confidence, and abstention propensity are
observable response tendencies. Their correctness consequences are not
personality. With six fixed systems, correlations are descriptive and cannot
support model-population or latent-trait claims. The semantic caution score
previously failed reliability and cross-task gates, so convergence with it is
a falsifier rather than a requirement that can promote a new disposition.
