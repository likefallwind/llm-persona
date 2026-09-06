# Educational-personality manuscript v3

This is the new manuscript source, not a completed submission. The previous
English/Chinese paper remains in its archived location. These sections replace
the six-question adaptation/routing narrative with the three educational-
personality questions agreed with the user.

Current written material: introduction, related work, construct definition,
prospective methods, measurement-development results, and limitations.
The 160-answer measurement pilot is complete. All 1,280 formal training responses passed generation audit;
all 3,840 training codes are now valid, and primary/style forecasts were locked
at 2026-09-05 11:00:25 UTC before any confirmation responses.
The first coding pass was interrupted after 3,238 saved records. Recovery
retains that run, reuses all 3,231 structurally valid codes, and uses the
original remaining repair allowance; see
[research/58](../../research/58_training_interruption_and_detached_recovery.md)
for the interruption audit and persistent execution details.
The original two repair passes left one GLM completion missing. A separately
recorded [single-code budget amendment](../../research/59_training_single_code_budget_amendment.md)
increased only that request's ceiling to 32,768 tokens, with at most two attempts.
It succeeded on the first attempt, using 3,511 completion tokens. Both budget
groups were audited under their actual contracts before combining all codes.
This is a disclosed protocol deviation; it is not described as compliance with
the original uniform budget. Original failed runs and terminal states survive.
The successor controllers continue under the original confirmation and
content policies. All 4,040 confirmation answers finished on their first
attempts at 2026-09-05 12:00:08 UTC and passed generation, deployment, forecast
timing, and judge-input lineage checks. The 12,120-request three-coder pass is
incomplete. A local Gateway outage interrupted coding after generation had
already finished. Following explicit user confirmation, the same coding child
was resumed at 2026-09-06 01:03:07 UTC; the original repair allowance and failure
records are preserved. See [Gateway recovery](../../research/63_gateway_outage_and_recovery.md).
Complete confirmation event labels and empirical results remain unavailable. See [generation completion](../../research/61_confirmation_generation_complete.md).
All 235 locked fitted models and 281,600 saved probabilities have also passed
[numerical reconstruction](../../research/60_training_complete_and_confirmation_started.md)
without refitting or reading confirmation outputs. This verifies serialization
and target-cell alignment, not predictive accuracy or independent implementation.
The corresponding Chinese introduction and methods are in `manuscript_zh.md`.
The completed pilot measurement figure is in `figures/measurement_pilot.pdf`.
The source-checked design schematic in `figures/study_design.pdf` connects
the three research questions to the frozen sampling and prediction sequence.
It contains planned counts only, with no empirical outcome or completion claim;
rebuild it with `scripts/plot_personality_design_v3.py`.
Confirmation results, an empirical abstract/conclusion, final results figures,
Chinese confirmation results and rendered submission checks remain required. Do not substitute
pilot numbers for prospective results or represent this directory as ready to
submit.

Scientific protocol: research/50_prospective_educational_personality_protocol_v3.md.
Literature comparison: research/51_related_work_boundary_and_paper_spine_v3.md.
Frozen design, prediction lock, raw completion audits, and item-level tables must
support every final empirical claim. These prospective-method sections will be
updated to disclose actual completion counts and any protocol deviations.
The working [claim–evidence ledger](evidence_ledger.md) separates currently
supported inventory/measurement statements from the ten confirmation questions
whose empirical answers remain unwritten. It records source tables, denominators
and interpretation limits for the final English/Chinese claim review.
The [resource-accounting snapshot](../../research/62_persisted_resource_accounting.md)
deduplicates reused records and includes known failed-attempt usage. Refresh it
after all experimental stages finish; its current token counts are partial
reported usage, with explicit missingness, not provider billing totals.

The protocol's mathematics and content-error sensitivity is now implemented in
[research/56](../../research/56_content_error_sensitivity_completion.md), with
rules fixed at 07:38:06 UTC before confirmation generation. A separate successor
waits for the original confirmation controller, then reviews 1,280 canonical
responses and 12 agent-authored controls with two reviewers. Its results remain
required; agreement and response-dependent screening do not establish causal
control of model ability.

Reading drafts are available in `build/working_draft_en.pdf` and
`build/working_draft_zh.pdf`. These are explicitly incomplete working
drafts, not venue-formatted submissions. Selected updated introduction,
related-work, measurement-figure, limitation, and reference pages have been
visually inspected; source/PDF hashes and the exact inspection scope are in
`build/build_provenance.json` and `build/render_review.json`.

