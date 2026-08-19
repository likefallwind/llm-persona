# Semantic panel technical-attrition amendment

Status: frozen on 2026-08-19 before the formal confirmatory semantic analysis.

The preregistered-style execution target was 360 blinded context batches and
1,080 judge annotations. One annotation,
`mathtutorbench_scaffolding|scaffolding-743|deepseek-v4-pro`, remained technically
unobtainable after three independently resumed rounds of three attempts. The
first two rounds returned empty visible content. In the third round, an
automated transport-only fallback kept the endpoint, model, prompt, candidate
order, and sampling parameters fixed but requested a non-streaming response;
the gateway returned HTTP 500 `InternalServiceError`. The prompt was not unusually
long (3,983 characters versus a 4,438-character within-task median), and 79 of
80 DeepSeek annotations in the same task succeeded.

This amendment was made without consulting the affected pair's scores and
before running the formal confirmatory semantic pipeline. No prompt was edited,
no judge route was changed, and no replacement context was selected. To keep a
rectangular three-judge panel and preserve the paired prompt-intervention design,
the failed generic batch and its prespecified pedagogy counterpart are excluded
for every judge. This removes 2/360 batches and 6/1,080 ratings (0.56%), leaving:

- 358 analyzed batches;
- 1,074 complete judge annotations;
- 2,148 response units (358 batches x 6 candidate models);
- 17,184 consensus dimension rows (2,148 responses x 8 dimensions);
- exactly three judges behind every consensus row.

The executable specification is `research/semantic_panel_exclusions_v1.json`.
Both the coverage gate and confirmatory analyzer validate it against the frozen
sample manifest. The paper must report this attrition. No result may describe
the panel as 360 complete batches or 1,080 complete annotations.

The raw append-only run log retains all failed retries. The exclusion is based
only on provider/transport failure, not on a score, model identity within the
blind slate, effect direction, or statistical significance.
