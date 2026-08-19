# Working paper outline

## Candidate title

**Beyond Personality and Fingerprints: Behavioral Evidence for Pedagogical Policy Signatures in AI Tutors**

## Provisional abstract

Claims that language models possess stable “personalities” are increasingly
challenged by prompt-fragile questionnaires and self-report--behavior gaps.  We
instead study pedagogical policy signatures: recurring, domain-specific actions
in authentic tutoring responses.  We audit 31,638 paired responses from six
models across six teaching arms, 57,516 negative-control responses, and an
extended nine-model, 26,586-response intervention panel.  Transparent policy
features identify models across held-out teaching families (0.242 accuracy versus
0.167 chance), but generic tasks yield stronger attribution, demonstrating that
model fingerprinting alone is not construct validity.  A within-item explicit
pedagogy intervention causes all nine models to ask more questions and produce
shorter turns, while contracting cross-model policy dispersion by 23.7%.  A
traditional classifier trained on 18,541 human-labelled teacher turns finds that
the intervention improves human next-action match for every model under three
measurement variants, yet sharply reduces match when the human teacher chose
direct `telling`—evidence of contextual oversteering.  On 14,770 identical
responses scored by two judge models, quadratic agreement is 0.810 and the causal
quality gain replicates.  On a distinct 482-pair expert preference calibration,
three planned semantic judges achieve 0.817--0.844 agreement and 0.900--0.919
position consistency, although their majority does not improve on the best judge.
In leave-one-model-out prediction with exact item fixed
effects, policy features improve tutoring-quality AUC by 0.023--0.031 over an item
baseline, whereas length adds only 0.002.  These results support stable and
steerable pedagogical policy signatures, not human-like personality, and reveal a
cost of one-size-fits-all tutoring prompts.  Blinded semantic and downstream-
learning validation remain required before this abstract is submission-ready.

## Research questions

1. Which response tendencies are stable across authentic teaching tasks after
   controlling the item and response length?
2. Which tendencies are tutoring-specific rather than generic model fingerprints?
3. Do those tendencies predict educational quality for a model never used to fit
   the predictor?
4. Does the same pedagogical instruction move different models in a shared
   direction, make them converge, or expose heterogeneous steerability?
5. Are conclusions robust to judge model, measurement route, and candidate--judge
   family overlap?

## Main figures

1. **Conceptual decomposition:** surface fingerprint → pedagogical policy
   signature → validated disposition, with the required test at each transition.
2. **Cross-task versus cross-domain attribution:** teaching and negative-control
   feature sets, emphasizing that attribution is not the endpoint.
3. **Causal prompt map:** nine-model baseline profiles, treatment vectors, and the
   0.763 dispersion ratio with item bootstrap interval.
4. **Incremental validity:** leave-one-model-out AUC for item baseline, +length,
   and +policy under both judges; show every model fold rather than only the mean.
5. **Judge robustness:** agreement distribution and paired prompt gains for
   MiniMax-M3 and DeepSeek-v4-flash, plus expert-preference and position-order
   calibration for all three planned semantic judges.
6. **Human-action validity:** three classifier variants, 54/54 positive overall
   prompt contrasts, and the telling-action collapse.
7. **Semantic validation (pending):** dimension reliability, task generalization,
   intervention movement, and leave-judge-out/self-family sensitivity.

## Confirmatory statistical spine

- Unit declarations: response, context, model, and judge are never interchangeable.
- Stable signature: within-item centering; task-family-held-out prediction;
  model-by-task variance with cluster bootstrap.
- Discriminant validity: negative-domain transfer and incremental prediction after
  negative-domain profiles.
- Consequential validity: leave-one-model-out outcome prediction with benchmark
  and exact-item fixed effects; compare nested models on AUC, Brier score, and
  calibration.
- Intervention: paired context effects, model × treatment heterogeneity, and
  context-cluster bootstrap; no pseudo-replication across six responses to one
  context.
- Judge audit: item agreement, rank agreement, judge × candidate-family effects,
  and leave-one-judge-out conclusions.
- Multiplicity: preregister primary semantic dimensions and use Holm or hierarchical
  testing; exploratory endpoints remain visibly labeled.

## Scope and nonclaims

- No claim that language models possess human Big Five personality.
- No population-of-models conclusion from six model means.
- No causal model-family or scale conclusion from the four approximate named pairs.
- No claim that judge agreement proves human or behavioral validity.
- No release of upstream text until its license and privacy status are resolved.

## Target positioning

The current empirical core is plausible for ACL/EMNLP/NAACL main-conference review
if the pending semantic and independent-criterion tests succeed.  A Nature-family
or similarly broad journal claim would additionally require externally meaningful
learning outcomes, a substantially larger and version-controlled model panel, and
preferably prospective student interaction evidence.  Dataset volume alone does
not bridge that gap.
