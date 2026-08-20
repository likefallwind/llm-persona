# Prospective factorial and request-order replication results

This report is generated from the complete frozen outputs. It lists every
registered headline gate and the prespecified paper-facing secondary tables.
A replication result can only preserve or downgrade a parent-panel claim.

## Completion

- Parent factorial: 2,560/2,560 responses, five models, 32 base problems.
- Order replication: 640/640 responses, five models, eight fixed base problems.
- Replication order plan: exact 16-cell block balance passed.

## Registered factor gates

| Factor | Parent target effect (95% CI) | Parent selective | Replication target effect (95% CI) | Replication selective | Joint order-robust | Verdict |
|---|---:|:---:|---:|:---:|:---:|---|
| Question policy | 0.773 [0.756, 0.790] | PASS | 0.809 [0.772, 0.841] | PASS | PASS | order-robust black-box component addressability |
| Answer policy | 0.895 [0.883, 0.908] | PASS | 0.922 [0.900, 0.950] | PASS | PASS | order-robust black-box component addressability |
| Tone policy | 0.595 [0.563, 0.623] | PASS | 0.550 [0.497, 0.597] | PASS | PASS | order-robust frozen encouragement-marker effect; not semantic warmth |

## Blind detector validation

This post-result audit is downgrade-only and cannot strengthen the original claim.

| Detector | Coverage | Balanced accuracy (95% CI) | Kappa | Validated |
|---|---:|---:|---:|:---:|
| question_first | 1.000 | 1.000 [1.000, 1.000] | 1.000 | YES |
| answer_reveal_correct | 1.000 | 0.996 [0.989, 1.000] | 0.992 | YES |
| warmth_marker | 1.000 | 0.818 [0.787, 0.847] | 0.631 | NO |

## Target effects for every model

| Factor | Model | Full parent | Matching parent subset | Randomized replication | Positive in subset and replication |
|---|---|---:|---:|---:|:---:|
| Question policy | MiniMax-M2.7 | 0.477 | 0.500 | 0.531 | YES |
| Question policy | MiniMax-M3 | 0.594 | 0.609 | 0.656 | YES |
| Question policy | deepseek-v4-pro | 0.930 | 0.875 | 0.953 | YES |
| Question policy | doubao-seed-2.0-lite | 0.996 | 0.984 | 1.000 | YES |
| Question policy | glm-5.2 | 0.867 | 0.906 | 0.906 | YES |
| Answer policy | MiniMax-M2.7 | 0.707 | 0.797 | 0.828 | YES |
| Answer policy | MiniMax-M3 | 0.824 | 0.797 | 0.828 | YES |
| Answer policy | deepseek-v4-pro | 0.992 | 0.984 | 0.984 | YES |
| Answer policy | doubao-seed-2.0-lite | 0.953 | 0.922 | 0.984 | YES |
| Answer policy | glm-5.2 | 1.000 | 1.000 | 0.984 | YES |
| Tone policy | MiniMax-M2.7 | 0.633 | 0.703 | 0.531 | YES |
| Tone policy | MiniMax-M3 | 0.637 | 0.547 | 0.562 | YES |
| Tone policy | deepseek-v4-pro | 0.602 | 0.641 | 0.609 | YES |
| Tone policy | doubao-seed-2.0-lite | 0.590 | 0.547 | 0.531 | YES |
| Tone policy | glm-5.2 | 0.512 | 0.531 | 0.516 | YES |

## Aggregate target and cross-effects

