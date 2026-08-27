# Prompt-contingent pedagogical policy signatures

Paired semantic response units: **11,424**; models: **6**; tasks: **2**; dimensions: **8**.

**Decision:** `prompt_contingent_policy_signatures_supported`

This secondary audit separates **default model differences**, **shared prompt deformation**, and **model-specific elasticity**. It is outcome-aware and cannot upgrade the frozen disposition decision.

## Exact-context variance decomposition

| task              | dimension              |   eta_squared_model |   eta_squared_prompt |   eta_squared_model_by_prompt |   prompt_to_model_ss_ratio |
|:------------------|:-----------------------|--------------------:|---------------------:|------------------------------:|---------------------------:|
| mathdial_hard     | affective_warmth       |              0.1128 |               0.0140 |                        0.0288 |                     0.1240 |
| mathdial_hard     | autonomy_support       |              0.0737 |               0.2536 |                        0.0371 |                     3.4419 |
| mathdial_hard     | cognitive_load         |              0.0355 |               0.1834 |                        0.0289 |                     5.1593 |
| mathdial_hard     | diagnostic_specificity |              0.0296 |               0.0285 |                        0.0054 |                     0.9633 |
| mathdial_hard     | elicitation            |              0.0777 |               0.3758 |                        0.0313 |                     4.8371 |
| mathdial_hard     | epistemic_caution      |              0.0013 |               0.0286 |                        0.0020 |                    21.7742 |
| mathdial_hard     | help_directness        |              0.0401 |               0.2679 |                        0.0266 |                     6.6846 |
| mathdial_hard     | personalization        |              0.0395 |               0.0030 |                        0.0060 |                     0.0760 |
| mathdial_standard | affective_warmth       |              0.1793 |               0.0026 |                        0.0343 |                     0.0145 |
| mathdial_standard | autonomy_support       |              0.0859 |               0.3302 |                        0.0381 |                     3.8427 |
| mathdial_standard | cognitive_load         |              0.0499 |               0.1989 |                        0.0218 |                     3.9872 |
| mathdial_standard | diagnostic_specificity |              0.0109 |               0.0360 |                        0.0120 |                     3.3070 |
| mathdial_standard | elicitation            |              0.0673 |               0.5071 |                        0.0322 |                     7.5319 |
| mathdial_standard | epistemic_caution      |              0.0151 |               0.1017 |                        0.0066 |                     6.7473 |
| mathdial_standard | help_directness        |              0.0615 |               0.3206 |                        0.0315 |                     5.2106 |
| mathdial_standard | personalization        |              0.0216 |               0.0026 |                        0.0084 |                     0.1193 |

The prompt and model-by-prompt columns are descriptive balanced sums of squares after exact-context control. They quantify observed behavioral deformation; they are not population-level model variance estimates.

## Model-specific elasticity

| task              | dimension              |   max_minus_min_model_delta |   permutation_p |   permutation_q_within_task |
|:------------------|:-----------------------|----------------------------:|----------------:|----------------------------:|
| mathdial_hard     | affective_warmth       |                      1.1750 |          0.0024 |                      0.0038 |
| mathdial_hard     | autonomy_support       |                      1.4000 |          0.0002 |                      0.0005 |
| mathdial_hard     | cognitive_load         |                      0.8500 |          0.0006 |                      0.0012 |
| mathdial_hard     | diagnostic_specificity |                      0.6000 |          0.3815 |                      0.5087 |
| mathdial_hard     | elicitation            |                      1.9500 |          0.0002 |                      0.0005 |
| mathdial_hard     | epistemic_caution      |                      0.1500 |          0.8890 |                      0.8890 |
| mathdial_hard     | help_directness        |                      1.3500 |          0.0002 |                      0.0005 |
| mathdial_hard     | personalization        |                      0.1750 |          0.7353 |                      0.8403 |
| mathdial_standard | affective_warmth       |                      1.0633 |          0.0002 |                      0.0003 |
| mathdial_standard | autonomy_support       |                      1.4304 |          0.0002 |                      0.0003 |
| mathdial_standard | cognitive_load         |                      0.7595 |          0.0002 |                      0.0003 |
| mathdial_standard | diagnostic_specificity |                      0.9367 |          0.0002 |                      0.0003 |
| mathdial_standard | elicitation            |                      1.8354 |          0.0002 |                      0.0003 |
| mathdial_standard | epistemic_caution      |                      0.3544 |          0.0340 |                      0.0340 |
| mathdial_standard | help_directness        |                      1.2532 |          0.0002 |                      0.0003 |
| mathdial_standard | personalization        |                      0.2911 |          0.0022 |                      0.0025 |

