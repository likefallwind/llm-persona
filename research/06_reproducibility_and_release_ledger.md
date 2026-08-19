# Reproducibility, privacy, and release ledger

Snapshot: 2026-08-19.

## Provenance boundaries

| Layer | Source / artifact | Stored here | Release status |
|---|---|---|---|
| Raw generations and scores | `$EDUBENCH_ROOT/reports/eval/**` | No copied source text; analyses retain IDs, hashes, features, labels, and scores | Governed by upstream benchmark/model terms |
| Human MathDial actions | Existing MathDial teacher turns and move labels | Classifier metrics plus hashes and inferred labels for generated responses | Cite and follow MathDial license |
| LongTutor histories | Existing prepared LongTutor checkout | IDs and derived scores only | Do not redistribute raw text until an explicit upstream license is established |
| External semantic coding | 360 sampled contexts × six candidate responses, sent to MiniMax official and the configured GLM/DeepSeek gateway | Blind mappings, response hashes, ratings, raw rating JSON, usage, and errors; prompts/source text are not copied | Release derived annotations and hashes; withhold source text |
| Local semantic smoke | Small Ollama runs | Derived smoke report | Not primary evidence; paused pending stronger server |

No new human annotation was collected.  Existing expert preferences and human
dialogue-act labels are reused as independent calibration/criterion data.

## External-transfer record

The user explicitly authorized the frozen external semantic experiment after
disclosure of destinations, sample size, and regex privacy audit.  Routes are:

- MiniMax-M3 via the official MiniMax endpoint, concurrency at most four;
- GLM-5.2 and DeepSeek-V4-Pro via the configured API gateway, concurrency at most
  eight.

The frozen manifest contains 360 contexts and 2,160 candidate responses; three
judges imply 1,080 calls.  Candidate identities are blinded and independently
shuffled per judge/context.  The preflight audit found no email, URL, IPv4,
China-ID-like, or China-mobile-like patterns.  Broad international-phone-like
regex hits were confined to 38 LongTutor contexts and appear to be numeric
histories; regex absence/presence is not a complete privacy determination.

This authorization does not automatically cover a new simulated-student study.
That would transmit a new payload class and requires a new disclosure.

## Completion gates

The semantic run is complete only if all hold:

1. `sample_manifest.json` contains 360 unique batches;
2. status reports 1,080 latest successful annotation IDs, zero current errors,
   and zero invalid JSONL rows;
3. `run_state/main.exit` and `run_state/longtutor.exit` both equal zero;
4. `run_state/finished` exists;
5. the confirmatory analyzer runs without `--allow-incomplete`;
6. every response consensus has exactly three distinct judges;
7. saved derived tables contain no source context or candidate response text.

`scripts/audit_release_privacy.py` enforces item 7 over every Git-eligible
artifact and rejects explicit source-text fields or absolute user-home paths.
This structural gate complements, but does not replace, upstream license review
or a substantive privacy assessment.

## Statistical reproducibility

- Sampling and candidate order are deterministic under seed `20260819`.
- The semantic panel is append-only and resumable by annotation ID.
- The external runner holds a nonblocking `flock` for its full lifetime and
  clears stale finalizer markers before a resumed pass; one JSONL must never have
  two active writers.
- Exact-context controls are used wherever the same prompt is answered by
  multiple models.
- Prompt effects resample underlying contexts rather than six correlated model
  responses as independent observations.
- Model-level conclusions remain descriptive with six systems.
- Intermediate single-judge results are kept outside the release path and ignored
  by version control.
- `research/05_semantic_analysis_plan.md` records which analyses were frozen
  before any second- or third-judge result was available.

## Release package

A defensible public package can contain code, environment pins, sample manifests,
hashes, derived feature/score tables, figures, and an exclusion/error ledger.  It
must not contain API credentials, raw LongTutor histories, or copied model
responses.  Before submission, verify each upstream dataset's current license and
write a dataset/model card naming the intended unit of analysis and nonclaims.

## Pull-request cadence

Research changes are published as reviewable draft PRs at evidence boundaries,
not as snapshots of a live experiment:

1. **Method baseline:** frozen protocols, analysis code, completed non-semantic
   evidence, paper scaffold, and privacy/reproducibility controls.
2. **Result freeze:** the three-judge semantic panel and sensitivity analyses,
   only after every completion gate above passes.
3. **Submission package:** consolidated manuscript, dataset/model cards, current
   license audit, and a clean-room reproduction report.

Additional draft PRs are opened whenever a later experiment changes a registered
claim or method.  Mutable annotation JSONL, run logs, status files, credentials,
and incomplete result directories are excluded.  Every PR body reports the exact
validation commands, active limitations, and whether its evidence is
confirmatory, exploratory, or still incomplete.
