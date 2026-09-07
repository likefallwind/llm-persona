# Reproducing the educational-personality study

Commands below run from the repository root in the existing `.venv`. They read
saved observations and do not issue model requests. Raw provider histories remain
local; this document does not claim that every required input has been publicly
released. A public replication bundle would need the selected measurement inputs
and their provenance as well as these scripts.

## Evidence entry points

The base directory is `artifacts/educational_personality_v2/prospective_formal`.

| Component | Entry point |
|---|---|
| Question banks | `data/educational_personality_candidate_templates_v3.json` and `data/educational_personality_confirmation_templates_v3.json` |
| Role prompts and source design | `scripts/prepare_personality_formal_v3.py`, `design_freeze.json`, stage `scenarios.jsonl`/`generation_manifest.jsonl`/`freeze.json` |
| Event rubric | `data/educational_personality_measurement_v2_2.json` |
| Primary and style forecasts | `prediction_lock.json`, `locked_predictions/` |
| Coder and generator sensitivity locks | `judge_sensitivity_lock.json`, `generator_deletion_lock.json` |
| Selected training measurement | `training/measurement_selection.json` |
| Selected confirmation measurement | `confirmation/measurement_selection.json`; selected complete diagnostics under `confirmation/transport_recovery/combined_diagnostics/` |
| Primary statistics | `confirmation_analysis/summary.json` and its source tables |
| Robustness | `confirmation_robustness/summary.json`, eight panels, five deletions, 200 source resamples |
| Content review | `content_sensitivity/measurement_selection.json`, selected diagnostics, `content_sensitivity/analysis/` |
| Budget sensitivity | `confirmation_budget_sensitivity/summary.json` and assignment/range tables |
| Descriptive and neutral checks | `confirmation_reporting/summary.json`, `confirmation_descriptive/`, `confirmation_inference_edges/`, `confirmation_neutral_bounds/` |
| Raw history and deviations | Original runs, research/58–69, amendments and local runtime receipts |

## Recompute primary comparisons into a separate output directory

```bash
.venv/bin/python scripts/analyze_personality_confirmation_v3.py \
  --diagnostics artifacts/educational_personality_v2/prospective_formal/confirmation/transport_recovery/combined_diagnostics \
  --output /tmp/personality-primary-reproduction
```

The script checks complete coverage and frozen inputs, scores saved predictions,
uses 32 equally weighted source groups, and writes all six primary comparisons.
It does not fit on confirmation labels. The canonical source forecast table
contains 1,280 answers; prompt, opportunity and sentinel observations have their
own denominators. The separate complete-main checkpoint already matches all
nine shared official tables, recorded with hashes in
`complete_main_checkpoint/checkpoint_equivalence_audit.json`.

```bash
.venv/bin/python scripts/analyze_personality_robustness_v3.py \
  --diagnostics artifacts/educational_personality_v2/prospective_formal/confirmation/transport_recovery/combined_diagnostics \
  --output /tmp/personality-robustness-reproduction \
  --training-resamples 200
```

This evaluates the previously locked panel forecasts and runs training-source
resampling with the disclosed fixed regularization ratio. It reuses the same
confirmation observations and is not an independent replication.

## Verify and build the paper

```bash
.venv/bin/python scripts/audit_personality_manuscript_tables_v3.py
.venv/bin/python scripts/render_personality_publication_figures_v3.py
.venv/bin/python scripts/build_personality_draft_v3.py
.venv/bin/python scripts/build_personality_acl_draft_v3.py
```

The table audit compares the English and Chinese default, absolute-loss,
primary-test, matched-prompt, secondary-event and content-subset tables directly with their
CSV sources. Figure variants preserve the frozen statistical computations and
write separate output hashes. The original reporting implementation and its
receipts remain unchanged. The builders use a local TeX installation, verify
citations and record source/PDF hashes. Their success does not replace a full
scientific or visual review.

## Interpretation and history

The exact claim-to-evidence map is [evidence_ledger.md](evidence_ledger.md).
Six primary tests retain their original majority labels and Holm correction;
content-screened subsets do not replace them. Source bootstraps, coder panels,
generator deletions and training-resample quantiles answer different questions.
No human personality, learning gain, education-only mechanism, universal model
pair separation or invariant neutral-wording profile follows from these checks.

The original quotation-copying measurement failure, training interruption,
Gateway outage, one training budget exception, six confirmation budget
exceptions and one further transport retry allowance remain part of the
execution record. Hashes and local timestamps support inspection; they are not
independent third-party preregistration. Provider usage accounting separately
reports known token totals, unknown usage and reused copies rather than
inventing a dollar cost or counting failed calls as free.

## Persisted resource accounting after the final repair

The 2026-09-07 02:18 UTC snapshot contains 26,856 unique saved request records,
28,773 saved HTTP attempts and 70,210,015 provider-reported total tokens. It
excludes 32,660 reused row copies and reports 3,589 attempts with unknown token
usage. These totals include material review, measurement development, failures,
and repairs; they are not the 5,320 formal tutor-generation requests alone.
The accounting script retains its generic snapshot warning about active or
unsaved work. All requested study controllers are now complete, but unsaved
interrupted attempts and provider billing remain outside the measured totals.
No missing usage is treated as zero cost.
