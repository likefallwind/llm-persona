# General-personality content audit: results

Snapshot: 2026-08-28. Status: **complete archive-only construct audit**. No
generator or judge calls were made.

## Bottom line

The earlier archive analysis did not show that Big Five, HEXACO, Dark Triad, or
Schwartz content was absent; it had not measured those constructs directly. The
completed audit now checks the full requested construct set and reaches a more
precise conclusion:

> The existing EduBenchmark archive contains one localized interpersonal signal
> that merits a small stability pilot, several real but construct-confounded
> behavioral axes, and large regions of general personality that are simply not
> identifiable from the old tasks.

No general personality construct is validated. A broad personality experiment
is not authorized by this audit.

## Coverage result

Twenty-two constructs or adjacent validity targets were audited. Nine have at
least a partial behavioral candidate; thirteen are not identifiable in the
archive.

- Big Five agreeableness, extraversion, and conscientiousness have partial
  manifestations; openness and emotional stability do not.
- HEXACO honesty-humility is only partially represented through epistemic
  behavior and lacks sincerity-under-incentive, status, greed, or cheating
  opportunities.
- Machiavellianism, narcissism, and psychopathy/callousness are not identified.
  Safety refusal cannot be relabeled a Dark Triad score.
- Schwartz benevolence, universalism, security, and conformity have partial task
  opportunities, but no explicit value trade-off. Self-direction, stimulation,
  hedonism, achievement, power, and tradition are not identified.
- Cooperation, risk preference, and impression management lack behavioral games,
  controlled payoffs, or honest-versus-ideal contrasts.

Standard questionnaire, scenario-choice, and self-report--behavior comparisons
are absent. Open behavior and education behavior are available; non-education
transfer is heterogeneous rather than purpose-built. Among stability tests,
only coarse cross-task role change and education-specific pedagogy prompting are
present. Paraphrase, order, format, temperature, irrelevant history, language,
and high/low trait interventions remain untested for general constructs.

## What the existing replies actually support

### Localized affiliation signal

Non-tutoring communal expression transports to default tutoring at rho=0.829
and correlates rho=0.771 with independently judged educational relational
communion. Its strongest surface-control correlation is 0.714, below the frozen
0.80 reduction threshold. This is the only cluster with two strong cross-role or
cross-source links.

However, its median correlation across ten individual non-tutoring tasks is only
0.371 and some task pairs reverse sharply. The evidence therefore supports a
specific unresolved hypothesis—an affiliation/agreeableness/benevolence-like
manifestation whose stability is uncertain—not a stable trait claim.

### Conscientiousness interpretation is falsified

Organizational style is the archive's strongest recurring general fingerprint
(median task rho=0.771), but it correlates **negatively** with objective IFEval
accuracy (rho=-0.886, exact p=0.035; within-cluster BH q=0.104). It also fails to
align positively with beneficial revision or overall self-monitoring accuracy.
Thus headings, bullets, and numbered steps cannot be upgraded to
conscientiousness; they remain style, with capability and instruction-following
confounds.

### Epistemic behavior is not honesty-humility

Epistemic-caution language correlates rho=0.771 with selective abstention, but
only -0.086 with overconfidence gap and -0.371 with beneficial revision. Its
cross-task recurrence and role transport are weak. Calibration, revision, and
abstention remain meaningful objective epistemic facets, but their partial
agreement with cautious wording does not identify HEXACO honesty-humility.

### Safety behavior is not a value ordering

Boundary/refusal wording correlates rho=0.771 with adversarial boundary
enforcement, yet correlates -0.486 with educational refusal and has the wrong
direction for SATA incorrect inclusion. The archive therefore detects real
task-specific safety policies, not a common security/conformity value. Provider
alignment and task competence are binding alternative explanations.

## Experimental consequence

The complete general-personality battery should not be run. The archive selects
one narrow follow-up: an affiliation stability-and-transfer pilot that separates
Big Five agreeableness-like interpersonal accommodation from Schwartz
benevolence-like value choice and from mere warm wording.

The pilot must use scenario choice plus open behavior, irrelevant perturbations,
high/low construct instructions, and both educational and non-educational tasks.
Its primary question is whether the default model ordering survives irrelevant
changes and predicts costly or conflictual behavior. A failure would close the
general-personality extension while leaving the educational-policy paper intact.

## Reproducibility

```bash
.venv/bin/python scripts/audit_general_personality_content_archive.py \
  --edubench-root /path/to/edubenchmark
```

Machine decision:
`artifacts/general_personality_content_archive_v1/decision.json`. Full tables:
`artifacts/general_personality_content_archive_v1/report.md`.

## Later targeted follow-up

The selected affiliation pilot is now complete. It passes its frozen open-
behavior stability gates but fails both general-trait convergence gates. The
archive decision therefore led to a stable, prompt-contingent behavioral cluster
rather than Big Five validation; see
`research/42_affiliation_stability_pilot_results.md`.

## Claim boundary

“Not identifiable” means the old tasks do not supply the required evidence; it
does not mean a construct is absent. “Pilot priority” means an ambiguity is worth
falsifying; it does not mean a trait has been found.
