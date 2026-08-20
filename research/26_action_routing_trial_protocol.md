# Prospective action-routing trial

Local method freeze: 2026-08-20. Status: **designed and generated, no response
calls started**. The method must be committed and pushed before live collection.

## Research question

The existing intervention produces a robust paradox: a uniform pedagogy prompt
improves average agreement with human teacher actions, reduces cross-model action
variation, improves `probing`, and harms `telling`. This trial asks whether a
context-conditioned policy can remove that target-specific harm without losing
the probing gain.

This is a stronger test than another persona or wording study. The adaptive arm
does not receive the human target label. It must infer from the conversation
whether the next move should be a diagnostic question, focused hint, direct
explanation, or brief acknowledgement. The trial therefore distinguishes
one-size-fits-all policy compliance from context-conditioned action selection.

## Source and external payload

The source is the public MathDial-derived `mathdial_bridge.json` used by
MathTutorBench. Each request contains the public math problem and conversation
with the final human teacher turn removed. It does not contain the held-out
teacher response, an archived model response, a private user log, or a target
label. The public manifest retains only IDs, derived labels, metadata, prompt
hashes, and the SHA-256 hash of the held-out teacher turn. The locally generated
request manifest containing benchmark text is excluded by `.gitignore`.

The user has authorized external API transmission. Routes and caps are:

- MiniMax-M3 and MiniMax-M2.7 via the official MiniMax endpoint, at most four
  concurrent requests; and
- GLM-5.2, DeepSeek-V4-Pro, and Doubao-Seed-2.0-Lite via the configured gateway,
  at most eight concurrent requests.

Qwen is excluded until the later server is available. No unavailable model may
be replaced after results.

## Context selection

The existing target-mapping audit links the held-out teacher response to an
unambiguous human MathDial action label without model-output inspection. The
trial uses the standard-difficulty contexts with target source
`exact_human_lookup`:

- all 48 eligible `telling` contexts; and
- 48 of the 410 eligible `probing` contexts selected by SHA-256 rank under seed
  `20260827`.

The 96-context selection is frozen in the manifest. Hash selection occurs before
new outcomes and prevents hand-selection of favorable probing examples.

## Four paired arms

Every context is crossed with four system policies:

1. **generic:** respond usefully and caringly in at most two sentences;
2. **uniform scaffold:** ask exactly one guiding question and prefer a question
   over direct explanation;
3. **adaptive router:** choose among a targeted diagnostic question, focused
   hint, direct explanation when explicit instruction is needed, or brief
   acknowledgement, based only on conversation evidence; and
4. **oracle action:** explicitly require the held-out target action.

The oracle arm is a detector and realization-ceiling diagnostic. Because it is
given the target, it can never support an adaptivity claim. Each non-oracle arm
uses one identical system prompt for both target groups, so its message does not
expose the context-specific target label. The historical uniform prompt does use
the generic phrase “probing questions,” but it is held constant for both
`probing` and `telling` contexts.

The complete design is 96 contexts x 4 arms x 5 models = **1,920 calls**. All
arms are rerun on the same provider snapshots; archived generic and uniform
responses are not used as controls. This avoids a serving-version confound.

## Request order and completion

For each model, the 384 requests are submitted in 48 deterministic hash-random
blocks. Every block contains exactly one request from each of the eight
target-action-by-arm strata. The per-model queue is frozen by seed `20260828`.

Completion is all-or-nothing: exactly 1,920 successful, nonempty, prompt-hash-
matching cells with ranks matching the public order plan. Failed requests may be
retried on the same route but cannot be replaced by another context, arm, model,
or provider. The writer is locked and resumable.

## Outcomes and inference

The three frozen TF--IDF/linear-SVM variants are trained on 18,541 existing human
MathDial teacher turns and then applied to the identical trial responses. No LLM
judge is used for the primary outcome. Each variant produces an action-match
indicator against the held-out human next action.

Contrasts are paired within context and model. Aggregate uncertainty resamples
the 96 contexts while retaining all five models; models remain a fixed panel.
Results are also reported separately for every model. Classifier variants are
robustness checks on the same responses, not independent samples.

The frozen gates, each required independently under all three classifiers, are:

- replicate the uniform prompt's probing benefit: uniform minus generic >= 0.10
  and the context-clustered lower 95% bound is above zero;
- replicate telling harm: uniform minus generic <= -0.15 and the upper bound is
  below zero;
- recover telling: adaptive minus uniform >= 0.15, lower bound above zero, and
  positive in every model;
- retain generic telling performance: the adaptive-minus-generic lower bound is
  above the -0.05 noninferiority margin;
- retain uniform probing performance: the adaptive-minus-uniform lower bound is
  above the -0.05 noninferiority margin;
- improve the balanced overall match: adaptive minus generic >= 0.05 with lower
  bound above zero; and
- validate action realization: oracle match >= 0.65 for both target actions.

Failure of any gate under any classifier downgrades the joint claim. All arm,
target, model, classifier, consensus, and failure results remain reportable.

## Frozen hashes

| Component | SHA-256 |
|---|---|
| `data/action_routing_trial_spec_v1.json` | `a21ba055036ebdcd8c701662f43830b6ed4f20b5b5d3a669ad130226b44d6927` |
| `scripts/generate_action_routing_trial.py` | `d27bfe269cfd117da6770b6e4db1544e248e27ed17ac24e5a6ba53fa8cd281c1` |
| `scripts/run_action_routing_trial.py` | `42c945c91bfcbcadd2743a1a555901f7da5bf6ab9b05169e3f0ed6924ad08368` |
| `scripts/analyze_action_routing_trial.py` | `bcd547035c8604e288f79e6bb7deb40085b0687201bba560086822e8fd21305b` |
| `scripts/analyze_dialogue_act_validity.py` | `21a4ce5cea6261c5cc90b92f6ae477be82dcf7dd0212e54a1d4955de557e9aa2` |
| `artifacts/action_routing_trial_v1/sample_manifest.jsonl` | `4c7b11e64e2e9963b9632aeefe63791f71a2964b3a61eab9aa2524bc4ea4283f` |
| `artifacts/action_routing_trial_v1/request_order_plan.jsonl` | `21bb71e599cac0cf91ecefda98cc565284fab56fe6508ee3082fe405edf30659` |
| `artifacts/dialogue_act_validity/target_mapping_audit.csv` | `e88b66557e42ed23f8121695b6c86fa5d24a0b2ec9ebbc8e7256edfe028081fe` |
| upstream `mathdial_bridge.json` | `96609c808383eea57d16bb24a49f302a9d84ffa323571c5989e57638bbaf2066` |
| upstream MathDial `train.jsonl` | `d6135869c02dccf8d14756fa2f0367c5352922bb263ec22dc0eeace4da815d43` |
| upstream MathDial `test.jsonl` | `3ec54ee8ab921dc6191bf5e2ee766d4e7916b4264394eb17a6be9b3fe486e50b` |

The generated design contains 384 unique prompt hashes, 48 contexts per target,
and exact eight-stratum balance in all 48 blocks for every model.

## Interpretation boundary

Success would show that context-conditioned policy selection improves agreement
with a frozen observed human action and avoids a reproducible one-size-policy
failure in this fixed model panel. It would not establish that the human action
is uniquely optimal, that action agreement improves learning, or that the five
models represent a model population. Learning claims remain reserved for the
separately planned prospective learner trial.
