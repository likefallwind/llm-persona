# Novelty positioning against the closest work

Snapshot: 2026-08-19.

| Work | Primary object | Naturally generated task behavior | Same-model cross-task test | Generic-fingerprint control | Paired causal steering | Independent behavioral / gold criterion |
|---|---|---:|---:|---:|---:|---:|
| PersonaLLM (NAACL Findings 2024) | Prompted Big Five personas | Partial (story writing after persona assignment) | No | No | Persona manipulation, not identical-item tutoring | Human perception of generated stories |
| TRAIT (NAACL Findings 2025) | Scenario-based personality inventory | No | No | No | Prompt sensitivity only | Psychometric reliability/validity |
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
| Student deployment audit (ACL 2026) | Intended-vs-actual student use | Yes: 500 deployed conversations | Four courses | Not applicable | No | Six validated dialogue metrics |
| PedRAG (EDM 2026 poster) | Theory-grounded runtime behavioral fidelity | Simulated multi-agent sessions | Within-session drift | No | Runtime retrieval vs prompt-only | Theory rubric; simulated mastery only |
| LongTutor (ACL 2026) | Long-history evidence → diagnosis → teaching | Yes | Three progressive tasks | No | No | Expert-annotated diagnosis and teaching references |
| **This study** | Model-conditioned pedagogical policy signatures | **Yes: 31,638 paired teaching responses** | **Yes: held-out teaching families** | **Yes: 57,516 non-tutoring responses** | **Yes: identical MathDial contexts, nine models** | **Existing human actions, expert preference calibration, human-gold diagnosis** |

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

There are now three closest-work fronts. *Letting Tutor Personas Speak Up* learns
how to steer one model toward variation embedded in human tutor dialogues.
StratL and Pedagogical Alignment optimize a predefined teaching policy. SHAPE
and Answer Leakage Robustness test withholding under adversarial student
pressure. Our question is narrower and orthogonal: do multiple deployed model
systems exhibit stable default policy differences across tasks, which parts are
merely stylometric, and what target and cross-effects appear when common policy
components are manipulated? The strongest comparative result is not better
steering or jailbreak defense, but the conjunction of cross-domain falsification,
same-item intervention, component-selectivity gates, and the telling-action
failure.

The prospective factorial protocol now pins routes, models, prompts, decoding,
deterministic metrics, and claim gates before outcome inspection. Future
population claims still require at least 14--20 versioned systems across open and
closed families on the same frozen contexts.
