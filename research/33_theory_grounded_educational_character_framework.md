# Theory-grounded dimensions for educational model character

Snapshot: 2026-08-26. Status: **complete literature-grounded framework,
frozen-data audit, and untouched-split confirmation**. This document does not
claim an outcome-blind preregistration and does not use human-like personality
language as an ontological assertion.

## Decision

The prior eight semantic dimensions were a useful first measurement panel, but
they were not organized by a compact theory of educational character. A better
structure is a three-plane, six-axis behavioral framework:

1. **interpersonal style:** instructional agency and relational communion;
2. **instructional policy:** assistance directness and next-step actionability;
3. **epistemic adaptation:** epistemic commitment and learner contingency.

Prompt elasticity is not a seventh content trait. It is a meta-property of every
axis: how far and in what direction a configured model moves when its system
policy changes.

This framework deliberately separates tendencies from competencies. Diagnostic
accuracy, factual correctness, action appropriateness, safety, and learning gain
are validation criteria or consequences, not personality dimensions.

## Why not start from Big Five or HEXACO?

Big Five and HEXACO are useful theories of human personality, but direct LLM
self-assessment has weak construct equivalence. Minor prompt, paraphrase, option
order, and response-format changes can destabilize scores, and a model can state
a trait without behaving accordingly. A behaviorist account of LM character is
more suitable: call something a character trait only when it appears as a
repeated behavioral pattern across situations, then measure whether that pattern
is stationary, interaction-reflective, or prompt-contingent.

Relevant evidence includes:

