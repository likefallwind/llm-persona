# Deterministic behavioral pilot

Paired responses analyzed: **57,516** across **4** benchmark arms and **6** models.

All features are transparent lexical/action proxies. They are useful for falsification and pipeline validation but are not yet validated pedagogical dispositions.

## Held-out task-family model attribution

Chance accuracy is 0.167. Each fold withholds an entire task family.

| feature_set         |   accuracy |   balanced_accuracy |
|:--------------------|-----------:|--------------------:|
| surface_plus_policy |      0.372 |               0.372 |
| surface             |      0.347 |               0.347 |
| policy              |      0.281 |               0.281 |
| length_only         |      0.240 |               0.240 |

## Most cross-task-stable proxies

Features are centered within each item across models before task aggregation, removing item-level content difficulty.

| feature               |   icc3_1 |   mean_pairwise_spearman |   task_count |
|:----------------------|---------:|-------------------------:|-------------:|
| hedge_rate            |    0.563 |                    0.494 |            4 |
| emoji_rate            |    0.448 |                    0.723 |            4 |
| answer_reveal_rate    |    0.431 |                    0.510 |            4 |
| numbered_step_rate    |    0.368 |                    0.714 |            4 |
| markdown_heading_rate |    0.354 |                    0.135 |            4 |
| table_present         |    0.340 |                    0.581 |            4 |
| explanation_rate      |    0.331 |                    0.205 |            4 |
| first_plural_rate     |    0.316 |                    0.344 |            4 |

## Paired prompt intervention (selected endpoints)

Delta = explicit LearnLM-style pedagogy prompt minus generic caring-teacher prompt on the same conversation and model.

No paired prompt intervention is defined for this role section.

## Interpretation boundary

Above-chance attribution demonstrates a reproducible signature, not personality. The next stage must replace proxy-only interpretation with multi-judge behavioral coding, outcome prediction, judge-swap robustness, and preregistered confirmatory analyses.
