# Literature map and research gap

Snapshot date: 2026-08-20.  This is a living map; it records claims supported by
primary paper pages rather than relying on secondary summaries.

## 1. Why a questionnaire paper is not enough

- PersonaLLM shows that prompted GPT-3.5/GPT-4 personas can reproduce designated
  Big Five profiles in questionnaires and stories.  This establishes
  *expressibility*, not stable default behavior in deployed tasks.
  [Jiang et al., NAACL Findings 2024](https://aclanthology.org/2024.findings-naacl.229/)
- TRAIT expands human personality inventories into 8K scenario questions and
  reports improved reliability and validity.  It remains an elicited test rather
  than a study of naturally produced domain behavior.
  [Lee et al., NAACL Findings 2025](https://aclanthology.org/2025.findings-naacl.469/)
- Minor option-order and negation perturbations substantially reduce psychometric
  consistency, showing that questionnaire answers are prompt-fragile.
  [Shu et al., NAACL 2024](https://aclanthology.org/2024.naacl-long.295/)
- A 2026 psychometric audit of 244 models finds that model identity explains only
  3% of Big Five score variance and four factors collapse into one highly
  correlated, socially desirable direction.  The authors conclude that the
  construct is not equivalent to human personality.
  [Zierahn et al., 2026](https://arxiv.org/abs/2603.19030)
- Direct behavioral tests reveal a self-report--behavior dissociation: alignment
  stabilizes questionnaire profiles, but those profiles do not reliably predict
  behavior, and persona injection moves self-reports more consistently than it
  moves behavior.
  [Han et al., 2025](https://arxiv.org/abs/2509.03730)
- The failure is not fixed simply by inventing LLM-native questionnaire factors.
  Across 25 models, five internally reliable self-report factors mostly fail to
  predict 2,500 open-ended behaviors rated by humans; critically, one factor
  correlates with LLM judges but not humans, exposing shared source variance that
  judge-ensemble reliability does not detect.
  [Contreras, 2026](https://arxiv.org/abs/2606.09843)
- Coherence can be recovered selectively when the probe targets a specific
  behavior and shares an appropriate context, but it collapses for broad Big Five
  traits and strongly context-primed behavior.  This motivates task-specific
  constructs and explicit cross-context validation.
  [Kocielnik et al., 2026](https://arxiv.org/abs/2606.12730)
- GenPT replaces fixed questionnaires with newly generated projective stimuli
  and a behavior-collection → interpretation → diagnosis pipeline.  It reduces
  some contamination and social-desirability threats, but still elicits behavior
  inside a purpose-built psychometric instrument rather than observing repeated
  behavior in an external application domain.
  [Wang et al., ACL 2026](https://aclanthology.org/2026.acl-long.1901/)
- A cross-task consistency framework assigns personas and tests them across
  surveys, essays, social posts, and single-/multi-turn dialogue. This is the
  closest personality-side precedent for cross-task recurrence, but it studies
  prompted personas rather than unassigned defaults in a consequential domain.
  [Reusens et al., Findings EMNLP 2025](https://aclanthology.org/2025.findings-emnlp.603/)

**Consequence for this project:** human personality tests are a deliberately
excluded primary endpoint.  We infer domain-specific dispositions from behavior,
then test whether they predict held-out behavior.  LLM-judge consensus is also
insufficient on its own: objective text measures, pre-existing benchmark outcomes,
judge swaps, negative controls, and eventually a non-LLM criterion must be kept as
separate sources of evidence.

## 2. What educational benchmarks already measure

- MRBench supplies 192 conversations, 1,596 tutor replies, and eight
  learning-science-grounded dimensions.  It evaluates pedagogical quality but does
  not estimate cross-task latent dispositions of tutor models.
  [Maurya et al., NAACL 2025](https://aclanthology.org/2025.naacl-long.57/)
- MathTutorBench combines multiple open-ended tutoring capabilities and reports
  that subject-solving expertise does not automatically imply good teaching.
  [Macina et al., EMNLP 2025](https://aclanthology.org/2025.emnlp-main.11/)
- MathDial formalizes teacher moves and the trade-off between learner opportunity
  and revealing solutions too early.
  [Macina et al., EMNLP Findings 2023](https://aclanthology.org/2023.findings-emnlp.372/)
- LongTutor evaluates the progression from historical evidence to knowledge-state
  diagnosis and adaptive teaching on expert-annotated real learning logs.  Its
  original experiments identify a mismatch between strong evidence acquisition
  and weaker diagnosis/teaching.  Our use is not to re-claim that benchmark
  finding, but to test an additional cross-task question: whether adaptive-
  teaching scores predict exact human-gold diagnosis for the same model and
  history after history difficulty is controlled.
  [Li et al., ACL 2026](https://aclanthology.org/2026.acl-long.1371/)
- Recent real-world analysis warns that benchmark-preferred scaffolding can fail
  when students do not take it up; scaffolding must be studied jointly with
  learner goals and interaction context.
  [Neagu et al., 2026](https://arxiv.org/abs/2606.15766)
- Tutor-persona steering work learns preference directions for scaffolding,
  directiveness, feedback, and affective support from human dialogues.  Its goal
  is behavioral control, whereas our first question is whether unprompted models
  possess stable cross-task differences and whether such differences are
  consequential.
  [Letting Tutor Personas Speak Up, 2026](https://arxiv.org/abs/2602.07639)
- PATS maps teaching strategies to *student* Big Five profiles and evaluates
  personality-aware simulated tutoring with human teachers. It is important
  adjacent work, but its personality construct belongs to the learner and its
  target is adaptation, not recurring default differences among tutor models.
  [Rooein et al., Findings EACL 2026](https://aclanthology.org/2026.findings-eacl.219/)
- Pedagogical Alignment and StratL already establish that predefined scaffolding
  policies can be trained or induced. Therefore, this project cannot claim to
  introduce pedagogical steering; its distinct question is measurement and
  construct validity of defaults, followed by component-selectivity tests.
  [Sonkar et al., Findings EMNLP 2024](https://aclanthology.org/2024.findings-emnlp.797/)
  [Puech et al., Findings ACL 2025](https://aclanthology.org/2025.findings-acl.1348/)
- ScaffoldLM and MHPO further show that learner-state memory, explicit planning,
  and trajectory-level optimization can improve a desired tutoring policy. They
  strengthen the boundary: our novelty is auditing naturally recurring defaults
  and their construct validity, not inventing a better control architecture.
  [ScaffoldLM, ACL 2026](https://aclanthology.org/2026.acl-long.325/)
  [MHPO, ACL 2026](https://aclanthology.org/2026.acl-long.518/)
- Context-ablation experiments on 75 real ITS scenarios show that three LLMs
  only marginally reproduce ITS adaptivity; a validated tutor-training
  classifier also identifies overly direct feedback.  This is a close study of
  learner-context sensitivity, but not a cross-model estimate of recurring
  default policies with generic fingerprint controls.
  [Borchers and Shou, 2025](https://arxiv.org/abs/2504.05570)
- PedRAG names a related declared-versus-enacted failure as *behavioral
  hallucination* and uses runtime theory retrieval to constrain Socratic
  behavior.  Its 144-session evaluation is a multi-agent simulation and its
  simulated mastery endpoint is not human learning evidence.
  [Nkambou et al., EDM 2026](https://educationaldatamining.org/edm2026/proceedings/2026.EDM.poster-demo-papers.368/)
- ACL 2026 work directly studies answer leakage under six adversarial and
  persuasive attack groups, multi-turn student agents, multiple tutor families,
  and tutor-side defenses. SHAPE independently formalizes answer-inducing
  pressure as a pedagogical jailbreak. These papers preclude novelty claims
  about answer-withholding conflict itself; our narrower addition is to place a
  non-adversarial learner request inside a complete question × answer × tone
  factorial and quantify both target and cross-effects.
  [Zhao et al., ACL 2026](https://aclanthology.org/2026.acl-long.1412/)
  [SHAPE, ACL 2026](https://aclanthology.org/2026.acl-long.529/)
- An in-situ audit of 12,650 messages across 500 conversations finds that
  deployment context outweighs system design or stated preference in predicting
  usage patterns, with answer extraction common. This is stronger ecological
  evidence than benchmark responses and requires us to keep deployment behavior
  and learner outcomes outside the present claim boundary.
  [Kobler et al., ACL 2026](https://aclanthology.org/2026.acl-long.875/)
- A preregistered three-base audit finds that general helpfulness judgments are
  judge-contingent even when targeted pedagogy contrasts persist, and recommends
  pairing targeted rubrics with deterministic process measures. This directly
  supports our measurement design but precludes presenting the general critique
  of aggregate LLM judging as novel.
  [Fan et al., 2026](https://arxiv.org/abs/2607.28128)
- A deployed Socratic supervisor enforces answer withholding with a deterministic
  help ceiling, LLM audit, and scripted personas. It explicitly does not claim
  learning outcomes. Our answer-policy result is therefore a comparative
  measurement and request-conflict result, not a first withholding mechanism.
  [Pisan, 2026](https://arxiv.org/abs/2608.12292)

### Why a prompted simulated student is not yet an outcome measure

- A large ACL 2026 audit formally evaluates simulated students along linguistic,
  behavioral, and cognitive axes.  Simple prompting performs poorly under both
  automated and human evaluation; supervised fine-tuning and preference
  optimization improve but still do not solve the problem.  A naive external-API
  student loop would therefore add apparent scale without credible learning
  validity.
  [Scarlatos et al., ACL 2026](https://aclanthology.org/2026.acl-long.1960/)
- Turn-level tutoring verifiers operationalize a more objective post-test in code
  tutoring through Recall@k and Pass@k before and after dialogue, and test more
  than one simulator.  This is a useful future design pattern, but it still relies
  on simulator fidelity and does not directly transfer to the current math data.
  [Training Turn-by-Turn Verifiers, ACL Findings 2025](https://aclanthology.org/2025.findings-acl.642/)
- Knowledge-graph-derived logic benchmarks provide objective error states and
  reveal a diagnostic-action gap: correct diagnosis does not reliably yield
  actionable feedback.  This motivates linking disposition measures separately
  to diagnosis and instructional action rather than collapsing both into one
  quality score.
  [Yasir et al., BEA 2026](https://aclanthology.org/2026.bea-1.56/)

**Consequence for this project:** do not rush a zero-shot simulated-student claim.
Use the existing LongTutor human-gold diagnosis and historical-evidence tasks as
independent prerequisite-competence criteria, while keeping real learning gain as
an explicit future requirement.

## 3. Why model attribution is not a disposition result

- Simple lexical and part-of-speech features can identify generator models across
  domains, and related models can retain family-level fingerprints.  Therefore,
  above-chance model attribution is an expected negative control rather than
  construct validity for pedagogical dispositions.
  [McGovern et al., GenAIDetect 2025](https://aclanthology.org/2025.genaidetect-1.6/)

Our own analysis mirrors this warning: model attribution is stronger on generic
negative-control tasks than on teaching tasks, while the geometry of policy
features is not strongly shared across those domains.  The paper must treat broad
fingerprinting as a confound to remove, not as its headline discovery.

## 4. Candidate contribution

The defensible gap is not “LLMs have Big Five personalities.”  It is:

> Existing work either elicits traits or projective behavior inside an instrument,
> detects broad generator fingerprints, evaluates tutor quality/adaptivity in a
> bounded benchmark, or steers a predefined tutoring persona.  We lack an
> application-behavior-first, psychometrically audited
> account of whether model-specific pedagogical policies persist across authentic
> tasks *after general model fingerprints are controlled*, predict independently
> measured educational actions, and respond causally to the same intervention.

The EduBenchmark panel uniquely supports this because the same items and harness
were used for multiple current model families.  The paired scaffolding versus
explicit-pedagogy prompt arms also provide a within-model, within-item
intervention, separating baseline disposition from steerability.

## 5. Non-overclaiming boundary

Even a highly stable model signature is not sufficient evidence of personality:
lexical habits, output length, provider templates, or instruction-following can
make model attribution easy.  The paper must therefore report three nested
objects:

1. **surface fingerprint** (lexical/morphosyntactic authorship cues),
2. **pedagogical policy signature** (interpretable teaching actions after surface
   controls), and
3. **validated disposition** (only dimensions that generalize, predict external
   criteria, and move under intervention).

## 6. Prompt-contingency update (2026-08-26)

Three adjacent findings sharpen the gap. Gupta et al. (BlackboxNLP 2024) show
that semantically equivalent prompts and option ordering destabilize LLM
personality-test scores, so self-report stability cannot be assumed. Kucheria et
al. (BEA 2025) find model-specific action and complexity patterns among three LLM
tutors, establishing direct educational precedent for baseline differences. The
Pedagogical Suitability Index study (arXiv:2608.05411; IEEE IRI 2026) reports an
almost unchanged aggregate score across standard versus defective student
prompts while subscores trade off, reinforcing the danger of aggregate masking.

The remaining gap is therefore not “do tutor models ever differ?” It is whether
the same fixed model panel supports a joint decomposition into default policy,
shared prompt displacement, and model-specific elasticity after task transfer,
generic-fingerprint controls, and bounded-scale sensitivity. The completed
secondary analysis in `research/32_prompt_contingent_policy_signature_results.md`
addresses that gap without upgrading the human-personality or disposition claim.

The completed theory-grounded extension in
`research/33_theory_grounded_educational_character_framework.md` and
`research/36_confirmatory_character_results.md` addresses the remaining
dimension-selection objection. It replaces Big Five self-report with teacher
interpersonal agency/communion, scaffolding directness/actionability,
epistemic-behavior, and learner-contingency axes. Its untouched four-family
judge split finds no additional validated axis: the contribution is a
construct-boundary map plus direct evidence that a large prompt response can
coexist with unstable cross-task model ordering.

Primary records:

- https://aclanthology.org/2024.blackboxnlp-1.20/
- https://aclanthology.org/2025.bea-1.64/
- https://arxiv.org/abs/2608.05411
