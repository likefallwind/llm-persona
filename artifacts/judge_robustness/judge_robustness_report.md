# Existing judge-swap robustness

This analysis uses already-generated scores; no new API call or data export was used.

|   run_pairs_checked |   common_items |   response_mismatches |   byte_identical_files |
|--------------------:|---------------:|----------------------:|-----------------------:|
|                  20 |          14770 |                     0 |                     18 |

Two files contained duplicate resume rows, so only 18/20 raw files were byte-identical. After last-row-per-item resolution, all shared candidate responses matched exactly and no item existed on only one side.

## Item-level agreement

| scope                           |     n |   exact_agreement |   within_half_point |   spearman |   quadratic_kappa |   m3_mean |   deepseek_mean |   mean_difference_m3_minus_deepseek |
|:--------------------------------|------:|------------------:|--------------------:|-----------:|------------------:|----------:|----------------:|------------------------------------:|
| ALL                             | 14770 |             0.808 |               0.955 |      0.806 |             0.810 |     0.593 |           0.614 |                              -0.021 |
| mathtutorbench_pedagogy         |  5750 |             0.834 |               0.962 |      0.645 |             0.684 |     0.828 |           0.860 |                              -0.032 |
| mathtutorbench_pedagogy_hard    |  1635 |             0.788 |               0.941 |      0.587 |             0.623 |     0.800 |           0.816 |                              -0.015 |
| mathtutorbench_scaffolding      |  5750 |             0.797 |               0.954 |      0.791 |             0.795 |     0.372 |           0.385 |                              -0.013 |
| mathtutorbench_scaffolding_hard |  1635 |             0.782 |               0.948 |      0.757 |             0.764 |     0.334 |           0.354 |                              -0.020 |

## Model-ranking agreement

| benchmark                       |   model_count |   rank_spearman |
|:--------------------------------|--------------:|----------------:|
| mathtutorbench_pedagogy         |             5 |           1.000 |
| mathtutorbench_pedagogy_hard    |             5 |           0.900 |
| mathtutorbench_scaffolding      |             5 |           1.000 |
| mathtutorbench_scaffolding_hard |             5 |           1.000 |
| ALL_TASK_MEAN                   |             5 |           1.000 |

## Prompt effect replicated across judges

| judge             | family   |   mean |   min |   max |
|:------------------|:---------|-------:|------:|------:|
| deepseek-v4-flash | hard     |  0.461 | 0.265 | 0.564 |
| deepseek-v4-flash | standard |  0.475 | 0.269 | 0.643 |
| minimax-m3        | hard     |  0.457 | 0.274 | 0.563 |
| minimax-m3        | standard |  0.463 | 0.263 | 0.602 |

Every listed mean is a within-model, within-item difference. Positive values mean the explicit pedagogy prompt received a higher pairwise win score than the generic caring-teacher prompt.

## Mean judge difference by candidate model

| model               |   mean_difference_m3_minus_deepseek |
|:--------------------|------------------------------------:|
| glm-5.2             |                              -0.027 |
| doubao-seed-2.0-pro |                              -0.023 |
| deepseek-v4-pro     |                              -0.022 |
| minimax-m2.7        |                              -0.018 |
| minimax-m3          |                              -0.011 |

A nonzero difference is judge severity/calibration, not automatically self-preference. The semantic-blind panel is still required to isolate self-family effects.

## Does transparent behavior predict held-out-model quality?

| judge             | feature_set               |   roc_auc |   balanced_accuracy |   brier |
|:------------------|:--------------------------|----------:|--------------------:|--------:|
| deepseek-v4-flash | item_plus_all_transparent |     0.894 |               0.819 |   0.130 |
| deepseek-v4-flash | item_plus_length          |     0.869 |               0.790 |   0.158 |
| deepseek-v4-flash | item_plus_policy_length   |     0.898 |               0.821 |   0.129 |
| deepseek-v4-flash | task_item                 |     0.867 |               0.789 |   0.157 |
| deepseek-v4-flash | task_only                 |     0.763 |               0.754 |   0.192 |
| minimax-m3        | item_plus_all_transparent |     0.890 |               0.809 |   0.136 |
| minimax-m3        | item_plus_length          |     0.869 |               0.794 |   0.158 |
| minimax-m3        | item_plus_policy_length   |     0.889 |               0.808 |   0.137 |
| minimax-m3        | task_item                 |     0.867 |               0.795 |   0.158 |
| minimax-m3        | task_only                 |     0.748 |               0.740 |   0.198 |

Models are held out one at a time. `task_item` knows the benchmark arm and exact item but not the candidate model. Feature models add response behavior to that strong item-difficulty baseline; no model identity is supplied.

### Incremental AUC over the task + item baseline

| judge             |   delta_item_plus_length_over_task_item_mean |   delta_item_plus_length_over_task_item_min |   delta_item_plus_length_over_task_item_max |   delta_item_plus_policy_length_over_task_item_mean |   delta_item_plus_policy_length_over_task_item_min |   delta_item_plus_policy_length_over_task_item_max |   delta_item_plus_all_transparent_over_task_item_mean |   delta_item_plus_all_transparent_over_task_item_min |   delta_item_plus_all_transparent_over_task_item_max |
|:------------------|---------------------------------------------:|--------------------------------------------:|--------------------------------------------:|----------------------------------------------------:|---------------------------------------------------:|---------------------------------------------------:|------------------------------------------------------:|-----------------------------------------------------:|-----------------------------------------------------:|
| deepseek-v4-flash |                                        0.002 |                                      -0.000 |                                       0.006 |                                               0.031 |                                              0.012 |                                              0.057 |                                                 0.027 |                                               -0.009 |                                                0.058 |
| minimax-m3        |                                        0.002 |                                      -0.002 |                                       0.006 |                                               0.023 |                                              0.005 |                                              0.050 |                                                 0.024 |                                                0.007 |                                                0.051 |

| judge             | feature_set               |   positive_model_folds |   nonzero_model_folds |   one_sided_exact_sign_p |
|:------------------|:--------------------------|-----------------------:|----------------------:|-------------------------:|
| deepseek-v4-flash | item_plus_length          |                      4 |                     5 |                   0.1875 |
| deepseek-v4-flash | item_plus_policy_length   |                      5 |                     5 |                   0.0312 |
| deepseek-v4-flash | item_plus_all_transparent |                      4 |                     5 |                   0.1875 |
| minimax-m3        | item_plus_length          |                      5 |                     6 |                   0.1094 |
| minimax-m3        | item_plus_policy_length   |                      6 |                     6 |                   0.0156 |
| minimax-m3        | item_plus_all_transparent |                      6 |                     6 |                   0.0156 |

## Current evidential status

The paired prompt effect is not a single-judge artifact if it is positive under both judges. However, these judges use the same pairwise pedagogical rubric, so this is robustness to judge model, not full construct validation.