The permutation test shuffles model labels within each paired context. A low adjusted value indicates that the fixed models do not merely share one common prompt effect.

## Residual identity across prompts

| train_arm   | test_arm   | train_task   | test_task   |   train_responses |   test_responses |   feature_count |   model_count |   chance_accuracy |   accuracy |   balanced_accuracy |   bootstrap_ci_low |   bootstrap_ci_high |
|:------------|:-----------|:-------------|:------------|------------------:|-----------------:|----------------:|--------------:|------------------:|-----------:|--------------------:|-------------------:|--------------------:|
| generic     | pedagogy   | ALL          | ALL         |               714 |              714 |               8 |             6 |            0.1667 |     0.3011 |              0.3011 |             0.2635 |              0.3348 |
| pedagogy    | generic    | ALL          | ALL         |               714 |              714 |               8 |             6 |            0.1667 |     0.2969 |              0.2969 |             0.2664 |              0.3262 |

Above-chance transfer means prompt steering did not erase model-conditioned response geometry. It remains a behavioral signature, not proof of an inner or human-like personality.

## Prompt movement relative to default model spread

| task              | dimension              |   baseline_model_range |   shared_prompt_mean_delta |   absolute_prompt_over_baseline_range |   ratio_bootstrap_ci_low |   ratio_bootstrap_ci_high |
|:------------------|:-----------------------|-----------------------:|---------------------------:|--------------------------------------:|-------------------------:|--------------------------:|
| mathdial_standard | affective_warmth       |                 1.4684 |                    -0.0949 |                                0.0647 |                   0.0066 |                    0.1330 |
| mathdial_standard | autonomy_support       |                 1.7722 |                     1.4262 |                                0.8048 |                   0.6385 |                    1.0289 |
| mathdial_standard | cognitive_load         |                 0.6835 |                    -0.7595 |                                1.1111 |                   0.7851 |                    1.4007 |
| mathdial_standard | diagnostic_specificity |                 0.4430 |                    -0.5612 |                                1.2667 |                   0.6775 |                    2.1827 |
| mathdial_standard | elicitation            |                 2.1519 |                     2.4705 |                                1.1480 |                   0.9458 |                    1.4374 |
| mathdial_standard | epistemic_caution      |                 0.2785 |                     0.4789 |                                1.7197 |                   0.8333 |                    3.5641 |
| mathdial_standard | help_directness        |                 1.7089 |                    -1.7089 |                                1.0000 |                   0.8300 |                    1.2040 |
| mathdial_standard | personalization        |                 0.3671 |                     0.0485 |                                0.1322 |                   0.0067 |                    0.3272 |
| mathdial_hard     | affective_warmth       |                 1.5500 |                    -0.2542 |                                0.1640 |                   0.0714 |                    0.2528 |
| mathdial_hard     | autonomy_support       |                 1.5750 |                     1.2500 |                                0.7937 |                   0.5863 |                    1.0357 |
| mathdial_hard     | cognitive_load         |                 0.8500 |                    -0.7208 |                                0.8480 |                   0.5854 |                    1.2143 |
| mathdial_hard     | diagnostic_specificity |                 0.9250 |                    -0.5000 |                                0.5405 |                   0.2348 |                    0.9444 |
| mathdial_hard     | elicitation            |                 2.2000 |                     2.1708 |                                0.9867 |                   0.7767 |                    1.3010 |
| mathdial_hard     | epistemic_caution      |                 0.1000 |                     0.1875 |                                1.8750 |                   0.1458 |                    3.7500 |
| mathdial_hard     | help_directness        |                 1.5250 |                    -1.5417 |                                1.0109 |                   0.7584 |                    1.3611 |
| mathdial_hard     | personalization        |                 0.3250 |                     0.0417 |                                0.1282 |                   0.0072 |                    0.4286 |

## Rank stability and reversals

