# Related-work relevance and source review

Review date: 2026-09-12. Scope: Section 2 of the integrated English v4 paper,
its bibliography, and its connection to the archived educational evaluations.
This is a targeted literature review, not an exhaustive systematic review.
No experiments or model-provider calls were added.

## Selection and organization

Section 2 now follows three connections: personality measurement and behavioral
consistency; teaching styles and adaptation; educational benchmarks and the
study's starting point. Each source below supports a specific statement.
Repeated summaries of our own methods were shortened. New references add
behavioral validation and instructional-context interventions, rather than
more examples of general role-playing or activation-vector construction.

| Source | Current publication information checked | Role in the revised text | Primary source |
|---|---|---|---|
| Serapio-García et al. | Nature Machine Intelligence 7, 1954–1968, December 2025 | Psychometric measurement and prompting to shape personality expression | https://www.nature.com/articles/s42256-025-01115-6 |
| TRAIT, Lee et al. | Findings NAACL 2025, 8412–8452 | Scenario-based personality assessment | https://aclanthology.org/2025.findings-naacl.469/ |
| The Personality Illusion, Han et al. | ICML 2026 listing; original preprint 2025 | Self-reports need not predict observed behavioral tasks | https://arxiv.org/abs/2509.03730 ; https://icml.cc/Downloads/2026 |
| Rethinking Psychometric Evaluation, Kocielnik et al. | CTB workshop at ICML 2026, not the main conference | Predictive coherence depends on instrument, behavior and conversational context | https://arxiv.org/abs/2606.12730 ; https://openreview.net/pdf/e88056fb9fe8b96e6f986afe1e3d174be5896340.pdf |
| Are Economists Always More Introverted?, Reusens et al. | Findings EMNLP 2025, 11268–11287 | Cross-task consistency of assigned personas | https://aclanthology.org/2025.findings-emnlp.603/ |
| Behavioral Mode Axes, Liu et al. | August 2026 arXiv preprint | Observable behavioral profiles across interaction contexts and activation control | https://arxiv.org/abs/2608.10703 |
| CIMA comparison, Kucheria et al. | BEA 2025, 873–881 | Direct precedent for differences in tutor actions and response complexity | https://aclanthology.org/2025.bea-1.64/ |
| Tutoring System Adaptivity, Borchers and Shou | AIED 2025, LNCS 15878, 407–420 | Removes contextual information to test instructional adaptation | https://link.springer.com/chapter/10.1007/978-3-031-98417-4_29 ; https://arxiv.org/html/2504.05570v1 |
| Tutor-persona steering, Lee et al. | BEA 2026, 78–92 | Learns tutor variation from human dialogue | https://aclanthology.org/2026.bea-1.7/ |
| PATS, Rooein et al. | Findings EACL 2026, 4186–4211 | Student-personality-conditioned strategies, distinct from our focus on models' own tendencies | https://aclanthology.org/2026.findings-eacl.219/ |
| MRBench, Maurya et al. | NAACL 2025, 1234–1251 | Human-annotated pedagogical evaluation dimensions | https://aclanthology.org/2025.naacl-long.57/ |
| MathTutorBench, Macina et al. | EMNLP 2025, 204–221 | Multiple open-ended tutoring capabilities | https://aclanthology.org/2025.emnlp-main.11/ |
| TutorBench, Srinivasa et al. | October 2025 arXiv preprint | Explanations, feedback and hints with example-specific rubrics | https://arxiv.org/html/2510.02663v1 |
| LongTutor, Li et al. | ACL 2026, 29712–29737 | Historical evidence, diagnosis and adaptive teaching | https://aclanthology.org/2026.acl-long.1371/ |

Six references were added: Serapio-García, Han, Kocielnik, Reusens, Borchers,
and Srinivasa. LongTutor was already cited in the appendices and is now
explicitly discussed in Related Work. The PATS DOI was completed.
Conference versions are distinguished from workshop papers and preprints.
No unverified page ranges or proceedings volume were invented for ICML or CTB.
The ICML download list identifies Han's title; the individual poster endpoint
was unavailable, so the reference links to the accessible author preprint.

## Scope decisions

Four previously cited works were removed from Section 2 and the bibliography:
PERSONA, Dynamic Persona Coherence, the Person–Situation–Behavior Triad, and
Personality Expression Across Contexts. They are adjacent background rather
than unrelated papers, but overlap with retained context/steering references.
The revised selection prioritizes direct behavioral validation, educational
context interventions, and the benchmark sources of our investigation.

Additional recent candidates were screened but not added: PTCBENCH uses
contextual personality questionnaires; an LLM-native instrument study focuses
on self-report validity; SafeTutors concerns joint safety/pedagogy; TACT concerns
pedagogical post-training; warmth-training work concerns accuracy and sycophancy.
The retained sources cover the closer connections within the main-page budget.
These exclusions do not imply that the other studies lack scientific value.

Candidate primary pages:

- https://arxiv.org/abs/2602.00016
- https://arxiv.org/abs/2606.09843
- https://arxiv.org/abs/2603.17373
- https://arxiv.org/abs/2608.03952
- https://www.nature.com/articles/s41586-026-10410-0

## Benchmark provenance and claim boundaries

The frozen census at
`artifacts/research_reassessment_20260905/archive_census.json` contains
MRBench, MathTutorBench, TutorBench and LongTutor settings. The adjacent
evaluation repository's benchmark source documentation identifies TutorBench
as the Scale AI benchmark (arXiv:2510.02663), not a similarly named benchmark.
Section 2 credits this evaluation starting point and directs readers to
Appendix B for role and provenance distinctions.

The text does not treat all archive records as tutoring, all benchmark scores
as personality labels, or all records as independent samples. It does not
claim to introduce these benchmarks. It also avoids claiming that previous
work studied only accuracy: these benchmarks already assess pedagogical
quality and model-specific strengths. Our additional question is when
observed teaching tendencies predict new responses and how instructions
reshape them. Behavioral forecasts are distinct from the self-report
prediction studies cited in the first paragraph.

## Retrieval and validation

Primary publisher/author pages and relevant method sections were used for
claim checks. Exa and the skill update check were unavailable due to DNS
resolution; the available web tool provided the primary-source checks.
Original literature and removed references remain in the pre-revision backup
and Git history. Final build, citation and layout checks are recorded in
`paper/educational_personality_v4/final_review.json`.
