# Theory-grounded educational-character panel

Status: **pilot analysis**; successful judge calls: **120/120**.
No raw educational context, candidate response, or reasoning trace is exported.

## Measurement and stability

| dimension               |   targets |   judges |   icc_3_1 |   icc_3_k |   score_sd_all_judges |   responses |   score_mean |   score_sd |   floor_fraction |   ceiling_fraction |   unique_scores |   models |   tasks |   icc_3_1_stability |   median_pairwise_spearman |   minimum_pairwise_spearman |
|:------------------------|----------:|---------:|----------:|----------:|----------------------:|------------:|-------------:|-----------:|-----------------:|-------------------:|----------------:|---------:|--------:|--------------------:|---------------------------:|----------------------------:|
| instructional_agency    |       180 |        4 |     0.699 |     0.903 |                 0.964 |         180 |        3.847 |      0.885 |            0.006 |              0.283 |               9 |        6 |       3 |               0.310 |                      0.224 |                       0.207 |
| relational_communion    |       180 |        4 |     0.830 |     0.951 |                 0.863 |         180 |        2.617 |      0.828 |            0.067 |              0.000 |               7 |        6 |       3 |               0.273 |                      0.493 |                       0.493 |
| next_step_actionability |       180 |        4 |     0.740 |     0.919 |                 1.427 |         180 |        3.039 |      1.338 |            0.261 |              0.028 |               9 |        6 |       3 |               0.371 |                      0.270 |                       0.101 |

## Fixed-panel decision

```json
{
  "rubric_version": "educational_character_confirmatory_v1",
  "analysis_split": "pilot",
  "classification": [
    {
      "dimension": "instructional_agency",
      "measurement_gates": {
        "icc_3_k_at_least_0_60": true,
        "score_sd_at_least_0_50": true,
        "floor_below_0_80": true,
        "ceiling_below_0_80": true,
        "judge_model_profile_rho_at_least_0_70": false
      },
      "signature_gates": {
        "cross_task_icc_or_rank_at_least_0_50": false,
        "all_observed_benchmark_variance_ci_above_zero": true
      },
      "criterion_gates": {
        "at_least_one_registered_behavior_anchor": false
      },
      "reliable_measurement": false,
      "pilot_proceed_unchanged": false,
      "cross_task_signature": false,
      "validated_character_axis": false,
      "classification_status": "pilot_measurement_fail"
    },
    {
      "dimension": "relational_communion",
      "measurement_gates": {
        "icc_3_k_at_least_0_60": true,
        "score_sd_at_least_0_50": true,
        "floor_below_0_80": true,
        "ceiling_below_0_80": true,
        "judge_model_profile_rho_at_least_0_70": true
      },
      "signature_gates": {
        "cross_task_icc_or_rank_at_least_0_50": false,
        "all_observed_benchmark_variance_ci_above_zero": false
      },
      "criterion_gates": {
        "at_least_one_registered_behavior_anchor": true
      },
      "reliable_measurement": true,
      "pilot_proceed_unchanged": true,
      "cross_task_signature": false,
      "validated_character_axis": false,
      "classification_status": "pilot_measurement_pass"
    },
    {
      "dimension": "next_step_actionability",
      "measurement_gates": {
        "icc_3_k_at_least_0_60": true,
        "score_sd_at_least_0_50": true,
        "floor_below_0_80": true,
        "ceiling_below_0_80": true,
        "judge_model_profile_rho_at_least_0_70": true
      },
      "signature_gates": {
        "cross_task_icc_or_rank_at_least_0_50": false,
        "all_observed_benchmark_variance_ci_above_zero": true
      },
      "criterion_gates": {
        "at_least_one_registered_behavior_anchor": false
      },
      "reliable_measurement": true,
      "pilot_proceed_unchanged": true,
      "cross_task_signature": false,
      "validated_character_axis": false,
      "classification_status": "pilot_measurement_pass"
    }
  ],
  "boundary": "The panel uses 4 judges across 4 model families. MiniMax contributes 1 judge(s); leave-one-family sensitivity is required before any formal cross-family validity claim.",
  "coverage": {
    "split": "pilot",
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
    "expected": 120,
    "successful": 120,
    "missing_or_failed": 0,
    "invalid_jsonl_rows": 0
  }
}
```

