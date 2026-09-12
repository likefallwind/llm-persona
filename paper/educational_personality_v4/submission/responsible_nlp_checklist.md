# Responsible NLP checklist: evidence-linked draft

11 September 2026. Author-facing preparation only. Use the [current ARR form and guidance](https://aclrollingreview.org/responsibleNLPresearch/) when the cycle opens. These are proposed answers, not submitted declarations. A “No” with an accurate explanation is preferable to an unsupported “Yes”.

| Field | Proposed answer and paper evidence |
|---|---|
| A1 Limitations | Yes — Limitations: settings/deployments, automated measurement, coverage of teaching tendencies |
| A2 Risks | Yes — Ethical Considerations; §7; Appendix B.2: overgeneralization, unwarranted educational interpretation, secondary-data privacy |
| B Artifacts | Yes — existing benchmark outputs, human-label reference datasets, synthetic stimuli and derived measurements |
| B1 Attribution | Partial / do not certify fully yet — §2 and Appendices A, B and K cite the principal sources. The 39-setting census includes heterogeneous upstream assets; Appendix B.2 does not claim a complete source-by-source permission audit |
| B2 Terms | Yes, with explicit limits — Appendix B.2 identifies MathDial CC BY-SA 4.0, the MathTutorBench paper/repository discrepancy, and LongTutor data/code terms. It does not assert resolved redistribution rights for every archive record or a licence for unreleased code |
| B3 Intended use | Yes, within the stated scope — Appendix B.2 and Ethical Considerations: model-behavior research, no learner reconstruction or trait diagnosis; raw histories are withheld |
| B4 Identifiers/content | Partial / explain — Appendix B.2 reports earlier identifier-pattern screening and text withholding; it does not claim a comprehensive privacy or offensive-content audit of the million-record corpus |
| B5 Documentation | Yes, with scope limits — §3, Limitations and Appendices A–E document panels, roles, English synthetic stimuli and heterogeneous archive coverage; no representative demographic sample is claimed |
| B6 Counts and splits | Yes — §3 and Appendices B, D, F, G and K distinguish raw records, source groups, repeated requests, generations and codes |
| C Experiments | Yes |
| C1 Compute/model size | Partial / explain — Appendix D.8 and stage details provide environment, API request coverage and completion/retry settings. Served parameter counts, provider GPU hours and total historical compute costs are not independently available |
| C2 Setup and hyperparameters | Yes — §3 and Appendix D.4: logistic forecasts, baselines, fitting, locking, source grouping; Appendices G and K distinguish later extensions |
| C3 Statistics | Yes — §§4–6 and Appendices A, F–K: point estimates, bootstrap intervals, clustering, correction families and retained sensitivities |
| C4 Implementation | Yes, with limits — Appendix D.8 lists the recorded package versions; Appendix D identifies model configurations and prediction settings. Exact reproduction of changing hosted weights is not claimed |
| D Human participants/annotators | No new recruitment or human annotation in this study. Existing MathDial teacher labels and LongTutor human-gold labels are reused as secondary references. Do not interpret this as absence of human-origin data |
| D1/D2/D5 | No new participant instructions, recruitment, payment or demographic sample. Cite upstream studies for original collection; do not invent or claim independent verification of those facts |
| D3 Consent | Requires author confirmation for secondary use. Appendix B.2 explicitly avoids asserting new consent. Public availability is not independent consent verification |
| D4 Ethics review | Requires author confirmation. No institutional approval or exemption has been supplied or inferred |
| E/E1 AI assistance | Yes — Acknowledgements names Codex and Claude Code, identifies Codex language polishing and revision, and discloses broader assistance in planning, stimuli, code, analysis, literature and development of manuscript text; §3 and appendices describe model coding/review. Human authors must review and accept responsibility |

Before upload, resolve the author-only fields above, use the live form's exact options, and provide these explanations wherever a simple Yes/No would be misleading. Some disclosure gaps may remain honestly answered “No”; this document does not certify institutional or legal compliance.
