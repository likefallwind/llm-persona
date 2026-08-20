# Blind validation of factorial surface detectors

Snapshot: 2026-08-19. This is a post-result, downgrade-only validation of the
three deterministic endpoints used in the prospective factorial and its
request-order replication. It is not a preregistration and cannot strengthen a
claim beyond its original operational scope.

## Completion and blinding

- 480 response units were selected without using detector values, factor cells,
  model identity, or estimated effects: 320 from the parent and 160 from the
  replication.
- Three judges independently annotated 48 ten-response batches, yielding
  144/144 complete batch annotations and a majority label for every response.
- Candidate order was independently hash-shuffled for each judge and batch.
- The transmitted payload contained only synthetic math problems, correct
  answers, and synthetic model responses; it excluded benchmark text, learner
  histories, identifiers, model identity, factor cells, detector values, and
  effect estimates.

## Frozen gates and results

A detector validates only when majority-label coverage is at least 0.95,
balanced accuracy is at least 0.90, its 2,000-replicate bootstrap 95% lower bound
is at least 0.80, and Cohen's kappa is at least 0.70.

| Detector | Coverage | Balanced accuracy (95% CI) | Kappa | Decision |
|---|---:|---:|---:|---|
| First sentence-like segment is a question | 1.000 | 1.000 [1.000, 1.000] | 1.000 | validated |
| Correct answer is explicitly revealed | 1.000 | 0.996 [0.989, 1.000] | 0.992 | validated |
| Frozen encouragement lexicon is present | 1.000 | 0.818 [0.787, 0.847] | 0.631 | **failed** |

## Downgrade decision

The first two factorial outcomes support the bounded behavioral descriptions
“question-first” and “correct answer explicitly revealed.” The third outcome
does not validate a broader semantic judgment of learner-directed warmth or
support. Every corresponding result is therefore reported only as a change in
the frozen encouragement-lexicon marker. The warm-tone system clause remains the
name of the randomized intervention, but a marker effect is not evidence that
responses became warmer, more supportive, empathic, or pedagogically better.

This negative measurement result does not alter the randomized numerical effect
on the literal marker, the every-model sign check, the request-order
replication, or interactions whose outcome is question-first. It does narrow the
construct those numbers are allowed to represent.
