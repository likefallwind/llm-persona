# Supplementary methods and audit tables

This appendix accompanies *Beyond Personality and Fingerprints*. It reports
design and audit details that do not fit the main paper.

## A. Units of analysis and dependence

The frozen corpus inventory contains 47,321 benchmark-item identifiers answered
successfully by all six core models (283,926 model responses) across all selected
roles.  The main transparent-feature analysis uses 31,638 teaching responses;
the generic negative controls use 57,516 responses.  The extended prompt panel
contains 26,586 MathDial responses from nine model aliases.

These counts are not treated as independent model samples.  The design has four
different inferential units:

| Claim | Unit resampled or held out | Scope of inference |
|---|---|---|
| Transparent cross-task signature | Entire benchmark family | Prediction on unseen task families within the frozen model panel |
| Prompt movement | Underlying paired context | Within-model response-policy change under the recorded bundled instruction |
| Held-out-model quality increment | Candidate model, with exact item effects | Transport to one held-out member of the six-model panel |
| Model-profile correlation/family resemblance | Model alias | Exploratory only; no model-population inference |

When six models answer the same context, bootstrap procedures resample the
context and retain all model-linked rows.  They never count the six correlated
answers as six independent context interventions.  The power audit separately
shows that response count cannot repair a six-model correlational design: about
14 models are required for 80% power at an absolute correlation of 0.7 and about
30 at 0.5 under the registered calculation.

## B. Corpus selection and failure handling

`build_corpus_inventory.py` scans only item-level prediction files and records a
row as successful when the latest occurrence of an item contains nonempty
response text and no error.  A summary, log, or process marker alone never counts
as a completed item.  For each benchmark/model alias, duplicate run directories
are resolved by successful unique-item count and then summary availability.  All
paired comparisons intersect successful item IDs before features or outcomes are
examined.

Inventory schema v2 stores upstream paths relative to `$EDUBENCH_ROOT`.  The
portable path resolver also accepts the earlier absolute-path schema for backward
compatibility.  The released inventory therefore describes the upstream logical
location without embedding a contributor's user-home path.

## C. Transparent feature system

Features are deterministic counts or rates over the archived response bytes.
Surface features include log character/token count, line and sentence counts,
mean sentence length, headings, bullets, numbered steps, LaTeX, emoji, and table
presence.  Policy proxies include question rate, final/one-question indicators,
second-person and inclusive-first-person language, praise, encouragement,
hedging, imperatives, learner-history references, answer reveal, explanation,
and diagnosis markers.  The multilingual regular expressions are versioned in
`run_behavioral_pilot.py`.

For profile analyses, each feature is centered across candidate models within an
exact benchmark item, then standardized within benchmark.  This removes shared
item difficulty and scale while retaining model-conditioned relative behavior.
The proxies are not labelled latent traits.  Model attribution uses multinomial
logistic regression with standardized numeric inputs and holds out one entire
prespecified task family.  Reported teaching and negative-control headline
accuracies are unweighted macro-averages over held-out families, preventing a
large benchmark from defining the result.

## D. Intervention and independent action criterion

Standard and hard MathTutorBench generic/pedagogy arms are paired through their
shared MathDial context.  The treatment vector is pedagogy minus generic for the
same model and context.  The instruction changes multiple policy components and
is therefore called a bundled intervention, not an isolated latent-trait
manipulation.  Cross-model dispersion is the mean distance among centered model
profiles; its ratio uses a context bootstrap that retains the multi-model block.

The action criterion is independent of the LLM quality judges.  Three
TF-IDF/linear-SVM variants (word, character, and hybrid) are trained on 18,541
existing human MathDial teacher turns.  Five-fold predictions group by math
problem, so near-duplicate turns from one problem cannot appear in both train and
test.  Exact bridge lookup is performed before generated outcomes are inspected.
Ambiguous or unmatched human targets are retained in the mapping audit but
excluded from action-match estimation.  The human target is a contextual teacher
choice, not a gold learning outcome.

