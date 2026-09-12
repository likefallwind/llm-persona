# Educational personality: an integrated first-paper draft

2026-09-11. All experimental components are integrated as one investigation.
The `v3`/`v4` paths are manuscript and artifact checkpoints, not separate papers.
The agreed direction and boundaries are recorded in
[the preparation plan](../../research/92_integrated_first_paper_preparation.md).

## Read and review

- [English manuscript PDF (anonymous ACL layout)](build/acl/anonymous_acl_draft.pdf)
- [English manuscript source](main.tex)
- [Claim and related-work ledger](evidence_ledger.md)
- [Quantitative evidence inventory](behavior_evidence_inventory.json)
- [Current build and review record](final_review.json)

Only the English manuscript and this PDF layout are maintained. The Chinese
manuscript and additional reading PDFs have been retired from this checkpoint;
Chinese translations for discussion are provided in conversation, not as a
second manuscript. Earlier checkpoints remain historical evidence records.

The paper now asks which teaching tendencies distinguish models, which persist
under input changes, and how explicit instructions reshape them. Broader findings
on assistance directness, response complexity, expressed confidence, affiliation,
and boundary behavior are included with their respective measurement and evidence
limits. Section 4 groups the findings by recurring helping differences, more limited
patterns, and shared or unresolved responses. Sections 5 and 6 test persistence
and deliberate control, respectively. Section 6 focuses on action convergence, changes in model ordering, and
instruction-dependent prediction;
the historical semantic results retain their secondary status and detailed
appendix support. The prospective action results supply the strongest linked new-source,
expression-transfer and matched-instruction evidence.

The introduction and related work state the contribution through prediction
and control of subsequent teaching behavior. Sections 3 and 5 prioritize the
experimental comparisons and their findings; generation settings and full
estimates remain in the appendices, including the contemporary wording control.
The manuscript is now formatted for a NAACL 2027 long-paper submission through
ARR October 2026: the conclusion ends on page 8; Limitations, ethical
considerations and an anonymous AI-assistance disclosure follow before references.
The abstract has 189 words. The complete PDF has 35 pages including appendices.
[Submission requirements and remaining author actions](submission/requirements_and_status.md)
record the verified rules, metadata draft and Responsible NLP checklist.

The subsequent review clarifies why the broad behavioral screen is followed by
three prospective action endpoints, explains the additional corroboration behind
the directness decision, and states the acknowledgement transfer result as a
loss of incremental predictive value. Coding-recovery details remain in the
appendix. Dataset attribution and close related-work comparisons were checked
against primary publications; the evidence ledger records their roles and limits.

The discussion develops three implications: predictable teaching tendencies
support informed expectations; instruction control does not determine the entire
teaching response; and behavioral evaluation should inform Harness design and
validation for the model being used. The first two interpret the behavioral
findings; the third proposes a use for AI education developers. Learning outcomes,
Harness benefits, and optimal system configurations are not empirical
contributions of this paper.

The post-conclusion Limitations section concentrates on three points: coverage of settings
and models, automated behavioral measurement, and further teaching
tendencies that remain to be tested. Evidence levels and technical disclosures
remain in the methods, results, and empirical appendices.

## Evidence and scope

The controlled action sequence contains 10,440 tutor generations from five
models; the paired archive contains 3,584 replies from seven historical
models. Other pilot and routing counts are reported separately, not
silently included in those totals. The million-record inventory is an archive
coverage count, not a million independent personality measurements.

No new human annotation was added. Automatic coding is not semantic ground truth;
the supplementary routing analysis uses an existing observed-teacher reference.
Two archive coder labels remain absent. The original 10,752-code completeness
gate did not pass; all affected majority labels are identified from the two
agreeing votes without inventing a third. Original failures and post-hoc
full-source coder bounds remain disclosed.

Existing experiments support the agreed bounded manuscript scope. This preparation
does not certify scientific quality or constitute external submission. Checked
manuscript-format requirements pass; author declarations and account actions
remain necessary before upload.

## Rebuild and audit

From the repository root:

```bash
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 .venv/bin/python scripts/build_personality_draft_v4.py
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 .venv/bin/python scripts/audit_personality_draft_v4.py
```

The builder renders ten supplementary evidence rows directly from five saved
result files, then builds the single English ACL-layout PDF.
The audit rereads the evidence sources, checks English tables, verifies frozen
experimental files and figures, and enumerates missing-vote majority bounds.
No command above makes model-provider calls or reruns experiments.

The official ACL style remains unmodified. Layout length, glyphs, references,
and inspected pages are reported separately in the current review record;
the build now rejects an overlong main paper or abstract and checks the
post-conclusion order, known PDF identity patterns and Type 3 fonts.
The evidence audit also verifies all eight cumulative screen decisions and all
twenty fixed expression stimuli against their saved sources.

## Whole-paper terminology review (2026-09-12)

The English main text and appendices use model, prediction, test problem,
standard tutoring prompt, and experimental condition consistently. Necessary
statistical terms and distinctions between historical analyses and predictions
fixed before response collection remain explicit. The existing table label
Canonical is defined as the standard tutoring prompt. Prompt quotations,
response excerpts, mathematical definitions and numeric table rows are unchanged.

Updated figure labels can be reproduced from the repository root with:

```bash
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 .venv/bin/python scripts/plot_personality_design_v4.py
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 .venv/bin/python scripts/render_personality_prompt_figure_v4.py
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 .venv/bin/python scripts/render_personality_transfer_figure_v4.py
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 .venv/bin/python scripts/render_personality_discovery_figures_v4.py
```

These commands render the saved design and results; they make no model-provider
requests. Rebuild the PDF afterward using the commands above.
