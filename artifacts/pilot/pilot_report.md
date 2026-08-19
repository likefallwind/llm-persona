# Deterministic behavioral pilot

Paired responses analyzed: **31,638** across **6** benchmark arms and **6** models.

All features are transparent lexical/action proxies. They are useful for falsification and pipeline validation but are not yet validated pedagogical dispositions.

## Held-out task-family model attribution

Chance accuracy is 0.167. Each fold withholds an entire task family.

| feature_set         |   accuracy |   balanced_accuracy |
|:--------------------|-----------:|--------------------:|
| surface_plus_policy |      0.251 |               0.251 |
| policy              |      0.242 |               0.242 |
| length_only         |      0.230 |               0.230 |
| surface             |      0.215 |               0.215 |

## Most cross-task-stable proxies

Features are centered within each item across models before task aggregation, removing item-level content difficulty.

| feature              |   icc3_1 |   mean_pairwise_spearman |   task_count |
|:---------------------|---------:|-------------------------:|-------------:|
| mean_sentence_tokens |    0.645 |                    0.619 |            6 |
| explanation_rate     |    0.546 |                    0.621 |            6 |
| first_plural_rate    |    0.484 |                    0.608 |            6 |
| hedge_rate           |    0.474 |                    0.524 |            6 |
| log_chars            |    0.470 |                    0.528 |            6 |
| emoji_rate           |    0.397 |                    0.796 |            6 |
| latex_rate           |    0.373 |                    0.448 |            6 |
| ends_question        |    0.366 |                    0.391 |            6 |

## Paired prompt intervention (selected endpoints)

Delta = explicit LearnLM-style pedagogy prompt minus generic caring-teacher prompt on the same conversation and model.

