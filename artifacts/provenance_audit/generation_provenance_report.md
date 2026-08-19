# Archived generation provenance audit

Audited **84** core-panel benchmark/model runs across primary tutoring, negative controls, and external criteria.

EduBenchmark checkout commit: `b82198351ccc52cd44384392b02483b06a6efb41`.
EduBenchmark working tree entries at audit time: **77**.

Every prediction and summary file is pinned by SHA-256 in `run_provenance.csv`.  Item IDs, response bytes, model labels, and usage are available for analysis, but hashes do not reconstruct provider-side settings that were never stored.

## Generation metadata coverage

| Field | Runs recording field | Total runs |
|---|---:|---:|
| temperature | 22 | 84 |
| top_p | 0 | 84 |
| top_k | 0 | 84 |
| seed | 0 | 84 |
| max_tokens | 22 | 84 |
| max_new_tokens | 0 | 84 |
| prompt_version | 0 | 84 |
| model_version | 0 | 84 |
| endpoint | 0 | 84 |
| base_url | 0 | 84 |
| provider | 0 | 84 |
| decoding | 0 | 84 |
| system_prompt | 0 | 84 |

## Interpretation

Only **0/84** runs record the minimum temperature + seed + prompt-version tuple used by this audit's strict exact-rerun definition.  Therefore the archive supports exact *analysis* reproduction from frozen response files, but not exact regeneration of every provider response.

The shared EduBenchmark adapters and exact-item overlap strengthen comparability, while provider-side aliases, system prompts, backend revisions, and missing decoding metadata remain uncontrolled.  The paper must describe the panel as deployed configurations at the archived run, not immutable model weights or a clean architecture intervention.
