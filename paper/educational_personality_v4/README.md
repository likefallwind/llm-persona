# Integrated expression-transfer manuscript checkpoint

2026-09-08. This draft incorporates the completed cue-transfer extension while
preserving the v3 manuscript and its first-stage evidence. It is not a submission
readiness certificate. Archive-dialogue coding was authorized and launched on 2026-09-08; completed
behavioral validation remains pending.

- [English reading PDF](build/working_draft_en.pdf)
- [Chinese reading PDF](build/working_draft_zh.pdf)
- [Anonymous ACL-layout PDF](build/acl/anonymous_acl_draft.pdf)
- [Chinese editable source](manuscript_zh.md)
- [Scientific assessment and remaining gaps](../../research/76_integrated_draft_quality_v4.md)
- [Completed expression-transfer results](../../research/74_cue_transfer_results_v4.md)

The central distinction is between transfer to new problems under the same
wording and transfer to new student expressions. Answer-revelation and
reasoning-elicitation defaults retain gains in both tests. The tested conditional
acknowledgement profile helps under original wording but loses its incremental
gain under the new expressions. This does not imply absence of cue response or
demonstrate emotional misattribution.

Rebuild locally with `.venv/bin/python scripts/render_personality_transfer_figure_v4.py`
and `.venv/bin/python scripts/build_personality_draft_v4.py` from the repository root.
The renderers preserve the pinned official ACL style and reuse the v3 build logic
with v4 output paths. The figure receipt maps all 12 points to completed analysis
tables. Build receipts record source and PDF hashes; they do not certify the science.

At the reviewed checkpoint the reading PDFs have 31 English and 25 Chinese pages.
The ACL-layout draft has 26 pages including references and appendices; the
conclusion is on page 9. Layout is inspectable, but the main text still needs
compression against the eventual venue requirements. No venue-specific compliance
claim is made. The source-specific old checks in v3 are not silently reused as a
quality verdict on this changed draft.

The post-result diagnosis in research/78 is also integrated. Its eight targeted
tests and all twelve comparisons against the unchanged transfer tables pass.
It separates absolute loss from relative gain without fitting a new predictor.

The source-held-out calibration check (research/79–80) is included with all
methods, fitting parameters, and explicit target-label adaptation boundaries.
Eleven targeted tests pass; no new API calls or human annotations are added.

The input-only scope audit (research/81) verifies the original sample and explains
short-context, eligibility and upstream-provenance limits without reading new codes.
