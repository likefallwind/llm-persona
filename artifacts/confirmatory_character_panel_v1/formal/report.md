# Theory-grounded educational-character panel

Status: **formal analysis**; successful judge calls: **1160/1160**.
No raw educational context, candidate response, or reasoning trace is exported.

## Measurement and stability

| dimension               |   targets |   judges |   icc_3_1 |   icc_3_k |   score_sd_all_judges |   responses |   score_mean |   score_sd |   floor_fraction |   ceiling_fraction |   unique_scores |   models |   tasks |   icc_3_1_stability |   median_pairwise_spearman |   minimum_pairwise_spearman |
|:------------------------|----------:|---------:|----------:|----------:|----------------------:|------------:|-------------:|-----------:|-----------------:|-------------------:|----------------:|---------:|--------:|--------------------:|---------------------------:|----------------------------:|
| instructional_agency    |      1740 |        4 |     0.692 |     0.900 |                 0.999 |        1740 |        3.680 |      0.893 |            0.010 |              0.182 |               9 |        6 |       3 |               0.639 |                      0.600 |                       0.486 |
| relational_communion    |      1740 |        4 |     0.812 |     0.945 |                 0.884 |        1740 |        2.591 |      0.836 |            0.070 |              0.001 |               9 |        6 |       3 |               0.478 |                      1.000 |                       1.000 |
| next_step_actionability |      1740 |        4 |     0.629 |     0.871 |                 1.231 |        1740 |        3.473 |      1.139 |            0.121 |              0.066 |               9 |        6 |       3 |              -0.111 |                     -0.771 |                      -0.829 |

## Fixed-panel decision

```json
{
  "rubric_version": "educational_character_confirmatory_v1",
  "analysis_split": "formal",
  "classification": [
    {
      "dimension": "instructional_agency",
      "measurement_gates": {
        "icc_3_k_at_least_0_60": true,
        "score_sd_at_least_0_50": true,
        "floor_below_0_80": true,
        "ceiling_below_0_80": true,
        "judge_model_profile_rho_at_least_0_70": true,
        "pilot_measurement_pass": false
      },
      "signature_gates": {
        "cross_task_icc_or_rank_at_least_0_50": true,
        "all_observed_benchmark_variance_ci_above_zero": true,
        "maximum_abs_old_scale_rho_below_0_80": true
      },
      "criterion_gates": {
        "at_least_one_registered_behavior_anchor": false
      },
      "reliable_measurement": false,
      "pilot_proceed_unchanged": null,
      "cross_task_signature": false,
      "validated_character_axis": false,
      "classification_status": "formal_signature_not_supported"
    },
    {
      "dimension": "relational_communion",
      "measurement_gates": {
        "icc_3_k_at_least_0_60": true,
        "score_sd_at_least_0_50": true,
        "floor_below_0_80": true,
        "ceiling_below_0_80": true,
        "judge_model_profile_rho_at_least_0_70": true,
        "pilot_measurement_pass": true
      },
      "signature_gates": {
        "cross_task_icc_or_rank_at_least_0_50": true,
        "all_observed_benchmark_variance_ci_above_zero": false,
        "maximum_abs_old_scale_rho_below_0_80": false
      },
      "criterion_gates": {
        "at_least_one_registered_behavior_anchor": false
      },
      "reliable_measurement": true,
      "pilot_proceed_unchanged": null,
      "cross_task_signature": false,
      "validated_character_axis": false,
      "classification_status": "formal_signature_not_supported"
    },
    {
      "dimension": "next_step_actionability",
      "measurement_gates": {
        "icc_3_k_at_least_0_60": true,
        "score_sd_at_least_0_50": true,
        "floor_below_0_80": true,
        "ceiling_below_0_80": true,
        "judge_model_profile_rho_at_least_0_70": false,
        "pilot_measurement_pass": true
      },
      "signature_gates": {
        "cross_task_icc_or_rank_at_least_0_50": false,
        "all_observed_benchmark_variance_ci_above_zero": true,
        "maximum_abs_old_scale_rho_below_0_80": true
      },
      "criterion_gates": {
        "at_least_one_registered_behavior_anchor": false
      },
      "reliable_measurement": false,
      "pilot_proceed_unchanged": null,
      "cross_task_signature": false,
      "validated_character_axis": false,
      "classification_status": "formal_signature_not_supported"
    }
  ],
  "boundary": "The panel uses 4 judges across 4 model families. MiniMax contributes 1 judge(s); leave-one-family sensitivity is required before any formal cross-family validity claim.",
  "coverage": {
    "split": "formal",
    "judges": [
      "glm-5.2",
      "deepseek-v4-pro",
      "doubao-seed-2.0-lite",
      "minimax-m2.7"
    ],
    "benchmarks": [
      "mathtutorbench_pedagogy",
      "mathtutorbench_pedagogy_hard",
      "mathtutorbench_scaffolding",
      "mathtutorbench_scaffolding_hard",
      "mathtutorbench_socratic"
    ],
    "expected": 1160,
    "successful": 1160,
    "missing_or_failed": 0,
    "invalid_jsonl_rows": 0
  }
}
```

