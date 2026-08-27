# Theory-grounded educational-character panel

Status: **pilot analysis**; successful judge calls: **120/120**.
No raw educational context, candidate response, or reasoning trace is exported.

## Measurement and stability

| dimension               |   targets |   judges |   icc_3_1 |   icc_3_k |   score_sd_all_judges |   responses |   score_mean |   score_sd |   floor_fraction |   ceiling_fraction |   unique_scores |   models |   tasks |   icc_3_1_stability |   median_pairwise_spearman |   minimum_pairwise_spearman |
|:------------------------|----------:|---------:|----------:|----------:|----------------------:|------------:|-------------:|-----------:|-----------------:|-------------------:|----------------:|---------:|--------:|--------------------:|---------------------------:|----------------------------:|
| information_sequencing  |       180 |        4 |     0.510 |     0.806 |                 0.768 |         180 |        3.806 |      0.583 |            0.000 |              0.033 |               8 |        6 |       3 |               0.319 |                      0.000 |                      -0.088 |
| next_step_actionability |       180 |        4 |     0.798 |     0.940 |                 1.388 |         180 |        3.161 |      1.314 |            0.200 |              0.050 |               9 |        6 |       3 |               0.518 |                      0.429 |                       0.223 |

## Fixed-panel decision

```json
{
  "rubric_version": "information_structure_facets_v1",
  "analysis_split": "pilot",
  "classification": [
    {
      "dimension": "information_sequencing",
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
      "dimension": "next_step_actionability",
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
    }
  ],
  "boundary": "The panel uses 4 judges across 3 model families. MiniMax contributes 2 judge(s); leave-one-family sensitivity is required before any formal cross-family validity claim.",
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

| dimension               |   mean_prompt_delta |   min_model_task_delta |   max_model_task_delta |
|:------------------------|--------------------:|-----------------------:|-----------------------:|
| information_sequencing  |              -0.042 |                 -0.500 |                  0.417 |
| next_step_actionability |               1.424 |                  0.500 |                  2.083 |

## Convergence with the original semantic panel

| new_dimension           | old_dimension          |   responses |   spearman |
|:------------------------|:-----------------------|------------:|-----------:|
| information_sequencing  | affective_warmth       |         180 |     -0.130 |
| information_sequencing  | autonomy_support       |         180 |     -0.085 |
| information_sequencing  | cognitive_load         |         180 |      0.457 |
| information_sequencing  | diagnostic_specificity |         180 |      0.326 |
| information_sequencing  | elicitation            |         180 |      0.035 |
| information_sequencing  | epistemic_caution      |         180 |     -0.025 |
| information_sequencing  | help_directness        |         180 |      0.243 |
| information_sequencing  | personalization        |         180 |      0.081 |
| next_step_actionability | affective_warmth       |         180 |     -0.064 |
| next_step_actionability | autonomy_support       |         180 |      0.376 |
| next_step_actionability | cognitive_load         |         180 |      0.017 |
| next_step_actionability | diagnostic_specificity |         180 |      0.176 |
| next_step_actionability | elicitation            |         180 |      0.437 |
| next_step_actionability | epistemic_caution      |         180 |      0.072 |
| next_step_actionability | help_directness        |         180 |     -0.237 |
| next_step_actionability | personalization        |         180 |      0.104 |

## Registered transparent-feature anchors

| new_dimension         | feature                |   expected_sign |   responses |   spearman | direction_pass   | magnitude_pass_0_30   |
|:----------------------|:-----------------------|----------------:|------------:|-----------:|:-----------------|:----------------------|
| instructional_agency  | imperative_rate        |               1 |           0 |        nan | False            | False                 |
| instructional_agency  | question_rate          |              -1 |           0 |        nan | False            | False                 |
| relational_communion  | praise_rate            |               1 |           0 |        nan | False            | False                 |
| relational_communion  | encouragement_rate     |               1 |           0 |        nan | False            | False                 |
| information_structure | bullet_rate            |               1 |           0 |        nan | False            | False                 |
| information_structure | numbered_step_rate     |               1 |           0 |        nan | False            | False                 |
| learner_contingency   | history_reference_rate |               1 |           0 |        nan | False            | False                 |
| learner_contingency   | diagnosis_rate         |               1 |           0 |        nan | False            | False                 |

## Interdimension correlations after exact-item centering

| left                   | right                   |   responses |   spearman |
|:-----------------------|:------------------------|------------:|-----------:|
| information_sequencing | next_step_actionability |         180 |      0.398 |

## Boundary

The panel uses 4 judges across 3 model families. MiniMax contributes 2 judge(s); leave-one-family sensitivity is required before any formal cross-family validity claim.
A response tendency is not correctness, diagnostic accuracy, action optimality, or learning gain.
