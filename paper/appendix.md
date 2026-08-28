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

## G. Prospective factorial and request-order replay

The public synthetic design crosses 32 elementary-math problems, two learner
requests, and eight system-policy cells over five model endpoints. The parent
panel completed 2,560/2,560 calls. Its runner used a lexicographic manifest, so
the outcome-blind order amendment selected two fixed problems from each of four
families and replayed 640 byte-identical prompts in a model-specific SHA-256
order. Every consecutive 16-call block contains all request-policy cells exactly
once. The replay completed 640/640 calls with zero errors, and observed queue
ranks match the public plan.

The analysis releases deterministic question-first, answer-reveal, frozen
encouragement-lexicon, and length metrics plus prompt and response hashes, not
provider text. It reports all
96 parent cells, 192 parent interaction rows, all model and family effects, and
the corresponding replication tables. The fixed paper-facing report is
`research/20_factorial_results.md`. Replication is downgrade-only and cannot
rescue a failed parent gate. The final joint result retains all three operational
effects but rejects both learner-request adaptation claims.

After aggregate results were known, we froze a post-result, downgrade-only
validation of the three primary detectors. An outcome-independent SHA-256 sample
contains 480 responses (320 parent and 160 replay). Three judges independently
labelled 48 blinded batches without model identity, factor cells, detector
values, or effects, producing 144/144 complete batch annotations. Question-first
and correct-answer reveal passed coverage, balanced-accuracy, bootstrap-lower-
bound, and kappa gates. The encouragement lexicon failed (balanced accuracy
0.818 [0.787, 0.847], kappa 0.631) and is therefore reported only as a literal
marker, not semantic warmth or support. Synthetic behavioral compliance is
neither learner modeling nor learning gain.

## H. General-personality archive audit and affiliation pilot

The archive-first audit prevents a large new personality battery from being
authorized merely because an educational axis has an intuitive human label. A
theory-first map covers the Big Five, HEXACO honesty--humility, Dark Triad,
Schwartz values, cooperation, risk, impression management, measurement routes,
and stability perturbations. Of 22 construct or validity targets, nine have a
partial behavioral candidate and thirteen are not identifiable in the archived
tasks. None validates. In particular, organizational style is recurrent but
correlates negatively with IFEval accuracy (rho=-0.886, exact p=0.035), so it is
not relabelled conscientiousness. The only selected ambiguity is affiliation:
non-tutoring communal expression transports to default tutoring (rho=0.829) and
relational communion (rho=0.771).

The resulting prospective pilot fixes five generator configurations, twelve
matched interpersonal conflicts, education and non-education domains, and four
conditions: default, an irrelevant interface context, high affiliation, and low
affiliation. It separately elicits a ten-item public-domain IPIP agreeableness
self-report, twelve balanced forced choices, and twelve open responses. Three
blinded judges rate the open responses on affiliative behavior, benevolent cost
acceptance, assertive dominance, surface warmth, and task effectiveness. All 280
generator calls and 144 judge batches completed without final errors.

All five preregistered default-stability gates pass: ICC(3,k)=0.931;
education/non-education profile rho=0.900; default/irrelevant profile rho=0.718;
irrelevant mean shift=-0.050; and between-model SD=0.445. The exact profile
p-values are 0.091 and 0.174 because the fixed panel has only five models. High
minus low prompting moves the primary score by 1.689 points and is positive for
all five models, but per-model shifts range from 0.444 to 2.917. High prompting
compresses model SD to 0.201, whereas low prompting expands it to 0.879.

The general-trait convergence gates fail. Default IPIP scores span only
4.2--4.9 and correlate -0.200 with open behavior. Every model chooses all twelve
affiliative forced-choice options at default, leaving no model variance. Open
affiliation also correlates 0.900 with surface warmth. The retained claim is a
localized cross-domain, prompt-contingent affiliation behavior cluster, not a
Big Five trait or a model-population estimate.

## I. Prospective action-routing falsification

Two frozen remedies test whether explicit action selection repairs the shared
prompt's telling harm. A 1,920-call balanced trial reproduces the uniform
prompt's probing gain and telling loss but rejects a one-pass adaptive menu. A
separate 2,400-call trial crosses five models with two independently worded
ASK/EXPLAIN selectors, both counterfactual executors, and a same-snapshot
single-pass baseline. ASK and EXPLAIN realization reaches 0.998 and 1.000, while
selector accuracy is only 0.519 [0.456, 0.583] and 0.500 [0.433, 0.563]. The
composed policies underperform single pass by -0.058 [-0.110, -0.004] and -0.077
[-0.131, -0.023]. This localizes the failure to contextual selection rather than
verbal realization; it does not establish a successful controller.

## J. Reproduction and release

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