- [Evaluating Language Model Character Traits](https://aclanthology.org/2024.findings-emnlp.77/),
  which formalizes a behaviorist alternative to anthropomorphic trait claims;
- [You don't need a personality test to know these models are unreliable](https://aclanthology.org/2024.naacl-long.295/)
  and [Do LLMs Have Distinct and Consistent Personality?](https://aclanthology.org/2025.findings-naacl.469/),
  which test prompt, paraphrase, option-order, refusal, content-validity, and
  behavioral-scenario failures of LLM personality instruments; and
- [PersonaLLM](https://aclanthology.org/2024.findings-naacl.229/), which is useful
  evidence that assigned Big Five personas can be expressed, but does not by
  itself establish unassigned cross-task dispositions.

### Framework-selection audit

The six axes are not a renamed version of the original semantic panel. They are
the smallest synthesis that keeps mature educational constructs while removing
three recurring confounds: human self-description, tutor competence, and
learning outcomes.

| Candidate framework | Useful contribution | Why it is not sufficient alone | Role in the final framework |
|---|---|---|---|
| Big Five / HEXACO and persona questionnaires | A vocabulary for human trait differences and a large psychometric literature | Scores depend heavily on item wording, option order, role prompting, and self-report format; behavioral equivalence is unproven | Excluded as the primary measurement model |
| Teacher interpersonal circumplex | A compact, bipolar geometry of agency and communion | Does not describe answer reveal, scaffolding depth, epistemic conduct, or learner adaptation | Supplies the two interpersonal axes |
| Self-determination-theory teaching circumplex | Separates autonomy support, structure, control, and chaos using need support and directiveness | Primarily a theory of teacher motivating style, not a complete tutor-response taxonomy | Clarifies that directiveness is not inherently bad and that structure is not control |
| AI-tutor quality rubrics such as MRBench | Separates guidance, answer reveal, actionability, coherence, tone, and error diagnosis | Mixes behavioral policy, response quality, and correctness in one evaluation space | Supplies observable criteria for directness and structuring; diagnostic accuracy remains competence |
| Tutor-move and scaffolding taxonomies | Orders moves from prompting/hinting to explaining/solving and identifies learner-support moves | Often categorical and turn-local rather than a stable cross-context model profile | Supplies the assistance-directness axis and behavioral anchors for contingency |
| Calibration, abstention, and self-correction benchmarks | Provide non-self-report observables for epistemic behavior | Each also contains a competence component, so tendency and correctness must be separated | Supplies multiple facets of epistemic commitment |
| Educational safety and refusal benchmarks | Can reveal stable boundary-enforcement or over-inclusion behavior | Safety outcomes entangle policy, knowledge, robustness, and scorer effects; different safety tasks need not share one permissiveness axis | Audited as a possible seventh axis and rejected as unidimensional |

This synthesis also explains why a single flat list is misleading. Agency and
communion describe the tutor-learner relationship; directness and actionability
describe how help is delivered; commitment and contingency describe how policy
responds to uncertainty and learner evidence. Correlations across planes are
empirical questions, not reasons to merge the constructs in advance.

### Rejected seventh axis: normative permissiveness

The frozen EduGuard runs permitted a direct test of whether education safety
behavior forms an additional permissive-to-boundary-enforcing character axis.
It does not. Adversarial attack-success propensity is highly stable across five
risk categories (ICC(3,1)=0.806; median pairwise model-rank rho=0.943), and SATA
incorrect-inclusion propensity is separately stable across ten
scenario-by-language contexts (ICC=0.761; rho=0.714). However, their six-model
cross-task Spearman correlation is -0.486, opposite to the prediction that both
are manifestations of one permissiveness trait.

The crossed model profiles make the problem concrete. MiniMax-M2.7 has the
lowest mean adversarial attack-success rate (0.026) but the highest SATA
incorrect-inclusion rate (0.271). DeepSeek-V4-Pro has the highest attack-success
rate (0.545) while its SATA inclusion rate is only 0.183. These outcomes support
task-specific safety-policy signatures, not a seventh general personality axis.
They also mix tendency with competence, and the adversarial scorer is
MiniMax-M3, including when MiniMax-M3 is the candidate. The executable audit is
`scripts/analyze_normative_boundary_axes.py`; aggregate-only results are in
`artifacts/normative_boundary_axes_v1/`.

## The proposed dimensional hierarchy

| Plane | Bipolar axis | Educational interpretation | Closest mature framework | Existing evidence in this repository | Current status |
|---|---|---|---|---|---|
| Interpersonal | **Instructional agency**: learner leads and explains ↔ tutor leads and directs | Who controls the next cognitive move? | Teacher interpersonal circumplex; agency/directiveness axis; SDT teaching circumplex | New four-judge agency scale plus `elicitation`, `autonomy_support`, imperatives, question policy, human tutor acts | Exploratory only. Formal measurement is strong (ICC(3,k)=0.900; minimum judge-profile rho=1.000; cross-task ICC=0.639), but the replacement four-family pilot missed the frozen profile gate (rho 0.657 versus 0.70), and registered transparent anchors miss magnitude. Formal recovery cannot override the pilot failure. |
| Interpersonal | **Relational communion**: distant/transactional ↔ warm/affiliative | Rapport, encouragement, validation, and relatedness | Teacher interpersonal circumplex; communion axis; need-supportive teaching | New communion scale plus `affective_warmth`, praise, encouragement, personalization | Reliably measurable (formal ICC(3,k)=0.945), but not a new cross-task axis. All Socratic candidate profiles collapse to the same centered mean, and formal convergence with `affective_warmth` is rho 0.805, above the fixed 0.80 reducibility boundary. |
| Instructional | **Assistance directness**: prompt/hint ↔ explain/solve | How much of the task remains with the learner? | Assistance dilemma; five-level scaffolding scale; tutor-move engagement spectrum | `help_directness`, answer reveal, explanation, probing/telling | Strongest current axis: reliable, cross-task stable, independently action-anchored, and prompt-responsive. It is the only dimension that passes the full existing disposition chain. |
| Instructional | **Next-step actionability**: vague direction ↔ immediately executable move | Can the learner identify the next operation, its input, and a checkable intermediate output? | SDT structure↔chaos; MRBench guidance/actionability/coherence; scaffolding taxonomies | New four-judge actionability scale, plus `cognitive_load`, response length, and steps | A strong prompt outcome, not a stable model axis. Formal ICC(3,k)=0.871, but minimum judge-profile rho=0.600 and cross-task ICC=-0.111 (median task rho=-0.771). Every judge-family leaveout retains the cross-task failure. |
| Epistemic | **Epistemic commitment**: cautious/revisable ↔ confident/committed | Confidence, willingness to revise, and willingness to abstain | Behaviorist truthfulness/caution; calibration, abstention, and self-correction | `epistemic_caution`, `p07_selfcheck`, `p08_calibration`, `p08_abstention` | Newly promising. Expressed confidence is strongly stable across four sources; answer revision and abstention have mixed stability. The old semantic caution scale fails to converge with expressed confidence and should be replaced rather than promoted. |
| Adaptive | **Learner contingency**: fixed policy ↔ learner-state responsive | Does the policy change when learner evidence changes? | Adaptive teaching, learner modelling, NTO tutoring-support moves | personalization, history reference, learner-request contrasts, LongTutor diagnosis, routing trials | Strong negative boundary. Personalization is not cross-task stable; learner requests fail registered adaptation gates; adaptive presentation does not predict human-gold diagnosis; both tested routing remedies fail. |

The teacher-interaction literature gives the most compact interpersonal basis:
[DITeB](https://doi.org/10.3389/feduc.2024.1397936) represents teacher behavior
on orthogonal **agency** and **communion** axes. The broader
[Situations-in-School circumplex](https://eric.ed.gov/?id=EJ1333957) crosses
need-supportiveness with directiveness to distinguish autonomy support,
structure, control, and chaos. These models are better suited to tutoring
behavior than human intrapsychic inventories because they describe what the
teacher does to and with a learner.

The instructional axes are independently supported by recent AI-tutor work.
[MRBench](https://aclanthology.org/2025.naacl-long.57/) separates mistake
identification, mistake location, answer reveal, guidance, actionability,
coherence, tone, and human-likeness. The 2026
[NTO Tutor Move Taxonomy](https://arxiv.org/abs/2603.05778) separates tutoring
decision support, learning support, social-emotional support, and logistical
support, while placing learning moves on a learner-engagement spectrum. A new
[five-level scaffolding study](https://arxiv.org/abs/2608.22993) distinguishes
Minimal, Prompting, Hinting, Explaining, and Solving and finds that over 95% of
14,637 authentic LLM tutor responses are Explaining or Solving. That result is
direct external convergence for our assistance-directness axis, not evidence
that high assistance improves learning.

## Prompt susceptibility is axis-specific

The paired generic-versus-pedagogy data contain 11,424 scored response units.
After exact-context control, they show that prompt influence is not a uniform
property of a model. The table reports the observed shared prompt movement
relative to the default six-model range, together with the prompt-to-model sum
of-squares ratio. These are fixed-panel descriptive quantities, not population
variance components.

| Proposed axis | Existing proxy | Prompt movement / default model range | Prompt/model SS ratio | Interpretation |
|---|---|---:|---:|---|
| Instructional agency | `autonomy_support`, `elicitation` | 0.79-1.15 | 3.44-7.53 | Highly prompt-sensitive. A system instruction can move the panel about as far as the entire default model spread, while models still differ in elasticity. |
| Assistance directness | `help_directness` | 1.00-1.01 | 5.21-6.68 | Highly prompt-sensitive but not erased: this axis has both a stable default signature and large steering effects. |
| Information structuring | `cognitive_load`; new actionability scale | 0.85-1.11 for load; 0.79-0.86 for actionability | 3.99-5.16 for load | Information amount and next-step actionability are highly steerable, but the new formal panel shows that actionability model rankings reverse across tasks. |
| Relational communion | `affective_warmth` | 0.06-0.16 | 0.01-0.12 | The shared prompt displacement is small relative to default model differences, but significant model-specific elasticity and prompt-sign reversals make a stable communion trait unsupported. |
| Learner contingency | `personalization` plus factorial learner-need contrasts | 0.13 | 0.08-0.12 | Generic/pedagogy wording barely moves personalization, and explicit learner-need contrasts fail. Models follow configured policy much more than learner evidence. |
| Epistemic commitment | objective confidence, revision, abstention | not yet tested with a matched prompt pair | not estimated | Existing data establish cross-context confidence stability, but not its elasticity to epistemic instructions. The failed semantic-caution proxy must not fill this gap. |

There are therefore two different prompt findings. First, prompts can impose a
large common policy shift on directness, agency, and information load. Second,
models retain residual identity across prompt arms: cross-arm model attribution
is 0.297-0.301 against 0.167 chance, and several axes show replicated
model-specific elasticity. The defensible object is consequently a
**prompt-contingent policy response surface** rather than either an immutable
personality or a fully prompt-determined response.

### What the fixed model panel looks like on the supported observables

The table below is deliberately restricted to the two strongest instructional
proxies and the new objective epistemic observables. The first two columns are
generic-arm, exact-item-centered means averaged over the standard and hard
MathDial tasks; positive directness means more answer-giving, and positive load
means more simultaneous information. Prompt deltas are pedagogy minus generic.
They locate a deployed configuration relative to this six-model panel rather
than assigning an intrinsic label to a model family.

| Model | Default information load | Default help directness | Load prompt delta | Directness prompt delta | Expressed confidence | Revision propensity | Unanswerable abstention |
|---|---:|---:|---:|---:|---:|---:|---:|
| DeepSeek-V4-Pro | -0.145 | -0.262 | -0.710 | -1.546 | 0.948 | 0.084 | 0.872 |
| Doubao-Seed-2.0-Pro | 0.163 | 0.048 | -1.088 | -2.096 | 0.977 | 0.019 | 0.832 |
| GLM-5.2 | -0.377 | -0.864 | -0.416 | -0.851 | 0.948 | 0.102 | 0.860 |
| MiniMax-M2.7 | 0.290 | 0.753 | -0.881 | -2.089 | 0.941 | 0.101 | 0.748 |
| MiniMax-M3 | 0.308 | 0.430 | -0.899 | -2.026 | 0.878 | 0.068 | 0.748 |
| Qwen3.5-4B | -0.239 | -0.104 | -0.446 | -1.144 | 0.956 | 0.025 | 0.912 |

Three contrasts are especially informative. MiniMax-M2.7 and M3 are the most
direct and information-dense by default, yet both move strongly toward less
direct and lighter responses under the pedagogy prompt. GLM is already the
least direct default configuration and moves less, so a common prompt narrows
but does not homogenize the panel. In the epistemic plane, Doubao combines the
highest expressed confidence with almost no revision, whereas Qwen combines
high confidence with the highest abstention. These crossed patterns are why
epistemic commitment should remain a small facet profile rather than one
"cautiousness" score.

## Existing-data validation of epistemic commitment

The executable analysis is
`scripts/analyze_epistemic_character_axes.py`. It reads only frozen scored rows
from `p07_selfcheck`, `p08_calibration`, and `p08_abstention`; it never exports a
prompt, response, reasoning trace, gold answer, or item text. Results are in
`artifacts/epistemic_character_axes_v1/`.

### Cross-context stability

| Observable tendency | Contexts | ICC(3,1) | Median pairwise task Spearman | Assessment |
|---|---:|---:|---:|---|
| Expressed confidence | 4 source benchmarks | 0.852 | 0.886 | Robust on both metrics |
| Answer-choice revision propensity | 4 source benchmarks | 0.537 | 0.472 | Mixed: ICC passes, rank gate narrowly misses |
| Abstention propensity on unanswerable items | 5 unanswerable categories | 0.346 | 0.705 | Mixed: median rank passes, ICC fails and the minimum pairwise rho is only 0.087 |

Expressed confidence is therefore a credible new finite-panel behavioral
signature. It is not calibrated confidence: models can report consistently high
confidence while being wrong. The six-model means range from 0.878 for
MiniMax-M3 to 0.977 for Doubao-Seed-2.0-Pro.

Revision and abstention are separable from confidence. GLM-5.2 and MiniMax-M2.7
change their answer choice on about 10% of self-check items, while Doubao and
Qwen change on about 2%. Qwen has the highest unanswerable-item abstention rate
(0.912) despite high expressed confidence (0.956); MiniMax-M3 reports the lowest
confidence but abstains on only 0.748 of unanswerable items. These crossed
profiles argue against compressing epistemic behavior into a single scalar.

The old `epistemic_caution` semantic score is not a substitute. It previously
failed judge reliability (ICC(3,k)=0.580) and cross-task stability
(ICC(3,1)=0.035); its six-model Spearman correlation with expressed confidence
is -0.029. The appropriate conclusion is that the original codebook did not
measure observable epistemic commitment well, not that the objective behaviors
are absent.

### Competence boundary

- Revision propensity is a tendency; fixing a wrong answer and breaking a right
  answer are competence consequences.
- Expressed confidence is a tendency; calibration error and correctness are
  competence consequences.
- Abstention propensity is a tendency; selectively abstaining only when a task is
  genuinely unanswerable is a competence consequence.

This distinction prevents a high-performing model from being called more
"conscientious" merely because it is more accurate.

## What the existing data now supports

1. **Assistance directness** is the strongest established education-character
   axis.
2. **Information load** remains a stable signature but is not structure.
   Direct measurement rejects information sequencing while retaining
   next-step actionability as a separate candidate axis.
3. **Expressed epistemic confidence** is a newly identified, strongly
   cross-source behavioral signature; revision and abstention are mixed but
   clearly nonredundant epistemic facets.
4. **Instructional agency** is prompt-sensitive, bridge-stable, and strong on
   the formal split, but the replacement four-family pilot failure and absent
   transparent grounding lock it to exploratory status.
5. **Relational communion** is reliably measurable but is not a new axis: the
   formal score is reducible to warmth and has no Socratic model variance.
6. **Next-step actionability** moves strongly and uniformly under pedagogy
   prompting, but its default model ordering is judge-sensitive and reverses
   across tasks; steerability is not disposition.
7. **Learner contingency** has a strong negative result: current models express
   stable configured policies more readily than they adapt those policies to
   learner evidence.

## Current confirmation and stopping rule

Do not administer Big Five or HEXACO questionnaires. The highest-value blinded
reannotation has now been run on a pair-preserving pilot of frozen responses.
Agency and communion separated cleanly at the response level; learner
contingency and information sequencing failed their fixed measurement gates;
next-step actionability survived the one permitted scale split. A compact
agency/communion/actionability bridge preserved all three source measurements,
but agency failed the replacement panel's strict cross-judge model-rank gate.

The untouched synthetic formal split is complete: 1,160/1,160 unique judge
calls, four judge families, zero errors. It confirms no additional cross-task
character axis. Communion is reliable but redundant with warmth and lacks
Socratic model variance; actionability is a large shared prompt response but
fails judge-profile and cross-task gates; agency remains exploratory because
the pilot failure is binding. No more wording revisions or same-context judge
panels are permitted. Further generator calls require a new identification
layer—learner outcomes, independently sampled model/provider routes,
learner-evidence interventions, or matched epistemic prompts—not another attempt
to rescue these axes. Learning outcomes remain a separate validation layer
rather than a personality score.

The later archive-only general-personality bridge audit preserves this stopping
rule. It does not add or rescue an educational axis. Across 123,468 eligible
free-form responses, no general behavioral manifestation passes joint non-
tutoring recurrence and default-tutoring transport gates; organizational style
is more stable than the content candidates. Communal expression and dialogic
engagement form a localized future hypothesis, but do not change the six-axis
educational framework or its evidential statuses. See
`research/38_existing_response_general_personality_bridge_results.md`.

A later construct-coverage audit and prospective affiliation pilot do not reopen
the failed educational axes. They identify one cross-domain affiliation behavior
profile that passes limited stability gates but fails self-report and forced-
choice convergence and overlaps strongly with warmth. This extends the same
default-plus-prompt-elasticity framework outside tutoring for one cluster; it
does not add a validated Big Five trait or change the educational-axis statuses.
See `research/42_affiliation_stability_pilot_results.md`.

## Claim boundary

The framework describes observed educational character in the behaviorist sense:
default response tendencies plus prompt and learner contingency. It does not
establish consciousness, human personality, empathy, motivation, or a latent
psychological structure shared with humans. All current model-level estimates
describe six fixed deployed configurations.
