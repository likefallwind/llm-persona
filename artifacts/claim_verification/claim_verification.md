# Release claim verification

Overall: **PASS**

| Claim | Observed | Expected | Pass |
|---|---:|---:|:---:|
| core common benchmark-item IDs | `47321` | `47321` | yes |
| core response count implied by paired panel | `283926` | `283926` | yes |
| primary teaching response rows | `31638` | `31638` | yes |
| negative-control response rows | `57516` | `57516` | yes |
| extended MathDial response rows | `26586` | `26586` | yes |
| primary held-out-family macro policy attribution | `0.242` | `0.242` | yes |
| primary held-out-family macro all-feature attribution | `0.251` | `0.251` | yes |
| negative-control macro all-feature attribution | `0.372` | `0.372` | yes |
| cross-domain policy-geometry Mantel r | `0.296` | `0.296` | yes |
| cross-domain policy-geometry exact p | `0.307` | `0.307` | yes |
| pedagogy/generic profile dispersion ratio | `0.763` | `0.763` | yes |
| dispersion bootstrap lower bound | `0.738` | `0.738` | yes |
| dispersion bootstrap upper bound | `0.794` | `0.794` | yes |
| identical responses in judge swap | `14770` | `14770` | yes |
| judge-swap response mismatches | `0` | `0` | yes |
| deepseek-v4-flash mean policy AUC increment | `0.031` | `0.031` | yes |
| deepseek-v4-flash positive held-out-model policy folds | `5` | `5` | yes |
| minimax-m3 mean policy AUC increment | `0.023` | `0.023` | yes |
| minimax-m3 positive held-out-model policy folds | `6` | `6` | yes |
| best judge expert-pair agreement | `0.844` | `0.844` | yes |
| majority minus best CI contains zero | `True` | `True` | yes |
| action-classifier contrasts with all nine models positive | `6` | `6` | yes |
| telling match drops for every classifier | `3` | `3` | yes |
| telling generic match range | `[0.394, 0.442]` | `[0.394, 0.442]` | yes |
| telling pedagogy match range | `[0.111, 0.125]` | `[0.111, 0.125]` | yes |
| LongTutor matched model-history rows | `6000` | `6000` | yes |
| LongTutor unique histories | `1000` | `1000` | yes |
| mean diagnosis-teaching-quality Spearman | `0.173` | `0.173` | yes |
| mean diagnosis-strategy-alignment Spearman | `0.208` | `0.208` | yes |
| mean evidence-teaching-quality Spearman | `-0.01` | `-0.01` | yes |
| LongTutor item-only diagnosis AUC | `0.822` | `0.822` | yes |
| LongTutor teaching-dimensions diagnosis AUC | `0.816` | `0.816` | yes |
| LongTutor teaching-mean diagnosis AUC | `0.817` | `0.817` | yes |
| LongTutor evidence RMSE invariant at reported precision | `[0.187]` | `[0.187]` | yes |
| semantic analyzed batches | `358` | `358` | yes |
| semantic eligible annotations | `1074` | `1074` | yes |
| semantic successful annotations | `1074` | `1074` | yes |
| semantic response units | `2148` | `2148` | yes |
| semantic consensus rows have three judges | `17184` | `17184` | yes |
| reliable semantic dimensions | `['help_directness', 'elicitation', 'cognitive_load']` | `['help_directness', 'elicitation', 'cognitive_load']` | yes |
| cross-task signature dimensions | `['help_directness', 'cognitive_load']` | `['help_directness', 'cognitive_load']` | yes |
| validated disposition dimensions | `['help_directness']` | `['help_directness']` | yes |
| frozen recommended thesis | `pedagogical_policy_signatures` | `pedagogical_policy_signatures` | yes |
| semantic held-out-task attribution | `0.322` | `0.322` | yes |
| combined held-out-task attribution | `0.391` | `0.391` | yes |
| minimum leave-one-judge profile Spearman | `0.959` | `0.959` | yes |
| telling help-directness contrast | `1.36` | `1.36` | yes |
| semantic prompt deltas standard | `[-1.709, 2.47, -0.759]` | `[-1.709, 2.47, -0.759]` | yes |
| semantic prompt deltas hard | `[-1.542, 2.171, -0.721]` | `[-1.542, 2.171, -0.721]` | yes |
| semantic diagnosis AUC item-only | `0.775` | `0.775` | yes |
| semantic diagnosis AUC all dimensions | `0.744` | `0.744` | yes |
