# Normative-boundary candidate axis: existing-data result

Snapshot: 2026-08-26. Status: **exploratory falsification on frozen EduGuard
data**.

## Question

Do education-safety behaviors support one additional model-character axis from
permissive/complying to boundary-enforcing/refusing?

## Analysis

`scripts/analyze_normative_boundary_axes.py` reads the selected core-six
EduGuard summaries and SATA scored rows. It exports only category/scenario
aggregates and never exports prompts, responses, extracted text, reasoning,
gold option sets, or item text.

Four observed tendencies were tested across contexts:

| Tendency | Contexts | ICC(3,1) | Median pairwise model-rank rho | Result |
|---|---:|---:|---:|---|
| Adversarial attack success | 5 risk categories | 0.806 | 0.943 | Stable within task |
| Educational-refusal style | 5 risk categories | 0.590 | 0.864 | Stable, but one category-pair rho is only 0.086 |
| SATA incorrect inclusion | 10 scenario-language cells | 0.761 | 0.714 | Stable within task |
| SATA omission | 10 scenario-language cells | 0.421 | 0.696 | Mixed stability |

## Falsification result

The two strongest permissiveness candidates do not converge across tasks. Mean
adversarial attack success and SATA incorrect inclusion have six-model Spearman
rho=-0.486. MiniMax-M2.7 combines the lowest attack success (0.026) with the
highest SATA incorrect inclusion (0.271), whereas DeepSeek-V4-Pro combines the
highest attack success (0.545) with substantially lower SATA inclusion (0.183).

Therefore **a single normative-permissiveness personality axis is not
supported**. The defensible result is that models have stable but task-specific
safety-policy signatures. Adversarial robustness, harmful-option recognition,
omission, and refusal quality should remain separate safety abilities or policy
facets.

## Boundary

Both measures are safety outcomes as well as behavioral tendencies. The
adversarial scorer uses MiniMax-M3 for every candidate, including MiniMax-M3,
so the result is not judge-family-independent. Six fixed systems do not support
model-population or latent-personality inference.
