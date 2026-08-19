# LongTutor diagnosis and evidence cross-task validity

Matched records: **6,000** model × history observations, **1,000** histories, **6** models. Diagnosis is an exact four-class human-gold outcome. Evidence accuracy aggregates reference-conditioned historical-memory questions; non-exact answers were judged for semantic equivalence by the same fixed MiniMax-M3 extractor across candidate models. Teaching scores come from the separate teaching task.

## Model summaries

| model               |   items |   diagnosis_accuracy |   evidence_accuracy |   teaching_quality |   history_utilization |   strategy_alignment |   coherence |   appropriateness |
|:--------------------|--------:|---------------------:|--------------------:|-------------------:|----------------------:|---------------------:|------------:|------------------:|
| deepseek-v4-pro     |    1000 |                0.437 |               0.792 |              3.973 |                 3.523 |                3.696 |       4.563 |             4.110 |
| doubao-seed-2.0-pro |    1000 |                0.377 |               0.801 |              4.235 |                 3.775 |                4.088 |       4.711 |             4.367 |
| glm-5.2             |    1000 |                0.350 |               0.807 |              3.932 |                 3.211 |                3.775 |       4.575 |             4.165 |
| minimax-m2.7        |    1000 |                0.278 |               0.712 |              3.038 |                 2.151 |                2.727 |       4.403 |             2.872 |
| minimax-m3          |    1000 |                0.415 |               0.787 |              3.914 |                 3.371 |                3.670 |       4.617 |             4.000 |
| qwen3.5-4b          |    1000 |                0.292 |               0.793 |              3.833 |                 3.576 |                3.682 |       4.201 |             3.873 |

Model means are descriptive only because there are six systems.

## Within-model associations

| objective_outcome   | teaching_measure    |   mean |    min |   max |
|:--------------------|:--------------------|-------:|-------:|------:|
| diagnosis_correct   | appropriateness     |  0.134 |  0.086 | 0.195 |
| diagnosis_correct   | coherence           |  0.081 |  0.038 | 0.125 |
| diagnosis_correct   | history_utilization |  0.128 |  0.072 | 0.189 |
| diagnosis_correct   | strategy_alignment  |  0.208 |  0.161 | 0.295 |
| diagnosis_correct   | teaching_quality    |  0.173 |  0.117 | 0.249 |
| evidence_accuracy   | appropriateness     | -0.007 | -0.061 | 0.043 |
| evidence_accuracy   | coherence           | -0.032 | -0.070 | 0.019 |
| evidence_accuracy   | history_utilization | -0.001 | -0.034 | 0.036 |
| evidence_accuracy   | strategy_alignment  | -0.007 | -0.060 | 0.043 |
| evidence_accuracy   | teaching_quality    | -0.010 | -0.068 | 0.047 |

## Held-out-model prediction with exact-history controls

| outcome           | predictors          |     auc |   accuracy |    rmse |
|:------------------|:--------------------|--------:|-----------:|--------:|
| diagnosis_correct | item_only           |   0.822 |      0.749 | nan     |
| diagnosis_correct | teaching_dimensions |   0.816 |      0.746 | nan     |
| diagnosis_correct | teaching_mean       |   0.817 |      0.746 | nan     |
| evidence_accuracy | item_only           | nan     |    nan     |   0.187 |
| evidence_accuracy | teaching_dimensions | nan     |    nan     |   0.187 |
| evidence_accuracy | teaching_mean       | nan     |    nan     |   0.187 |

Each fold trains on five models and tests the sixth. The item-only baseline absorbs history difficulty; teaching measures test incremental cross-task association.

## Interpretation boundary

Human-gold diagnosis is a stronger external criterion than a prompted simulated student. Evidence accuracy is a secondary, reference-grounded but LLM-judged criterion. Both measure prerequisite tutor competence rather than student learning gain. A positive association does not show that any teaching style causes learning.
