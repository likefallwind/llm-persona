# Novelty positioning against the closest work

Snapshot: 2026-08-20.

| Work | Primary object | Naturally generated task behavior | Same-model cross-task test | Generic-fingerprint control | Paired causal steering | Independent behavioral / gold criterion |
|---|---|---:|---:|---:|---:|---:|
| PersonaLLM (NAACL Findings 2024) | Prompted Big Five personas | Partial (story writing after persona assignment) | No | No | Persona manipulation, not identical-item tutoring | Human perception of generated stories |
| TRAIT (NAACL Findings 2025) | Scenario-based personality inventory | No | No | No | Prompt sensitivity only | Psychometric reliability/validity |
| Persona consistency (Findings EMNLP 2025) | Assigned-persona consistency across tasks and runs | Prompted behavior | Yes, across elicitation formats | No | Persona assignment | Internal consistency and judge inference |
| GenPT (ACL 2026) | Generative projective psychometrics | Elicited projective behavior | Context sensitivity, not external task families | Social-desirability controls, not generator fingerprints | Context/persona framing | SCORS-G/SRAS interpretation pipeline |
| MRBench (NAACL 2025) | Tutor response quality taxonomy | Yes, within benchmark | No | No | No | Human labels on eight dimensions |
| MathTutorBench (EMNLP 2025) | Open-ended tutor capability | Yes | Multiple benchmark components | No generator-fingerprint control | Some prompt/benchmark contrasts | Reward-model and benchmark criteria |
| Borchers & Shou (2025) | ITS learner-context adaptivity | Yes: 75 ITS scenarios | Context ablation, not default cross-task recurrence | No | Yes: remove context fields | Validated tutor-training classifier |
| Pedagogical Alignment (Findings EMNLP 2024) | Trained scaffold-vs-answer preference | Synthetic training behavior | No | No | Training intervention, not same-item prompting | Synthetic preferences and perplexity metrics |
| StratL (Findings ACL 2025) | Productive-failure tutoring-plan steering | Field prototype | One multi-turn strategy | No | Prompt optimization | Field study with 17 students |
| Tutor Personas Speak Up (BEA 2026) | Tutor-specific activation steering | Human-dialogue-derived target personas | Dialogue contexts, not broad task families | Lexical preservation, not negative domains | Yes, learned steering vector | Ground-truth utterance alignment and preference |
| PATS (Findings EACL 2026) | Strategy adaptation to student personality | Simulated dialogues grounded by a classroom case | Two educational tasks | No | Personality-conditioned prompting | Human-teacher and LLM preferences |
| SHAPE (ACL 2026) | Pedagogical-jailbreak safety/helpfulness | Synthetic benchmark pairs | Knowledge-graph contexts | No | Graph-gated generation | Attack robustness and helpfulness |
| Answer Leakage Robustness (ACL 2026) | Withholding under adversarial student pressure | Multi-turn simulated attacks | Math plus selected transfer domains | No | Tutor prompts and defenses | Rule filter plus calibrated LLM judge |
| Helpfulness-as-pedagogy audit (arXiv 2026) | Validity of generic helpfulness judging | Fixed simulated student, three tutor bases | Within controlled dialogue phases | No | Conversational vs pedagogical policies | Two frozen judges plus deterministic process measures |
| Socratic withholding supervisor (arXiv 2026) | Deployed help-ceiling enforcement | Scripted personas through a live system | Course-specific deployment | Not applicable | Policy core, detector, and judge | Four compliance gates; no learning outcome |
| Student deployment audit (ACL 2026) | Intended-vs-actual student use | Yes: 500 deployed conversations | Four courses | Not applicable | No | Six validated dialogue metrics |
| PedRAG (EDM 2026 poster) | Theory-grounded runtime behavioral fidelity | Simulated multi-agent sessions | Within-session drift | No | Runtime retrieval vs prompt-only | Theory rubric; simulated mastery only |
| LongTutor (ACL 2026) | Long-history evidence → diagnosis → teaching | Yes | Three progressive tasks | No | No | Expert-annotated diagnosis and teaching references |
| Strategize Before Teaching (Findings EACL 2023) | Joint strategy prediction and tutor-response generation | Tutoring corpora | Three dialogue datasets | No | Learned joint selector/generator | Tutor-strategy labels |
| Tutor CoPilot (arXiv 2025 revision) | Human-selected expert strategy → LM guidance | Yes: live tutoring | Live K--12 platform | Not applicable | Human selects from strategy options | Preregistered learner mastery outcome |
| SLOW (arXiv 2026) | Learner-state reasoning → action selection | Simulated/evaluated tutoring | Within framework | No | Modular workspace and selector | Hybrid human--AI judgments |
| **This study** | Model-conditioned pedagogical policy signatures | **Yes: 31,638 paired teaching responses plus 4,320 prospective action-control responses** | **Yes: held-out teaching families** | **Yes: 57,516 non-tutoring responses** | **Yes: identical MathDial contexts, concurrent baselines** | **Existing human actions, expert preference calibration, human-gold diagnosis** |

## The actual novelty claim

The project should not claim to invent tutor dimensions, tutor personas, or AI-
tutor evaluation.  Its novel combination is the *construct-validity audit* of
default model behavior:

1. distinguish a broad generator fingerprint from a tutoring-specific policy;
2. estimate recurrence on unseen educational task families using a paired panel;
3. perturb the same context and model with a shared instruction to measure
   steerability and policy convergence;
4. test whether an aggregate improvement hides action-specific harm;
5. audit evaluator competence, position, and candidate-family overlap; and
6. require convergence with existing human actions and human-gold diagnosis
   rather than LLM-judge agreement alone.

This package is stronger than a “models have personalities” paper because its
negative controls can falsify the disposition interpretation.  It is also
distinct from a benchmark paper: the outcome is a theory and measurement audit of
model-conditioned tutor policies across already-generated tasks.

## Anticipated reviewer comparison

There are now four closest-work fronts. *Letting Tutor Personas Speak Up* learns
how to steer one model toward variation embedded in human tutor dialogues.
StratL, ScaffoldLM, MHPO, and Pedagogical Alignment optimize a predefined
teaching policy. SHAPE, Answer Leakage Robustness, and the Socratic supervisor
test or enforce withholding under student pressure. The preregistered
helpfulness audit independently establishes that aggregate judge scores can be
invalid pedagogy signals. Our question is narrower and orthogonal: do multiple deployed model
systems exhibit stable default policy differences across tasks, which parts are
merely stylometric, and what target and cross-effects appear when common policy
components are manipulated? The strongest comparative result is not better
steering or jailbreak defense, but the conjunction of cross-domain falsification,
same-item intervention, component-selectivity gates, and the telling-action
failure.

The prospective routing extension must be positioned as a falsification, not a
controller contribution. Two-stage strategy selection and modular
learner-state/action architectures are prior art. The new evidence is that two
independently worded binary selectors perform near chance and significantly
worse than a concurrently rerun single-pass policy on the same contexts, while
counterfactual ASK/EXPLAIN executors realize the requested action almost
perfectly. That same-serving-period decomposition directly identifies a
selection--execution gap and shows that naive modularization can amplify the
policy anchoring it is intended to correct.

The prospective factorial protocol now pins routes, models, prompts, decoding,
deterministic metrics, and claim gates before outcome inspection. Future
population claims still require at least 14--20 versioned systems across open and
closed families on the same frozen contexts.
