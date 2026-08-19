# Dataset and release card

Snapshot: 2026-08-19.  This card covers the evidence used by the pedagogical
disposition study, not every benchmark present in EduBenchmark.

## Dataset composition

The analysis is built from model generations already produced by the shared
EduBenchmark harness.  The core paired panel contains six models answering the
same successful benchmark items.  The frozen inventory contains 47,321 common
benchmark-item IDs and 283,926 corresponding core-panel responses across all
roles.  Primary tutoring analyses use a prespecified subset; negative controls,
judge calibration, and external criteria are kept separate in
`data/benchmark_roles.json`.

Saved research artifacts contain response hashes, benchmark/item IDs, model
labels, deterministic transparent features, inferred action labels, scores, and
aggregate statistics.  They do not copy source prompts or raw model responses.

## Source and license audit

| Source | Use in this study | Authoritative license evidence checked 2026-08-19 | Release decision |
|---|---|---|---|
| EduBenchmark evaluation outputs | Existing model generations and scores | Locally generated research outputs; upstream dataset terms still apply to embedded text | Release analysis code, hashes, and derived tables; do not release copied response text |
| [MathDial](https://github.com/eth-nlped/mathdial) | Human teacher dialogue-act labels and problems underlying the MathTutorBench bridge | Official repository states CC BY-SA 4.0 | Cite MathDial and preserve attribution/share-alike obligations; public derived labels contain no dialogue text |
| [MathTutorBench](https://github.com/eth-lre/mathtutorbench) | Paired generic/pedagogy prompt arms and bridge items | The official paper states code and dataset are CC BY 4.0; the audited repository root exposes no standalone license file | Cite paper/repository; release no copied bridge text until repository-level terms are clarified |
| [LongTutor](https://aclanthology.org/2026.acl-long.1371/) | Long-history teaching, evidence, and human-gold diagnosis criteria | Paper datasheet states data CC BY 4.0 and evaluation code MIT; current official repository points back to paper for terms | Cite paper; withhold raw histories and prompts, and release only IDs, hashes, derived measurements, and aggregate results |
| Frozen semantic panel | Eight-dimensional blind ratings of 2,160 sampled candidate responses | New derived annotations created for this study; underlying source text remains governed by the rows above | Release blind mappings, hashes, ratings, usage/error metadata, and aggregate tables after completeness/privacy gates; no text |

The conservative release decision is intentional: an open repository does not
by itself establish permission to redistribute every embedded prompt, provider
output, or upstream derivative.  Before archival publication, the exact commit
of each source repository and a final license check must be recorded.

## Personal and sensitive information

MathDial uses crowdworker teachers paired with simulated student behavior.
LongTutor is derived from real-world learning logs and includes longitudinal
student interaction histories.  This repository does not retain source text in
its public analysis tables.  External semantic coding was preceded by a regex
audit for common identifiers, but such screening cannot prove that text is free
of all personal or sensitive information.  Therefore the semantic release is
text-free even after the external calls finish.

## Sampling and exclusions

- A benchmark/model cell is considered available only when the inventory finds
  successful item-level artifacts, not merely a prediction or log file.
- Core comparisons require the same item ID for all six models.
- Role membership is frozen in `data/benchmark_roles.json`; judge-only tasks are
  never treated as tutor behavior.
- The external semantic sample is deterministic under seed `20260819` and is
  complete only at 360 unique batches and 1,080 latest successful annotations.
- Ambiguous or unmatched MathDial action targets are excluded before generated
  model outcomes are examined.
- The LongTutor objective analysis uses 1,000 histories shared by all six models;
  diagnosis is compared to human gold, whereas semantic evidence equivalence is
  explicitly secondary because it is LLM-judged.

## Intended and prohibited interpretations

The data support comparisons of observable model-conditioned pedagogical policy
under the recorded harness.  They are not a representative sample of all LLMs,
not evidence that models have human personality, not a clinical or psychological
instrument, and not proof of student learning gains.  The data must not be used
to reconstruct or deanonymize learners, infer sensitive traits, rank individual
teachers or students, or claim provider-wide behavior beyond the evaluated model
aliases and dates.

## Reproduction and access

`scripts/reproduce_completed.sh` regenerates all completed non-semantic analyses
from a local EduBenchmark checkout.  `scripts/finalize_semantic_analysis.sh`
enforces full semantic coverage before generating the confirmatory tables.  A
public archive should include hashes and acquisition instructions so authorized
researchers can reconstruct results without redistributing the protected text.
`scripts/audit_release_privacy.py` is the mechanical release-structure gate;
upstream license verification and substantive privacy review remain separate
human responsibilities.