| Panel | Factor | Outcome | Mean difference (95% CI) | Target outcome |
|---|---|---|---:|:---:|
| Parent | Question policy | question_first | 0.773 [0.756, 0.790] | YES |
| Parent | Question policy | answer_reveal_correct | -0.008 [-0.023, 0.008] | NO |
| Parent | Question policy | warmth_marker | 0.076 [0.055, 0.098] | NO |
| Parent | Answer policy | question_first | 0.079 [0.061, 0.097] | NO |
| Parent | Answer policy | answer_reveal_correct | 0.895 [0.883, 0.908] | YES |
| Parent | Answer policy | warmth_marker | -0.016 [-0.050, 0.018] | NO |
| Parent | Tone policy | question_first | -0.118 [-0.132, -0.104] | NO |
| Parent | Tone policy | answer_reveal_correct | 0.006 [-0.005, 0.019] | NO |
| Parent | Tone policy | warmth_marker | 0.595 [0.563, 0.623] | YES |
| Replication | Question policy | question_first | 0.809 [0.772, 0.841] | YES |
| Replication | Question policy | answer_reveal_correct | 0.016 [-0.009, 0.047] | NO |
| Replication | Question policy | warmth_marker | 0.062 [0.025, 0.103] | NO |
| Replication | Answer policy | question_first | 0.097 [0.078, 0.119] | NO |
| Replication | Answer policy | answer_reveal_correct | 0.922 [0.900, 0.950] | YES |
| Replication | Answer policy | warmth_marker | -0.031 [-0.078, 0.009] | NO |
| Replication | Tone policy | question_first | -0.103 [-0.125, -0.078] | NO |
| Replication | Tone policy | answer_reveal_correct | 0.016 [-0.009, 0.041] | NO |
| Replication | Tone policy | warmth_marker | 0.550 [0.497, 0.597] | YES |

## Learner-request effects for every model

| Panel | Group | Contrast | Mean difference (95% CI) |
|---|---|---|---:|
| Parent | ALL | direct_minus_explore_reveal | 0.073 [0.061, 0.085] |
| Parent | MiniMax-M2.7 | direct_minus_explore_reveal | 0.184 [0.133, 0.238] |
| Parent | MiniMax-M3 | direct_minus_explore_reveal | 0.176 [0.141, 0.215] |
| Parent | deepseek-v4-pro | direct_minus_explore_reveal | 0.000 [-0.012, 0.012] |
| Parent | doubao-seed-2.0-lite | direct_minus_explore_reveal | 0.008 [-0.008, 0.023] |
| Parent | glm-5.2 | direct_minus_explore_reveal | 0.000 [0.000, 0.000] |
| Parent | ALL | explore_minus_direct_question | -0.030 [-0.047, -0.014] |
| Parent | MiniMax-M2.7 | explore_minus_direct_question | -0.070 [-0.125, -0.016] |
| Parent | MiniMax-M3 | explore_minus_direct_question | -0.062 [-0.098, -0.031] |
| Parent | deepseek-v4-pro | explore_minus_direct_question | 0.008 [-0.020, 0.035] |
| Parent | doubao-seed-2.0-lite | explore_minus_direct_question | 0.004 [0.000, 0.012] |
| Parent | glm-5.2 | explore_minus_direct_question | -0.031 [-0.074, 0.012] |
| Replication | ALL | direct_minus_explore_reveal | 0.066 [0.041, 0.087] |
| Replication | MiniMax-M2.7 | direct_minus_explore_reveal | 0.141 [0.016, 0.266] |
| Replication | MiniMax-M3 | direct_minus_explore_reveal | 0.172 [0.109, 0.234] |
| Replication | deepseek-v4-pro | direct_minus_explore_reveal | -0.016 [-0.047, 0.000] |
| Replication | doubao-seed-2.0-lite | direct_minus_explore_reveal | 0.016 [0.000, 0.047] |
| Replication | glm-5.2 | direct_minus_explore_reveal | 0.016 [0.000, 0.047] |
| Replication | ALL | explore_minus_direct_question | -0.016 [-0.037, 0.006] |
| Replication | MiniMax-M2.7 | explore_minus_direct_question | -0.062 [-0.156, 0.031] |
| Replication | MiniMax-M3 | explore_minus_direct_question | 0.000 [-0.078, 0.078] |
| Replication | deepseek-v4-pro | explore_minus_direct_question | -0.047 [-0.109, 0.000] |
| Replication | doubao-seed-2.0-lite | explore_minus_direct_question | 0.000 [0.000, 0.000] |
| Replication | glm-5.2 | explore_minus_direct_question | 0.031 [-0.031, 0.078] |

## Family target effects

