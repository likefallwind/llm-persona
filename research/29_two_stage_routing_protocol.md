# Prospective two-stage selection-then-execution trial

Local method freeze: 2026-08-20. Status: **designed and generated; no trial
response call started**. The complete method must be committed and published in
a draft PR before collection.

## Why this trial exists

The prospective one-pass action-routing trial produced three jointly informative
results on the same 96 public MathDial-derived contexts:

1. a uniform questioning prompt independently reproduced a probing benefit and
   a telling harm under all three frozen human-action classifiers;
2. a single-pass adaptive menu partially reduced that harm but remained worse
   than generic on telling and did not improve balanced overall match; and
3. explicit oracle prompts achieved perfect binary question/no-question
   realization, although the four-way classifiers confused many probing
   questions with the neighboring `focus` class.

The post-hoc mechanism hypothesis is therefore a **selection bottleneck**: the
fixed model panel can realize an explicitly chosen binary teaching action but
does not reliably choose that action from the conversation when selection and
response generation occur in one pass. This trial tests that hypothesis
prospectively.

## Closest-work boundary

The architecture itself is not novel. Plan/realize separation has a long history
in dialogue generation, including explicit two-stage open-domain response
planning ([Jiang et al., 2020](https://aclanthology.org/2020.findings-emnlp.247/)).
Pedagogical steering has used predefined multi-turn transition graphs
([Puech et al., 2025](https://aclanthology.org/2025.findings-acl.1348/)), and a
BEA 2025 study already found that modern LLMs struggle to predict future tutor
strategy even though strategy predicts student outcomes
([Ikram et al., 2025](https://aclanthology.org/2025.bea-1.55/)).

The intended contribution is narrower: a same-context, same-model,
same-serving-period causal decomposition of educational action **selection** and
**realization**, motivated by a prospectively replicated contextual harm rather
than by architecture proposal alone. The trial uses a held-out observed human
action, deterministic binary realization, two order-counterbalanced selectors,
and a concurrently rerun single-pass baseline.

## Contexts and external payload

The trial inherits exactly the 96 contexts frozen before the previous action
trial: all 48 eligible exact-human-lookup `telling` contexts and the same
hash-selected 48 `probing` contexts. Their parent public manifest and all source
hashes are pinned in the specification. No context can be added, removed, or
relabelled.

Each external request contains only the public math problem, public conversation
history with the last human teacher turn removed, and one frozen system prompt.
It never contains the held-out teacher response, its target label, an archived
model response, or a private user log. The full request manifest stays in the
gitignored `run/` directory; the public manifest contains only identifiers,
labels, hashes, and design metadata.

The user has authorized external API transmission. MiniMax-M3 and MiniMax-M2.7
use the official MiniMax route at at most four concurrent requests; GLM-5.2,
DeepSeek-V4-Pro, and Doubao-Seed-2.0-Lite use the configured gateway at at most
eight. Qwen remains excluded until the later server is available.

## Five target-invariant calls per context

Every context and model receives all five calls, regardless of the held-out
human target and regardless of any selector output:

1. **selector ASK-first:** choose `ASK` or `EXPLAIN`, with ASK described first;
2. **selector EXPLAIN-first:** the same binary decision under independently
   rewritten wording and reversed presentation order;
3. **ASK executor:** generate exactly one targeted diagnostic question;
4. **EXPLAIN executor:** directly explain the missing idea using declarative
   sentences and no question; and
5. **single-pass adaptive:** rerun the failed one-pass adaptive menu under the
   same provider snapshot as the two-stage calls.

Selector output is parsed by the frozen regex `^(ASK|EXPLAIN)[.!]?$` after
whitespace trimming and uppercasing. Invalid output remains `INVALID`, scores as
incorrect, and cannot be repaired, retried for formatting, or excluded.

Both counterfactual executor responses are generated for every context before
analysis. Each selector is composed after collection by choosing the already
generated executor response associated with its parsed action. Provider calls
are therefore never conditionally selected based on an observed experimental
outcome.

The complete design is 96 contexts x five calls x five models = **2,400 calls**.

## Ordering and completion

For each model, the 480 requests are divided into 48 SHA-256-randomized blocks.
Every block contains exactly one request from each of the ten
human-target-by-call-type strata. Completion requires exactly 2,400 successful,
nonempty, prompt-hash-matching responses with frozen ranks, zero unexpected
keys, and exact ten-stratum balance. Failed calls may retry on the same route
under the frozen policy but cannot be replaced.

## Registered outcomes

The human reference is binarized before outcomes: human `probing` maps to `ASK`
and human `telling` maps to `EXPLAIN`.

Primary outcomes are deliberately classifier-free:

- selector validity and selector agreement with the held-out human binary
  action;
- ASK-executor question-mark realization and EXPLAIN-executor no-question
  realization;
- composed two-stage binary action agreement; and
- paired composed-minus-single-pass binary agreement within context and model.

Question marks operationalize binary action realization, not full pedagogical
quality. The three frozen four-way human-action SVMs are applied as secondary
measurement-sensitive outcomes, with every result reported but no success gate.

Contexts are bootstrap clusters; all five models remain a fixed panel. Both
selector wordings must independently pass all of these frozen gates:

- valid output rate at least 0.98;
- human binary-action accuracy at least 0.60, with lower 95% bound above 0.50
  and accuracy above 0.50 in every model;
- composed-minus-single-pass match at least +0.08, lower 95% bound above zero,
  and positive in every model;
- ASK question realization and EXPLAIN no-question realization each at least
  0.95 overall and at least 0.90 in every model; and
- absolute ASK-first versus EXPLAIN-first selector-accuracy difference no more
  than 0.10.

Failure of either selector, either executor, the wording gap, or any every-model
gate rejects the joint two-stage claim. No pooled average can rescue a failed
wording.

## Frozen design audit

The generated design has 480 public sample rows, 480 unique prompt hashes, 48
contexts per human target, 96 samples per call type, zero public `messages`
fields, and exact ten-stratum balance in all 48 blocks for every model.

| Component | SHA-256 |
|---|---|
| `data/two_stage_routing_trial_spec_v1.json` | `6b1ac30ccc94a53ee3160969ca33e6901e2a1b0f71439250c73ec298ab5e4d0a` |
| `scripts/generate_two_stage_routing_trial.py` | `f0c06ce63f373929fb8dc03efd5bb81cc58567105662f2fa28c3be5ecac59c5e` |
| `scripts/run_two_stage_routing_trial.py` | `b79390876a812e61c6908aa13d716a3282ff68a32b45b9ed3ce49c4ad03d60e6` |
| `scripts/analyze_two_stage_routing_trial.py` | `2ac0d521666d17de6bf18edfedbc8907ec11b5393ef0fb71f3ef01d08ea6278a` |
| `scripts/run_two_stage_routing_trial.sh` | `20662567cf162d1b3aa06dfb196f76cebb64bab4f64e60e571f1aaf1fde4f327` |
| `artifacts/two_stage_routing_trial_v1/sample_manifest.jsonl` | `b0b134710bc714ad37987b6dab13613dc7149c9f0b88c7721eece4235aefabfc` |
| `artifacts/two_stage_routing_trial_v1/request_order_plan.jsonl` | `37920d195f1a4575f5be81e07f4eabd6a1ac8aad6e343beaf31198e32bc85840` |

## Interpretation boundary

Success would show that explicit stage separation improves agreement with one
observed human binary action relative to a concurrently rerun one-pass prompt in
this fixed panel. Failure would show that simply exposing a discrete selector is
insufficient. Neither result establishes that the human move is uniquely
optimal, that the generated response is high quality, or that any policy improves
student learning. Those claims remain reserved for a later learner-outcome trial.
