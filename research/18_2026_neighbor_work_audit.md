# 2025--2026 closest-work audit

Snapshot: 2026-08-19. Sources below are official ACL Anthology records or the
paper's primary preprint. This audit was completed while the prospective
factorial panel was still collecting and before its outcomes were inspected.

## What is already claimed

| Work | Evidence object and scale | What it establishes | Boundary relative to this study |
|---|---|---|---|
| Pedagogical Alignment (Findings EMNLP 2024) | Synthetic preferences; Llama and Mistral alignment experiments | Preference learning can shift scaffolding versus direct-answer behavior | Trains a predefined binary objective; does not estimate naturally recurring policies across deployed systems or separate them from generator fingerprints |
| Pedagogical Steering / StratL (Findings ACL 2025) | Prompt optimization for a productive-failure transition graph; field study with 17 Singapore high-school students | A multi-turn tutoring plan can be induced and followed in a real setting | Optimizes one desired plan; does not test multiple default policy dimensions, cross-task recurrence, or component selectivity |
| Prompt-Moderated Math Tutoring (Findings EMNLP 2025) | Three-phase tertiary study with 49 students | Prompt moderation can change interaction and performance, including a negative moderated-versus-unmoderated result | Provides learner evidence absent here, but does not conduct a multi-model construct-validity audit of default tutor policies |
| Tutor Personas Speak Up (BEA 2026) | Human tutor-dialogue preferences and activation steering | Tutor-specific scaffolding, directiveness, feedback, and affective-support variation can be learned and controlled | Learns target variation from human tutors; our archive asks whether deployed model systems already exhibit recurring defaults and which signals survive fingerprint controls |
| PATS (Findings EACL 2026) | A teaching-strategy-to-student-personality taxonomy, simulated dialogues, and human-teacher preferences | Tutors can condition strategies on simulated student personality profiles | The personality belongs to the learner, not the tutor model; it studies personalization, not model-conditioned default policies |
| SHAPE (ACL 2026) | 9,087 student-question pairs and two pedagogical-jailbreak settings | Safety, helpfulness, and pedagogy can be jointly evaluated and improved under answer-inducing pressure | Treats answer extraction as an adversarial safety problem; does not factor question, answer, and tone policies or test cross-task default recurrence |
| Answer Leakage Robustness (ACL 2026) | 240 GSM8K evaluation problems, six attack groups, multi-turn student agents, multiple tutor families and defenses | Tutor answer-withholding is fragile under strategic student pressure | Directly overlaps the learner-request/withholding contrast, so this study cannot claim to introduce that problem; our distinct test is non-adversarial request conflict inside a complete three-policy factorial plus archived cross-task measurement |
| Your Students Don't Use LLMs Like You Wish They Did (ACL 2026) | 12,650 messages in 500 conversations across four courses | Deployment context can dominate intended tutor design and students often seek answers | Stronger ecological evidence about student use; our archive is broad across models/tasks but is not an in-situ learner-use study |
| Rethinking Scaffolding (ICML 2026 workshop preprint) | 9,490 chats across nine benchmark and deployment datasets | Benchmark-preferred scaffolding and actual student uptake can diverge | Reinforces that question asking or withholding is not universally beneficial and that our action-matching results must not be called learning gains |
| IHEval (NAACL 2025) | 3,538 examples across nine aligned/conflicting instruction tasks | Models struggle to follow priority when system and lower-priority instructions conflict | Makes instruction hierarchy the correct construct for the learner-request contrast; system-over-user behavior is not evidence of personality, empathy, or pedagogical appropriateness |

Primary records:

- [Sonkar et al., 2024](https://aclanthology.org/2024.findings-emnlp.797/)
- [Puech et al., 2025](https://aclanthology.org/2025.findings-acl.1348/)
- [Steindl et al., 2025](https://aclanthology.org/2025.findings-emnlp.605/)
- [Lee et al., 2026](https://aclanthology.org/2026.bea-1.7/)
- [Rooein et al., 2026](https://aclanthology.org/2026.findings-eacl.219/)
- [Zhao et al., SHAPE, 2026](https://aclanthology.org/2026.acl-long.529/)
- [Zhao et al., Answer Leakage, 2026](https://aclanthology.org/2026.acl-long.1412/)
- [Kobler et al., 2026](https://aclanthology.org/2026.acl-long.875/)
- [Neagu et al., 2026](https://arxiv.org/abs/2606.15766)
- [Zhang et al., IHEval, 2025](https://aclanthology.org/2025.naacl-long.425/)

## Revised novelty boundary

The study must not claim any of the following:

1. first pedagogical steering or pedagogical alignment method;
2. first tutor-persona or personality-aware tutoring study;
3. first answer-withholding or pedagogical-jailbreak evaluation;
4. first analysis of real educational dialogue behavior; or
5. evidence that scaffolding, warmth, or withholding improves learning.

The defensible contribution is the conjunction of evidence that no closest work
currently supplies: repeated naturally generated outputs from a shared
multi-model deployment harness; held-out educational-family recurrence; a large
generic-domain generator-fingerprint negative control; same-item policy
intervention; independent human actions and human-gold diagnosis boundaries;
and a prospectively frozen three-component factorial that reports target and
cross-effects rather than treating a bundled prompt as a scalar treatment.

## Mandatory interpretation tests for the factorial result

- Compare answer-policy results directly with SHAPE and Answer Leakage
  Robustness; do not rename ordinary request conflict as a novel jailbreak.
- Interpret positive system-over-user effects as instruction-hierarchy behavior,
  following IHEval rather than as empathy, learner understanding, or pedagogical
  benefit.
- Interpret learner-request responsiveness jointly with the real-deployment
  findings: blindly preserving scaffolding can itself be a mismatch.
- If factor selectivity fails, report bundled controllability and remove any
  component-level controllability claim.
- If selectivity succeeds, claim only black-box instruction addressability on
  the five frozen deployed systems and 32 synthetic contexts.
- Keep real learning outcomes as an unmet requirement even if every compliance
  gate passes.
