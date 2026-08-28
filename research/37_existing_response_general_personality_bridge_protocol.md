# Existing-response general-personality bridge audit

Date frozen: 2026-08-28. Status: **outcome-blind protocol for a secondary
analysis of existing responses**. No new generator or judge calls are authorized
by this protocol.

## Research question

The educational-character results support a prompt-contingent pedagogical policy
surface, but do not establish a domain-general model personality. This audit asks
a narrower screening question:

> Do transparent behavioral manifestations recur across non-tutoring roles and
> default tutoring responses strongly enough to justify a new, purpose-built
> general-personality experiment?

The audit is a bridge to the existing research, not a replacement for it. It
retains the same decomposition into a model-conditioned default, prompt-induced
displacement, and model-specific elasticity. The new issue is whether any
default component transports across roles outside tutoring.

## Corpus and eligibility freeze

The authoritative input is `artifacts/inventory/corpus_inventory.json`. It
contains 27 benchmarks with a complete six-model panel, 47,321 paired items, and
283,926 paired responses. The fixed eligibility map is
`data/general_personality_bridge_manifest_v1.json`.

Only responses that permit meaningful free-form behavioral expression enter the
content analysis. One-character answers, short verdict labels, step indices, and
machine-constrained score outputs remain in the coverage audit but are excluded
from personality interpretation. Included response text is read locally and is
never written to this repository; released outputs contain aggregate profiles,
counts, paths already present in the inventory, and response hashes only where
already governed by an existing artifact.

## Candidate manifestations

These are screening proxies, not human Big Five or HEXACO scores:

1. **communal expression**: inclusive first-person language, direct address,
   praise, and encouragement;
2. **dialogic engagement**: direct address, inclusive language, and question
   asking;
3. **directive expression**: imperatives, explanation, and answer commitment,
   opposed by questions and hedging;
4. **epistemic caution language**: hedges and explicit uncertainty or limitation
   language, opposed by answer commitment;
5. **boundary/refusal expression**: explicit inability, refusal, or apology
   language. This is reported separately because safety policy and competence
   can dominate it.

Two surface controls are mandatory:

- **organizational style**: headings, bullets, and numbered steps;
- **verbosity**: response token count.

No proxy is labeled agreeableness, extraversion, conscientiousness,
honesty-humility, or neuroticism. Openness and emotional stability are not
identified by this corpus and are explicitly unmeasured.

## Exact-item control and profile construction

For every included benchmark and feature, subtract the six-model mean within the
same item, then standardize within benchmark. Aggregate these controlled values
first by model and benchmark, then by model and domain. This removes shared item
content and prevents large benchmarks from dominating domain averages.

The non-tutoring pool comprises general reasoning, instruction following,
self-monitoring, safety assistance, and educational assessment. The default
tutoring pool contains LongTutor teaching plus the generic MathTutorBench
standard and hard arms. Explicit-pedagogy and Socratic arms are kept separate as
prompted tutoring.

## Analyses

1. Report coverage and all exclusion reasons.
2. Estimate ICC(3,1) and median pairwise six-model Spearman correlation across
   benchmarks for every candidate and surface control.
3. Compare equally weighted non-tutoring-domain profiles with default tutoring
   profiles using exact six-model permutation tests.
4. Correlate the non-tutoring manifestations with their nearest existing
   educational axes: communion, agency/directness, and expressed epistemic
   confidence. These associations are hypothesis-generating because six model
   means are underpowered.
5. Report whether each candidate is strongly aligned (absolute rho at least
   0.80) with organizational style or verbosity. Such alignment is a confound,
   not supporting evidence.
6. Compare generic/default and prompted tutoring profiles descriptively. This
   reuses the existing prompt-contingency claim and cannot establish general
   personality steering.

## Screening decision

An existing-response bridge candidate is called **promising for a new
experiment**, never validated, only if all of the following hold:

1. it is a content candidate rather than a surface control;
2. either ICC(3,1) or median pairwise rank correlation across at least three
   non-tutoring benchmarks is at least 0.50;
3. its non-tutoring versus default-tutoring rank correlation has absolute value
   at least 0.70;
4. its non-tutoring profile is not correlated at absolute rho at least 0.80 with
   either surface control; and
5. the observed direction is interpretable without relabeling competence,
   correctness, refusal success, or formatting as personality.

If no candidate passes, the existing archive does not justify a broad
general-personality claim. A new experiment may still be scientifically useful,
but it will not be presented as a confirmatory follow-up to an archive signal.

If at least one candidate passes, the next experiment must use scenario-based and
open-ended measures, irrelevant-context perturbations, trait-relevant
interventions, and both educational and non-educational downstream tasks. Direct
questionnaire scores remain a secondary bridge rather than the primary endpoint.

## Claim boundary

This audit can identify recurring language and interaction policies of six fixed
deployed configurations. It cannot establish human personality, internal mental
states, a universal latent structure, model-family traits, or temporal stability
across provider revisions. Large response count reduces item sampling error but
does not repair a six-model population or construct-validity limitation.
