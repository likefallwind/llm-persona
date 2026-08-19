# Confirmatory semantic panel

Coverage: **1,074/1,074** annotations; **2,148** response-level units; **8** prespecified descriptive dimensions.

The analysis retains **358** of **360** frozen batches after the audited technical exclusion of **2** paired batches.

Candidate identity was blinded independently for each judge. The confirmatory unit is the response-level median across judges. The labels are prespecified candidate behavioral dimensions, not human personality traits; only dimensions passing the reported validity gates are interpreted as dispositions.

## Judge reliability

| dimension              |   targets |   judges |   icc_3_1 |   icc_3_k |   score_sd |
|:-----------------------|----------:|---------:|----------:|----------:|-----------:|
| help_directness        |      2148 |        3 |     0.760 |     0.905 |      1.480 |
| elicitation            |      2148 |        3 |     0.897 |     0.963 |      1.657 |
| autonomy_support       |      2148 |        3 |     0.601 |     0.819 |      1.298 |
| affective_warmth       |      2148 |        3 |     0.832 |     0.937 |      1.257 |
| diagnostic_specificity |      2148 |        3 |     0.801 |     0.924 |      1.617 |
| personalization        |      2148 |        3 |     0.623 |     0.832 |      1.023 |
| cognitive_load         |      2148 |        3 |     0.663 |     0.855 |      1.023 |
| epistemic_caution      |      2148 |        3 |     0.316 |     0.580 |      0.798 |

Pairwise means:

| dimension              |   exact_agreement |   within_one |   spearman |   quadratic_weighted_kappa |
|:-----------------------|------------------:|-------------:|-----------:|---------------------------:|
| affective_warmth       |             0.624 |        0.943 |      0.860 |                      0.829 |
| autonomy_support       |             0.393 |        0.778 |      0.633 |                      0.570 |
| cognitive_load         |             0.504 |        0.923 |      0.673 |                      0.653 |
| diagnostic_specificity |             0.548 |        0.860 |      0.825 |                      0.802 |
| elicitation            |             0.681 |        0.931 |      0.847 |                      0.897 |
| epistemic_caution      |             0.646 |        0.837 |      0.301 |                      0.302 |
| help_directness        |             0.555 |        0.849 |      0.732 |                      0.760 |
| personalization        |             0.647 |        0.859 |      0.626 |                      0.622 |

## Cross-task stability

| dimension              |   models |   tasks |   icc_3_1_across_tasks |   median_pairwise_task_spearman |   min_pairwise_task_spearman |
|:-----------------------|---------:|--------:|-----------------------:|--------------------------------:|-----------------------------:|
| help_directness        |        6 |       4 |                  0.629 |                           0.647 |                        0.290 |
| elicitation            |        6 |       4 |                  0.475 |                           0.468 |                       -0.123 |
| autonomy_support       |        6 |       4 |                  0.610 |                           0.734 |                        0.600 |
| affective_warmth       |        6 |       4 |                  0.479 |                           0.714 |                        0.543 |
| diagnostic_specificity |        6 |       4 |                  0.203 |                           0.371 |                       -0.086 |
| personalization        |        6 |       4 |                  0.340 |                           0.257 |                       -0.058 |
| cognitive_load         |        6 |       4 |                  0.663 |                           0.677 |                        0.257 |
| epistemic_caution      |        6 |       4 |                  0.035 |                           0.129 |                       -0.655 |

With six models, these are finite-panel descriptive stability estimates; they are not population-level psychometrics.

### Held-out-task model attribution

| feature_set               |   accuracy |   balanced_accuracy |
|:--------------------------|-----------:|--------------------:|
| length_only               |      0.239 |               0.239 |
| semantic                  |      0.322 |               0.322 |
| transparent               |      0.353 |               0.353 |
| transparent_plus_semantic |      0.391 |               0.391 |

Chance is 0.167. Attribution demonstrates a cross-task signature, not by itself a validated disposition.

## Model variance after exact-context control

| dimension              |   partial_eta_squared_model_after_item |   max_minus_min_model_mean |
|:-----------------------|---------------------------------------:|---------------------------:|
| affective_warmth       |                                  0.252 |                      1.068 |
| autonomy_support       |                                  0.196 |                      1.043 |
| cognitive_load         |                                  0.159 |                      0.644 |
| diagnostic_specificity |                                  0.105 |                      0.721 |
| elicitation            |                                  0.214 |                      1.438 |
| epistemic_caution      |                                  0.034 |                      0.214 |
| help_directness        |                                  0.185 |                      1.041 |
| personalization        |                                  0.084 |                      0.497 |

## Same-context prompt intervention

