# Internal red-team review

Date: 2026-08-19.  Standard: skeptical ACL/EMNLP area-chair review, not a demo
bar.  This document intentionally argues against the paper's strongest claims.

## Likely rejection arguments

### 1. “This is stylometry relabeled as personality.”

**Why it is serious:** model attribution is above chance on teaching responses,
but it is even stronger on MCQ and instruction-following negative controls.
Lexical fingerprints are known to survive domain transfer.

**Current answer:** the manuscript does not call attribution a disposition.  It
separates surface, policy, and validated disposition; centers within item; reports
negative-domain transfer; and requires policy features to add outcome prediction
beyond exact-item and length baselines.  Policy+length adds 0.023--0.031 AUC while
length alone adds about 0.002.

**Still needed:** blinded semantic dimensions must show incremental validity after
transparent and negative-domain profiles.  If they do not, the disposition claim
must be withdrawn and the contribution reframed as steerable policy fingerprints.

### 2. “Six models cannot support psychometrics.”

**Why it is serious:** thousands of responses are nested in only six core model
systems.  Treating responses as independent model samples is pseudo-replication.

**Current answer:** all claims declare their unit.  Prompt effects are paired over
contexts within a fixed model; held-out-model prediction is reported fold by fold;
model-level correlations are explicitly exploratory.  The power audit estimates
that even |r|=0.7 needs about 14 models for 80% power.

**Still needed:** expand the version-controlled model panel to at least 14--20
systems for model-level correlational claims, or remove those claims entirely.

### 3. “The outcome and the predictors share the same rubric.”

**Why it is serious:** lexical action proxies such as questioning and answer reveal
overlap with what a tutoring-quality judge rewards.  Both existing judges may
share alignment-shaped preferences.

**Current answer:** two judge models agree on identical responses, and the strong
item baseline makes the incremental prediction nontrivial.  However, this is only
judge robustness, not independent criterion validity.

The three planned semantic judges were also audited on an existing 482-pair
expert preference set, with both A/B orders retained.  Expert agreement is
0.817--0.844 and order consistency is 0.900--0.919.  This supports competence and
position robustness, but the three-judge majority does not outperform MiniMax-M3
and therefore cannot be presented as a human-ground-truth substitute.

**New independent evidence:** a conventional TF-IDF/SVM classifier trained on
18,541 human-labelled MathDial teacher turns reaches problem-grouped macro F1
0.559--0.571.  Three classifier variants agree that the prompt increases match to
the observed human next action for all nine models in both difficulty sets (54/54
positive contrasts).  This removes the LLM-judge dependency for the intervention
direction, although action agreement is not a learning outcome.

**Still needed:** reference-grounded error localization, subsequent simulated
student success scored objectively, or prospective learner outcomes.  Merely
adding more LLM judges does not resolve shared source variance.

### 4. “The intervention only makes models imitate the rubric.”

**Why it is serious:** an explicit LearnLM-style prompt may directly mention
questioning and scaffolding, so a larger judge score is partly manipulation-check
success.

**Current answer:** report action-level heterogeneity rather than only the score:
all nine models ask more questions and shorten answers, but praise, diagnosis,
imperatives, and answer revealing move differently.  Profile convergence and
heterogeneous treatment vectors are more informative than the aggregate win.

**Still needed:** use held-out semantic dimensions not named in the prompt and test
whether the treatment improves an independently measured downstream outcome.
The new dialogue-act analysis partly answers this and also reveals a failure:
human `telling`-target match drops from 0.394--0.442 to 0.111--0.125 across three
classifiers, consistent with over-application of the question-asking policy.

### 5. “Candidate--judge family overlap causes self-preference.”

**Why it is serious:** MiniMax-M3 judges MiniMax candidates; the DeepSeek swap
includes a DeepSeek candidate.  Rank stability does not exclude family bias.

**Current answer:** candidate order is independently randomized and blind for each
judge, the same response bytes are scored, and the confirmatory analyzer reports
judge residuals for own-family versus other candidates.  A separate human-
preference calibration finds pairwise judge kappas of 0.614--0.719.

**Still needed:** finish the active three-judge panel and inspect the prespecified
judge × candidate-family interaction and leave-one-judge-out conclusions.  A local
8B/12B smoke test produced valid JSON but confidence 1 and is not reliable enough
to replace frontier judges; further local work is paused until a stronger server
is available.

### 6. “The family analysis is underpowered and causally uninterpretable.”

**Why it is serious:** four approximate pairs differ in generation, training, and
serving.  Baseline resemblance is borderline (p=0.0512) and disappears after the
pedagogy prompt.

**Answer:** agree.  Keep this exploratory and out of the abstract; it motivates a
future controlled lineage study but does not support a causal family claim.

### 7. “Real-world educational value is missing.”

**Why it is serious:** response quality and policy are not student learning.
Scaffolding can fail when learners do not engage with it.

**Current answer:** the paper targets tutor policy measurement, not learning gain.
It uses authentic multi-turn contexts and avoids equating benchmark preference
with learning.

The existing LongTutor panel now supplies a harder prerequisite criterion.  On
6,000 matched model × history observations, teaching quality correlates only
weakly with human-gold diagnosis correctness (mean within-model Spearman 0.173),
and adding its four dimensions fails to improve held-out-model prediction beyond
exact history difficulty (AUC 0.816 versus 0.822).  Historical-evidence prediction
also shows no RMSE gain, although non-exact evidence equivalence uses a fixed
MiniMax-M3 judge and is therefore a secondary criterion.  The human-gold diagnosis
negative result directly rejects the idea that an
adaptive-sounding response proves accurate learner modeling.

