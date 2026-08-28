# Existing-response general-personality bridge: results

Status: **complete archive-only screening analysis**. No generator or judge calls were made.

## Corpus

The inventory contains **283,926** paired responses (47,321 items, six models, 27 benchmarks). The frozen free-form eligibility rule retains **123,468** responses from 16 benchmarks. Short labels and constrained outputs remain in the coverage table but are not interpreted as personality.

| benchmark                           | include   | domain                 | condition        |   paired_items |   paired_responses | rationale                                                                        |
|:------------------------------------|:----------|:-----------------------|:-----------------|---------------:|-------------------:|:---------------------------------------------------------------------------------|
| agieval                             | True      | general_reasoning      | baseline         |           3672 |              22032 | free-form reasoning response                                                     |
| asap_2                              | False     | educational_assessment | baseline         |             30 |                180 | only 30 paired items and model-dependent one-character versus long-form output   |
| bea2025_judge                       | False     | judge                  | baseline         |           5258 |              31548 | nearly all outputs are short verdict labels                                      |
| ceval                               | False     | general_reasoning      | baseline         |           1345 |               8070 | one-character answer output                                                      |
| eduguard_adversarial                | True      | safety_assistance      | baseline         |            801 |               4806 | free-form response under a fixed safety evaluation role                          |
| eduguard_sata                       | False     | safety_assistance      | baseline         |           4491 |              26946 | structured short-label output; objective safety profiles are analyzed separately |
| ifeval                              | True      | instruction_following  | baseline         |            536 |               3216 | free-form instruction-following response                                         |
| longtutor_diagnosis                 | False     | learner_diagnosis      | baseline         |           1000 |               6000 | short structured diagnostic labels                                               |
| longtutor_evidence                  | False     | learner_diagnosis      | baseline         |           3000 |              18000 | mostly short evidence identifiers or spans                                       |
| longtutor_teaching                  | True      | default_tutoring       | default_tutoring |           1000 |               6000 | free-form teaching response without the matched LearnLM-style intervention       |
| mathtutorbench_judge_calibration    | False     | judge                  | baseline         |            964 |               5784 | one-character preference output                                                  |
| mathtutorbench_mistake_correction   | True      | educational_assessment | baseline         |           1001 |               6006 | free-form error correction and explanation                                       |
| mathtutorbench_mistake_location     | False     | educational_assessment | baseline         |           2004 |              12024 | short step-index output                                                          |
| mathtutorbench_pedagogy             | True      | prompted_tutoring      | pedagogy_prompt  |           1150 |               6900 | matched explicit-pedagogy intervention arm                                       |
| mathtutorbench_pedagogy_hard        | True      | prompted_tutoring      | pedagogy_prompt  |            327 |               1962 | matched hard explicit-pedagogy intervention arm                                  |
| mathtutorbench_scaffolding          | True      | default_tutoring       | default_tutoring |           1150 |               6900 | matched generic caring-teacher arm                                               |
| mathtutorbench_scaffolding_hard     | True      | default_tutoring       | default_tutoring |            327 |               1962 | matched hard generic caring-teacher arm                                          |
| mathtutorbench_socratic             | True      | prompted_tutoring      | socratic_prompt  |           1319 |               7914 | free-form response under a specific Socratic role                                |
| mathtutorbench_solution_correctness | False     | educational_assessment | baseline         |           2004 |              12024 | short binary verdict output                                                      |
| mmlu_pro                            | True      | general_reasoning      | baseline         |           4033 |              24198 | free-form reasoning response                                                     |
| mooccube_prereq                     | True      | general_reasoning      | baseline         |            300 |               1800 | free-form prerequisite reasoning response                                        |
| mrbench_judge                       | False     | judge                  | baseline         |           6617 |              39702 | nearly all outputs are short rating labels                                       |
| p07_selfcheck                       | True      | self_monitoring        | baseline         |            546 |               3276 | free-form answer review response                                                 |
| p08_abstention                      | True      | self_monitoring        | baseline         |            500 |               3000 | free-form answer-or-abstain response                                             |
| p08_calibration                     | True      | self_monitoring        | baseline         |            549 |               3294 | free-form answer with expressed confidence                                       |
| pedagogy_benchmark                  | False     | pedagogy_knowledge     | baseline         |             30 |                180 | one-character answer output and only 30 paired items                             |
| sas_bench                           | True      | educational_assessment | baseline         |           3367 |              20202 | structured but content-rich scoring and error analysis                           |

