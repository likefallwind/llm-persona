# Semantic judge run status

|   manifest_batches |   excluded_batches |   analyzed_batches |   expected_annotations |   successful_annotations |   current_errors |   missing_annotations |   raw_jsonl_rows |   superseded_retry_rows |   invalid_jsonl_rows |
|-------------------:|-------------------:|-------------------:|-----------------------:|-------------------------:|-----------------:|----------------------:|-----------------:|------------------------:|---------------------:|
|                360 |                  2 |                358 |                   1074 |                     1074 |                0 |                     0 |             1082 |                       2 |                    0 |

## Coverage

| judge           | benchmark                       |   success |   error |   missing |   expected |   success_rate |
|:----------------|:--------------------------------|----------:|--------:|----------:|-----------:|---------------:|
| MiniMax-M3      | longtutor_teaching              |        40 |       0 |         0 |         40 |          1.000 |
| MiniMax-M3      | mathtutorbench_pedagogy         |        79 |       0 |         0 |         79 |          1.000 |
| MiniMax-M3      | mathtutorbench_pedagogy_hard    |        40 |       0 |         0 |         40 |          1.000 |
| MiniMax-M3      | mathtutorbench_scaffolding      |        79 |       0 |         0 |         79 |          1.000 |
| MiniMax-M3      | mathtutorbench_scaffolding_hard |        40 |       0 |         0 |         40 |          1.000 |
| MiniMax-M3      | mathtutorbench_socratic         |        80 |       0 |         0 |         80 |          1.000 |
| deepseek-v4-pro | longtutor_teaching              |        40 |       0 |         0 |         40 |          1.000 |
| deepseek-v4-pro | mathtutorbench_pedagogy         |        79 |       0 |         0 |         79 |          1.000 |
| deepseek-v4-pro | mathtutorbench_pedagogy_hard    |        40 |       0 |         0 |         40 |          1.000 |
| deepseek-v4-pro | mathtutorbench_scaffolding      |        79 |       0 |         0 |         79 |          1.000 |
| deepseek-v4-pro | mathtutorbench_scaffolding_hard |        40 |       0 |         0 |         40 |          1.000 |
| deepseek-v4-pro | mathtutorbench_socratic         |        80 |       0 |         0 |         80 |          1.000 |
| glm-5.2         | longtutor_teaching              |        40 |       0 |         0 |         40 |          1.000 |
| glm-5.2         | mathtutorbench_pedagogy         |        79 |       0 |         0 |         79 |          1.000 |
| glm-5.2         | mathtutorbench_pedagogy_hard    |        40 |       0 |         0 |         40 |          1.000 |
| glm-5.2         | mathtutorbench_scaffolding      |        79 |       0 |         0 |         79 |          1.000 |
| glm-5.2         | mathtutorbench_scaffolding_hard |        40 |       0 |         0 |         40 |          1.000 |
| glm-5.2         | mathtutorbench_socratic         |        80 |       0 |         0 |         80 |          1.000 |

## Confidence among successful annotations

| judge           |   count |   mean |   median |   min |   max |
|:----------------|--------:|-------:|---------:|------:|------:|
| MiniMax-M3      |     358 |  3.905 |    4.000 |     1 |     5 |
| deepseek-v4-pro |     358 |  4.615 |    5.000 |     1 |     5 |
| glm-5.2         |     358 |  4.059 |    4.000 |     1 |     5 |

## Current error signatures

No current errors.

Only the latest row for each annotation ID determines status; earlier failed retry rows remain in the append-only JSONL for auditability.
Technical exclusions: **2** frozen batches; the gate covers **358** complete analyzed batches.
