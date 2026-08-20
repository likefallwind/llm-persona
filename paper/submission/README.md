# ACL/ARR anonymous submission package

`main.tex` uses the official ACL review style and contains no author names or
affiliations.  The generated `submission.pdf` is the review artifact; it must be
rebuilt and inspected before upload.

## Pinned official style

- repository: <https://github.com/acl-org/acl-style-files>
- commit: `d5adc823ff0f80f98c80405ca0ab66c68e684409`
- `acl.sty` SHA-256:
  `19dfeddc2c0e448f3926a0bef048a9db3f3611b46265b760caabd7ada4f361de`
- `acl_natbib.bst` SHA-256:
  `6fbb306202290f4b68e74ac1460a8b27398500cb6dfeb4492e74c457eae7cd1e`

The upstream style files are deliberately not vendored or modified.  Clone the
pinned commit and point the build script at that checkout:

```bash
git clone https://github.com/acl-org/acl-style-files.git /tmp/acl-style-files
git -C /tmp/acl-style-files checkout d5adc823ff0f80f98c80405ca0ab66c68e684409
ACL_STYLE_DIR=/tmp/acl-style-files ./scripts/build_acl_submission.sh
```

The script checks both file hashes, compiles in a temporary directory, and
copies only the final PDF into this directory.  `SOURCE_DATE_EPOCH` is pinned so
repeated builds with the same TeX toolchain are byte-stable.

The 2026-08-19 result build is nine PDF pages. Main text, limitations, and ethics
end on page 8; references begin on page 8 and continue through page 9, so the
manuscript remains within an eight-page main-content limit. `pdfinfo` reports
blank author/title metadata, `pdffonts` reports every font embedded and no Type 3
font, and text extraction contains no local path or contributor identity. The
factorial table has no overfull box warning.

These structural properties are now executable rather than only manually
recorded. `scripts/audit_acl_submission.py --require-pass` checks review mode,
anonymous TeX authorship, page-8 main-content termination, reference-only page 9,
blank PDF author/title metadata, embedded non-Type-3 fonts, identity/local-path
patterns, and the required claim-boundary wording. Its report is stored under
`artifacts/submission_audit/`. Final visual inspection and the live venue rules
remain separate requirements.

## Pre-upload gates

1. Confirm `\usepackage[review]{acl}` remains enabled.
2. Inspect the PDF for author-identifying text and broken figures or citations.
3. Confirm the complete 480-unit, three-judge detector audit preserves the
   registered downgrade: question-first and correct-answer reveal pass, while
   the encouragement lexicon fails as a semantic warmth measure.
4. Run `./scripts/reproduce_completed.sh` and the manifest verifier.
5. Complete the current ARR Responsible NLP checklist in the submission form;
   `research/15_arr_responsible_nlp_checklist.md` is the local evidence map.
6. Recheck the venue page limit and deadline on the official ARR pages.
