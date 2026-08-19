# Research charter

## Core question

Do contemporary language models exhibit stable, predictive, and causally
manipulable **pedagogical dispositions** across authentic educational tasks?

This wording is intentional.  Human personality labels are not assumed to be
valid constructs for language models.  The study begins with behavior and only
retains latent dimensions that pass reliability, discriminant-validity,
out-of-domain prediction, and intervention tests.

## Falsifiable claims

1. **Stable signature:** after controlling for task, item, competence, and length,
   model identity explains reproducible variance in pedagogical behavior.
2. **Cross-task validity:** a disposition estimated on some task families predicts
   behavior on held-out task families better than verbosity, benchmark score, or
   a task-only baseline.
3. **Consequential validity:** the disposition predicts external educational
   outcomes such as scaffolding quality, error diagnosis, history use, and safe
   redirection rather than merely lexical style.
4. **Causal addressability:** targeted prompts move the intended disposition and
   downstream behavior without merely increasing response length or degrading
   correctness.

Any dimension that fails these tests will be reported as task-conditioned style,
not as a general model disposition.

## Primary threats to validity

- anthropomorphizing model behavior with human self-report constructs;
- prompt, decoding, provider, or model-version differences masquerading as traits;
- competence, task difficulty, and verbosity confounding behavioral judgments;
- shared LLM-judge bias and self-preference;
- data leakage across repeated prompts or benchmark variants;
- pseudo-replication from treating many responses from one model as independent
  model samples;
- post-hoc naming of latent factors without preregistered behavioral anchors.

## Evidence threshold

The intended paper needs paired raw outputs, a frozen corpus manifest,
task-grouped held-out evaluation, hierarchical uncertainty estimates, multiple
independent measurement methods, judge-swap analysis, negative controls,
interventions, and exact reproducibility artifacts.  Aggregate leaderboard scores
or questionnaire-style personality tests alone are insufficient.
