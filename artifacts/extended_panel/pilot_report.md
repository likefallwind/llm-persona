# Deterministic behavioral pilot

Paired responses analyzed: **26,586** across **4** benchmark arms and **9** models.

All features are transparent lexical/action proxies. They are useful for falsification and pipeline validation but are not yet validated pedagogical dispositions.

## Held-out task-family model attribution

Chance accuracy is 0.111. Each fold withholds an entire task family.

| feature_set         |   accuracy |   balanced_accuracy |
|:--------------------|-----------:|--------------------:|
| surface_plus_policy |      0.285 |               0.285 |
| policy              |      0.232 |               0.232 |
| surface             |      0.207 |               0.207 |
| length_only         |      0.163 |               0.163 |

## Most cross-task-stable proxies

Features are centered within each item across models before task aggregation, removing item-level content difficulty.

| feature              |   icc3_1 |   mean_pairwise_spearman |   task_count |
|:---------------------|---------:|-------------------------:|-------------:|
| emoji_rate           |    0.981 |                    0.875 |            4 |
| mean_sentence_tokens |    0.859 |                    0.911 |            4 |
| log_chars            |    0.825 |                    0.858 |            4 |
| log_tokens           |    0.812 |                    0.839 |            4 |
| latex_rate           |    0.745 |                    0.794 |            4 |
| explanation_rate     |    0.728 |                    0.725 |            4 |
| first_plural_rate    |    0.711 |                    0.800 |            4 |
| second_person_rate   |    0.692 |                    0.728 |            4 |

## Paired prompt intervention (selected endpoints)

Delta = explicit LearnLM-style pedagogy prompt minus generic caring-teacher prompt on the same conversation and model.