| task              | dimension              |   mean_delta |   models_positive |   models_negative |   models_bh_significant |
|:------------------|:-----------------------|-------------:|------------------:|------------------:|------------------------:|
| mathdial_hard     | affective_warmth       |       -0.254 |                 1 |                 5 |                       2 |
| mathdial_hard     | autonomy_support       |        1.250 |                 6 |                 0 |                       5 |
| mathdial_hard     | cognitive_load         |       -0.721 |                 0 |                 6 |                       5 |
| mathdial_hard     | diagnostic_specificity |       -0.500 |                 0 |                 6 |                       2 |
| mathdial_hard     | elicitation            |        2.171 |                 6 |                 0 |                       6 |
| mathdial_hard     | epistemic_caution      |        0.188 |                 6 |                 0 |                       0 |
| mathdial_hard     | help_directness        |       -1.542 |                 0 |                 6 |                       6 |
| mathdial_hard     | personalization        |        0.042 |                 4 |                 1 |                       0 |
| mathdial_standard | affective_warmth       |       -0.095 |                 1 |                 5 |                       3 |
| mathdial_standard | autonomy_support       |        1.426 |                 6 |                 0 |                       6 |
| mathdial_standard | cognitive_load         |       -0.759 |                 0 |                 6 |                       6 |
| mathdial_standard | diagnostic_specificity |       -0.561 |                 0 |                 6 |                       4 |
| mathdial_standard | elicitation            |        2.470 |                 6 |                 0 |                       6 |
| mathdial_standard | epistemic_caution      |        0.479 |                 6 |                 0 |                       6 |
| mathdial_standard | help_directness        |       -1.709 |                 0 |                 6 |                       6 |
| mathdial_standard | personalization        |        0.049 |                 5 |                 1 |                       2 |

## Judge-family bias audit

| judge           |   own_minus_other_residual |
|:----------------|---------------------------:|
| MiniMax-M3      |                      0.014 |
| deepseek-v4-pro |                      0.009 |
| glm-5.2         |                      0.001 |

Positive values mean the judge scored same-family candidates higher than its residual relative to the other two judges; this is a bias diagnostic, not proof of favoritism.

## Candidate-position audit

| judge           |   residual_points_per_position_slope |   max_minus_min_position_mean |
|:----------------|-------------------------------------:|------------------------------:|
| MiniMax-M3      |                                0.010 |                         0.160 |
| deepseek-v4-pro |                                0.009 |                         0.106 |
| glm-5.2         |                                0.006 |                         0.075 |

Residuals compare each judge with the other judges on the identical response and dimension. Candidate order was independently randomized, so a nonzero position slope diagnoses presentation bias.

## Leave-one-judge-out robustness

| excluded_judge   |   profile_cells |   spearman_vs_all_judges |
|:-----------------|----------------:|-------------------------:|
| MiniMax-M3       |             288 |                    0.961 |
| deepseek-v4-pro  |             288 |                    0.962 |
| glm-5.2          |             288 |                    0.959 |

## Incremental association with existing response quality

| feature_set               |   auc |   brier |   auc_gain_vs_transparent |
|:--------------------------|------:|--------:|--------------------------:|
| semantic_only             | 0.923 |   0.109 |                     0.017 |
| task_item_only            | 0.891 |   0.143 |                    -0.015 |
| transparent_only          | 0.906 |   0.126 |                     0.000 |
| transparent_plus_semantic | 0.921 |   0.111 |                     0.015 |

AUC is evaluated by holding out each candidate model. Association is not evidence that a disposition causally improves learning.

## Independent dialogue-act convergence

| dimension              |   telling_n |   probing_or_focus_n |   telling_minus_probing_or_focus |
|:-----------------------|------------:|---------------------:|---------------------------------:|
| help_directness        |         286 |                  907 |                            1.360 |
| elicitation            |         286 |                  907 |                           -1.914 |
| autonomy_support       |         286 |                  907 |                           -1.244 |
| affective_warmth       |         286 |                  907 |                           -0.083 |
| diagnostic_specificity |         286 |                  907 |                            0.256 |
| personalization        |         286 |                  907 |                           -0.003 |
| cognitive_load         |         286 |                  907 |                            0.593 |
| epistemic_caution      |         286 |                  907 |                           -0.254 |

The classifier was trained only on existing human MathDial dialogue-act labels. This validates alignment with observed tutor moves, not student learning gains.

## Interpretation boundary

A defensible paper claim requires convergence of reliability, cross-task stability, exact-context model variance, intervention sensitivity, and independent action validity. Any dimension failing those gates must be reported as context-specific or measurement-limited rather than as a stable disposition.
