# Extended nine-model panel

Responses: **26,586**; models: **9**; paired prompt arms: **4**.

## Does behavior resemble model family?

| profile         |   observed_family_pair_distance |   null_mean_distance |   lower_tail_p |   permutations |
|:----------------|--------------------------------:|---------------------:|---------------:|---------------:|
| generic         |                          0.9910 |               1.2869 |         0.0512 |          50000 |
| pedagogy        |                          1.0170 |               0.9818 |         0.6219 |          50000 |
| treatment_delta |                          0.7108 |               0.8050 |         0.1034 |          50000 |

| profile         | within_named_family   |   mean |   median |   count |
|:----------------|:----------------------|-------:|---------:|--------:|
| generic         | False                 | 1.3229 |   1.2531 |      32 |
| generic         | True                  | 0.9910 |   0.9686 |       4 |
| pedagogy        | False                 | 0.9766 |   1.0715 |      32 |
| pedagogy        | True                  | 1.0170 |   1.1245 |       4 |
| treatment_delta | False                 | 0.8167 |   0.8821 |      32 |
| treatment_delta | True                  | 0.7108 |   0.8062 |       4 |

The four named pairs are approximate family comparisons, not clean scaling experiments: model generation, training, and serving differ within every pair.

## Does the explicit pedagogy prompt make models converge?

|   generic_dispersion |   pedagogy_dispersion |   dispersion_ratio_pedagogy_over_generic |   bootstrap_ci_low |   bootstrap_ci_high |   probability_ratio_below_one |
|---------------------:|----------------------:|-----------------------------------------:|-------------------:|--------------------:|------------------------------:|
|               1.2860 |                0.9811 |                                   0.7629 |             0.7383 |              0.7939 |                        1.0000 |

Dispersion is the mean Euclidean distance between model profiles after within-item centering and feature standardization. A ratio below one means convergence.

## Directional invariants and heterogeneity

| family               | feature            |   models_positive |   models_negative |   models_zero |   model_count |   min_model_mean_delta |   max_model_mean_delta |
|:---------------------|:-------------------|------------------:|------------------:|--------------:|--------------:|-----------------------:|-----------------------:|
| mathdial_bridge      | question_rate      |                 9 |                 0 |             0 |             9 |                 1.9992 |                 3.3830 |
| mathdial_bridge_hard | question_rate      |                 9 |                 0 |             0 |             9 |                 1.8779 |                 3.4735 |
| mathdial_bridge      | answer_reveal_rate |                 1 |                 8 |             0 |             9 |                -0.1652 |                 0.0295 |
| mathdial_bridge_hard | answer_reveal_rate |                 3 |                 6 |             0 |             9 |                -0.2161 |                 0.0585 |
| mathdial_bridge      | praise_rate        |                 6 |                 3 |             0 |             9 |                -0.9507 |                 1.2891 |
| mathdial_bridge_hard | praise_rate        |                 6 |                 3 |             0 |             9 |                -1.1134 |                 1.0303 |
| mathdial_bridge      | log_tokens         |                 0 |                 9 |             0 |             9 |                -0.4780 |                -0.1916 |
| mathdial_bridge_hard | log_tokens         |                 0 |                 9 |             0 |             9 |                -0.4506 |                -0.2011 |

A universal sign across all nine models is stronger evidence of a prompt-level policy effect. Mixed signs reveal model-specific adaptation rather than simple compliance strength.

## Interpretation

The extended panel can separate three phenomena: persistent baseline signature, common response to an explicit pedagogical constraint, and model-specific treatment response. None alone licenses a human-personality claim.
