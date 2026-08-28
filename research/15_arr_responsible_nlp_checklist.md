# ARR Responsible NLP checklist evidence map

Snapshot: 2026-08-28.  This is an internal preparation aid, not a substitute for
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
- The prospective factorial is scoped to black-box component addressability;
  the paper reports synthetic-task, deterministic-detector, provider-snapshot,
  delayed-replay, and component-interaction limitations.
- The post-result detector audit is explicitly downgrade-only: question-first
  and correct-answer reveal validate, while the encouragement lexicon fails
  semantic warmth validation and is reported only literally.
- The executable decision rule prevents promotion from policy signatures to a
  disposition thesis when fewer than two dimensions pass all tiers.
- The general-personality archive audit distinguishes nine partial candidates
  from thirteen constructs that are not identifiable in the available tasks;
  neither category is reported as a validated or absent trait.
- The targeted affiliation pilot reports five fixed model configurations,
  underpowered exact profile tests, one irrelevant perturbation, model/judge
  family overlap, and strong overlap between open affiliation and surface warmth.
- Self-report and forced-choice failures remain headline results; inducibility
  under high/low prompts is not treated as default-trait validity.

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
- The 2,560-call factorial and 640-call replay have public specifications,
  prompt hashes, a complete randomized-order plan, derived metrics, complete
  cell/interaction tables, and machine-checked downgrade-only decisions. Raw
  provider responses remain excluded.
- The detector audit publishes its outcome-independent sample plan, payload
  audit, 480 majority labels, subgroup diagnostics, and frozen pass thresholds;
  raw synthetic provider text and judge payloads remain excluded.
- The affiliation pilot publishes its frozen specification, hashes, conditions,
  derived consensus ratings, profiles, gate decisions, and complete error
  ledgers. All 280 generator calls and 144 judge batches completed; raw provider
  and judge response text remains ignored and outside the release.

## Data, privacy, and external services

- Public artifacts contain hashes, identifiers, derived measurements, and
  aggregate outputs rather than benchmark prompts, generated responses, or
  longitudinal learner histories.
- LongTutor histories are withheld as a privacy-minimizing choice even though
  its paper describes a permissive data license.
- The semantic coding payload was transmitted only after explicit authorization.
- The prospective API payload contains only synthetic math problems, synthetic
  wrong work, synthetic learner requests, and frozen policy clauses; it contains
  no benchmark response, real learner history, identifier, or private source
  text.
- The detector-validation payload contains only synthetic problems, correct
  answers, and synthetic model responses; it excludes model identity, factor
  cells, detector values, effects, benchmark text, and learner histories.
- One provider failure and the paired complete-case exclusion are reported in
  the main paper, appendix, executable JSON rule, and attrition amendment.
- The affiliation prompts use synthetic interpersonal conflicts rather than real
  learner or workplace records. Generator identities are hidden from judges, but
  three judge families overlap with three of five generator families and this is
  disclosed as a limitation.

## Annotation and evaluation

- The semantic rubric, candidate blinding, independent slate randomization,
  three-judge coverage gate, reliability criteria, leave-one-judge sensitivity,
  and bias diagnostics are documented.
- LLM-judge agreement and calibration are not labelled human ground truth.
- Human-labelled dialogue actions and human-gold LongTutor diagnosis are used as
  complementary criteria, but neither is represented as student learning gain.
- Deterministic factorial endpoints are reported as surface behaviors. Failed
  learner-request gates and reproduced policy interactions remain central rather
  than being hidden by the successful system-clause effects.

## Compute and artifacts to add at submission time

- Record API model aliases, annotation counts, and any available provider usage
  totals in the final form; do not estimate unlogged energy or carbon values.
- Record the PDF page count, exact ACL style commit, final repository commit,
  artifact URL, and license decisions.
- Perform an author-identity scan over TeX, PDF metadata, acknowledgements,
  repository URLs, and supplementary filenames before anonymous upload.
- Run `scripts/audit_acl_submission.py --require-pass`; it machine-checks the
  current PDF's eight-page content boundary, post-conclusion section ordering,
  metadata, embedded fonts, Type-3 absence,
  local-path/identity patterns, and mandatory scope language. Still inspect the
  rendered PDF visually and recheck the live venue rules.
- Disclose the use of generative tools for research design, coding, analysis, or
  writing at the granularity required by the current ARR AI-assistance policy;
  all authors remain responsible for the manuscript and citations.