## Prompt effects

| dimension               |   mean_prompt_delta |   min_model_task_delta |   max_model_task_delta |
|:------------------------|--------------------:|-----------------------:|-----------------------:|
| instructional_agency    |              -0.910 |                 -1.667 |                 -0.167 |
| next_step_actionability |               1.576 |                  0.583 |                  2.500 |
| relational_communion    |              -0.361 |                 -1.167 |                  0.333 |

## Convergence with the original semantic panel

| new_dimension           | old_dimension          |   responses |   spearman |
|:------------------------|:-----------------------|------------:|-----------:|
| instructional_agency    | affective_warmth       |         180 |      0.057 |
| instructional_agency    | autonomy_support       |         180 |     -0.760 |
| instructional_agency    | cognitive_load         |         180 |      0.269 |
| instructional_agency    | diagnostic_specificity |         180 |      0.178 |
| instructional_agency    | elicitation            |         180 |     -0.712 |
| instructional_agency    | epistemic_caution      |         180 |     -0.154 |
| instructional_agency    | help_directness        |         180 |      0.708 |
| instructional_agency    | personalization        |         180 |     -0.022 |
| next_step_actionability | affective_warmth       |         180 |     -0.040 |
| next_step_actionability | autonomy_support       |         180 |      0.388 |
| next_step_actionability | cognitive_load         |         180 |     -0.062 |
| next_step_actionability | diagnostic_specificity |         180 |      0.152 |
| next_step_actionability | elicitation            |         180 |      0.430 |
| next_step_actionability | epistemic_caution      |         180 |      0.092 |
| next_step_actionability | help_directness        |         180 |     -0.292 |
| next_step_actionability | personalization        |         180 |      0.070 |
| relational_communion    | affective_warmth       |         180 |      0.833 |
| relational_communion    | autonomy_support       |         180 |      0.002 |
| relational_communion    | cognitive_load         |         180 |     -0.142 |
| relational_communion    | diagnostic_specificity |         180 |     -0.248 |
| relational_communion    | elicitation            |         180 |     -0.053 |
| relational_communion    | epistemic_caution      |         180 |     -0.274 |
| relational_communion    | help_directness        |         180 |     -0.062 |
| relational_communion    | personalization        |         180 |      0.155 |

## Registered transparent-feature anchors

| new_dimension         | feature                |   expected_sign |   responses |   spearman | direction_pass   | magnitude_pass_0_30   |
|:----------------------|:-----------------------|----------------:|------------:|-----------:|:-----------------|:----------------------|
| instructional_agency  | imperative_rate        |               1 |         180 |     -0.088 | False            | False                 |
| instructional_agency  | question_rate          |              -1 |         180 |     -0.257 | True             | False                 |
| relational_communion  | praise_rate            |               1 |         180 |      0.370 | True             | True                  |
| relational_communion  | encouragement_rate     |               1 |         180 |     -0.064 | False            | False                 |
| information_structure | bullet_rate            |               1 |           0 |    nan     | False            | False                 |
| information_structure | numbered_step_rate     |               1 |           0 |    nan     | False            | False                 |
| learner_contingency   | history_reference_rate |               1 |           0 |    nan     | False            | False                 |
| learner_contingency   | diagnosis_rate         |               1 |           0 |    nan     | False            | False                 |

## Interdimension correlations after exact-item centering

| left                 | right                   |   responses |   spearman |
|:---------------------|:------------------------|------------:|-----------:|
| instructional_agency | relational_communion    |         180 |     -0.046 |
| instructional_agency | next_step_actionability |         180 |     -0.493 |
| relational_communion | next_step_actionability |         180 |     -0.080 |

## Boundary

The panel uses 4 judges across 4 model families. MiniMax contributes 1 judge(s); leave-one-family sensitivity is required before any formal cross-family validity claim.
A response tendency is not correctness, diagnostic accuracy, action optimality, or learning gain.
