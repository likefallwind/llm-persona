# Leave-one-judge-out semantic sensitivity

| excluded_judge   |   profile_spearman_vs_full |   prompt_cells |   prompt_sign_reversals |   max_absolute_prompt_delta_change |   mean_absolute_prompt_delta_change |
|:-----------------|---------------------------:|---------------:|------------------------:|-----------------------------------:|------------------------------------:|
| MiniMax-M3       |                      0.961 |             96 |                       3 |                              0.363 |                               0.085 |
| deepseek-v4-pro  |                      0.962 |             96 |                       2 |                              0.272 |                               0.086 |
| glm-5.2          |                      0.959 |             96 |                       1 |                              0.222 |                               0.077 |

Prompt sign reversals are counted over model × task × dimension cells and are never hidden by averaging. Detailed prompt and cross-task ICC changes are saved alongside this report.
