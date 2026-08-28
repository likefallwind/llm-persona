# Existing-response general-personality bridge: results

Snapshot: 2026-08-28. Status: **complete archive-only screening analysis**.
The protocol, corpus eligibility map, candidate manifestations, surface controls,
and decision rule were frozen before these aggregate profiles were inspected. No
generator or judge calls were made.

## Bottom line

The existing archive does **not yet support a domain-general personality bridge**.
It supports a more discriminating result:

> Six deployed model configurations have recurring formatting and verbosity
> fingerprints, plus domain-specific educational policy profiles. Two
> interpersonal manifestations show partial cross-domain continuity, but neither
> passes the joint stability-and-transport screen required to motivate a new
> experiment as confirmation of an archive signal.

This result strengthens rather than replaces the existing conclusion. The
supported object remains a prompt-contingent pedagogical policy response surface,
not a fixed general personality expressed inside tutoring.

## Corpus triage

The frozen inventory contains 27 benchmarks with all six core models, 47,321
paired items, and 283,926 paired responses. Sixteen benchmarks contain responses
with enough free-form behavioral expression for this audit: 20,578 paired items
and 123,468 model responses. The other 11 benchmarks remain in the coverage
audit but are excluded from personality interpretation because their outputs are
mostly one-character answers, rating labels, step indices, or similarly
constrained structures.

The included non-tutoring roles cover general reasoning, instruction following,
self-monitoring, safety assistance, and educational assessment. Default tutoring
uses LongTutor teaching and the generic standard/hard MathTutorBench arms.
Explicit-pedagogy and Socratic arms are kept separate. Every feature is centered
within exact item across the six models and standardized within benchmark; raw
response text is never exported.

## Frozen screening outcomes

| Candidate manifestation | Non-tutoring ICC | Median task rho | Non-tutoring to default tutoring rho | Max abs surface-control rho | Decision |
|---|---:|---:|---:|---:|---|
| Communal expression | 0.269 | 0.371 | 0.829 | 0.714 | Transport is strong, but non-tutoring recurrence fails |
| Dialogic engagement | 0.364 | 0.543 | 0.657 | 0.771 | Recurrence screen passes by median rank, but transport misses 0.70 |
| Directive expression | 0.189 | 0.143 | -0.086 | 0.429 | Fails recurrence and transport |
| Epistemic-caution language | 0.252 | 0.143 | -0.200 | 0.600 | Fails recurrence and transport |
| Boundary/refusal expression | -0.014 | 0.086 | -0.257 | 0.657 | Fails and remains policy/competence entangled |

No candidate passes all frozen gates. The high communal-expression transport is
not a single-domain artifact: its leave-one-non-tutoring-domain-out correlation
with default tutoring ranges from 0.657 to 0.943. The failure is instead that the
models reorder sharply among the ten individual non-tutoring tasks (minimum
pairwise rho -0.886). This is exactly the distinction between an attractive
pooled profile and a stable disposition.

Dialogic engagement is the complementary near miss. Its median non-tutoring task
correlation is 0.543, but its default-tutoring transport is only 0.657; its
leave-one-domain-out values range from 0.600 to 0.714. The archive therefore
localizes one plausible future construct cluster—interpersonal affiliation and
engagement—without validating it.

## The strongest general signal is still style

The organizational-style control is the only profile with strong non-tutoring
recurrence on both metrics (ICC 0.601; median rho 0.771). Verbosity transports
from non-tutoring to default tutoring at rho 0.771 and from default to prompted
tutoring at rho 0.886 (exact p=0.035). These results agree with the earlier
negative-control analysis: broad model identity is real, but much of the most
portable identity is formatting and length rather than a content-valid
personality trait.

## Bridge to the existing educational axes

The exploratory six-model associations point in a coherent interpersonal
direction but do not survive multiple-testing correction:

- non-tutoring communal expression correlates 0.771 with the formal relational-
  communion score (exact p=0.104);
- dialogic engagement correlates -0.486 with instructional agency and -0.543
  with validated assistance directness, both in the expected direction; and
- directive expression has the wrong sign for both agency (-0.429) and
  assistance directness (-0.486).

The language-only epistemic proxy does not recover the objective epistemic
signature: epistemic-caution language correlates +0.200 with expressed
confidence, opposite the expected direction. This independently reinforces the
previous decision to prefer objective confidence, revision, and abstention
behavior over generic caution wording.

## Relationship to prompt contingency

The archive screen does not re-estimate the already established common prompt
main effect: exact-item centering within each prompt arm removes that effect by
construction. It can inspect relative model reordering. The most general-looking
candidate, communal expression, correlates 0.829 between non-tutoring and default
tutoring but only 0.257 between non-tutoring and prompted tutoring. Dialogic
engagement correlates -0.029 between default and prompted tutoring. Thus a pooled
default resemblance can be substantially reorganized by an education-policy
prompt, consistent with the existing model-specific elasticity result.

The earlier semantic and factorial experiments remain authoritative for shared
prompt displacement. This audit adds a new boundary: residual model identity
across prompts is not equivalent to stable domain-general personality content.

## Experimental decision

Under the user's staged rule—mine the existing archive first and run new calls
only if the archive supplies a credible signal—the full general-personality
experiment does **not** start. Calling it confirmatory would overstate what the
archive shows.

If the broader personality question is later retained as a separate paper-level
objective, the archive supplies only one defensible starting hypothesis:

> affiliation/dialogic engagement may form a cross-domain interpersonal
> manifestation, but it must be tested with purpose-built, scenario-based and
> open-ended tasks under irrelevant-context perturbations before it can be linked
> to Big Five agreeableness/extraversion or HEXACO constructs.

That future pilot should be small and gated. It should not administer a broad
inventory panel, and it should not reopen the failed educational axes. A formal
general-personality study would additionally require a larger independently
sampled model panel; hundreds of thousands of responses reduce item uncertainty
but do not turn six model means into a population-level latent-trait sample.

## Reproducibility

```bash
EDUBENCH_ROOT=/path/to/edubenchmark \
  .venv/bin/python scripts/analyze_existing_general_personality_bridge.py
```

Protocol: `research/37_existing_response_general_personality_bridge_protocol.md`.
Machine decision: `artifacts/general_personality_bridge_v1/decision.json`.
Full aggregate report: `artifacts/general_personality_bridge_v1/report.md`.

## Later targeted follow-up

The stricter archive-confirmation verdict above remains unchanged. A subsequent
construct-coverage audit used the localized affiliation near miss to select a
new prospective falsification pilot rather than claim archive confirmation. That
pilot finds stable cross-domain open affiliation behavior but rejects
self-report and forced-choice convergence; see
`research/42_affiliation_stability_pilot_results.md`.

## Claim boundary

The analysis concerns observable language and interaction policies in six fixed
deployed configurations. It does not establish human personality, mental states,
Big Five/HEXACO construct equivalence, model-family traits, or temporal stability
across provider revisions.
