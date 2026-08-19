# Discriminant-validity negative control

Teaching responses: **31,638**. Negative-control responses: **57,516**. Models: **6**.

All features were centered within item across models and standardized within benchmark before this analysis. This removes shared item content and benchmark scale.

## Cross-domain model attribution

| train_domain     | test_domain      | feature_set         |   n_train |   n_test |   accuracy |   balanced_accuracy |
|:-----------------|:-----------------|:--------------------|----------:|---------:|-----------:|--------------------:|
| teaching         | negative_control | length_only         |     11772 |    12864 |      0.251 |               0.251 |
| teaching         | negative_control | surface             |     11772 |    12864 |      0.255 |               0.255 |
| teaching         | negative_control | policy              |     11772 |    12864 |      0.224 |               0.224 |
| teaching         | negative_control | surface_plus_policy |     11772 |    12864 |      0.253 |               0.253 |
| negative_control | teaching         | length_only         |     12864 |    11772 |      0.193 |               0.193 |
| negative_control | teaching         | surface             |     12864 |    11772 |      0.205 |               0.205 |
| negative_control | teaching         | policy              |     12864 |    11772 |      0.196 |               0.196 |
| negative_control | teaching         | surface_plus_policy |     12864 |    11772 |      0.219 |               0.219 |

Chance accuracy is 0.167. Above-chance transfer means a feature set contains model-specific information that is not unique to tutoring.

## Cross-domain feature ranks

| feature                |   cross_domain_spearman |   exact_two_sided_p |
|:-----------------------|------------------------:|--------------------:|
| numbered_step_rate     |                   0.943 |               0.018 |
| emoji_rate             |                   0.829 |               0.060 |
| mean_sentence_tokens   |                   0.771 |               0.104 |
| log_tokens             |                   0.771 |               0.104 |
| first_plural_rate      |                   0.771 |               0.104 |
| hedge_rate             |                   0.714 |               0.137 |
| second_person_rate     |                   0.657 |               0.176 |
| table_present          |                   0.638 |               0.196 |
| imperative_rate        |                   0.600 |               0.243 |
| log_chars              |                   0.543 |               0.298 |
| history_reference_rate |                   0.543 |               0.298 |
| bullet_rate            |                   0.371 |               0.498 |

## Policy-profile geometry

| feature_set   |   model_count |   distance_matrix_correlation |   exact_two_sided_p |   permutations |
|:--------------|--------------:|------------------------------:|--------------------:|---------------:|
| policy        |             6 |                         0.296 |               0.307 |            720 |

## Consequence

Any proxy that transfers strongly to test-taking or generic instruction following must be labeled a domain-general model fingerprint, not a pedagogical disposition. Confirmatory semantic dimensions must demonstrate incremental validity after controlling these negative-domain profiles.