| family               | model                | feature            |   n_pairs |   generic_mean |   pedagogy_mean |   mean_delta |   paired_dz |   wilcoxon_p |   bh_q |
|:---------------------|:---------------------|:-------------------|----------:|---------------:|----------------:|-------------:|------------:|-------------:|-------:|
| mathdial_bridge      | deepseek-v4-flash    | answer_reveal_rate |      1150 |         0.2701 |          0.1323 |      -0.1379 |     -0.1418 |       0.0000 | 0.0000 |
| mathdial_bridge      | deepseek-v4-pro      | answer_reveal_rate |      1150 |         0.2467 |          0.1212 |      -0.1255 |     -0.1251 |       0.0001 | 0.0001 |
| mathdial_bridge      | doubao-seed-2.0-lite | answer_reveal_rate |      1150 |         0.4412 |          0.3643 |      -0.0769 |     -0.0651 |       0.0362 | 0.0563 |
| mathdial_bridge      | doubao-seed-2.0-pro  | answer_reveal_rate |      1150 |         0.2121 |          0.1943 |      -0.0177 |     -0.0204 |       0.8910 | 1.0000 |
| mathdial_bridge      | glm-5.2              | answer_reveal_rate |      1150 |         0.3018 |          0.1365 |      -0.1652 |     -0.1667 |       0.0000 | 0.0000 |
| mathdial_bridge      | minimax-m2.7         | answer_reveal_rate |      1150 |         0.2491 |          0.1525 |      -0.0966 |     -0.0907 |       0.0048 | 0.0083 |
| mathdial_bridge      | minimax-m3           | answer_reveal_rate |      1150 |         0.3798 |          0.2481 |      -0.1317 |     -0.1061 |       0.0002 | 0.0004 |
| mathdial_bridge      | qwen3.5-4b           | answer_reveal_rate |      1150 |         0.4026 |          0.2585 |      -0.1440 |     -0.1125 |       0.0049 | 0.0085 |
| mathdial_bridge      | qwen3.8-27b          | answer_reveal_rate |      1150 |         0.1880 |          0.2175 |       0.0295 |      0.0258 |       0.2931 | 0.4103 |
| mathdial_bridge      | deepseek-v4-flash    | imperative_rate    |      1150 |         1.8796 |          1.9622 |       0.0826 |      0.0321 |       0.4288 | 0.5751 |
| mathdial_bridge      | deepseek-v4-pro      | imperative_rate    |      1150 |         1.9869 |          1.8274 |      -0.1596 |     -0.0572 |       0.0243 | 0.0385 |
| mathdial_bridge      | doubao-seed-2.0-lite | imperative_rate    |      1150 |         0.7642 |          1.4268 |       0.6626 |      0.2909 |       0.0000 | 0.0000 |
| mathdial_bridge      | doubao-seed-2.0-pro  | imperative_rate    |      1150 |         1.0440 |          2.1078 |       1.0638 |      0.4501 |       0.0000 | 0.0000 |
| mathdial_bridge      | glm-5.2              | imperative_rate    |      1150 |         2.3066 |          2.3447 |       0.0381 |      0.0131 |       0.9625 | 1.0000 |
| mathdial_bridge      | minimax-m2.7         | imperative_rate    |      1150 |         0.8637 |          1.3990 |       0.5353 |      0.2256 |       0.0000 | 0.0000 |
| mathdial_bridge      | minimax-m3           | imperative_rate    |      1150 |         1.8424 |          2.3261 |       0.4838 |      0.1714 |       0.0000 | 0.0000 |
| mathdial_bridge      | qwen3.5-4b           | imperative_rate    |      1150 |         1.9608 |          1.4371 |      -0.5236 |     -0.1881 |       0.0000 | 0.0000 |
| mathdial_bridge      | qwen3.8-27b          | imperative_rate    |      1150 |         1.2353 |          1.3921 |       0.1568 |      0.0561 |       0.0318 | 0.0498 |
| mathdial_bridge      | deepseek-v4-flash    | log_tokens         |      1150 |         3.7720 |          3.4182 |      -0.3538 |     -1.0108 |       0.0000 | 0.0000 |
| mathdial_bridge      | deepseek-v4-pro      | log_tokens         |      1150 |         3.6294 |          3.2993 |      -0.3302 |     -1.0358 |       0.0000 | 0.0000 |
| mathdial_bridge      | doubao-seed-2.0-lite | log_tokens         |      1150 |         3.9537 |          3.5194 |      -0.4343 |     -1.4642 |       0.0000 | 0.0000 |
| mathdial_bridge      | doubao-seed-2.0-pro  | log_tokens         |      1150 |         3.9915 |          3.5135 |      -0.4780 |     -1.6982 |       0.0000 | 0.0000 |
| mathdial_bridge      | glm-5.2              | log_tokens         |      1150 |         3.7949 |          3.5084 |      -0.2865 |     -0.9091 |       0.0000 | 0.0000 |
| mathdial_bridge      | minimax-m2.7         | log_tokens         |      1150 |         3.6757 |          3.4090 |      -0.2667 |     -0.7193 |       0.0000 | 0.0000 |
| mathdial_bridge      | minimax-m3           | log_tokens         |      1150 |         3.7393 |          3.5477 |      -0.1916 |     -0.5695 |       0.0000 | 0.0000 |
| mathdial_bridge      | qwen3.5-4b           | log_tokens         |      1150 |         3.6852 |          3.4675 |      -0.2177 |     -0.5140 |       0.0000 | 0.0000 |
| mathdial_bridge      | qwen3.8-27b          | log_tokens         |      1150 |         3.5459 |          3.2886 |      -0.2572 |     -0.9040 |       0.0000 | 0.0000 |
| mathdial_bridge      | deepseek-v4-flash    | outcome_primary    |       224 |         0.1451 |          0.8125 |       0.6674 |      1.4099 |       0.0000 | 0.0000 |
| mathdial_bridge      | deepseek-v4-pro      | outcome_primary    |      1150 |         0.5004 |          0.8396 |       0.3391 |      0.6690 |       0.0000 | 0.0000 |
| mathdial_bridge      | doubao-seed-2.0-lite | outcome_primary    |      1004 |         0.2694 |          0.8596 |       0.5901 |      1.2295 |       0.0000 | 0.0000 |
| mathdial_bridge      | doubao-seed-2.0-pro  | outcome_primary    |      1150 |         0.3496 |          0.8670 |       0.5174 |      1.0554 |       0.0000 | 0.0000 |
| mathdial_bridge      | glm-5.2              | outcome_primary    |      1150 |         0.5948 |          0.8583 |       0.2635 |      0.5521 |       0.0000 | 0.0000 |
| mathdial_bridge      | minimax-m2.7         | outcome_primary    |      1150 |         0.1426 |          0.7448 |       0.6022 |      1.2665 |       0.0000 | 0.0000 |
| mathdial_bridge      | minimax-m3           | outcome_primary    |      1150 |         0.2713 |          0.8317 |       0.5604 |      1.1322 |       0.0000 | 0.0000 |
| mathdial_bridge      | qwen3.5-4b           | outcome_primary    |      1150 |         0.2422 |          0.7396 |       0.4974 |      1.0717 |       0.0000 | 0.0000 |
| mathdial_bridge      | deepseek-v4-flash    | praise_rate        |      1150 |         1.5260 |          2.5435 |       1.0175 |      0.3730 |       0.0000 | 0.0000 |
| mathdial_bridge      | deepseek-v4-pro      | praise_rate        |      1150 |         1.1118 |          1.4140 |       0.3021 |      0.1084 |       0.0023 | 0.0041 |
| mathdial_bridge      | doubao-seed-2.0-lite | praise_rate        |      1150 |         3.0712 |          2.1205 |      -0.9507 |     -0.3762 |       0.0000 | 0.0000 |
| mathdial_bridge      | doubao-seed-2.0-pro  | praise_rate        |      1150 |         2.2156 |          2.5063 |       0.2907 |      0.1330 |       0.0000 | 0.0000 |
| mathdial_bridge      | glm-5.2              | praise_rate        |      1150 |         1.3345 |          1.5943 |       0.2598 |      0.1172 |       0.0000 | 0.0001 |
| mathdial_bridge      | minimax-m2.7         | praise_rate        |      1150 |         1.4366 |          2.7257 |       1.2891 |      0.4626 |       0.0000 | 0.0000 |
| mathdial_bridge      | minimax-m3           | praise_rate        |      1150 |         2.4785 |          2.3110 |      -0.1675 |     -0.0673 |       0.0277 | 0.0438 |
| mathdial_bridge      | qwen3.5-4b           | praise_rate        |      1150 |         1.9715 |          1.1958 |      -0.7758 |     -0.2981 |       0.0000 | 0.0000 |
| mathdial_bridge      | qwen3.8-27b          | praise_rate        |      1150 |         1.7923 |          2.6679 |       0.8756 |      0.2913 |       0.0000 | 0.0000 |
| mathdial_bridge      | deepseek-v4-flash    | question_rate      |      1150 |         0.4829 |          3.1939 |       2.7110 |      1.4429 |       0.0000 | 0.0000 |
| mathdial_bridge      | deepseek-v4-pro      | question_rate      |      1150 |         1.0730 |          3.8904 |       2.8174 |      1.3022 |       0.0000 | 0.0000 |
| mathdial_bridge      | doubao-seed-2.0-lite | question_rate      |      1150 |         0.2275 |          3.1555 |       2.9280 |      2.6097 |       0.0000 | 0.0000 |
| mathdial_bridge      | doubao-seed-2.0-pro  | question_rate      |      1150 |         0.3752 |          3.1789 |       2.8038 |      2.5949 |       0.0000 | 0.0000 |
| mathdial_bridge      | glm-5.2              | question_rate      |      1150 |         1.1526 |          3.1518 |       1.9992 |      1.2503 |       0.0000 | 0.0000 |
| mathdial_bridge      | minimax-m2.7         | question_rate      |      1150 |         0.2814 |          3.6173 |       3.3359 |      2.0847 |       0.0000 | 0.0000 |
| mathdial_bridge      | minimax-m3           | question_rate      |      1150 |         0.6622 |          3.2064 |       2.5442 |      1.4904 |       0.0000 | 0.0000 |
| mathdial_bridge      | qwen3.5-4b           | question_rate      |      1150 |         0.1653 |          3.3030 |       3.1376 |      2.6020 |       0.0000 | 0.0000 |
| mathdial_bridge      | qwen3.8-27b          | question_rate      |      1150 |         0.3991 |          3.7820 |       3.3830 |      2.0200 |       0.0000 | 0.0000 |
| mathdial_bridge_hard | deepseek-v4-flash    | answer_reveal_rate |       327 |         0.3178 |          0.1659 |      -0.1520 |     -0.1474 |       0.0165 | 0.0265 |
| mathdial_bridge_hard | deepseek-v4-pro      | answer_reveal_rate |       327 |         0.2461 |          0.1254 |      -0.1207 |     -0.1122 |       0.0615 | 0.0940 |
| mathdial_bridge_hard | doubao-seed-2.0-lite | answer_reveal_rate |       327 |         0.5006 |          0.3351 |      -0.1654 |     -0.1265 |       0.0338 | 0.0527 |
| mathdial_bridge_hard | doubao-seed-2.0-pro  | answer_reveal_rate |       327 |         0.2240 |          0.2604 |       0.0363 |      0.0349 |       0.4094 | 0.5524 |
| mathdial_bridge_hard | glm-5.2              | answer_reveal_rate |       327 |         0.3513 |          0.1947 |      -0.1566 |     -0.1455 |       0.0058 | 0.0099 |
| mathdial_bridge_hard | minimax-m2.7         | answer_reveal_rate |       327 |         0.2884 |          0.1462 |      -0.1422 |     -0.1162 |       0.0394 | 0.0609 |
| mathdial_bridge_hard | minimax-m3           | answer_reveal_rate |       327 |         0.2764 |          0.3350 |       0.0585 |      0.0479 |       0.2857 | 0.4037 |
| mathdial_bridge_hard | qwen3.5-4b           | answer_reveal_rate |       327 |         0.4647 |          0.2486 |      -0.2161 |     -0.1602 |       0.0282 | 0.0445 |
| mathdial_bridge_hard | qwen3.8-27b          | answer_reveal_rate |       327 |         0.2202 |          0.2355 |       0.0154 |      0.0119 |       0.5324 | 0.6995 |
| mathdial_bridge_hard | deepseek-v4-flash    | imperative_rate    |       327 |         1.7271 |          1.9180 |       0.1909 |      0.0675 |       0.2138 | 0.3070 |
| mathdial_bridge_hard | deepseek-v4-pro      | imperative_rate    |       327 |         1.8990 |          1.6373 |      -0.2617 |     -0.0903 |       0.0863 | 0.1302 |
| mathdial_bridge_hard | doubao-seed-2.0-lite | imperative_rate    |       327 |         0.7949 |          1.0376 |       0.2427 |      0.1092 |       0.0232 | 0.0370 |
| mathdial_bridge_hard | doubao-seed-2.0-pro  | imperative_rate    |       327 |         1.1006 |          1.9287 |       0.8280 |      0.3283 |       0.0000 | 0.0000 |
| mathdial_bridge_hard | glm-5.2              | imperative_rate    |       327 |         2.2916 |          1.8107 |      -0.4809 |     -0.1712 |       0.0026 | 0.0045 |
| mathdial_bridge_hard | minimax-m2.7         | imperative_rate    |       327 |         0.7915 |          1.0286 |       0.2371 |      0.0978 |       0.0893 | 0.1343 |
| mathdial_bridge_hard | minimax-m3           | imperative_rate    |       327 |         1.9137 |          2.0184 |       0.1047 |      0.0352 |       0.6186 | 0.8010 |
| mathdial_bridge_hard | qwen3.5-4b           | imperative_rate    |       327 |         2.0850 |          1.5880 |      -0.4970 |     -0.1739 |       0.0029 | 0.0051 |
| mathdial_bridge_hard | qwen3.8-27b          | imperative_rate    |       327 |         1.4824 |          1.0889 |      -0.3935 |     -0.1375 |       0.0380 | 0.0589 |
| mathdial_bridge_hard | deepseek-v4-flash    | log_tokens         |       327 |         3.7013 |          3.4186 |      -0.2827 |     -0.7993 |       0.0000 | 0.0000 |
| mathdial_bridge_hard | deepseek-v4-pro      | log_tokens         |       327 |         3.5356 |          3.2431 |      -0.2925 |     -0.7691 |       0.0000 | 0.0000 |
| mathdial_bridge_hard | doubao-seed-2.0-lite | log_tokens         |       327 |         3.8803 |          3.4406 |      -0.4398 |     -1.3977 |       0.0000 | 0.0000 |
| mathdial_bridge_hard | doubao-seed-2.0-pro  | log_tokens         |       327 |         3.9146 |          3.4640 |      -0.4506 |     -1.5118 |       0.0000 | 0.0000 |
| mathdial_bridge_hard | glm-5.2              | log_tokens         |       327 |         3.6982 |          3.3889 |      -0.3092 |     -0.9204 |       0.0000 | 0.0000 |
| mathdial_bridge_hard | minimax-m2.7         | log_tokens         |       327 |         3.5903 |          3.3454 |      -0.2450 |     -0.5875 |       0.0000 | 0.0000 |
| mathdial_bridge_hard | minimax-m3           | log_tokens         |       327 |         3.6918 |          3.4501 |      -0.2418 |     -0.7297 |       0.0000 | 0.0000 |
| mathdial_bridge_hard | qwen3.5-4b           | log_tokens         |       327 |         3.6243 |          3.4232 |      -0.2011 |     -0.4798 |       0.0000 | 0.0000 |
| mathdial_bridge_hard | qwen3.8-27b          | log_tokens         |       327 |         3.4397 |          3.2058 |      -0.2339 |     -0.7888 |       0.0000 | 0.0000 |
| mathdial_bridge_hard | deepseek-v4-flash    | outcome_primary    |       284 |         0.1778 |          0.7430 |       0.5651 |      1.1788 |       0.0000 | 0.0000 |
| mathdial_bridge_hard | deepseek-v4-pro      | outcome_primary    |       327 |         0.4128 |          0.8532 |       0.4404 |      0.8857 |       0.0000 | 0.0000 |
| mathdial_bridge_hard | doubao-seed-2.0-lite | outcome_primary    |       269 |         0.2230 |          0.7974 |       0.5743 |      1.1752 |       0.0000 | 0.0000 |
| mathdial_bridge_hard | doubao-seed-2.0-pro  | outcome_primary    |       327 |         0.3425 |          0.8639 |       0.5214 |      1.0568 |       0.0000 | 0.0000 |
| mathdial_bridge_hard | glm-5.2              | outcome_primary    |       327 |         0.5612 |          0.8349 |       0.2737 |      0.5678 |       0.0000 | 0.0000 |
| mathdial_bridge_hard | minimax-m2.7         | outcome_primary    |       327 |         0.1300 |          0.6621 |       0.5321 |      1.1213 |       0.0000 | 0.0000 |
| mathdial_bridge_hard | minimax-m3           | outcome_primary    |       327 |         0.2248 |          0.7875 |       0.5627 |      1.1188 |       0.0000 | 0.0000 |
| mathdial_bridge_hard | qwen3.5-4b           | outcome_primary    |       327 |         0.2187 |          0.6284 |       0.4098 |      0.8625 |       0.0000 | 0.0000 |
| mathdial_bridge_hard | deepseek-v4-flash    | praise_rate        |       327 |         1.4942 |          2.0378 |       0.5436 |      0.1876 |       0.0000 | 0.0000 |
| mathdial_bridge_hard | deepseek-v4-pro      | praise_rate        |       327 |         1.0555 |          1.1539 |       0.0984 |      0.0369 |       0.4163 | 0.5601 |
| mathdial_bridge_hard | doubao-seed-2.0-lite | praise_rate        |       327 |         3.1316 |          2.0182 |      -1.1134 |     -0.3773 |       0.0000 | 0.0000 |
| mathdial_bridge_hard | doubao-seed-2.0-pro  | praise_rate        |       327 |         1.8626 |          1.9475 |       0.0849 |      0.0361 |       0.7837 | 0.9974 |
| mathdial_bridge_hard | glm-5.2              | praise_rate        |       327 |         1.2201 |          1.2806 |       0.0605 |      0.0260 |       0.9030 | 1.0000 |
| mathdial_bridge_hard | minimax-m2.7         | praise_rate        |       327 |         1.3466 |          2.3769 |       1.0303 |      0.3525 |       0.0000 | 0.0000 |
| mathdial_bridge_hard | minimax-m3           | praise_rate        |       327 |         2.0852 |          1.8717 |      -0.2135 |     -0.0862 |       0.0913 | 0.1368 |
| mathdial_bridge_hard | qwen3.5-4b           | praise_rate        |       327 |         1.8705 |          1.3904 |      -0.4801 |     -0.1726 |       0.0015 | 0.0026 |
| mathdial_bridge_hard | qwen3.8-27b          | praise_rate        |       327 |         1.5052 |          2.3272 |       0.8221 |      0.2581 |       0.0000 | 0.0000 |
| mathdial_bridge_hard | deepseek-v4-flash    | question_rate      |       327 |         0.5011 |          3.1246 |       2.6234 |      1.2619 |       0.0000 | 0.0000 |
| mathdial_bridge_hard | deepseek-v4-pro      | question_rate      |       327 |         1.1511 |          4.2229 |       3.0718 |      1.2066 |       0.0000 | 0.0000 |
| mathdial_bridge_hard | doubao-seed-2.0-lite | question_rate      |       327 |         0.2260 |          3.2388 |       3.0128 |      2.1711 |       0.0000 | 0.0000 |
| mathdial_bridge_hard | doubao-seed-2.0-pro  | question_rate      |       327 |         0.6372 |          3.3273 |       2.6901 |      1.8973 |       0.0000 | 0.0000 |
| mathdial_bridge_hard | glm-5.2              | question_rate      |       327 |         1.6006 |          3.4785 |       1.8779 |      1.0394 |       0.0000 | 0.0000 |
| mathdial_bridge_hard | minimax-m2.7         | question_rate      |       327 |         0.3743 |          3.6426 |       3.2682 |      1.6801 |       0.0000 | 0.0000 |
| mathdial_bridge_hard | minimax-m3           | question_rate      |       327 |         0.7629 |          3.5075 |       2.7446 |      1.4389 |       0.0000 | 0.0000 |
| mathdial_bridge_hard | qwen3.5-4b           | question_rate      |       327 |         0.1479 |          3.3703 |       3.2224 |      2.2239 |       0.0000 | 0.0000 |
| mathdial_bridge_hard | qwen3.8-27b          | question_rate      |       327 |         0.6480 |          4.1215 |       3.4735 |      1.6860 |       0.0000 | 0.0000 |

## Interpretation boundary

Above-chance attribution demonstrates a reproducible signature, not personality. The next stage must replace proxy-only interpretation with multi-judge behavioral coding, outcome prediction, judge-swap robustness, and preregistered confirmatory analyses.
