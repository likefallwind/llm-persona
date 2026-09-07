# Educational-personality manuscript v3

> This is the completed first-stage manuscript checkpoint. The overall research-quality goal remains active; [research/70](../../research/70_quality_goal_reopened.md) supersedes any interpretation of this checkpoint as top-conference readiness.

The new manuscript answers three questions: which deployed models' tutoring
actions recur, whether default and student-state profiles predict new source
problems, and how neutral wording and explicit teaching instructions change
those profiles. The earlier paper and failed measurements remain archived.

On 2026-09-07, complete confirmation measurement comprises 4,040 answers,
12,120 valid coder outputs and 32,320 majority response–event rows. The six
primary comparisons, eight coder panels, five generator deletions, 200 training
resamples, neutral inference checks and six-code budget sensitivity are complete.
The original failures and all three bounded budget/transport amendments remain
disclosed. `confirmation/measurement_selection.json` selects the authoritative
full diagnostics under `artifacts/educational_personality_v2/prospective_formal/`.

English and Chinese sources now contain the empirical abstract, all three RQ
results, discussion, conclusion, measurement development and detailed appendices.
The [claim–evidence ledger](evidence_ledger.md) maps the current findings to exact
tables and uncertainty. Three default-prediction gains pass the primary rule;
only acknowledgement has a resolved student-state increment. The paper retains
repeat variability, model-deletion attenuation, neutral-wording precision limits
and the distinction between demanded and permissible actions under instructions.

All 2,584 content reviews are valid after seven structural repairs, with the
[serialization correction](../../research/68_content_payload_validation_correction.md)
and original failures preserved. The five subset analyses are integrated.
Either-reviewer error screening retains 1,065 responses on all 32 sources and
preserves the predictive pattern. Natural-error positive agreement is only
18.5%, despite 24/24 matching controls; the paper explicitly limits correctness
and causal interpretations.

The research analyses, bilingual synthesis and final rendered manuscripts are
complete. The [final review record](final_review.json) binds the actual source,
evidence and PDF hashes, 15 bilingual result-paragraph pairs, six figure-caption
pairs, and six empirical tables. The [scientific assessment](../../research/69_completed_content_and_final_scientific_assessment.md)
explains why the current evidence answers the scoped question, what is new
relative to prior work, and where reviewers may reasonably disagree. This is an
agent editorial assessment; conference acceptance and external peer review are
not claimed. No paper has been submitted.

## Reading and layout artifacts

- [English reading draft](build/working_draft_en.pdf)
- [Chinese reading draft](build/working_draft_zh.pdf)
- [Anonymous ACL layout](build/acl/anonymous_acl_draft.pdf)
- [English source](main.tex), shared [sections](sections/), [Chinese source](manuscript_zh.md)

The final English reading PDF has 26 pages, the Chinese PDF 20, and the
anonymous ACL layout 21 including references and appendices. In the ACL PDF,
the conclusion is on page 8, references begin on page 9, and appendices begin
on page 10. All pages received layout inspection; the final content tables were
also inspected at page resolution. Fonts are embedded, citations and line
numbers resolve, and no overfull boxes or missing glyphs remain. Legacy
`working_draft` filenames are retained for link compatibility; the PDFs contain
the completed empirical manuscript. Exact venue and author submission fields
remain outside these local deliverables.

```bash
.venv/bin/python scripts/build_personality_draft_v3.py
.venv/bin/python scripts/build_personality_acl_draft_v3.py
.venv/bin/python scripts/audit_personality_manuscript_tables_v3.py
.venv/bin/python scripts/finalize_personality_manuscript_v3.py
```

These commands run from the repository root and use the local TeX installation.
The ACL template is official, pinned to commit
`d5adc823ff0f80f98c80405ca0ab66c68e684409`, and unmodified. The ACL wrapper uses
exactly the same English chapter sources as the reading draft. Source/PDF hashes
are recorded by both builders; the final review records scientific status separately.
Rebuilding verifies artifacts, but a changed manuscript requires renewed editorial
and visual review before refreshing the final completion record.

## Figures and reproducibility

The frozen reporting controller completed the descriptive, inference-boundary
and five confirmation-figure outputs. Its original figures, script hashes and
`confirmation_reporting/summary.json` remain intact. The publication variants from `scripts/render_personality_publication_figures_v3.py`
use readable labels at two-column width, shorten repeated headings, and keep
one decimal in the repeated-profile heatmap so that 99.6% is not displayed as
100%. They write separate artifacts and provenance; the original analysis and
figures remain intact. An earlier one-decimal-only variant is also retained.

The [study design](figures/study_design.pdf) and [excluded pilot](figures/measurement_pilot.pdf)
remain explicitly distinguished from confirmation results. Figures and tables
must be assessed with source counts (32 canonical, 16 prompt, 8 opportunity,
4 sentinel sources), not their larger repeated-response totals.

The prospective methods are in [research/50](../../research/50_prospective_educational_personality_protocol_v3.md),
the literature boundary in [research/51](../../research/51_related_work_boundary_and_paper_spine_v3.md),
and all final evidence requirements in the [ledger](evidence_ledger.md).
`scripts/finalize_semantic_analysis.sh` validates the earlier study and is not
the completion gate for this manuscript.
