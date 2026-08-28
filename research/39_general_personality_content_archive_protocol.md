# General-personality content audit of existing EduBenchmark responses

Date frozen: 2026-08-28. Status: **secondary construct-coverage audit**. The
behavioral-proxy screen in research 37--38 was already complete when this map was
frozen, so this analysis is not presented as outcome-blind preregistration. No
new generator or judge calls are part of this stage.

## Why this audit is separate

The first archive bridge measured five transparent behavioral manifestations.
It did not directly test the full content of Big Five, HEXACO honesty-humility,
the Dark Triad, or Schwartz values. A null result for those proxies therefore
cannot be used to claim that the broader constructs are absent.

This audit asks two prior questions for every construct:

1. Does EduBenchmark contain a behavior that could manifest the construct?
2. Does it contain the choice, conflict, or perturbation required to distinguish
   the construct from capability, formatting, provider policy, or task role?

The authoritative mapping is
`data/general_personality_construct_map_v1.json`.

## Construct coverage

The map covers all five Big Five dimensions, HEXACO honesty-humility, all three
Dark Triad constructs, all ten Schwartz values, cooperation, risk preference,
and social-desirability/impression-management validity. It also separately
records the availability of standard questionnaires, scenario choice, open
behavior, education transfer, non-education transfer, and ten stability
perturbations.

Each construct receives one of two archive statuses:

- `partial_behavioral_candidate`: at least one relevant behavior exists, but
  the archive cannot fully identify the construct;
- `not_identifiable`: the necessary opportunity, incentive, or contrast is
  absent.

These are measurement-coverage labels, not positive or negative trait scores.

## Cross-indicator falsification checks

For partially observable clusters, existing aggregate profiles are compared
across independent task or scoring sources using six-model Spearman rank
correlations and exact permutation p-values:

- communal expression versus judged educational communion;
- organizational style versus IFEval accuracy, beneficial revision, and
  self-monitoring accuracy;
- epistemic-caution language versus overconfidence, selective abstention, and
  beneficial revision;
- boundary/refusal language versus adversarial boundary enforcement,
  educational refusal, and SATA incorrect inclusion.

The expected signs are specified in the analysis script. Benjamini--Hochberg
adjustments are reported within construct cluster. These model-level tests are
diagnostic and underpowered at n=6; they cannot validate a latent trait.

## Follow-up decision

No construct can be called archive-validated. A purpose-built pilot priority is
allowed only as a transparent design-selection rule when a localized candidate
has two expected-direction cross-role/source links at absolute rho at least
0.70, is below the previous 0.80 surface-reduction threshold, and its unresolved
failure is specifically a stability question that a controlled pilot can
falsify.

This weaker rule prioritizes a future pilot; it does not overturn the stricter
archive-confirmation gate in research 37. Any follow-up must remain small and
targeted. It cannot be described as confirmation of a general personality trait.

## Claim boundary

The audit concerns observable policies of six fixed deployed configurations.
Large item counts improve response sampling but not the six-model population,
construct equivalence, self-report validity, model-family inference, or temporal
stability across provider revisions.