## Screening decision

Verdict: `existing_archive_does_not_yet_support_general_personality_bridge`.

| axis                        | non_tutoring_stability_gate   | cross_domain_transport_gate   | surface_nonreduction_gate   | interpretability_gate   |   non_tutoring_icc3_1 |   non_tutoring_median_pairwise_spearman |   non_tutoring_to_default_tutoring_spearman |   max_abs_surface_control_spearman | promising_for_new_experiment   |
|:----------------------------|:------------------------------|:------------------------------|:----------------------------|:------------------------|----------------------:|----------------------------------------:|--------------------------------------------:|-----------------------------------:|:-------------------------------|
| communal_expression         | False                         | True                          | True                        | True                    |                 0.269 |                                   0.371 |                                       0.829 |                              0.714 | False                          |
| dialogic_engagement         | True                          | False                         | True                        | True                    |                 0.364 |                                   0.543 |                                       0.657 |                              0.771 | False                          |
| directive_expression        | False                         | False                         | True                        | True                    |                 0.189 |                                   0.143 |                                      -0.086 |                              0.429 | False                          |
| epistemic_caution_language  | False                         | False                         | True                        | True                    |                 0.252 |                                   0.143 |                                      -0.200 |                              0.600 | False                          |
| boundary_refusal_expression | False                         | False                         | True                        | False                   |                -0.014 |                                   0.086 |                                      -0.257 |                              0.657 | False                          |

A large item count controls response sampling error, but the decision remains a six-model construct screen. A candidate must recur across non-tutoring tasks, transport to default tutoring, and avoid reduction to organizational style or verbosity.

## Cross-task stability

| pool              | axis                        |   task_count |   icc3_1 |   median_pairwise_spearman |   minimum_pairwise_spearman |   task_pairs |
|:------------------|:----------------------------|-------------:|---------:|---------------------------:|----------------------------:|-------------:|
| non_tutoring      | communal_expression         |           10 |    0.269 |                      0.371 |                      -0.886 |           45 |
| non_tutoring      | dialogic_engagement         |           10 |    0.364 |                      0.543 |                      -0.657 |           45 |
| non_tutoring      | directive_expression        |           10 |    0.189 |                      0.143 |                      -0.771 |           45 |
| non_tutoring      | epistemic_caution_language  |           10 |    0.252 |                      0.143 |                      -0.714 |           45 |
| non_tutoring      | boundary_refusal_expression |           10 |   -0.014 |                      0.086 |                      -0.829 |           45 |
| non_tutoring      | organizational_style        |           10 |    0.601 |                      0.771 |                      -0.091 |           45 |
| non_tutoring      | verbosity                   |           10 |    0.442 |                      0.543 |                      -0.714 |           45 |
| default_tutoring  | communal_expression         |            3 |    0.239 |                      0.429 |                       0.429 |            3 |
| default_tutoring  | dialogic_engagement         |            3 |    0.471 |                      0.771 |                       0.543 |            3 |
| default_tutoring  | directive_expression        |            3 |    0.759 |                      0.600 |                       0.600 |            3 |
| default_tutoring  | epistemic_caution_language  |            3 |    0.591 |                      0.543 |                       0.371 |            3 |
| default_tutoring  | boundary_refusal_expression |            3 |    0.420 |                      0.543 |                       0.486 |            3 |
| default_tutoring  | organizational_style        |            3 |    0.012 |                      0.439 |                       0.131 |            3 |
| default_tutoring  | verbosity                   |            3 |   -0.146 |                     -0.657 |                      -0.657 |            3 |
| prompted_tutoring | communal_expression         |            3 |    0.170 |                      0.086 |                      -0.371 |            3 |
| prompted_tutoring | dialogic_engagement         |            3 |    0.688 |                      0.771 |                       0.714 |            3 |
| prompted_tutoring | directive_expression        |            3 |    0.662 |                      0.829 |                       0.771 |            3 |
| prompted_tutoring | epistemic_caution_language  |            3 |    0.439 |                      0.029 |                      -0.029 |            3 |
| prompted_tutoring | boundary_refusal_expression |            3 |   -0.053 |                     -0.348 |                      -0.516 |            3 |
| prompted_tutoring | organizational_style        |            3 |    0.835 |                      0.775 |                       0.775 |            3 |
| prompted_tutoring | verbosity                   |            3 |    0.518 |                      0.371 |                       0.371 |            3 |
| all_baseline      | communal_expression         |           13 |    0.286 |                      0.514 |                      -0.886 |           78 |
| all_baseline      | dialogic_engagement         |           13 |    0.319 |                      0.400 |                      -0.886 |           78 |
| all_baseline      | directive_expression        |           13 |    0.111 |                      0.086 |                      -0.771 |           78 |
| all_baseline      | epistemic_caution_language  |           13 |    0.079 |                     -0.057 |                      -0.943 |           78 |
| all_baseline      | boundary_refusal_expression |           13 |   -0.020 |                      0.086 |                      -0.829 |           78 |
| all_baseline      | organizational_style        |           13 |    0.492 |                      0.486 |                      -0.393 |           78 |
| all_baseline      | verbosity                   |           13 |    0.364 |                      0.486 |                      -0.714 |           78 |

