# Public artifact privacy audit

Status: **FAIL**

Scanned 424 Git-eligible artifact files; files ignored by `.gitignore` were excluded.

The gate rejects explicit source-text fields and absolute user-home paths. It is a release-structure check, not proof that indirect identifiers or all sensitive information are absent.

## Failures

- artifacts/action_routing_trial_v1/run/responses.jsonl: forbidden JSON fields ['response']
- artifacts/factorial_detector_validation_v1/run/annotations.jsonl: forbidden JSON fields ['raw_judge_response']
- artifacts/factorial_order_replication_v1/run/responses.jsonl: forbidden JSON fields ['response']
- artifacts/factorial_paraphrase_replication_v1/run/responses.jsonl: forbidden JSON fields ['response']
- artifacts/factorial_prompt_v1/run/responses.jsonl: forbidden JSON fields ['response']
- artifacts/semantic_judge/external_smoke_short_v1/annotations.jsonl: forbidden JSON fields ['raw_judge_response']
- artifacts/semantic_judge/external_smoke_v1/annotations.jsonl: forbidden JSON fields ['raw_judge_response']
- artifacts/semantic_judge/full_v1/annotations.jsonl: forbidden JSON fields ['raw_judge_response']
- artifacts/semantic_judge/full_v1/run.log: contains an absolute user-home path
- artifacts/semantic_judge/local_smoke_qwen/annotations.jsonl: forbidden JSON fields ['raw_judge_response']
- artifacts/semantic_judge/local_smoke_short/annotations.jsonl: forbidden JSON fields ['raw_judge_response']
- artifacts/two_stage_routing_trial_v1/run/responses.jsonl: forbidden JSON fields ['response']
