# Working paper outline

## Candidate title

**Do AI Tutors Have Stable Educational Personalities? Behavioral Differences,
Prompt Effects, and Their Limits**

The phrase *educational personality* is defined operationally in the first page:
a recurring tendency in observable teaching behavior. It does not assert a human
mental trait, consciousness, or equivalence to human personality inventories.

## Starting question and data opportunity

Different AI tutors feel different in use. Some explain or reveal more, some ask
questions and preserve learner work, some express greater certainty, and some
sound warmer or more affiliative. The paper asks whether these impressions reflect
behavior that recurs across educational situations, how much the behavior changes
under a shared prompt, and whether a stable or induced style is appropriate to the
learner context.

EduBenchmark makes this question unusually testable. Multiple deployed model
configurations answered the same items under a shared harness across educational
and non-educational tasks, including paired generic and explicit-pedagogy prompts.
The study therefore begins with the large existing response archive. New calls are
reserved for narrow questions that the archive leaves unresolved.

## Provisional abstract

AI tutors often appear to have different educational personalities: some explain
directly, some prefer questions, and others appear more confident or warm. It is
unclear whether these impressions reflect recurring model behavior or the prompt
currently in use. We study multiple models under shared educational tasks and
prompts, beginning with a large archive of paired responses and adding targeted
tests only where the archive leaves a clear uncertainty. The results give a
qualified affirmative answer. Assistance directness recurs across teaching tasks
and relates to independently inferred teacher actions; expressed confidence also
retains a model ordering across several task sources; and a five-model pilot finds
limited cross-domain stability in open affiliative behavior. At the same time, a
shared pedagogy prompt moves several teaching behaviors by roughly the size of the
default differences between models. Model differences remain after prompting, but
their magnitude and sometimes their ordering change. Many intuitive personalities
do not survive the same tests: actionability is easy to induce but not stable
across tasks, communion overlaps warmth, learner responsiveness is unsupported,
and personality questionnaires do not predict open behavior. Stable teaching
style is also not teaching quality. A common question-oriented prompt improves
average agreement with teacher actions but reduces agreement when the reference
teacher explains directly; models can realize an explicitly assigned question or
explanation but do not reliably choose between them from the dialogue. AI tutors
therefore exhibit a small number of recurring, strongly prompt-dependent
educational tendencies, not a complete human-like personality or a guarantee of
adaptive teaching.

## Research questions

1. Which apparent educational-personality differences recur across teaching
   tasks when the item, response length, and general writing style are controlled?
2. How much does a shared pedagogy prompt change those differences, and which
   model differences remain afterward?
3. Which intuitive dimensions fail because they are unstable, redundant, tied to
   one task, or unsupported by open behavior?
4. Does a stable or prompt-induced teaching style correspond to context-appropriate
   action, learner-state diagnosis, or responsiveness to learner requests?
5. Do standard personality questionnaires agree with open behavior inside and
   outside education?

## Findings to foreground

### Findings that support the initial intuition

1. **Assistance directness is the clearest recurring educational tendency.**
   Some configurations consistently explain or reveal more, while others leave
   more work to the learner. It survives cross-task and independent-action checks.
2. **Expressed confidence has a stable model ordering across several sources.**
   Confidence, revision, and abstention remain separate behaviors and must not be
   collapsed into correctness or one caution score.
3. **Open affiliative behavior shows limited cross-domain stability.** The result
   survives one irrelevant-context change in a five-model pilot, but overlaps
   surface warmth and is not Big Five agreeableness.
4. **Prompting does not erase all model differences.** Cross-prompt identity
   transfer remains above chance, and models differ in how much they change.

### Findings that limit or reverse the initial intuition

1. **Prompt sensitivity is not stability.** Next-step actionability moves strongly
   under the pedagogy prompt but reverses model ordering across tasks.
2. **Warmth, communion, personalization, and autonomy do not form several validated
   personality dimensions.** Some are reliably judged but redundant or unstable.
3. **Learner responsiveness is not supported.** System-level teaching instructions
   control behavior far more than ordinary learner requests, and teaching style
   does not improve human-gold learner-state diagnosis.
4. **A more pedagogical-looking style is not always more appropriate.** More
   questioning improves average action agreement but reduces it in direct-
   explanation contexts.
5. **Ability to enact a style is not ability to select it.** Models nearly perfectly
   realize assigned ASK/EXPLAIN actions, while explicit selectors remain near
   chance and two-stage composition underperforms direct generation.
6. **Questionnaire personality is not open behavior.** Agreeableness self-report
   is compressed and negatively ordered relative to open affiliation; forced
   choice is at ceiling.
7. **Stable form cannot be relabeled as a human trait.** Organizational style is
   not conscientiousness, cautious wording is not honesty--humility, and distinct
   safety policies do not form one permissiveness value.

## Paper organization

### 1. Introduction

- Begin with recognizable differences among AI tutors: direct versus eliciting,
  confident versus cautious, warm versus transactional.