## Cross-domain transport

| axis                        | left_pool        | right_pool        |   spearman |   exact_two_sided_p |   model_count |
|:----------------------------|:-----------------|:------------------|-----------:|--------------------:|--------------:|
| communal_expression         | non_tutoring     | default_tutoring  |      0.829 |               0.060 |             6 |
| communal_expression         | non_tutoring     | prompted_tutoring |      0.257 |               0.659 |             6 |
| communal_expression         | default_tutoring | prompted_tutoring |      0.314 |               0.564 |             6 |
| dialogic_engagement         | non_tutoring     | default_tutoring  |      0.657 |               0.176 |             6 |
| dialogic_engagement         | non_tutoring     | prompted_tutoring |      0.200 |               0.714 |             6 |
| dialogic_engagement         | default_tutoring | prompted_tutoring |     -0.029 |               1.000 |             6 |
| directive_expression        | non_tutoring     | default_tutoring  |     -0.086 |               0.920 |             6 |
| directive_expression        | non_tutoring     | prompted_tutoring |      0.429 |               0.420 |             6 |
| directive_expression        | default_tutoring | prompted_tutoring |      0.600 |               0.243 |             6 |
| epistemic_caution_language  | non_tutoring     | default_tutoring  |     -0.200 |               0.714 |             6 |
| epistemic_caution_language  | non_tutoring     | prompted_tutoring |     -0.600 |               0.243 |             6 |
| epistemic_caution_language  | default_tutoring | prompted_tutoring |      0.600 |               0.243 |             6 |
| boundary_refusal_expression | non_tutoring     | default_tutoring  |     -0.257 |               0.659 |             6 |
| boundary_refusal_expression | non_tutoring     | prompted_tutoring |     -0.029 |               1.000 |             6 |
| boundary_refusal_expression | default_tutoring | prompted_tutoring |      0.714 |               0.137 |             6 |
| organizational_style        | non_tutoring     | default_tutoring  |      0.600 |               0.243 |             6 |
| organizational_style        | non_tutoring     | prompted_tutoring |      0.541 |               0.268 |             6 |
| organizational_style        | default_tutoring | prompted_tutoring |      0.541 |               0.268 |             6 |
| verbosity                   | non_tutoring     | default_tutoring  |      0.771 |               0.104 |             6 |
| verbosity                   | non_tutoring     | prompted_tutoring |      0.429 |               0.420 |             6 |
| verbosity                   | default_tutoring | prompted_tutoring |      0.886 |               0.035 |             6 |