| task              | dimension              |   generic_to_pedagogy_spearman |   pairwise_rank_reversals |   rank_reversal_fraction |
|:------------------|:-----------------------|-------------------------------:|--------------------------:|-------------------------:|
| mathdial_hard     | affective_warmth       |                         0.7827 |                         2 |                   0.1429 |
| mathdial_hard     | autonomy_support       |                         0.9276 |                         1 |                   0.0714 |
| mathdial_hard     | cognitive_load         |                         0.2609 |                         6 |                   0.4286 |
| mathdial_hard     | diagnostic_specificity |                         0.6377 |                         3 |                   0.2143 |
| mathdial_hard     | elicitation            |                         0.6667 |                         3 |                   0.2143 |
| mathdial_hard     | epistemic_caution      |                        -0.1540 |                         7 |                   0.5833 |
| mathdial_hard     | help_directness        |                         0.2029 |                         6 |                   0.4286 |
| mathdial_hard     | personalization        |                         0.9559 |                         0 |                   0.0000 |
| mathdial_standard | affective_warmth       |                         0.4058 |                         4 |                   0.2857 |
| mathdial_standard | autonomy_support       |                         0.5798 |                         4 |                   0.2857 |
| mathdial_standard | cognitive_load         |                         0.5294 |                         4 |                   0.3077 |
| mathdial_standard | diagnostic_specificity |                        -0.2571 |                         9 |                   0.6000 |
| mathdial_standard | elicitation            |                         0.6000 |                         4 |                   0.2667 |
| mathdial_standard | epistemic_caution      |                         0.1449 |                         6 |                   0.4286 |
| mathdial_standard | help_directness        |                         0.3714 |                         5 |                   0.3333 |
| mathdial_standard | personalization        |                         0.3714 |                         5 |                   0.3333 |

## Floor/ceiling-adjusted elasticity sensitivity

| task              | dimension              |   complete_nonboundary_contexts |   retained_context_fraction |   max_minus_min_adjusted_elasticity |   permutation_p |   permutation_q_within_task |
|:------------------|:-----------------------|--------------------------------:|----------------------------:|------------------------------------:|----------------:|----------------------------:|
| mathdial_hard     | affective_warmth       |                              18 |                      0.4500 |                              0.4630 |          0.4389 |                      0.7023 |
| mathdial_hard     | autonomy_support       |                              36 |                      0.9000 |                              0.6088 |          0.0002 |                      0.0016 |
| mathdial_hard     | cognitive_load         |                              16 |                      0.4000 |                              0.2812 |          0.4351 |                      0.7023 |
| mathdial_hard     | diagnostic_specificity |                              21 |                      0.5250 |                              0.2183 |          0.8324 |                      0.9650 |
| mathdial_hard     | elicitation            |                              19 |                      0.4750 |                              0.4474 |          0.0004 |                      0.0016 |
| mathdial_hard     | epistemic_caution      |                              40 |                      1.0000 |                              0.0562 |          0.9650 |                      0.9650 |
| mathdial_hard     | help_directness        |                              31 |                      0.7750 |                              0.4059 |          0.0058 |                      0.0155 |
| mathdial_hard     | personalization        |                              38 |                      0.9500 |                              0.0570 |          0.8998 |                      0.9650 |
| mathdial_standard | affective_warmth       |                              50 |                      0.6329 |                              0.5800 |          0.0002 |                      0.0003 |
| mathdial_standard | autonomy_support       |                              70 |                      0.8861 |                              0.3595 |          0.0008 |                      0.0011 |
| mathdial_standard | cognitive_load         |                              36 |                      0.4557 |                              0.5324 |          0.0002 |                      0.0003 |
| mathdial_standard | diagnostic_specificity |                              53 |                      0.6709 |                              0.4513 |          0.0002 |                      0.0003 |
| mathdial_standard | elicitation            |                              41 |                      0.5190 |                              0.3598 |          0.0002 |                      0.0003 |
| mathdial_standard | epistemic_caution      |                              76 |                      0.9620 |                              0.1206 |          0.2254 |                      0.2254 |
| mathdial_standard | help_directness        |                              58 |                      0.7342 |                              0.4282 |          0.0002 |                      0.0003 |
| mathdial_standard | personalization        |                              79 |                      1.0000 |                              0.1213 |          0.0026 |                      0.0030 |

This sensitivity divides movement by the directional headroom available on the 1--5 scale. It tests whether elasticity heterogeneity survives the most direct floor/ceiling explanation.

## Decision audit

| check                                                                   | passed   |
|:------------------------------------------------------------------------|:---------|
| at_least_two_frozen_cross_task_signatures                               | True     |
| shared_prompt_compresses_nine_model_profiles                            | True     |
| at_least_two_reliable_dimensions_shift_in_both_tasks                    | True     |
| at_least_two_reliable_dimensions_move_at_least_0_75_baseline_range      | True     |
| model_identity_transfers_across_prompt_arms_and_tasks                   | True     |
| replicated_model_specific_semantic_elasticity_after_headroom_adjustment | True     |

## Interpretation

The supported object is a prompt-contingent policy response surface: a model-conditioned default plus a shared intervention effect and, where replicated, a model-specific response. Strong instruction following does not establish context-appropriate action selection, learner-state understanding, or learning benefit.

Boundary: The audit characterizes observable prompt-contingent tutor policies in a fixed deployed-model panel. It does not upgrade the frozen disposition decision, establish human-like personality, infer learner understanding, or demonstrate learning gains.
