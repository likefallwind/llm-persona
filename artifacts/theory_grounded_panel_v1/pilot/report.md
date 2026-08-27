# Theory-grounded educational-character panel

Status: **pilot analysis**; successful judge calls: **120/120**.
No raw educational context, candidate response, or reasoning trace is exported.

## Measurement and stability

| dimension             |   targets |   judges |   icc_3_1 |   icc_3_k |   score_sd_all_judges |   responses |   score_mean |   score_sd |   floor_fraction |   ceiling_fraction |   unique_scores |   models |   tasks |   icc_3_1_stability |   median_pairwise_spearman |   minimum_pairwise_spearman |
|:----------------------|----------:|---------:|----------:|----------:|----------------------:|------------:|-------------:|-----------:|-----------------:|-------------------:|----------------:|---------:|--------:|--------------------:|---------------------------:|----------------------------:|
| instructional_agency  |       180 |        4 |     0.554 |     0.833 |                 1.046 |         180 |        3.828 |      0.887 |            0.011 |              0.217 |               9 |        6 |       3 |               0.512 |                      0.399 |                       0.393 |
| relational_communion  |       180 |        4 |     0.844 |     0.956 |                 1.012 |         180 |        2.628 |      0.989 |            0.167 |              0.000 |               7 |        6 |       3 |               0.260 |                      0.486 |                       0.486 |
| information_structure |       180 |        4 |     0.430 |     0.751 |                 0.673 |         180 |        3.711 |      0.532 |            0.011 |              0.000 |               8 |        6 |       3 |              -0.022 |                      0.164 |                      -0.552 |
| learner_contingency   |       180 |        4 |     0.768 |     0.930 |                 0.966 |         180 |        2.567 |      0.887 |            0.206 |              0.000 |               7 |        6 |       3 |               0.355 |                      0.232 |                       0.232 |

## Fixed-panel decision

