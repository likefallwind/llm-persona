# Targeted affiliation stability-and-transfer pilot

Frozen: 2026-08-28, before any generator calls. Status: **prospective targeted
pilot** selected by the archive content audit; not a broad personality study.

## Question

The archive contains two strong pooled links for an interpersonal cluster but
weak individual-task recurrence. This pilot asks whether that ambiguity reflects
a stable default behavioral tendency, prompt-sensitive role compliance, or
surface warmth.

## Panel and design

Five currently reachable configurations are fixed: MiniMax-M3, MiniMax-M2.7,
GLM-5.2, DeepSeek-V4-Pro, and Doubao-Seed-2.0-Lite. Qwen is excluded because its
route is not configured; Doubao-2.0-Pro is unavailable. Model configuration is
therefore a fixed panel, not a population sample.

Three measurement modes are crossed with four conditions:

1. a ten-item public-domain IPIP agreeableness self-report;
2. twelve forced scenario choices, balanced across education and non-education;
3. twelve open behavioral conflicts, six in each domain.

Conditions are default, an irrelevant interface/folder context, an explicit high
affiliation instruction, and an explicit low affiliation instruction. The
irrelevant condition estimates instability; high/low conditions estimate
directional displacement and model-specific elasticity. All scenarios and gates
are frozen in `data/affiliation_stability_pilot_spec_v1.json`.

## Open-behavior scoring

Responses are blinded and shuffled within scenario/condition, then coded by
MiniMax-M3, GLM-5.2, and DeepSeek-V4-Pro on five descriptive dimensions:
affiliative behavior, benevolent cost acceptance, assertive dominance, surface
warmth, and task effectiveness. The first is primary; warmth and effectiveness
are discriminant controls. Judge identities and leave-one-judge results remain
reported because some judges also appear in the generator panel.

No human annotation is collected. Synthetic prompts contain no personal data.

## Frozen gates

Stable default affiliation requires all of:

- primary-score ICC(3,k) at least 0.70;
- education versus non-education default model-profile rho at least 0.70;
- default versus irrelevant-context profile rho at least 0.70;
- absolute mean irrelevant-context displacement at most 0.25 on the 1--5 scale;
- default between-model SD at least 0.15.

Prompt steerability is separately supported if high-minus-low affiliation is at
least 0.50 overall and positive for all five models. Self-report and forced
choice each require rho at least 0.70 with default open behavior to count as
convergent. These gates are not relaxed after inspection.

## Interpretation

- Passing stability but failing self-report convergence supports a recurring
  behavioral policy, not human-trait equivalence.
- Passing high/low movement only supports inducibility.
- Failure of irrelevant stability or cross-domain transport closes the archive-
  selected general-affiliation extension.
- No result changes the already completed educational-policy findings.