| family               | model               | feature            |   n_pairs |   generic_mean |   pedagogy_mean |   mean_delta |   paired_dz |   wilcoxon_p |   bh_q |
|:---------------------|:--------------------|:-------------------|----------:|---------------:|----------------:|-------------:|------------:|-------------:|-------:|
| mathdial_bridge      | deepseek-v4-pro     | answer_reveal_rate |      1150 |         0.2467 |          0.1212 |      -0.1255 |     -0.1251 |       0.0001 | 0.0001 |
| mathdial_bridge      | doubao-seed-2.0-pro | answer_reveal_rate |      1150 |         0.2121 |          0.1943 |      -0.0177 |     -0.0204 |       0.8910 | 1.0000 |
| mathdial_bridge      | glm-5.2             | answer_reveal_rate |      1150 |         0.3018 |          0.1365 |      -0.1652 |     -0.1667 |       0.0000 | 0.0000 |
| mathdial_bridge      | minimax-m2.7        | answer_reveal_rate |      1150 |         0.2491 |          0.1525 |      -0.0966 |     -0.0907 |       0.0048 | 0.0083 |
| mathdial_bridge      | minimax-m3          | answer_reveal_rate |      1150 |         0.3798 |          0.2481 |      -0.1317 |     -0.1061 |       0.0002 | 0.0004 |
| mathdial_bridge      | qwen3.5-4b          | answer_reveal_rate |      1150 |         0.4026 |          0.2585 |      -0.1440 |     -0.1125 |       0.0049 | 0.0085 |
| mathdial_bridge      | deepseek-v4-pro     | imperative_rate    |      1150 |         1.9869 |          1.8274 |      -0.1596 |     -0.0572 |       0.0243 | 0.0381 |
| mathdial_bridge      | doubao-seed-2.0-pro | imperative_rate    |      1150 |         1.0440 |          2.1078 |       1.0638 |      0.4501 |       0.0000 | 0.0000 |
| mathdial_bridge      | glm-5.2             | imperative_rate    |      1150 |         2.3066 |          2.3447 |       0.0381 |      0.0131 |       0.9625 | 1.0000 |
| mathdial_bridge      | minimax-m2.7        | imperative_rate    |      1150 |         0.8637 |          1.3990 |       0.5353 |      0.2256 |       0.0000 | 0.0000 |
| mathdial_bridge      | minimax-m3          | imperative_rate    |      1150 |         1.8424 |          2.3261 |       0.4838 |      0.1714 |       0.0000 | 0.0000 |
| mathdial_bridge      | qwen3.5-4b          | imperative_rate    |      1150 |         1.9608 |          1.4371 |      -0.5236 |     -0.1881 |       0.0000 | 0.0000 |
| mathdial_bridge      | deepseek-v4-pro     | log_tokens         |      1150 |         3.6294 |          3.2993 |      -0.3302 |     -1.0358 |       0.0000 | 0.0000 |
| mathdial_bridge      | doubao-seed-2.0-pro | log_tokens         |      1150 |         3.9915 |          3.5135 |      -0.4780 |     -1.6982 |       0.0000 | 0.0000 |
| mathdial_bridge      | glm-5.2             | log_tokens         |      1150 |         3.7949 |          3.5084 |      -0.2865 |     -0.9091 |       0.0000 | 0.0000 |
| mathdial_bridge      | minimax-m2.7        | log_tokens         |      1150 |         3.6757 |          3.4090 |      -0.2667 |     -0.7193 |       0.0000 | 0.0000 |
| mathdial_bridge      | minimax-m3          | log_tokens         |      1150 |         3.7393 |          3.5477 |      -0.1916 |     -0.5695 |       0.0000 | 0.0000 |
| mathdial_bridge      | qwen3.5-4b          | log_tokens         |      1150 |         3.6852 |          3.4675 |      -0.2177 |     -0.5140 |       0.0000 | 0.0000 |
| mathdial_bridge      | deepseek-v4-pro     | outcome_primary    |      1150 |         0.5004 |          0.8396 |       0.3391 |      0.6690 |       0.0000 | 0.0000 |
| mathdial_bridge      | doubao-seed-2.0-pro | outcome_primary    |      1150 |         0.3496 |          0.8670 |       0.5174 |      1.0554 |       0.0000 | 0.0000 |
| mathdial_bridge      | glm-5.2             | outcome_primary    |      1150 |         0.5948 |          0.8583 |       0.2635 |      0.5521 |       0.0000 | 0.0000 |
| mathdial_bridge      | minimax-m2.7        | outcome_primary    |      1150 |         0.1426 |          0.7448 |       0.6022 |      1.2665 |       0.0000 | 0.0000 |
| mathdial_bridge      | minimax-m3          | outcome_primary    |      1150 |         0.2713 |          0.8317 |       0.5604 |      1.1322 |       0.0000 | 0.0000 |
| mathdial_bridge      | qwen3.5-4b          | outcome_primary    |      1150 |         0.2422 |          0.7396 |       0.4974 |      1.0717 |       0.0000 | 0.0000 |
| mathdial_bridge      | deepseek-v4-pro     | praise_rate        |      1150 |         1.1118 |          1.4140 |       0.3021 |      0.1084 |       0.0023 | 0.0042 |
| mathdial_bridge      | doubao-seed-2.0-pro | praise_rate        |      1150 |         2.2156 |          2.5063 |       0.2907 |      0.1330 |       0.0000 | 0.0000 |
| mathdial_bridge      | glm-5.2             | praise_rate        |      1150 |         1.3345 |          1.5943 |       0.2598 |      0.1172 |       0.0000 | 0.0001 |
| mathdial_bridge      | minimax-m2.7        | praise_rate        |      1150 |         1.4366 |          2.7257 |       1.2891 |      0.4626 |       0.0000 | 0.0000 |
| mathdial_bridge      | minimax-m3          | praise_rate        |      1150 |         2.4785 |          2.3110 |      -0.1675 |     -0.0673 |       0.0277 | 0.0433 |
| mathdial_bridge      | qwen3.5-4b          | praise_rate        |      1150 |         1.9715 |          1.1958 |      -0.7758 |     -0.2981 |       0.0000 | 0.0000 |
| mathdial_bridge      | deepseek-v4-pro     | question_rate      |      1150 |         1.0730 |          3.8904 |       2.8174 |      1.3022 |       0.0000 | 0.0000 |
| mathdial_bridge      | doubao-seed-2.0-pro | question_rate      |      1150 |         0.3752 |          3.1789 |       2.8038 |      2.5949 |       0.0000 | 0.0000 |
| mathdial_bridge      | glm-5.2             | question_rate      |      1150 |         1.1526 |          3.1518 |       1.9992 |      1.2503 |       0.0000 | 0.0000 |
| mathdial_bridge      | minimax-m2.7        | question_rate      |      1150 |         0.2814 |          3.6173 |       3.3359 |      2.0847 |       0.0000 | 0.0000 |
| mathdial_bridge      | minimax-m3          | question_rate      |      1150 |         0.6622 |          3.2064 |       2.5442 |      1.4904 |       0.0000 | 0.0000 |
| mathdial_bridge      | qwen3.5-4b          | question_rate      |      1150 |         0.1653 |          3.3030 |       3.1376 |      2.6020 |       0.0000 | 0.0000 |
| mathdial_bridge_hard | deepseek-v4-pro     | answer_reveal_rate |       327 |         0.2461 |          0.1254 |      -0.1207 |     -0.1122 |       0.0615 | 0.0936 |
| mathdial_bridge_hard | doubao-seed-2.0-pro | answer_reveal_rate |       327 |         0.2240 |          0.2604 |       0.0363 |      0.0349 |       0.4094 | 0.5532 |
| mathdial_bridge_hard | glm-5.2             | answer_reveal_rate |       327 |         0.3513 |          0.1947 |      -0.1566 |     -0.1455 |       0.0058 | 0.0098 |
| mathdial_bridge_hard | minimax-m2.7        | answer_reveal_rate |       327 |         0.2884 |          0.1462 |      -0.1422 |     -0.1162 |       0.0394 | 0.0607 |
| mathdial_bridge_hard | minimax-m3          | answer_reveal_rate |       327 |         0.2764 |          0.3350 |       0.0585 |      0.0479 |       0.2857 | 0.4023 |
| mathdial_bridge_hard | qwen3.5-4b          | answer_reveal_rate |       327 |         0.4647 |          0.2486 |      -0.2161 |     -0.1602 |       0.0282 | 0.0439 |
| mathdial_bridge_hard | deepseek-v4-pro     | imperative_rate    |       327 |         1.8990 |          1.6373 |      -0.2617 |     -0.0903 |       0.0863 | 0.1301 |
| mathdial_bridge_hard | doubao-seed-2.0-pro | imperative_rate    |       327 |         1.1006 |          1.9287 |       0.8280 |      0.3283 |       0.0000 | 0.0000 |
| mathdial_bridge_hard | glm-5.2             | imperative_rate    |       327 |         2.2916 |          1.8107 |      -0.4809 |     -0.1712 |       0.0026 | 0.0046 |
| mathdial_bridge_hard | minimax-m2.7        | imperative_rate    |       327 |         0.7915 |          1.0286 |       0.2371 |      0.0978 |       0.0893 | 0.1340 |
| mathdial_bridge_hard | minimax-m3          | imperative_rate    |       327 |         1.9137 |          2.0184 |       0.1047 |      0.0352 |       0.6186 | 0.8034 |
| mathdial_bridge_hard | qwen3.5-4b          | imperative_rate    |       327 |         2.0850 |          1.5880 |      -0.4970 |     -0.1739 |       0.0029 | 0.0051 |
| mathdial_bridge_hard | deepseek-v4-pro     | log_tokens         |       327 |         3.5356 |          3.2431 |      -0.2925 |     -0.7691 |       0.0000 | 0.0000 |
| mathdial_bridge_hard | doubao-seed-2.0-pro | log_tokens         |       327 |         3.9146 |          3.4640 |      -0.4506 |     -1.5118 |       0.0000 | 0.0000 |
| mathdial_bridge_hard | glm-5.2             | log_tokens         |       327 |         3.6982 |          3.3889 |      -0.3092 |     -0.9204 |       0.0000 | 0.0000 |
| mathdial_bridge_hard | minimax-m2.7        | log_tokens         |       327 |         3.5903 |          3.3454 |      -0.2450 |     -0.5875 |       0.0000 | 0.0000 |
| mathdial_bridge_hard | minimax-m3          | log_tokens         |       327 |         3.6918 |          3.4501 |      -0.2418 |     -0.7297 |       0.0000 | 0.0000 |
| mathdial_bridge_hard | qwen3.5-4b          | log_tokens         |       327 |         3.6243 |          3.4232 |      -0.2011 |     -0.4798 |       0.0000 | 0.0000 |
| mathdial_bridge_hard | deepseek-v4-pro     | outcome_primary    |       327 |         0.4128 |          0.8532 |       0.4404 |      0.8857 |       0.0000 | 0.0000 |
| mathdial_bridge_hard | doubao-seed-2.0-pro | outcome_primary    |       327 |         0.3425 |          0.8639 |       0.5214 |      1.0568 |       0.0000 | 0.0000 |
| mathdial_bridge_hard | glm-5.2             | outcome_primary    |       327 |         0.5612 |          0.8349 |       0.2737 |      0.5678 |       0.0000 | 0.0000 |
| mathdial_bridge_hard | minimax-m2.7        | outcome_primary    |       327 |         0.1300 |          0.6621 |       0.5321 |      1.1213 |       0.0000 | 0.0000 |
| mathdial_bridge_hard | minimax-m3          | outcome_primary    |       327 |         0.2248 |          0.7875 |       0.5627 |      1.1188 |       0.0000 | 0.0000 |
| mathdial_bridge_hard | qwen3.5-4b          | outcome_primary    |       327 |         0.2187 |          0.6284 |       0.4098 |      0.8625 |       0.0000 | 0.0000 |
| mathdial_bridge_hard | deepseek-v4-pro     | praise_rate        |       327 |         1.0555 |          1.1539 |       0.0984 |      0.0369 |       0.4163 | 0.5601 |
| mathdial_bridge_hard | doubao-seed-2.0-pro | praise_rate        |       327 |         1.8626 |          1.9475 |       0.0849 |      0.0361 |       0.7837 | 1.0000 |
| mathdial_bridge_hard | glm-5.2             | praise_rate        |       327 |         1.2201 |          1.2806 |       0.0605 |      0.0260 |       0.9030 | 1.0000 |
| mathdial_bridge_hard | minimax-m2.7        | praise_rate        |       327 |         1.3466 |          2.3769 |       1.0303 |      0.3525 |       0.0000 | 0.0000 |
| mathdial_bridge_hard | minimax-m3          | praise_rate        |       327 |         2.0852 |          1.8717 |      -0.2135 |     -0.0862 |       0.0913 | 0.1363 |
| mathdial_bridge_hard | qwen3.5-4b          | praise_rate        |       327 |         1.8705 |          1.3904 |      -0.4801 |     -0.1726 |       0.0015 | 0.0027 |
| mathdial_bridge_hard | deepseek-v4-pro     | question_rate      |       327 |         1.1511 |          4.2229 |       3.0718 |      1.2066 |       0.0000 | 0.0000 |
| mathdial_bridge_hard | doubao-seed-2.0-pro | question_rate      |       327 |         0.6372 |          3.3273 |       2.6901 |      1.8973 |       0.0000 | 0.0000 |
| mathdial_bridge_hard | glm-5.2             | question_rate      |       327 |         1.6006 |          3.4785 |       1.8779 |      1.0394 |       0.0000 | 0.0000 |
| mathdial_bridge_hard | minimax-m2.7        | question_rate      |       327 |         0.3743 |          3.6426 |       3.2682 |      1.6801 |       0.0000 | 0.0000 |
| mathdial_bridge_hard | minimax-m3          | question_rate      |       327 |         0.7629 |          3.5075 |       2.7446 |      1.4389 |       0.0000 | 0.0000 |
| mathdial_bridge_hard | qwen3.5-4b          | question_rate      |       327 |         0.1479 |          3.3703 |       3.2224 |      2.2239 |       0.0000 | 0.0000 |

## Interpretation boundary

Above-chance attribution demonstrates a reproducible signature, not personality. The next stage must replace proxy-only interpretation with multi-judge behavioral coding, outcome prediction, judge-swap robustness, and preregistered confirmatory analyses.
