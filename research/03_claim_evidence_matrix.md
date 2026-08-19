# Claim--evidence--threat matrix

Snapshot: 2026-08-19.  “Supported” below means supported in the present corpus,
not established for the population of all language models.

| Claim | Strongest current evidence | Main falsifier / threat | Status |
|---|---|---|---|
| Models leave stable response signatures across educational tasks. | 31,638 six-model teaching responses; leave-one-task-family-out policy attribution has an unweighted family macro-average of 0.242 versus 0.167 chance; several within-item-centered proxies have ICC(3,1) 0.47--0.65. | Generic model fingerprints, verbosity, and only six systems. | Supported as a signature, not a disposition. |
| A broad fingerprint is not the same as a pedagogical policy. | On 57,516 negative-control responses, the unweighted held-out-family macro-average is stronger (0.372 with all transparent features); cross-domain policy-geometry Mantel correlation is only 0.296, exact p=0.307. The blind semantic panel nevertheless reaches 0.322 held-out-task attribution and adds to transparent features (0.391 combined versus 0.353 transparent). | Only six systems; attribution remains a signature diagnostic rather than construct validity by itself. | Negative control and semantic incremental signal jointly support the narrower policy-signature construct. |
| Explicit pedagogy instructions causally change tutoring behavior. | Within-model, within-item MathDial comparisons: all nine models increase question rate and reduce response length in both standard and hard sets; prompt-driven profile dispersion contracts to 0.763 of baseline, bootstrap 95% CI [0.738, 0.794]. | Prompt arms also change wording and rubric alignment; not all dimensions move uniformly. | Strong support for causal addressability, not for a single latent trait. |
| Prompt effects are not an artifact of one evaluator. | On 14,770 identical responses, MiniMax-M3 versus DeepSeek-v4-flash judge agreement has quadratic kappa 0.810; prompt outcome gains replicate under both judges (mean 0.457--0.475). On a separate 482-pair expert preference set shown in both orders, the planned semantic judges agree with experts at 0.817--0.844 and are position-consistent at 0.900--0.919. | All are LLM judges and may share source variance; the three-judge majority (0.835) does not beat the best individual judge (0.844; difference -0.009, bootstrap CI [-0.027, 0.007]). | Judge competence and position robustness supported; majority is not human ground truth. |
| Pedagogical actions predict educational quality beyond task difficulty and verbosity. | Leave-one-model-out prediction with exact-item fixed effects: adding policy+length raises mean AUC by 0.031 under DeepSeek and 0.023 under MiniMax; every model fold improves (exact one-sided sign p=0.031 and 0.016). Length alone adds about 0.002. | Outcome is rubric-based LLM judgement; feature vocabulary partly overlaps the rubric. | Strong rubric-validity result, complemented by the independent human-action criterion below. |
| The prompt changes behavior in a way that aligns with human teacher actions, but not uniformly. | A conventional classifier trained on 18,541 human-labelled MathDial teacher turns obtains problem-grouped macro F1 0.559--0.571. Across three TF-IDF/SVM variants, all 54 classifier × difficulty × model prompt contrasts improve next-action match. Mean gains are 0.091--0.114 standard and 0.145--0.180 hard. | The classifier is imperfect and action match is not learning gain. The prompt explicitly asks guiding questions. | Independent-method causal validity supported; the action-specific trade-off is scientifically important. |
| A one-size pedagogy prompt can suppress appropriate direct instruction. | For human `telling` targets, generic-prompt match is 0.394--0.442 across classifier variants, but pedagogy-prompt match falls to 0.111--0.125. Independently, `telling` responses are 1.360 semantic points higher in help directness, while the prompt reduces help directness by 1.709 standard and 1.542 hard points. | Only 48 standard target items (432 model responses per arm); dialogue-act labels are coarse and not outcomes. | Robust action harm with confirmatory semantic mechanism convergence. |
| Appearing to teach adaptively is not equivalent to objectively diagnosing the learner. | Across 6,000 model-history observations, existing teaching scores do not improve diagnosis (0.816 versus 0.822 item-only). In the blind 40-history semantic subset, all semantic dimensions also underperform exact-history controls (mean AUC 0.744 versus 0.775), and no diagnosis association survives within-outcome BH correction. | Only diagnosis is exact human-gold scoring; the blinded subset has 40 histories. | Strong diagnosis null/boundary result under both existing and confirmatory semantic measurements. |
| Dispositions persist within model families. | In a nine-model panel, four approximate within-family pairs are closer at baseline than random matchings (p=0.0512). | Only four non-clean pairs; training, generation, and serving all differ; minimum sign-test p with four pairs is 0.0625. | Suggestive only; must not be a headline claim. |
| Semantic dimensions are reliable and distinguishable from surface style. | The exclusion-aware panel has 1,074/1,074 annotations and 2,148 responses with three judges each. Help directness, elicitation, and cognitive load pass reliability; leave-one-judge profile Spearman is 0.959--0.962. Semantic attribution is 0.322 and combined attribution 0.391 versus 0.353 transparent. | One paired context (0.56%) was technically excluded before formal analysis; LLM judges may share source variance; six models limit transport. | Help directness and cognitive load are cross-task signatures; only help directness is a validated disposition. The paper is therefore framed as policy signatures. |
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

## Remaining requirements before upload

- Keep the three reproduction scopes distinct: the complete semantic finalizer
  was rerun locally with private inputs; a fresh checkout verified every frozen
  public artifact; and GitHub CI installed exact dependency versions on a new
  Ubuntu runner before repeating tests, claims, privacy, and figure gates. CI did
  not receive private source responses or rerun provider generation.
- Extend the human-labelled dialogue-act criterion with a downstream outcome;
  action agreement is independent of LLM judges but still is not student learning.
- Treat naive prompted student simulation as invalid unless the simulator is
  separately calibrated; the completed 40-history linkage is a negative
  prerequisite-competence result, not learning effectiveness.
- Expand the independently sampled model panel if making population-level or
  family-level claims; six model means cannot support latent-trait correlations.
- Preserve the context-clustered confirmatory estimands and disclose that the
  decision rule was frozen after two judges were partially inspected; it is not
  a preregistration.
- Resolve upstream license and privacy review before releasing any text. The
  code, derived artifacts, manifest, hashes, and exclusion ledger are packaged.
- Apply `research/11_submission_decision_rule.md` without dropping failed
  semantic dimensions or weakening the third-judge reveal thresholds.