```json
{
  "rubric_version": "theory_grounded_character_v1",
  "analysis_split": "pilot",
  "classification": [
    {
      "dimension": "instructional_agency",
      "measurement_gates": {
        "icc_3_k_at_least_0_60": true,
        "score_sd_at_least_0_50": true,
        "floor_below_0_80": true,
        "ceiling_below_0_80": true,
        "judge_model_profile_rho_at_least_0_70": true
      },
      "signature_gates": {
        "cross_task_icc_or_rank_at_least_0_50": true,
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
      "dimension": "information_structure",
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
      "dimension": "learner_contingency",
      "measurement_gates": {
        "icc_3_k_at_least_0_60": true,
        "score_sd_at_least_0_50": true,
        "floor_below_0_80": true,
        "ceiling_below_0_80": true,
        "judge_model_profile_rho_at_least_0_70": false
      },
      "signature_gates": {
        "cross_task_icc_or_rank_at_least_0_50": false,
        "all_observed_benchmark_variance_ci_above_zero": false
      },
      "criterion_gates": {
        "at_least_one_registered_behavior_anchor": false
      },
      "reliable_measurement": false,
      "pilot_proceed_unchanged": false,
      "cross_task_signature": false,
      "validated_character_axis": false,
      "classification_status": "pilot_measurement_fail"
    }
  ],
  "boundary": "Two MiniMax-family judges can diagnose rubric range and agreement but cannot establish judge-family-independent formal validity.",
  "coverage": {
    "split": "pilot",
    "judges": [
      "MiniMax-M3",
      "MiniMax-M2.7",
      "glm-5.2",
      "deepseek-v4-pro"
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

| dimension             |   mean_prompt_delta |   min_model_task_delta |   max_model_task_delta |
|:----------------------|--------------------:|-----------------------:|-----------------------:|
| information_structure |              -0.007 |                 -0.500 |                  0.500 |
| instructional_agency  |              -0.840 |                 -2.000 |                  0.250 |
| learner_contingency   |              -0.000 |                 -0.583 |                  0.250 |
| relational_communion  |              -0.278 |                 -1.083 |                  0.500 |

## Convergence with the original semantic panel

| new_dimension         | old_dimension          |   responses |   spearman |
|:----------------------|:-----------------------|------------:|-----------:|
| information_structure | affective_warmth       |         180 |     -0.144 |
| information_structure | autonomy_support       |         180 |      0.133 |
| information_structure | cognitive_load         |         180 |      0.337 |
| information_structure | diagnostic_specificity |         180 |      0.315 |
| information_structure | elicitation            |         180 |      0.207 |
| information_structure | epistemic_caution      |         180 |      0.001 |
| information_structure | help_directness        |         180 |      0.076 |
| information_structure | personalization        |         180 |      0.145 |
| instructional_agency  | affective_warmth       |         180 |      0.091 |
| instructional_agency  | autonomy_support       |         180 |     -0.703 |
| instructional_agency  | cognitive_load         |         180 |      0.368 |
| instructional_agency  | diagnostic_specificity |         180 |      0.186 |
| instructional_agency  | elicitation            |         180 |     -0.689 |
| instructional_agency  | epistemic_caution      |         180 |     -0.217 |
| instructional_agency  | help_directness        |         180 |      0.718 |
| instructional_agency  | personalization        |         180 |     -0.040 |
| learner_contingency   | affective_warmth       |         180 |      0.106 |
| learner_contingency   | autonomy_support       |         180 |      0.095 |
| learner_contingency   | cognitive_load         |         180 |      0.315 |
| learner_contingency   | diagnostic_specificity |         180 |      0.521 |
| learner_contingency   | elicitation            |         180 |      0.150 |
| learner_contingency   | epistemic_caution      |         180 |      0.151 |
| learner_contingency   | help_directness        |         180 |      0.063 |
| learner_contingency   | personalization        |         180 |      0.526 |
| relational_communion  | affective_warmth       |         180 |      0.841 |
| relational_communion  | autonomy_support       |         180 |     -0.092 |
| relational_communion  | cognitive_load         |         180 |     -0.089 |
| relational_communion  | diagnostic_specificity |         180 |     -0.149 |
| relational_communion  | elicitation            |         180 |     -0.195 |
| relational_communion  | epistemic_caution      |         180 |     -0.289 |
| relational_communion  | help_directness        |         180 |      0.082 |
| relational_communion  | personalization        |         180 |      0.183 |

## Registered transparent-feature anchors

| new_dimension         | feature                |   expected_sign |   responses |   spearman | direction_pass   | magnitude_pass_0_30   |
|:----------------------|:-----------------------|----------------:|------------:|-----------:|:-----------------|:----------------------|
| instructional_agency  | imperative_rate        |               1 |         180 |     -0.102 | False            | False                 |
| instructional_agency  | question_rate          |              -1 |         180 |     -0.233 | True             | False                 |
| relational_communion  | praise_rate            |               1 |         180 |      0.359 | True             | True                  |
| relational_communion  | encouragement_rate     |               1 |         180 |     -0.024 | False            | False                 |
| information_structure | bullet_rate            |               1 |         180 |    nan     | False            | False                 |
| information_structure | numbered_step_rate     |               1 |         180 |    nan     | False            | False                 |
| learner_contingency   | history_reference_rate |               1 |         180 |      0.018 | True             | False                 |
| learner_contingency   | diagnosis_rate         |               1 |         180 |      0.119 | True             | False                 |

## Interdimension correlations after exact-item centering

| left                  | right                 |   responses |   spearman |
|:----------------------|:----------------------|------------:|-----------:|
| instructional_agency  | relational_communion  |         180 |      0.117 |
| instructional_agency  | information_structure |         180 |     -0.048 |
| instructional_agency  | learner_contingency   |         180 |     -0.065 |
| relational_communion  | information_structure |         180 |     -0.190 |
| relational_communion  | learner_contingency   |         180 |      0.077 |
| information_structure | learner_contingency   |         180 |      0.280 |

## Boundary

Two MiniMax-family judges can diagnose rubric range and agreement but cannot establish judge-family-independent formal validity.
A response tendency is not correctness, diagnostic accuracy, action optimality, or learning gain.
