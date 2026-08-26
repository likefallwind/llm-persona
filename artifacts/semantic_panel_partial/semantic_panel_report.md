# Confirmatory semantic panel

Coverage: **405/1,080** annotations; **1,920** response-level units; **8** prespecified descriptive dimensions.

Candidate identity was blinded independently for each judge. The confirmatory unit is the response-level median across judges. The labels are behavioral pedagogical dispositions, not human personality traits.

## Judge reliability

| dimension              |   targets |   judges |   icc_3_1 |   icc_3_k |   score_sd |
|:-----------------------|----------:|---------:|----------:|----------:|-----------:|
| help_directness        |       510 |        2 |     0.670 |     0.802 |      1.016 |
| elicitation            |       510 |        2 |     0.653 |     0.790 |      0.951 |
| autonomy_support       |       510 |        2 |     0.519 |     0.683 |      0.817 |
| affective_warmth       |       510 |        2 |     0.730 |     0.844 |      0.833 |
| diagnostic_specificity |       510 |        2 |     0.785 |     0.879 |      1.312 |
| personalization        |       510 |        2 |     0.154 |     0.267 |      0.488 |
| cognitive_load         |       510 |        2 |     0.448 |     0.619 |      0.692 |
| epistemic_caution      |       510 |        2 |     0.166 |     0.285 |      0.871 |

Pairwise means:

| dimension              |   exact_agreement |   within_one |   spearman |   quadratic_weighted_kappa |
|:-----------------------|------------------:|-------------:|-----------:|---------------------------:|
| affective_warmth       |             0.639 |        0.990 |      0.746 |                      0.721 |
| autonomy_support       |             0.467 |        0.955 |      0.463 |                      0.505 |
| cognitive_load         |             0.539 |        0.976 |      0.398 |                      0.440 |
| diagnostic_specificity |             0.537 |        0.922 |      0.778 |                      0.775 |
| elicitation            |             0.547 |        0.947 |      0.458 |                      0.652 |
| epistemic_caution      |             0.396 |        0.816 |      0.172 |                      0.165 |
| help_directness        |             0.522 |        0.951 |      0.625 |                      0.670 |
| personalization        |             0.714 |        0.961 |      0.173 |                      0.154 |

## Cross-task stability

| dimension              |   models |   tasks |   icc_3_1_across_tasks |   median_pairwise_task_spearman |   min_pairwise_task_spearman |
|:-----------------------|---------:|--------:|-----------------------:|--------------------------------:|-----------------------------:|
| help_directness        |        6 |       3 |                  0.599 |                           0.600 |                        0.314 |
| elicitation            |        6 |       3 |                  0.649 |                           0.870 |                        0.714 |
| autonomy_support       |        6 |       3 |                  0.663 |                           0.771 |                        0.714 |
| affective_warmth       |        6 |       3 |                  0.484 |                           0.943 |                        0.943 |
| diagnostic_specificity |        6 |       3 |                 -0.147 |                          -0.759 |                       -0.941 |
| personalization        |        6 |       3 |                  0.589 |                           0.334 |                        0.213 |
| cognitive_load         |        6 |       3 |                  0.606 |                           0.580 |                        0.309 |
| epistemic_caution      |        6 |       3 |                 -0.179 |                          -0.029 |                       -0.313 |

With six models, these are finite-panel descriptive stability estimates; they are not population-level psychometrics.

### Held-out-task model attribution

| feature_set               |   accuracy |   balanced_accuracy |
|:--------------------------|-----------:|--------------------:|
| length_only               |      0.240 |               0.240 |
| semantic                  |      0.302 |               0.302 |
| transparent               |      0.327 |               0.327 |
| transparent_plus_semantic |      0.369 |               0.369 |

Chance is 0.167. Attribution demonstrates a cross-task signature, not by itself a validated disposition.

## Model variance after exact-context control

| dimension              |   partial_eta_squared_model_after_item |   max_minus_min_model_mean |
|:-----------------------|---------------------------------------:|---------------------------:|
| affective_warmth       |                                  0.227 |                      0.924 |
| autonomy_support       |                                  0.170 |                      1.004 |
| cognitive_load         |                                  0.121 |                      0.534 |
| diagnostic_specificity |                                  0.050 |                      0.469 |
| elicitation            |                                  0.182 |                      1.284 |
| epistemic_caution      |                                  0.026 |                      0.174 |
| help_directness        |                                  0.157 |                      0.935 |
| personalization        |                                  0.073 |                      0.321 |