The English draft includes the completed measurement-development results and
an archive scope appendix. The Chinese draft covers introduction, related work,
methods, archive scope, measurement development, and limitations with the shared
bibliography. Prospective empirical sections remain required. Build both with local TeX:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/build_personality_draft_v3.py
```

The [archive role and provenance audit](../../research/54_archive_role_and_tutor_provenance_audit.md)
traces 39 task roles to current adapter code and verifies the 122 tutor prediction
files against the frozen census. Current-role classification is not proof of
identical historical generation prompts.

The [full-grid rehearsal and inference-boundary record](../../research/55_full_grid_rehearsal_and_inference_boundary.md)
documents the synthetic integration test, the pre-confirmation treatment of
degenerate equivalence intervals, and closer educational precedents added to
the introduction. The synthetic test is never empirical personality evidence.

Five confirmation figure builders are ready in
`scripts/plot_personality_confirmation_v3.py`: locked prediction losses, the six
primary comparisons, default/repetition profiles, paired prompt effects, and
student-state rates. Synthetic layouts were visually inspected in `/tmp` only;
the review is recorded in
`artifacts/educational_personality_v2/figure_readiness/layout_review.json`.
No empirical confirmation figure has been generated. The renderer requires
complete confirmation measurement, the locked analysis, robustness calculations,
and the separate inference-edge audit, and verifies their recorded input hashes.
It also requires the [bounded neutral-wording check](../../research/57_design_precision_and_neutral_coverage.md).
The nominal t intervals can under-cover sparse outcomes even with nonzero
variance. Observed neutral shifts remain reportable, but the current sixteen
sources cannot support the population-equivalence tolerance under the
conservative bounded-source check.

After the confirmation controller completes, run the additional descriptive
analysis using the diagnostics path in `confirmation/measurement_selection.json`
(see research/53), then the interpretation audit and renderer:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/audit_personality_inference_edges_v3.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/audit_personality_neutral_bounds_v3.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/plot_personality_confirmation_v3.py
```

These commands are not part of the frozen confirmation controller. The local
successor `scripts/finish_personality_reporting_v3.py` now waits for that
controller's lock and successful final state, then runs the descriptive analysis,
both interpretation audits, and the renderer in this order. It records the
executed script hashes and durable logs in
`prospective_formal/confirmation_reporting/run/`, with a separate completion
summary. It adds no API calls or statistical rules. The independent content
review successor must also finish before scientific synthesis is complete.
Generated figures still
require inspection against the numerical results before inclusion in either
manuscript; rendering does not establish scientific or submission readiness.

The main methods now follow the three research questions in 956 English words,
with complete methods and protocol history retained in
`sections/detailed_methods.tex` (Appendix B). The Chinese reading draft uses
the same main-text structure and retains its complete method record in an
explicitly named appendix. This is an editorial reorganization; experimental
policies, inputs, estimators and empirical claims were not changed. The design
figure appears once per language. Both PDFs rebuilt with resolved references;
seven changed-page samples were visually inspected, with the exact scope and
PDF hashes recorded in `build/render_review.json`. The final empirical sections
and venue layout are still required.

An additional anonymous two-column draft is now available at
[build/acl/anonymous_acl_draft.pdf](build/acl/anonymous_acl_draft.pdf). It uses the
[official ACL styles](https://github.com/acl-org/acl-style-files) pinned to
commit `d5adc823ff0f80f98c80405ca0ab66c68e684409`; the downloaded files are
unmodified, with source hashes in `third_party/acl_style_files/provenance.json`.
The wrapper is generated from `main.tex` and uses the same chapter files and
bibliography, so it does not create a second editable English manuscript.
The two existing diagrams and archive table span both columns. Build it offline
with the existing local TeX installation:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/build_personality_acl_draft_v3.py
```

The builder verifies template hashes, A4 paper, embedded fonts and stable
cross-references/line numbers. A clean auxiliary-file build stabilized after
four LaTeX passes; all eleven current pages were visually inspected, recorded
in `build/acl/render_review.json`. The current page count includes references
and appendices and does not include the still-missing empirical sections.
This is a layout draft, not a submitted paper or a claim that the eventual
paper satisfies a selected venue's page limit. The current official
[formatting guidance](https://acl-org.github.io/ACLPUB/formatting.html) is a
starting point; the selected venue's call remains authoritative.
