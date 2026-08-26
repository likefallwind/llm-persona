# Semantic scale diagnostics

## Consensus across all tasks

| dimension              |   ratings |   mean |    sd |   floor_fraction |   ceiling_fraction |   unique_values |   normalized_entropy |
|:-----------------------|----------:|-------:|------:|-----------------:|-------------------:|----------------:|---------------------:|
| affective_warmth       |      1920 |  2.417 | 1.124 |            0.287 |              0.022 |               9 |                1.054 |
| autonomy_support       |      1920 |  2.668 | 1.135 |            0.216 |              0.013 |               9 |                1.095 |
| cognitive_load         |      1920 |  2.204 | 0.905 |            0.193 |              0.013 |               8 |                0.988 |
| diagnostic_specificity |      1920 |  2.624 | 1.448 |            0.357 |              0.098 |               9 |                1.116 |
| elicitation            |      1920 |  3.565 | 1.632 |            0.241 |              0.412 |               9 |                0.996 |
| epistemic_caution      |      1920 |  1.374 | 0.642 |            0.691 |              0.001 |               8 |                0.654 |
| help_directness        |      1920 |  2.816 | 1.420 |            0.199 |              0.213 |               9 |                1.151 |
| personalization        |      1920 |  2.506 | 0.932 |            0.223 |              0.004 |               9 |                0.844 |

## Low-information task × arm scales

| task              | arm      | dimension              |   ratings |   mean |    sd |   floor_fraction |   ceiling_fraction |   unique_values |   normalized_entropy |
|:------------------|:---------|:-----------------------|----------:|-------:|------:|-----------------:|-------------------:|----------------:|---------------------:|
| mathdial_hard     | generic  | epistemic_caution      |       240 |  1.238 | 0.489 |            0.792 |              0.000 |               3 |                0.370 |
| mathdial_standard | generic  | epistemic_caution      |       480 |  1.231 | 0.604 |            0.848 |              0.002 |               5 |                0.351 |
| mathdial_standard | pedagogy | personalization        |       480 |  2.935 | 0.381 |            0.002 |              0.000 |               7 |                0.625 |
| socratic          | socratic | affective_warmth       |       480 |  1.000 | 0.000 |            1.000 |              0.000 |               1 |               -0.000 |
| socratic          | socratic | diagnostic_specificity |       480 |  1.050 | 0.269 |            0.963 |              0.000 |               3 |                0.114 |
| socratic          | socratic | elicitation            |       480 |  4.802 | 0.443 |            0.000 |              0.819 |               4 |                0.329 |
| socratic          | socratic | epistemic_caution      |       480 |  1.038 | 0.255 |            0.977 |              0.000 |               3 |                0.077 |

These are measurement diagnostics, not exclusion rules. Low-variance dimensions remain in the report and cannot support strong cross-model conclusions merely because another test is significant.
