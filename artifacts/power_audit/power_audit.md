# Semantic design power and inferential-resolution audit

## Paired prompt effects

| design                           |   n_independent_context_pairs | multiplicity_rule       |   alpha |   minimum_dz_for_80pct_power |
|:---------------------------------|------------------------------:|:------------------------|--------:|-----------------------------:|
| hard prompt pair per model       |                            40 | single planned contrast |   0.050 |                        0.454 |
| hard prompt pair per model       |                            40 | six-model Bonferroni    |   0.008 |                        0.576 |
| standard prompt pair per model   |                            80 | single planned contrast |   0.050 |                        0.317 |
| standard prompt pair per model   |                            80 | six-model Bonferroni    |   0.008 |                        0.398 |
| pooled standard + hard per model |                           120 | single planned contrast |   0.050 |                        0.258 |
| pooled standard + hard per model |                           120 | six-model Bonferroni    |   0.008 |                        0.322 |

The unit is a distinct conversation context, not a response and not a judge rating. The calculation is a paired-t approximation for a standardized within-context effect (`dz`); ordinal mixed models may differ slightly.

## Model-level correlations

|   target_absolute_correlation |   models_needed_for_80pct_power |
|------------------------------:|--------------------------------:|
|                           0.3 |                            85.0 |
|                           0.5 |                            30.0 |
|                           0.7 |                            14.0 |
|                           0.8 |                            10.0 |

The current six-model core panel is not powered for aggregate trait--outcome correlations. Such correlations must remain exploratory. The defensible confirmatory route is item-level held-out-model prediction with context clustering, plus a larger model panel for population-level claims.

## Exact-test resolution

| claim_unit                                      |   independent_units |   smallest_one_sided_exact_sign_p |   smallest_two_sided_exact_sign_p |
|:------------------------------------------------|--------------------:|----------------------------------:|----------------------------------:|
| direction shared across six models              |                   6 |                            0.0156 |                            0.0312 |
| direction shared across four named family pairs |                   4 |                            0.0625 |                            0.1250 |

Thousands of item responses estimate conditional behavior precisely, but they do not increase the number of independently sampled model systems. Claims about the population of models must use the model count, whereas prompt effects within a fixed model may use paired contexts.

## Design decision

The frozen 80-context standard arm is adequate for moderate within-model semantic prompt effects; the 40-context hard arm is only sensitive to moderate-to-large effects after six-model multiplicity correction. For the paper, pool standard and hard only under a preregistered shared-effect model, otherwise report the hard arm as a lower-powered robustness test. Do not use the six model means to claim a general latent-trait correlation.
