# Reproducibility, privacy, and release ledger

Snapshot: 2026-08-28.

## Provenance boundaries

| Layer | Source / artifact | Stored here | Release status |
|---|---|---|---|
| Raw generations and scores | `$EDUBENCH_ROOT/reports/eval/**` | No copied source text; analyses retain IDs, hashes, features, labels, and scores | Governed by upstream benchmark/model terms |
| Human MathDial actions | Existing MathDial teacher turns and move labels | Classifier metrics plus hashes and inferred labels for generated responses | Cite and follow MathDial license |
| LongTutor histories | Existing prepared LongTutor checkout | IDs and derived scores only | Do not redistribute raw text until an explicit upstream license is established |
| External semantic coding | 360 sampled contexts × six candidate responses, sent to MiniMax official and the configured GLM/DeepSeek gateway | Blind mappings, response hashes, ratings, raw rating JSON, usage, and errors; prompts/source text are not copied | Release derived annotations and hashes; withhold source text |
| Theory-grounded character confirmation | Pair-preserving public/synthetic MathTutorBench split scored by GLM-5.2, DeepSeek-V4-Pro, Doubao-Seed-2.0-Lite, and MiniMax-M2.7 through one local Gateway | Frozen manifest, payload audit, blind mappings, hashes, ratings, and aggregate tables; no source text in derived outputs | Release manifests and aggregate/hash-only tables; keep raw judge JSON local and disclose the single-route limitation |
| Existing-response general-personality bridge | 283,926 paired archived responses; 123,468 free-form responses pass the frozen eligibility map | Aggregate benchmark/domain/model profiles, stability and transport tables, no prompts or response text | Release protocol, eligibility map, code, aggregate artifacts, and negative decision; no new external transfer occurred |
| General-personality content audit | Existing aggregate bridge, educational, epistemic, safety, and IFEval results for the fixed six-model panel | Construct map, aggregate indicator profiles and correlations; no prompts or response text | Release mapping, code, aggregate artifacts, and bounded pilot-priority decision; no new external transfer occurred |
| Targeted affiliation stability pilot | 56 frozen synthetic request units x five generators plus 48 blinded open-behavior batches x three judges | Frozen synthetic spec/manifest, hashes, anonymized ratings, and aggregate tables; raw provider and judge responses remain local | Release protocol, synthetic prompts, code, derived scores, and bounded decision; disclose model/judge overlap and five-model limit |
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

### Theory-grounded confirmation transfer boundary

The later theory-grounded panel uses the same six frozen candidate responses but
executes only the 30 pilot and 290 formal public/synthetic MathTutorBench slates.
The 40 sampled LongTutor histories remain in the deterministic inventory so the
split can be audited, but `--run-benchmarks` excludes them from every external
request. Candidate model identities, prompt-arm labels, gold answers, API keys,
and reasoning traces are absent from the judge payload. The final judge panel is
four model families on one configured Gateway route; this supports family
leaveout sensitivity, not provider-route replication.

Two compact-bridge attempts are transport debris and ignored wholesale. V1 hit
the MiniMax official Token Plan ceiling; v2 imposed a 4,096-token cap that
starved hidden reasoning and produced empty GLM outputs. V3 restores uncapped
judge output and is the sole eligible compact panel. The raw V3 annotation JSONL,
run log, and run-state markers remain ignored; released derived tables contain
only IDs, hashes, blind labels, scores, and aggregates.

The V3 formal run is complete: 1,160/1,160 unique eligible calls, 290 per
judge, zero failed or invalid rows, `run_state/exit=0`, and a durable
`run_state/finished` marker. A post-completion dry run refreshed
`payload_audit.json` with `run_split=formal`, 290 execution batches, 1,160 judge
calls, and the five permitted MathTutorBench benchmark names. The formal
analyzer ran with `--require-complete`, the pilot decision prerequisite, 2,000
context-clustered bootstrap iterations, and seed `20260826`.

Aggregate outputs are in `artifacts/confirmatory_character_panel_v1/formal/`;
the family leaveout and quality-boundary outputs are colocated, and the six-axis
synthesis is in `artifacts/educational_character_framework_v1/`. The executable
result interpretation is documented in
`research/36_confirmatory_character_results.md`. No raw annotation is needed to
state the released aggregate decision.

## Completion gates

The semantic run is complete only if all hold:

1. `sample_manifest.json` contains 360 unique batches;
2. the validated exclusion file removes exactly one failed prompt pair and status
   reports 1,074/1,074 eligible successes, zero eligible errors, and zero invalid
   JSONL rows;
3. `run_state/main.exit` and `run_state/longtutor.exit` both equal zero;
4. `run_state/finished` exists;
5. the confirmatory analyzer runs without `--allow-incomplete`;
6. all 2,148 retained responses have exactly three judges and yield 17,184
   response-dimension consensus rows;
7. saved derived tables contain no source context or candidate response text.

The theory-grounded formal extension adds its own gates: exactly 1,160 eligible
synthetic formal judge calls (290 slates by four judges), zero missing/failed
IDs, `run_state/exit=0`, `run_state/finished`, a pilot-decision prerequisite that
formal recovery cannot override, and four leave-one-family sensitivity passes
for any dimension called family-robust. All coverage and process gates are now
satisfied. No new dimension is called a formal cross-task signature, so the
family-robust designation does not upgrade any failed construct.

`scripts/audit_release_privacy.py` enforces item 7 over every Git-eligible
artifact and rejects explicit source-text fields or absolute user-home paths.
This structural gate complements, but does not replace, upstream license review
or a substantive privacy assessment.

As of this snapshot the **whole-repository release privacy gate fails** on 12
pre-existing Git-eligible raw-run files: response-bearing factorial/routing
JSONL, raw semantic-judge JSONL, smoke annotations, and one semantic run log
containing an absolute home path. These files predate the theory-grounded formal
extension and remain tracked; they must be removed from the release index or
redacted under a separately authorized release-cleanup change. The new
confirmatory judge audit, formal aggregate panel, six-axis synthesis, and
normative aggregate directories pass targeted privacy scans (2, 37, 5, and 7
Git-eligible files respectively). The repository must not be represented as
privacy-release-ready until the older tracked files are resolved.

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
- `build_reproducibility_manifest.py` hashes only tracked or unignored eligible
  files, so live annotations, logs, run state, bytecode caches, and credentials
  cannot make a clean checkout's manifest unsatisfiable.
- `research/05_semantic_analysis_plan.md` records which analyses were frozen
  before any second- or third-judge result was available.
- `scripts/finalize_semantic_analysis.sh` applies strict completeness gates to
  the semantic, parent-factorial, order-replication, paraphrase, action-routing,
  and two-stage panels before rebuilding every released analysis directory.
- Provider response JSONL and private request manifests are ignored inputs. The
  public package therefore supports verification of frozen designs, released
  derived tables, registered decisions, and hashes; exact table regeneration
  additionally requires governed access to those raw inputs.

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