| Panel | Family | Factor | Mean difference |
|---|---|---|---:|
| Parent | arithmetic_mean | Answer policy | 0.928 |
| Parent | arithmetic_mean | Question policy | 0.775 |
| Parent | arithmetic_mean | Tone policy | 0.659 |
| Parent | fraction_addition | Answer policy | 0.878 |
| Parent | fraction_addition | Question policy | 0.787 |
| Parent | fraction_addition | Tone policy | 0.581 |
| Parent | linear_equation | Answer policy | 0.897 |
| Parent | linear_equation | Question policy | 0.778 |
| Parent | linear_equation | Tone policy | 0.613 |
| Parent | percentage_discount | Answer policy | 0.878 |
| Parent | percentage_discount | Question policy | 0.750 |
| Parent | percentage_discount | Tone policy | 0.525 |
| Replication | arithmetic_mean | Answer policy | 0.975 |
| Replication | arithmetic_mean | Question policy | 0.812 |
| Replication | arithmetic_mean | Tone policy | 0.512 |
| Replication | fraction_addition | Answer policy | 0.900 |
| Replication | fraction_addition | Question policy | 0.812 |
| Replication | fraction_addition | Tone policy | 0.600 |
| Replication | linear_equation | Answer policy | 0.925 |
| Replication | linear_equation | Question policy | 0.863 |
| Replication | linear_equation | Tone policy | 0.487 |
| Replication | percentage_discount | Answer policy | 0.887 |
| Replication | percentage_discount | Question policy | 0.750 |
| Replication | percentage_discount | Tone policy | 0.600 |

## ALL-group interactions on primary outcomes

| Panel | Order | Factors | Outcome | Interaction (95% CI) |
|---|---:|---|---|---:|
| Parent | 2 | answer_policy*tone_policy | answer_reveal_correct | 0.016 [-0.008, 0.042] |
| Parent | 2 | answer_policy*tone_policy | question_first | 0.102 [0.066, 0.139] |
| Parent | 2 | answer_policy*tone_policy | warmth_marker | -0.030 [-0.097, 0.041] |
| Parent | 2 | question_policy*answer_policy | answer_reveal_correct | -0.012 [-0.044, 0.020] |
| Parent | 2 | question_policy*answer_policy | question_first | 0.158 [0.120, 0.194] |
| Parent | 2 | question_policy*answer_policy | warmth_marker | 0.008 [-0.048, 0.066] |
| Parent | 2 | question_policy*tone_policy | answer_reveal_correct | 0.016 [-0.020, 0.050] |
| Parent | 2 | question_policy*tone_policy | question_first | -0.236 [-0.266, -0.208] |
| Parent | 2 | question_policy*tone_policy | warmth_marker | 0.155 [0.112, 0.195] |
| Parent | 3 | question_policy*answer_policy*tone_policy | answer_reveal_correct | 0.025 [-0.047, 0.094] |
| Parent | 3 | question_policy*answer_policy*tone_policy | question_first | 0.203 [0.138, 0.278] |
| Parent | 3 | question_policy*answer_policy*tone_policy | warmth_marker | 0.009 [-0.103, 0.116] |
| Replication | 2 | answer_policy*tone_policy | answer_reveal_correct | 0.031 [-0.019, 0.081] |
| Replication | 2 | answer_policy*tone_policy | question_first | 0.119 [0.069, 0.169] |
| Replication | 2 | answer_policy*tone_policy | warmth_marker | -0.062 [-0.163, 0.012] |
| Replication | 2 | question_policy*answer_policy | answer_reveal_correct | 0.031 [-0.025, 0.094] |
| Replication | 2 | question_policy*answer_policy | question_first | 0.194 [0.156, 0.237] |
| Replication | 2 | question_policy*answer_policy | warmth_marker | 0.013 [-0.075, 0.113] |
| Replication | 2 | question_policy*tone_policy | answer_reveal_correct | 0.019 [-0.031, 0.062] |
| Replication | 2 | question_policy*tone_policy | question_first | -0.206 [-0.256, -0.162] |
| Replication | 2 | question_policy*tone_policy | warmth_marker | 0.125 [0.050, 0.206] |
| Replication | 3 | question_policy*answer_policy*tone_policy | answer_reveal_correct | 0.037 [-0.050, 0.125] |
| Replication | 3 | question_policy*answer_policy*tone_policy | question_first | 0.237 [0.125, 0.350] |
| Replication | 3 | question_policy*answer_policy*tone_policy | warmth_marker | 0.025 [-0.162, 0.225] |

## Interpretation boundary

- Effects measure black-box instruction following on five frozen deployed systems.
- A failed selectivity or replication gate remains a central negative result.
- System-over-user behavior is instruction-hierarchy behavior, not empathy or learner understanding.
- Correct answer formatting is not tutoring quality or learning gain.
- The encouragement lexicon fails semantic warmth validation; its effects are literal marker effects only.
- Full released CSV files retain all surface outcomes, model groups, cells, and interactions.