### Leave-one-non-tutoring-domain-out transport

| axis                        | omitted_non_tutoring_domain   |   spearman |   exact_two_sided_p |   model_count |
|:----------------------------|:------------------------------|-----------:|--------------------:|--------------:|
| communal_expression         | educational_assessment        |      0.714 |               0.137 |             6 |
| dialogic_engagement         | educational_assessment        |      0.657 |               0.176 |             6 |
| directive_expression        | educational_assessment        |     -0.086 |               0.920 |             6 |
| epistemic_caution_language  | educational_assessment        |     -0.200 |               0.714 |             6 |
| boundary_refusal_expression | educational_assessment        |     -0.257 |               0.659 |             6 |
| organizational_style        | educational_assessment        |      0.600 |               0.243 |             6 |
| verbosity                   | educational_assessment        |      0.771 |               0.104 |             6 |
| communal_expression         | general_reasoning             |      0.657 |               0.176 |             6 |
| dialogic_engagement         | general_reasoning             |      0.600 |               0.243 |             6 |
| directive_expression        | general_reasoning             |      0.029 |               1.000 |             6 |
| epistemic_caution_language  | general_reasoning             |     -0.371 |               0.498 |             6 |
| boundary_refusal_expression | general_reasoning             |     -0.257 |               0.659 |             6 |
| organizational_style        | general_reasoning             |      0.657 |               0.176 |             6 |
| verbosity                   | general_reasoning             |      0.771 |               0.104 |             6 |
| communal_expression         | instruction_following         |      0.829 |               0.060 |             6 |
| dialogic_engagement         | instruction_following         |      0.657 |               0.176 |             6 |
| directive_expression        | instruction_following         |     -0.543 |               0.298 |             6 |
| epistemic_caution_language  | instruction_following         |     -0.200 |               0.714 |             6 |
| boundary_refusal_expression | instruction_following         |     -0.257 |               0.659 |             6 |
| organizational_style        | instruction_following         |      0.600 |               0.243 |             6 |
| verbosity                   | instruction_following         |      0.771 |               0.104 |             6 |
| communal_expression         | safety_assistance             |      0.714 |               0.137 |             6 |
| dialogic_engagement         | safety_assistance             |      0.714 |               0.137 |             6 |
| directive_expression        | safety_assistance             |      0.143 |               0.803 |             6 |
| epistemic_caution_language  | safety_assistance             |     -0.600 |               0.243 |             6 |
| boundary_refusal_expression | safety_assistance             |      0.200 |               0.714 |             6 |
| organizational_style        | safety_assistance             |      0.657 |               0.176 |             6 |
| verbosity                   | safety_assistance             |      0.886 |               0.035 |             6 |
| communal_expression         | self_monitoring               |      0.943 |               0.018 |             6 |
| dialogic_engagement         | self_monitoring               |      0.657 |               0.176 |             6 |
| directive_expression        | self_monitoring               |     -0.200 |               0.714 |             6 |
| epistemic_caution_language  | self_monitoring               |     -0.200 |               0.714 |             6 |
| boundary_refusal_expression | self_monitoring               |     -0.257 |               0.659 |             6 |
| organizational_style        | self_monitoring               |      0.600 |               0.243 |             6 |
| verbosity                   | self_monitoring               |      0.829 |               0.060 |             6 |

## Surface-style confounds