## Same-context prompt intervention

| task              | dimension              |   mean_delta |   models_positive |   models_negative |   models_bh_significant |
|:------------------|:-----------------------|-------------:|------------------:|------------------:|------------------------:|
| mathdial_hard     | affective_warmth       |       -0.094 |                 3 |                 3 |                       1 |
| mathdial_hard     | autonomy_support       |        1.406 |                 6 |                 0 |                       5 |
| mathdial_hard     | cognitive_load         |       -0.633 |                 0 |                 6 |                       5 |
| mathdial_hard     | diagnostic_specificity |       -0.371 |                 0 |                 6 |                       2 |
| mathdial_hard     | elicitation            |        2.102 |                 6 |                 0 |                       6 |
| mathdial_hard     | epistemic_caution      |        0.325 |                 6 |                 0 |                       3 |
| mathdial_hard     | help_directness        |       -1.492 |                 0 |                 6 |                       6 |
| mathdial_hard     | personalization        |        0.129 |                 5 |                 1 |                       1 |
| mathdial_standard | affective_warmth       |       -0.029 |                 1 |                 5 |                       3 |
| mathdial_standard | autonomy_support       |        1.321 |                 6 |                 0 |                       6 |
| mathdial_standard | cognitive_load         |       -0.710 |                 0 |                 6 |                       6 |
| mathdial_standard | diagnostic_specificity |       -0.196 |                 1 |                 5 |                       4 |
| mathdial_standard | elicitation            |        2.278 |                 6 |                 0 |                       6 |
| mathdial_standard | epistemic_caution      |        0.595 |                 6 |                 0 |                       6 |
| mathdial_standard | help_directness        |       -1.606 |                 0 |                 6 |                       6 |
| mathdial_standard | personalization        |        0.188 |                 6 |                 0 |                       4 |

## Judge-family bias audit

| judge      |   own_minus_other_residual |
|:-----------|---------------------------:|
| MiniMax-M3 |                      0.031 |
| glm-5.2    |                     -0.003 |

Positive values mean the judge scored same-family candidates higher than its residual relative to the other two judges; this is a bias diagnostic, not proof of favoritism.

## Candidate-position audit

| judge      |   residual_points_per_position_slope |   max_minus_min_position_mean |
|:-----------|-------------------------------------:|------------------------------:|
| MiniMax-M3 |                                0.017 |                         0.299 |
| glm-5.2    |                                0.012 |                         0.187 |

Residuals compare each judge with the other judges on the identical response and dimension. Candidate order was independently randomized, so a nonzero position slope diagnoses presentation bias.

## Leave-one-judge-out robustness

| excluded_judge   |   profile_cells |   spearman_vs_all_judges |
|:-----------------|----------------:|-------------------------:|
| MiniMax-M3       |              96 |                    0.641 |
| glm-5.2          |             240 |                    0.996 |

## Incremental association with existing response quality

| feature_set               |   auc |   brier |   auc_gain_vs_transparent |
|:--------------------------|------:|--------:|--------------------------:|
| semantic_only             | 0.922 |   0.109 |                     0.016 |
| task_item_only            | 0.890 |   0.143 |                    -0.016 |
| transparent_only          | 0.906 |   0.126 |                     0.000 |
| transparent_plus_semantic | 0.920 |   0.111 |                     0.014 |

AUC is evaluated by holding out each candidate model. Association is not evidence that a disposition causally improves learning.

## Independent dialogue-act convergence

| dimension              |   telling_n |   probing_or_focus_n |   telling_minus_probing_or_focus |
|:-----------------------|------------:|---------------------:|---------------------------------:|
| help_directness        |         286 |                  919 |                            1.366 |
| elicitation            |         286 |                  919 |                           -1.821 |
| autonomy_support       |         286 |                  919 |                           -1.237 |
| affective_warmth       |         286 |                  919 |                           -0.140 |
| diagnostic_specificity |         286 |                  919 |                            0.161 |
| personalization        |         286 |                  919 |                           -0.075 |
| cognitive_load         |         286 |                  919 |                            0.566 |
| epistemic_caution      |         286 |                  919 |                           -0.331 |

The classifier was trained only on existing human MathDial dialogue-act labels. This validates alignment with observed tutor moves, not student learning gains.

## Interpretation boundary

A defensible paper claim requires convergence of reliability, cross-task stability, exact-context model variance, intervention sensitivity, and independent action validity. Any dimension failing those gates must be reported as context-specific or measurement-limited rather than as a stable disposition.
