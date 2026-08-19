# Semantic-to-LongTutor criterion validity (exploratory)

Matched **240** response-level observations: **40** histories × **6** models. Semantic scores describe a teaching response. Diagnosis correctness is exact match to a human-gold class. Historical-evidence accuracy comes from separate model calls and reference answers, with non-exact equivalence scored by a fixed MiniMax-M3 judge.

This analysis was designed after the MiniMax-only interim view and is not part of the prospective multi-judge analysis freeze.

## Held-out-model prediction with exact-history controls

| outcome           | feature_set                                |     auc |   accuracy |    rmse |   gain_vs_item |
|:------------------|:-------------------------------------------|--------:|-----------:|--------:|---------------:|
| diagnosis_correct | all_semantic                               |   0.744 |      0.633 | nan     |         -0.030 |
| diagnosis_correct | diagnosis_personalization                  |   0.759 |      0.642 | nan     |         -0.016 |
| diagnosis_correct | item_only                                  |   0.775 |      0.692 | nan     |          0.000 |
| diagnosis_correct | semantic_without_diagnosis_personalization |   0.757 |      0.633 | nan     |         -0.017 |
| evidence_accuracy | all_semantic                               | nan     |    nan     |   0.201 |         -0.009 |
| evidence_accuracy | diagnosis_personalization                  | nan     |    nan     |   0.196 |         -0.004 |
| evidence_accuracy | item_only                                  | nan     |    nan     |   0.192 |          0.000 |
| evidence_accuracy | semantic_without_diagnosis_personalization | nan     |    nan     |   0.196 |         -0.005 |

For diagnosis, positive gain is AUC improvement over item-only. For evidence, positive gain is RMSE reduction. Every model fold is retained in the CSV.

## Exact-history-centered associations

| outcome           | dimension              |   matched_responses |   exact_item_centered_pearson |   permutation_p |   permutations |   bh_q_within_outcome |
|:------------------|:-----------------------|--------------------:|------------------------------:|----------------:|---------------:|----------------------:|
| diagnosis_correct | help_directness        |                 240 |                        -0.064 |           0.399 |           5000 |                 0.759 |
| diagnosis_correct | elicitation            |                 240 |                         0.049 |           0.474 |           5000 |                 0.759 |
| diagnosis_correct | autonomy_support       |                 240 |                         0.055 |           0.421 |           5000 |                 0.759 |
| diagnosis_correct | affective_warmth       |                 240 |                         0.168 |           0.015 |           5000 |                 0.117 |
| diagnosis_correct | diagnostic_specificity |                 240 |                         0.013 |           0.875 |           5000 |                 0.875 |
| diagnosis_correct | personalization        |                 240 |                        -0.010 |           0.841 |           5000 |                 0.875 |
| diagnosis_correct | cognitive_load         |                 240 |                        -0.129 |           0.057 |           5000 |                 0.228 |
| diagnosis_correct | epistemic_caution      |                 240 |                         0.038 |           0.675 |           5000 |                 0.875 |
| evidence_accuracy | help_directness        |                 240 |                        -0.054 |           0.447 |           5000 |                 0.595 |
| evidence_accuracy | elicitation            |                 240 |                         0.098 |           0.167 |           5000 |                 0.414 |
| evidence_accuracy | autonomy_support       |                 240 |                         0.108 |           0.127 |           5000 |                 0.414 |
| evidence_accuracy | affective_warmth       |                 240 |                         0.091 |           0.259 |           5000 |                 0.414 |
| evidence_accuracy | diagnostic_specificity |                 240 |                         0.089 |           0.213 |           5000 |                 0.414 |
| evidence_accuracy | personalization        |                 240 |                         0.139 |           0.060 |           5000 |                 0.414 |
| evidence_accuracy | cognitive_load         |                 240 |                        -0.038 |           0.542 |           5000 |                 0.620 |
| evidence_accuracy | epistemic_caution      |                 240 |                        -0.036 |           0.695 |           5000 |                 0.695 |

Permutation tests shuffle model-linked semantic scores within each history and use BH correction across the eight dimensions for each objective outcome.

## Interpretation boundary

Diagnosis is an external prerequisite-competence test, not student learning gain; evidence accuracy remains LLM-judged. Failure is informative: a reliable behavioral disposition may still be disconnected from accurate learner-state inference.
