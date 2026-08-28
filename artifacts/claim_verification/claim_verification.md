# Release claim verification

Overall: **PASS**

| Claim | Observed | Expected | Pass |
|---|---:|---:|:---:|
| core common benchmark-item IDs | `47321` | `47321` | yes |
| core response count implied by paired panel | `283926` | `283926` | yes |
| general-personality bridge included responses | `123468` | `123468` | yes |
| general-personality bridge promising candidates | `[]` | `[]` | yes |
| general-personality bridge verdict | `existing_archive_does_not_yet_support_general_personality_bridge` | `existing_archive_does_not_yet_support_general_personality_bridge` | yes |
| general bridge organizational-style ICC | `0.601` | `0.601` | yes |
| general bridge organizational-style median task rho | `0.771` | `0.771` | yes |
| general bridge communal transport | `0.829` | `0.829` | yes |
| general bridge dialogic transport | `0.657` | `0.657` | yes |
| general-personality constructs audited | `22` | `22` | yes |
| general-personality partial candidates | `9` | `9` | yes |
| general-personality unidentifiable constructs | `13` | `13` | yes |
| validated general-personality constructs | `[]` | `[]` | yes |
| general-personality targeted pilot priority | `['agreeableness_affiliation_and_benevolence']` | `['agreeableness_affiliation_and_benevolence']` | yes |
| organization versus IFEval rho | `-0.886` | `-0.886` | yes |
| organization versus IFEval exact p | `0.035` | `0.035` | yes |
| affiliation generator calls | `280` | `280` | yes |
| affiliation judge calls | `144` | `144` | yes |
| affiliation primary ICC3k | `0.931` | `0.931` | yes |
| affiliation cross-domain rho | `0.9` | `0.9` | yes |
| affiliation irrelevant-context rho | `0.718` | `0.718` | yes |
| affiliation high-low effect | `1.689` | `1.689` | yes |
| affiliation directional models | `5` | `5` | yes |
| affiliation self-report behavior rho | `-0.2` | `-0.2` | yes |
| affiliation forced-choice ceiling | `None` | `None` | yes |
| stable default affiliation supported | `True` | `True` | yes |
| general personality convergence rejected | `False` | `False` | yes |
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
| prompt-contingent signature verdict | `prompt_contingent_policy_signatures_supported` | `prompt_contingent_policy_signatures_supported` | yes |
| prompt-contingent signature decision gates | `True` | `True` | yes |
| headroom-adjusted replicated elasticity dimensions | `['elicitation', 'help_directness']` | `['elicitation', 'help_directness']` | yes |
| mathdial_standard reliable-dimension prompt/model SS ratio range | `[3.987, 7.532]` | `[3.987, 7.532]` | yes |
| mathdial_hard reliable-dimension prompt/model SS ratio range | `[4.837, 6.685]` | `[4.837, 6.685]` | yes |
| mathdial_standard reliable-dimension prompt/default-range ratio | `[1.0, 1.148]` | `[1.0, 1.148]` | yes |
| mathdial_hard reliable-dimension prompt/default-range ratio | `[0.848, 1.011]` | `[0.848, 1.011]` | yes |
| pooled cross-prompt identity accuracy | `[0.301, 0.297]` | `[0.301, 0.297]` | yes |
| pooled cross-prompt identity lower bounds exceed chance | `True` | `True` | yes |
| cross-task cross-prompt transfer directions | `4` | `4` | yes |
| cross-task cross-prompt lower bounds exceed chance | `True` | `True` | yes |
| character formal judge calls | `1160` | `1160` | yes |
| character formal missing or failed calls | `0` | `0` | yes |
| character formal classifications | `{'instructional_agency': 'formal_signature_not_supported', 'relational_communion': 'formal_signature_not_supported', 'next_step_actionability': 'formal_signature_not_supported'}` | `{'instructional_agency': 'formal_signature_not_supported', 'relational_communion': 'formal_signature_not_supported', 'next_step_actionability': 'formal_signature_not_supported'}` | yes |
| agency pilot failure remains binding | `False` | `False` | yes |
| character formal ICC(3,k) | `[0.9, 0.945, 0.871]` | `[0.9, 0.945, 0.871]` | yes |
| formal actionability minimum judge-profile rho | `0.6` | `0.6` | yes |
| formal actionability cross-task stability | `[-0.111, -0.771]` | `[-0.111, -0.771]` | yes |
| formal communion convergence with warmth | `0.805` | `0.805` | yes |
| mathdial_standard confirmatory character prompt effects and scale ratios | `[-0.995, 1.047, 0.679, 0.856]` | `[-0.995, 1.047, 0.679, 0.856]` | yes |
| mathdial_hard confirmatory character prompt effects and scale ratios | `[-1.039, 0.88, 0.942, 0.787]` | `[-1.039, 0.88, 0.942, 0.787]` | yes |
| formal actionability judge-family robust | `False` | `False` | yes |
| all confirmatory scores mean quality AUC gain | `0.0035` | `0.0035` | yes |
| educational character supported axes | `['assistance_directness', 'epistemic_commitment']` | `['assistance_directness', 'epistemic_commitment']` | yes |
| educational character exploratory axes | `['instructional_agency']` | `['instructional_agency']` | yes |
| educational character rejected axes | `['relational_communion', 'next_step_actionability', 'learner_contingency']` | `['relational_communion', 'next_step_actionability', 'learner_contingency']` | yes |
| semantic diagnosis AUC item-only | `0.775` | `0.775` | yes |
| semantic diagnosis AUC all dimensions | `0.744` | `0.744` | yes |
| prospective factorial response rows | `2560` | `2560` | yes |
| parent factorial target effects | `[0.773, 0.895, 0.595]` | `[0.773, 0.895, 0.595]` | yes |
| parent factorial selective factors | `[True, True, True]` | `[True, True, True]` | yes |
| parent learner-request gates | `[False, False]` | `[False, False]` | yes |
| order-replication response rows | `640` | `640` | yes |
| order-replication exact block balance | `True` | `True` | yes |
| replication factorial target effects | `[0.809, 0.922, 0.55]` | `[0.809, 0.922, 0.55]` | yes |
| joint order-robust factors | `[True, True, True]` | `[True, True, True]` | yes |
| order-robust learner-request gates | `[False, False]` | `[False, False]` | yes |
| factorial detector validation response units | `480` | `480` | yes |
| factorial detector validation annotations | `144` | `144` | yes |
| factorial detector validation batches | `48` | `48` | yes |
| factorial detector validation decisions | `[True, True, False]` | `[True, True, False]` | yes |
| factorial detector balanced accuracies | `[1.0, 0.996, 0.818]` | `[1.0, 0.996, 0.818]` | yes |
| factorial detector kappa values | `[1.0, 0.992, 0.631]` | `[1.0, 0.992, 0.631]` | yes |
| learner-outcome trial remains planning only | `planning_only_not_preregistered_not_started` | `planning_only_not_preregistered_not_started` | yes |
| learner-outcome conservative power plan passes | `True` | `True` | yes |
| learner-outcome planned sample and cells | `[3300, 12, 275]` | `[3300, 12, 275]` | yes |
| anonymous ACL submission audit | `True` | `True` | yes |
| ACL PDF page count | `9` | `9` | yes |
| ACL PDF embedded fonts and identity boundary | `[True, True, True]` | `[True, True, True]` | yes |