| axis                        | surface_control      |   spearman |   exact_two_sided_p |   candidate_max_abs_surface_rho |
|:----------------------------|:---------------------|-----------:|--------------------:|--------------------------------:|
| communal_expression         | organizational_style |      0.029 |               1.000 |                           0.714 |
| communal_expression         | verbosity            |      0.714 |               0.137 |                           0.714 |
| dialogic_engagement         | organizational_style |      0.086 |               0.920 |                           0.771 |
| dialogic_engagement         | verbosity            |      0.771 |               0.104 |                           0.771 |
| directive_expression        | organizational_style |      0.257 |               0.659 |                           0.429 |
| directive_expression        | verbosity            |      0.429 |               0.420 |                           0.429 |
| epistemic_caution_language  | organizational_style |      0.257 |               0.659 |                           0.600 |
| epistemic_caution_language  | verbosity            |      0.600 |               0.243 |                           0.600 |
| boundary_refusal_expression | organizational_style |     -0.143 |               0.803 |                           0.657 |
| boundary_refusal_expression | verbosity            |     -0.657 |               0.176 |                           0.657 |

## Bridge to the existing educational axes

| general_manifestation      | educational_axis        |   expected_sign |   spearman | direction_matches   |   exact_two_sided_p |   model_count |   bh_q |
|:---------------------------|:------------------------|----------------:|-----------:|:--------------------|--------------------:|--------------:|-------:|
| communal_expression        | relational_communion    |               1 |      0.771 | True                |               0.104 |             6 |  0.581 |
| dialogic_engagement        | instructional_agency    |              -1 |     -0.486 | True                |               0.356 |             6 |  0.581 |
| dialogic_engagement        | assistance_directness   |              -1 |     -0.543 | True                |               0.298 |             6 |  0.581 |
| directive_expression       | instructional_agency    |               1 |     -0.429 | False               |               0.420 |             6 |  0.581 |
| directive_expression       | assistance_directness   |               1 |     -0.486 | False               |               0.356 |             6 |  0.581 |
| epistemic_caution_language | epistemic_commitment    |              -1 |      0.200 | False               |               0.714 |             6 |  0.714 |
| organizational_style       | next_step_actionability |               1 |     -0.371 | False               |               0.498 |             6 |  0.581 |

These six-model correlations are hypothesis-generating. They cannot estimate a latent general-personality structure or establish that an educational axis is caused by a human personality analogue.

## Existing prompt-related model reordering on the same manifestations

| pair     | axis                        |   mean_absolute_relative_displacement |   minimum_relative_displacement |   maximum_relative_displacement |
|:---------|:----------------------------|--------------------------------------:|--------------------------------:|--------------------------------:|
| hard     | boundary_refusal_expression |                                 0.035 |                          -0.053 |                           0.052 |
| hard     | communal_expression         |                                 0.071 |                          -0.156 |                           0.147 |
| hard     | dialogic_engagement         |                                 0.150 |                          -0.344 |                           0.183 |
| hard     | directive_expression        |                                 0.080 |                          -0.113 |                           0.156 |
| hard     | epistemic_caution_language  |                                 0.048 |                          -0.067 |                           0.082 |
| hard     | organizational_style        |                                 0.000 |                           0.000 |                           0.000 |
| hard     | verbosity                   |                                 0.243 |                          -0.646 |                           0.355 |
| standard | boundary_refusal_expression |                                 0.032 |                          -0.078 |                           0.056 |
| standard | communal_expression         |                                 0.093 |                          -0.191 |                           0.167 |
| standard | dialogic_engagement         |                                 0.129 |                          -0.331 |                           0.189 |
| standard | directive_expression        |                                 0.086 |                          -0.145 |                           0.146 |
| standard | epistemic_caution_language  |                                 0.056 |                          -0.055 |                           0.089 |
| standard | organizational_style        |                                 0.008 |                          -0.023 |                           0.016 |
| standard | verbosity                   |                                 0.298 |                          -0.714 |                           0.435 |

Exact-item centering is performed separately inside each prompt arm, so the common prompt main effect is removed by construction. This table reports only models' relative movement around that common effect. The existing semantic and factorial analyses remain authoritative for shared prompt displacement and model-specific elasticity; this is not a new general-personality intervention.

## Boundary

Screening of observable language and interaction policies in six fixed deployed configurations; not human personality, latent-trait validation, family-level inference, or provider-version stability.
