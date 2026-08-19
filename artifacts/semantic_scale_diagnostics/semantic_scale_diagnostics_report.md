# Semantic scale diagnostics

## Consensus across all tasks

| dimension              |   ratings |   mean |    sd |   floor_fraction |   ceiling_fraction |   unique_values |   normalized_entropy |
|:-----------------------|----------:|-------:|------:|-----------------:|-------------------:|----------------:|---------------------:|
| affective_warmth       |      2148 |  2.498 | 1.178 |            0.298 |              0.042 |               5 |                0.877 |
| autonomy_support       |      2148 |  2.378 | 1.180 |            0.324 |              0.027 |               5 |                0.897 |
| cognitive_load         |      2148 |  2.210 | 0.967 |            0.287 |              0.015 |               5 |                0.809 |
| diagnostic_specificity |      2148 |  2.732 | 1.580 |            0.373 |              0.201 |               5 |                0.938 |
| elicitation            |      2148 |  3.558 | 1.666 |            0.244 |              0.490 |               5 |                0.819 |
| epistemic_caution      |      2148 |  1.314 | 0.657 |            0.780 |              0.002 |               5 |                0.440 |
| help_directness        |      2148 |  2.765 | 1.451 |            0.270 |              0.213 |               5 |                0.933 |
| personalization        |      2148 |  2.556 | 0.955 |            0.236 |              0.014 |               5 |                0.626 |

## Low-information task × arm scales

| task              | arm      | dimension              |   ratings |   mean |    sd |   floor_fraction |   ceiling_fraction |   unique_values |   normalized_entropy |
|:------------------|:---------|:-----------------------|----------:|-------:|------:|-----------------:|-------------------:|----------------:|---------------------:|
| mathdial_hard     | generic  | epistemic_caution      |       240 |  1.137 | 0.459 |            0.904 |              0.000 |               4 |                0.244 |
| mathdial_hard     | generic  | personalization        |       240 |  2.946 | 0.449 |            0.021 |              0.008 |               5 |                0.310 |
| mathdial_hard     | pedagogy | personalization        |       240 |  2.987 | 0.296 |            0.008 |              0.004 |               5 |                0.162 |
| mathdial_standard | generic  | epistemic_caution      |       474 |  1.190 | 0.586 |            0.876 |              0.006 |               5 |                0.308 |
| mathdial_standard | pedagogy | personalization        |       474 |  2.886 | 0.400 |            0.027 |              0.000 |               4 |                0.229 |
| socratic          | socratic | affective_warmth       |       480 |  1.000 | 0.000 |            1.000 |              0.000 |               1 |               -0.000 |
| socratic          | socratic | diagnostic_specificity |       480 |  1.000 | 0.000 |            1.000 |              0.000 |               1 |               -0.000 |
| socratic          | socratic | elicitation            |       480 |  4.992 | 0.091 |            0.000 |              0.992 |               2 |                0.030 |
| socratic          | socratic | epistemic_caution      |       480 |  1.052 | 0.315 |            0.973 |              0.000 |               3 |                0.082 |
| socratic          | socratic | personalization        |       480 |  1.229 | 0.582 |            0.852 |              0.000 |               3 |                0.324 |

These are measurement diagnostics, not exclusion rules. Low-variance dimensions remain in the report and cannot support strong cross-model conclusions merely because another test is significant.
