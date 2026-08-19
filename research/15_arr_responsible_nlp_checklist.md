# ARR Responsible NLP checklist evidence map

Snapshot: 2026-08-19.  This is an internal preparation aid, not a substitute for
the current ARR form.  The official call requires the ACL template and the
official author checklist says review mode must be enabled.  Recheck both pages
immediately before upload:

- <https://aclrollingreview.org/cfp>
- <https://aclrollingreview.org/authorchecklist>

## Claims and limitations

- The abstract and conclusion scope inference to the frozen finite model panel.
- No model-population, immutable-weight, human-personality, or learning-gain
  claim is made.
- Section 7 reports the six-model limit, correlated response structure,
  judge-dependence, missing provider provenance, and the distinction between
  action agreement and learning outcomes.
- The executable decision rule prevents promotion from policy signatures to a
  disposition thesis when fewer than two dimensions pass all tiers.

## Reproducibility

- `artifacts/reproducibility_manifest.json` records Git-eligible paths and
  SHA-256 values.
- `scripts/reproduce_completed.sh` and CI verify registered claims, tests,
  privacy structure, and figures.
- `research/14_clean_room_reproduction.md` reports a fresh-checkout audit and
  explicitly separates its reused local dependency environment from the
  independently provisioned GitHub runner.
- GitHub Actions run `32257044437` installs the exact versions in
  `requirements.txt` on a new Python 3.13 Ubuntu runner and passes public-package
  tests, claims, privacy, figures, and clean-worktree gates. It does not receive
  private corpus inputs.
- Provider-side generation is not exactly reproducible; the paper discloses the
  absent seed/prompt-version fields and partial temperature coverage.

## Data, privacy, and external services

- Public artifacts contain hashes, identifiers, derived measurements, and
  aggregate outputs rather than benchmark prompts, generated responses, or
  longitudinal learner histories.
- LongTutor histories are withheld as a privacy-minimizing choice even though
  its paper describes a permissive data license.
- The semantic coding payload was transmitted only after explicit authorization.
- One provider failure and the paired complete-case exclusion are reported in
  the main paper, appendix, executable JSON rule, and attrition amendment.

## Annotation and evaluation

- The semantic rubric, candidate blinding, independent slate randomization,
  three-judge coverage gate, reliability criteria, leave-one-judge sensitivity,
  and bias diagnostics are documented.
- LLM-judge agreement and calibration are not labelled human ground truth.
- Human-labelled dialogue actions and human-gold LongTutor diagnosis are used as
  complementary criteria, but neither is represented as student learning gain.

## Compute and artifacts to add at submission time

- Record API model aliases, annotation counts, and any available provider usage
  totals in the final form; do not estimate unlogged energy or carbon values.
- Record the PDF page count, exact ACL style commit, final repository commit,
  artifact URL, and license decisions.
- Perform an author-identity scan over TeX, PDF metadata, acknowledgements,
  repository URLs, and supplementary filenames before anonymous upload.