- Explain why educational behavior is a better test than a personality
  questionnaire: it occurs in an application with consequential choices.
- Introduce the shared-response archive as the reason the question can be tested
  without first inventing a new inventory.
- State the qualified answer: a few recurring differences are real, prompts change
  them substantially, and many intuitive traits fail behavioral validation.

### 2. Related work

Organize around two limitations rather than paper-by-paper summaries:

- LLM personality studies establish elicited expression but often lack external
  task behavior and self-report--behavior convergence.
- AI-tutor evaluations measure response quality or induce a desired policy but
  rarely estimate recurring defaults and prompt effects jointly across models and
  tasks.

### 3. What counts as evidence of educational personality?

- Define educational personality as recurring observable teaching behavior.
- Separate recurrence, prompt sensitivity, context appropriateness, competence,
  and learner outcomes.
- Explain that model attribution alone may be a generic generator fingerprint.
- Introduce the theory-grounded candidate set without promising that every
  dimension exists: directness, agency, communion, actionability, epistemic
  behavior, and learner responsiveness.

### 4. Data and evidence path

- Existing same-item educational and generic responses.
- Paired generic and pedagogy prompts.
- Human teacher actions and human-gold learner diagnosis.
- Targeted prompt-control and action-selection tests.
- Archive-selected affiliation pilot with open behavior, self-report, and forced
  choice.

Statistical details, freeze timing, judge audits, and release controls remain
complete but support this evidence path rather than define the narrative.

### 5. Which educational differences recur?

- Lead with assistance directness.
- Add expressed confidence while separating confidence, revision, and abstention.
- Report information load as a weaker signature, not a validated personality.
- Present affiliation as limited cross-domain evidence.

### 6. How prompts change the apparent personality

- Compare prompt movement with default between-model differences.
- Show that identity remains after prompting.
- Show model-specific changes and rank reversals.
- State plainly that stable does not mean immutable, and steerable does not mean
  stable.

### 7. Which intuitive personalities fail?

- Actionability: strongly induced, not cross-task stable.
- Communion: reliably judged, but overlaps warmth and lacks variance in one task.
- Personalization and learner responsiveness: unsupported.
- General-personality labels: archive coverage gaps and failed convergence.
- Questionnaire agreeableness: no agreement with open affiliation.

Treat these as substantive answers about where personality intuitions go wrong,
not as a list of non-significant tests.

### 8. What stable teaching style does and does not imply

- Overall questioning gain versus reduced direct-explanation agreement.
- System instructions versus ordinary learner requests.
- Teaching presentation versus learner-state diagnosis.
- Assigned-action realization versus dialogue-conditioned action selection.

This section asks whether a recurring or induced personality is pedagogically
appropriate. It does not introduce a separate controller paper inside the paper.

### 9. Discussion

- AI-tutor personality should be measured through repeated open behavior.
- Defaults and behavior under several reasonable prompts should be reported
  together.
- Stable style must not be treated as a quality or adaptivity ranking.
- Model selection and prompt design jointly determine the tutor a learner sees.
- Real learning benefit remains untested.

## Main figures

1. **Research question and evidence path:** observed tutor impressions → archive
   recurrence test → prompt comparison → independent educational checks → narrow
   follow-up.
2. **What persists:** model profiles for assistance directness and expressed
   confidence, with evidence status clearly distinguished.
3. **What prompting changes:** default profiles, common movement, and remaining
   model differences for the reliable teaching dimensions.
4. **Supported and unsupported intuitions:** a compact evidence map showing which
   proposed dimensions recur, overlap, or fail behavioral validation.
5. **Why personality is not quality:** overall action agreement versus probing and
   telling contexts, followed by assigned-action realization versus action choice.

## Statistical role

The statistics remain essential, but they answer supporting questions:

- Does the observed ordering recur beyond one task?
- Is it larger than writing-style and length confounds?
- Does the same prompt move every model, and by how much?
- Does an apparent dimension relate to an independent educational behavior?
- Does the conclusion survive judge, wording, and order changes?

The paper should state the behavioral answer before giving the statistic. Tables
of every model, task, judge, confidence interval, and failed gate belong in the
appendix unless they change the interpretation.

## Scope and nonclaims

- “Educational personality” is an observable recurring tendency, not a claim of
  human-like inner personality.
- Six-model and five-model profiles do not support population or family claims.
- A stable behavior is not necessarily appropriate, accurate, or beneficial.
- No result demonstrates student learning gain.
- Provider prompts, aliases, and serving versions remain part of the observed
  configuration.

## Writing rule

Each result section should follow this order:

1. the intuition being tested;
2. the behavioral answer;
3. the evidence that makes the answer credible;
4. the counterexample or boundary;
5. what the answer means for AI tutoring.

Do not use significance, reliability, or a newly named construct as the subject
of a paragraph when the paragraph can instead state what the models repeatedly
did.