**Still needed for a broad journal:** prospective interactions or a separately
validated learner simulator with objective pre/post problem completion and
robustness to simulator choice.  ACL 2026 evidence shows that simple prompted
student simulators are poor on linguistic, behavioral, and cognitive fidelity, so
a quick API loop would not resolve this threat.  Main-conference scope may be
defensible without learning claims if the paper remains about tutor policy.

### 8. “The corpus cannot be audited or released.”

**Why it is serious:** LongTutor contains long histories, broad phone-like regex
matches, and no standalone LICENSE file in the audited upstream repository root.

**Current answer:** manifests store hashes and IDs rather than copies; runs are
resumable; external transmission is paused unless explicitly authorized.  The
LongTutor paper's datasheet states CC BY 4.0 for data and MIT for evaluation
code, while the current repository README points back to the paper for terms.

**Still needed:** complete a privacy review before any text release or new
destination.  The planned package remains code, hashes, and derived annotations;
the paper license statement does not remove the privacy risk of longitudinal
learning histories.

### 9. “The semantic judges score a six-candidate slate, not isolated responses.”

**Why it is serious:** even with absolute 1--5 anchors, seeing all six answers can
induce contrast, range compression, or winner/loser comparisons.  The resulting
scores may be batch-relative rather than transportable measurements.

**Current answer:** every judge sees the same response set, exact context is the
unit of comparison, candidate order is independently randomized, and position
residuals are audited on the identical response.  The main claims concern
within-context model differences and paired prompt movement, for which a shared
slate is partly advantageous.

**Still needed:** report marginal score distributions and ceiling/floor rates by
task and judge.  Do not claim absolute score calibration across benchmarks.  A
future isolated-response subsample would be needed to quantify slate effects.

### 10. “The models are a convenience panel, not a population sample.”

**Why it is serious:** the six systems were selected because they have complete
paired coverage, not sampled from a well-defined model population.  Vendor,
language, alignment, size, and serving versions are entangled.

**Current answer:** all model-level claims say “in this finite panel”; no
population, scaling, or vendor-family inference is allowed.  The nine-model
intervention panel expands response heterogeneity but does not solve sampling.

A provenance audit now pins 84 relevant prediction/summary pairs by SHA-256.  It
also shows that temperature is retained for 22/84 runs and neither seed nor
prompt version for any run.  Thus analysis reproduction is byte-defined, but
provider-response regeneration is not.

**Still needed:** prospectively pin provider/model versions, dates, prompts, and
decoding settings.  For future population
claims, prospectively sample at least 14--20 versioned systems across open and
closed families and repeat the same frozen contexts.

### 11. “Benchmark familiarity and post-training contamination explain the result.”

**Why it is serious:** current models or judges may have seen MathDial, MRBench,
or benchmark rubrics during training.  Familiarity could improve rubric-shaped
behavior and judge agreement without establishing a general tutor policy.

**Current answer:** model attribution is held out by task family, LongTutor uses
long real histories, and exact-item causal contrasts compare the same model and
context under two prompts.  Contamination cannot alone explain within-item prompt
movement, but it can affect baselines and criterion alignment.

**Still needed:** add a small, procedurally generated held-out context set after
the models' knowledge cutoff or remove any claim of benchmark-unseen
generalization.  Hash-based sampling is unbiased within the archive but does not
make the archive uncontaminated.

### 12. “The paired prompt changes more than pedagogy.”

**Why it is serious:** the explicit arm can alter length, register, and compliance
because it is a more detailed instruction.  It is not a clean intervention on one
latent disposition.

**Current answer:** the manuscript calls it a bundled policy intervention, reports
the full treatment vector, and treats convergence plus the telling failure as the
result.  It does not estimate a single latent causal coefficient.

**Still needed:** avoid language such as “causal effect of personality.”  A later
factorial prompt study should vary questioning, directness, warmth, and diagnosis
instructions separately while holding prompt length and specificity comparable.

### 13. “Behavior-first personality and tutor adaptivity already exist.”

**Why it is serious:** ACL 2026 GenPT explicitly replaces fixed self-report with
generative projective behavior collection.  Borchers and Shou already use
learner-context ablations and a validated tutor-training classifier to test LLM
tutor adaptivity.  PedRAG explicitly studies declared-versus-enacted pedagogical
behavior under runtime control.

**Current answer:** the novelty is not the phrase *behavior-first*, a new tutor
taxonomy, or the general observation that prompts change teaching.  It is the
joint identification design over previously generated application behavior:
same-item multi-model coverage, held-out educational families, a large generic-
domain fingerprint control, a shared paired intervention, action-specific harm,
judge-family/position audits, and a human-gold diagnosis boundary test.  GenPT
elicits behavior inside a psychometric instrument; the ITS study tests context
sensitivity in 75 scenarios; PedRAG evaluates a control architecture in 144
simulated sessions.

**Still needed:** retain the explicit closest-work table and never use
“first behavior-based LLM personality study.”  If the semantic panel fails, the
negative construct-validity result must remain the contribution rather than
being hidden behind a renamed trait.

## Decision after red-team review

The present work is not yet “毫无争议” top-tier-ready.  It now has two complementary
core results: policy behavior adds held-out-model quality prediction beyond exact-
item and length controls, and the intervention changes an independently inferred
human teacher action in the same direction across all nine models and three
classifiers.  The telling-action failure makes the contribution less promotional
and more scientifically informative.  Construct validity and downstream learning
validity remain incomplete.  The next go/no-go gate is the blinded semantic panel.
If it collapses to surface features or varies substantially by judge, the correct
conclusion is still steerable policy fingerprints, not stable dispositions.