## E. Quality and LongTutor criteria

Quality models are evaluated leave-one-candidate-model-out.  Exact item one-hot
effects form the baseline; length and policy features are nested additions.
Every held-out-model fold is reported.  A second judge scores byte-identical
responses, and a separate 482-pair expert preference set shown in both orders
audits three judges for competence and position consistency.  Judge agreement is
robustness evidence, not human ground truth.

LongTutor analyses join teaching, diagnosis, and evidence tasks on exact history
and model.  Human-gold diagnosis is exact categorical scoring.  Non-exact
historical-evidence equivalence uses one fixed LLM judge and remains secondary.
Held-out-model prediction includes exact-history one-hot effects before teaching
scores are added.  These are prerequisite learner-modeling criteria, not pre/post
learning gains.

## F. Confirmatory semantic panel

The deterministic sample contains 360 context-arm batches and 2,160 candidate
responses: 40 LongTutor histories; 80 standard MathDial pairs; 40 hard MathDial
pairs; and 80 Socratic contexts.  MiniMax-M3, GLM-5.2, and DeepSeek-V4-Pro each
rate all batches.  Candidate model identities are hidden and slate order is
independently shuffled by judge and batch.

The eight descriptive 1--5 dimensions are help directness, elicitation, autonomy
support, affective warmth, diagnostic specificity, personalization, cognitive
load, and epistemic caution.  The runner is append-only and resumable by
annotation ID.  A nonblocking file lock prevents future concurrent writers.
One DeepSeek annotation remained unavailable after three rounds of three
attempts: two streaming rounds returned empty visible content, and a
transport-only non-streaming fallback surfaced HTTP 500. Before formal analysis
and without consulting the pair's scores, we excluded the failed generic batch
and its prespecified pedagogy counterpart for all three judges. The executable
rule is `research/semantic_panel_exclusions_v1.json`; no replacement item or
alternate judge route was used. Confirmatory analysis is impossible unless the
latest retained state has:

1. 1,074 successful eligible annotation IDs and zero eligible errors/invalid lines;
2. six candidates per context-arm batch;
3. 2,148 unique response units and 17,184 response-dimension consensus rows; and
4. exactly three distinct judges for every consensus row.

All eight dimensions remain in the report.  Reliability, scale range,
leave-one-judge stability, exact-context model variance, cross-task stability,
semantic attribution, prompt direction, action convergence, quality increment,
LongTutor human-gold diagnosis, judge-family residuals, and candidate-position
effects are saved as separate tables.  The frozen decision hierarchy can
downgrade the paper to policy signatures; no failed dimension is deleted.

The final decision retained help directness, elicitation, and cognitive load as
reliable measurements. Help directness and cognitive load passed the cross-task
signature tier; only help directness passed an independent disposition criterion.
Because fewer than two dimensions reached that tier, the registered title rule
selected the policy-signature framing. Semantic held-out-task attribution is
0.322 from semantic features alone and 0.391 when combined with transparent
features, versus 0.167 chance.

## G. Reproduction and release

The provenance audit pins 84 relevant prediction/summary pairs by SHA-256.
Temperature is recoverable for 22/84 runs and seed/prompt-version for none, so
the analysis is reproducible from frozen bytes but provider-side generation is
not exactly recreatable.  The public package contains code, IDs, hashes, derived
features/scores, aggregate tables, figures, and error/exclusion ledgers.  It
contains no copied benchmark prompt, model response, or LongTutor history.

`reproduce_completed.sh` rebuilds the completed non-semantic analyses and fails
on registered-claim drift, release-structure violations, syntax errors, or
submission-decision test failures.  GitHub CI independently rechecks frozen
claims and public artifacts without access to the private upstream corpus.  The
structural privacy check does not prove that every indirect identifier is absent;
license review and substantive privacy review remain separate requirements.
