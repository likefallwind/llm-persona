# Educational personality: integrated research manuscript

2026-09-08. This version integrates the first-stage prospective study,
expression-transfer extension, and identified-majority archive analysis.
The v3 manuscript and frozen experimental records remain preserved.

- [English reading PDF](build/working_draft_en.pdf)
- [Chinese reading PDF](build/working_draft_zh.pdf)
- [Anonymous ACL-layout PDF](build/acl/anonymous_acl_draft.pdf)
- [Editable Chinese manuscript](manuscript_zh.md)
- [Scientific quality assessment](../../research/89_final_scientific_assessment_v4.md)
- [Archive results and interpretation](../../research/87_archive_identified_majority_results_v4.md)
- [Full-source missing-coder sensitivity](../../research/88_full_source_coder_bounds_v4.md)

Default revelation and elicitation gains transfer across problems and tested
expressions; the acknowledgement state profile loses its increment under new
expressions. Archived replies show substantial model gains under general tutoring
and much smaller gains under explicit probing. The supported object is an action
profile with specified contextual boundaries, not a human personality taxonomy,
emotion understanding, or learning benefit.

The study uses 10,440 newly generated tutor replies from five deployments and
3,584 archived replies from seven historical configurations. The million-record
archive supplies an audited exploration scope, not a million independent semantic
personality measurements. No human annotation is added, and upstream human
quality/preference labels are not the behavioral targets.

Two archive coder labels remain absent after provider refusals. The original
10,752-code coverage gate **did not pass**. Agreement of the other two votes
identifies all affected majorities without imputing a third vote. Both the
254-source complete-coder analysis and exhaustive full-256-source coder bounds
are reported as post-hoc amendments. See research/85–88 and the archive appendix.

From the repository root, rebuild and verify locally:

```bash
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 .venv/bin/python scripts/build_personality_draft_v4.py
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 .venv/bin/python scripts/audit_personality_draft_v4.py
```

These commands make no API calls. Source/PDF hashes, bilingual table checks,
majority enumeration, and scenario-range checks are recorded separately from
the scientific assessment. The pinned official ACL style is unchanged. The
layout is not a declaration of compliance with an unspecified venue's rules.

Companion evidence is in `artifacts/educational_personality_v4/`: use
`cue_transfer/analysis/` for expression results and
`archive_validation/analysis_selection.json` for the explicit archive-analysis
selection. Raw requests, answers, provider error bodies, and credentials are
excluded from the tracked paper package; local frozen input hashes retain the
connection to the authorized source archive.
