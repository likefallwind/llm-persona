# Claim--evidence--threat matrix

Snapshot: 2026-08-19.  “Supported” below means supported in the present corpus,
not established for the population of all language models.

| Claim | Strongest current evidence | Main falsifier / threat | Status |
|---|---|---|---|
| Models leave stable response signatures across educational tasks. | 31,638 six-model teaching responses; leave-one-task-family-out policy attribution has an unweighted family macro-average of 0.242 versus 0.167 chance; several within-item-centered proxies have ICC(3,1) 0.47--0.65. | Generic model fingerprints, verbosity, and only six systems. | Supported as a signature, not a disposition. |
| A broad fingerprint is not the same as a pedagogical policy. | On 57,516 negative-control responses, the unweighted held-out-family macro-average is stronger (0.372 with all transparent features); cross-domain policy-geometry Mantel correlation is only 0.296, exact p=0.307. | Current semantic proxies are lexical and may miss shared policy structure. | Negative control passes provisionally; semantic coding pending. |
| Explicit pedagogy instructions causally change tutoring behavior. | Within-model, within-item MathDial comparisons: all nine models increase question rate and reduce response length in both standard and hard sets; prompt-driven profile dispersion contracts to 0.763 of baseline, bootstrap 95% CI [0.738, 0.794]. | Prompt arms also change wording and rubric alignment; not all dimensions move uniformly. | Strong support for causal addressability, not for a single latent trait. |
| Prompt effects are not an artifact of one evaluator. | On 14,770 identical responses, MiniMax-M3 versus DeepSeek-v4-flash judge agreement has quadratic kappa 0.810; prompt outcome gains replicate under both judges (mean 0.457--0.475). On a separate 482-pair expert preference set shown in both orders, the planned semantic judges agree with experts at 0.817--0.844 and are position-consistent at 0.900--0.919. | All are LLM judges and may share source variance; the three-judge majority (0.835) does not beat the best individual judge (0.844; difference -0.009, bootstrap CI [-0.027, 0.007]). | Judge competence and position robustness supported; majority is not human ground truth. |
| Pedagogical actions predict educational quality beyond task difficulty and verbosity. | Leave-one-model-out prediction with exact-item fixed effects: adding policy+length raises mean AUC by 0.031 under DeepSeek and 0.023 under MiniMax; every model fold improves (exact one-sided sign p=0.031 and 0.016). Length alone adds about 0.002. | Outcome is rubric-based LLM judgement; feature vocabulary partly overlaps the rubric. | Strong rubric-validity result, complemented by the independent human-action criterion below. |
| The prompt changes behavior in a way that aligns with human teacher actions, but not uniformly. | A conventional classifier trained on 18,541 human-labelled MathDial teacher turns obtains problem-grouped macro F1 0.559--0.571. Across three TF-IDF/SVM variants, all 54 classifier × difficulty × model prompt contrasts improve next-action match. Mean gains are 0.091--0.114 standard and 0.145--0.180 hard. | The classifier is imperfect and action match is not learning gain. The prompt explicitly asks guiding questions. | Independent-method causal validity supported; the action-specific trade-off is scientifically important. |
| A one-size pedagogy prompt can suppress appropriate direct instruction. | For human `telling` targets, generic-prompt match is 0.394--0.442 across classifier variants, but pedagogy-prompt match falls to 0.111--0.125. The inferred telling share drops by 0.234--0.280. | Only 48 standard target items (432 model responses per arm); dialogue-act labels are coarse. | Robust harm signal requiring confirmatory semantic and downstream tests. |
| Appearing to teach adaptively is not equivalent to objectively diagnosing the learner. | Across the same 1,000 LongTutor histories and six models (6,000 matched observations), separate teaching quality has only weak within-model association with human-gold diagnosis accuracy (mean Spearman 0.173). With exact-history controls and a held-out candidate model, adding four teaching scores does not improve diagnosis AUC (0.816 versus 0.822 item-only). It also does not improve reference-grounded memory-evidence RMSE (both 0.187). | Teaching quality and non-exact evidence equivalence are LLM-judged; only diagnosis is exact human-gold scoring. Only 40 histories enter the blinded semantic panel. | Strong diagnosis null/boundary result; semantic-to-objective linkage remains pending. |
| Dispositions persist within model families. | In a nine-model panel, four approximate within-family pairs are closer at baseline than random matchings (p=0.0512). | Only four non-clean pairs; training, generation, and serving all differ; minimum sign-test p with four pairs is 0.0625. | Suggestive only; must not be a headline claim. |
| Semantic dimensions are reliable and distinguishable from surface style. | Frozen blind eight-dimension protocol, three judges, 2,160 responses, deterministic sample and independent blind candidate order. External transmission was explicitly authorized after payload disclosure; the resumable 1,080-annotation run is active with a strict completeness gate. | LLM judges can share bias; local 8B audit was slow and low-confidence and has been paused pending a stronger server. | Design frozen and run active; no confirmatory claim until all three judges complete. |
| Model-level dispositions predict outcomes across benchmarks. | Existing benchmark outcomes include history use, self-correction, abstention, and educational safety. | Six model means are severely underpowered: about 14 models are needed even for an absolute correlation of 0.7 at 80% power. | Exploratory only until panel expansion. |

## Current paper-level conclusion

The data already reject two simplistic stories:

1. the signal is *only* verbosity or item difficulty; policy features add held-out-model quality prediction after both controls, and
2. the signal is a universal, human-like personality; general fingerprints are stronger on non-tutoring tasks, family resemblance is weak, and prompt responses are heterogeneous.

The strongest defensible thesis is therefore narrower and more useful:

> AI tutors exhibit model-conditioned pedagogical policy signatures that are
> partially stable, causally steerable, and incrementally predictive of judged
> tutoring quality and human-labelled next actions, but steering toward a generic
> “ask questions” policy can suppress contextually appropriate telling.  These
> signatures are distinct from both generic generator fingerprints and human
> personality traits.

## Requirements before a top-tier submission claim

- Complete blinded semantic coding with at least two architecturally distinct
  measurement routes and report leave-judge-out stability and self-family bias.
- Extend the new human-labelled dialogue-act criterion with a downstream outcome;
  action agreement is independent of LLM judges but still is not student learning.
- Link the 40 LongTutor semantic-panel histories to human-gold diagnosis and
  evidence accuracy.  Treat naive prompted student simulation as invalid unless
  the simulator is separately calibrated.
- Expand the independently sampled model panel if making population-level or
  family-level claims; six model means cannot support latent-trait correlations.
- Fit cluster-aware confirmatory models and freeze the exact primary contrasts
  before viewing semantic labels.
- Package manifests, hashes, scripts, environment, and an auditable exclusion
  ledger; clarify upstream licenses before releasing any text.
- Apply `research/11_submission_decision_rule.md` without dropping failed
  semantic dimensions or weakening the third-judge reveal thresholds.