## Prompt effects

| dimension               |   mean_prompt_delta |   min_model_task_delta |   max_model_task_delta |
|:------------------------|--------------------:|-----------------------:|-----------------------:|
| instructional_agency    |              -1.017 |                 -1.534 |                 -0.345 |
| next_step_actionability |               0.964 |                  0.331 |                  1.865 |
| relational_communion    |              -0.183 |                 -0.544 |                  0.223 |

## Convergence with the original semantic panel

| new_dimension           | old_dimension          |   responses |   spearman |
|:------------------------|:-----------------------|------------:|-----------:|
| instructional_agency    | affective_warmth       |        1728 |     -0.023 |
| instructional_agency    | autonomy_support       |        1728 |     -0.755 |
| instructional_agency    | cognitive_load         |        1728 |      0.339 |
| instructional_agency    | diagnostic_specificity |        1728 |      0.017 |
| instructional_agency    | elicitation            |        1728 |     -0.665 |
| instructional_agency    | epistemic_caution      |        1728 |     -0.118 |
| instructional_agency    | help_directness        |        1728 |      0.689 |
| instructional_agency    | personalization        |        1728 |     -0.055 |
| next_step_actionability | affective_warmth       |        1728 |     -0.046 |
| next_step_actionability | autonomy_support       |        1728 |      0.184 |
| next_step_actionability | cognitive_load         |        1728 |      0.029 |
| next_step_actionability | diagnostic_specificity |        1728 |      0.145 |
| next_step_actionability | elicitation            |        1728 |      0.308 |
| next_step_actionability | epistemic_caution      |        1728 |      0.073 |
| next_step_actionability | help_directness        |        1728 |     -0.194 |
| next_step_actionability | personalization        |        1728 |      0.050 |
| relational_communion    | affective_warmth       |        1728 |      0.805 |
| relational_communion    | autonomy_support       |        1728 |      0.012 |
| relational_communion    | cognitive_load         |        1728 |     -0.010 |
| relational_communion    | diagnostic_specificity |        1728 |     -0.114 |
| relational_communion    | elicitation            |        1728 |     -0.016 |
| relational_communion    | epistemic_caution      |        1728 |     -0.119 |
| relational_communion    | help_directness        |        1728 |      0.003 |
| relational_communion    | personalization        |        1728 |      0.072 |

## Registered transparent-feature anchors

| new_dimension         | feature                |   expected_sign |   responses |   spearman | direction_pass   | magnitude_pass_0_30   |
|:----------------------|:-----------------------|----------------:|------------:|-----------:|:-----------------|:----------------------|
| instructional_agency  | imperative_rate        |               1 |        1740 |     -0.121 | False            | False                 |
| instructional_agency  | question_rate          |              -1 |        1740 |     -0.189 | True             | False                 |
| relational_communion  | praise_rate            |               1 |        1740 |      0.236 | True             | False                 |
| relational_communion  | encouragement_rate     |               1 |        1740 |      0.039 | True             | False                 |
| information_structure | bullet_rate            |               1 |           0 |    nan     | False            | False                 |
| information_structure | numbered_step_rate     |               1 |           0 |    nan     | False            | False                 |
| learner_contingency   | history_reference_rate |               1 |           0 |    nan     | False            | False                 |
| learner_contingency   | diagnosis_rate         |               1 |           0 |    nan     | False            | False                 |

## Interdimension correlations after exact-item centering

| left                 | right                   |   responses |   spearman |
|:---------------------|:------------------------|------------:|-----------:|
| instructional_agency | relational_communion    |        1740 |     -0.008 |
| instructional_agency | next_step_actionability |        1740 |     -0.164 |
| relational_communion | next_step_actionability |        1740 |     -0.054 |

## Boundary

The panel uses 4 judges across 4 model families. MiniMax contributes 1 judge(s); leave-one-family sensitivity is required before any formal cross-family validity claim.
A response tendency is not correctness, diagnostic accuracy, action optimality, or learning gain.
