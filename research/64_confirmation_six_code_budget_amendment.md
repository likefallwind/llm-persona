# Six-code confirmation completion-budget amendment

Recorded on 2026-09-07 before computing primary confirmation results. The original
first pass and two structural repair passes terminated on 2026-09-06 at
16:51:22 UTC with 12,114 valid codes out of 12,120. The dependent content and
reporting controllers correctly stopped. Their terminal states are archived with
the amendment. Earlier estimated completion times did not account for this stop.

All six remaining requests belong to the GLM-5.3 coder. In both repair passes,
each request exhausted both 16,384-token attempts, returned finish_reason=length,
and produced no visible answer. The amendment selects every request failing this
objective rule, with no selection by its event labels, agreement, or study results.

One additional, separately recorded run permits at most two attempts per request,
max_tokens=32,768, client timeout=720 seconds, temperature=0, and the identical
model, messages, rubric, API route, and parser. It therefore allows at most 12
new HTTP attempts. Gateway concurrency remains capped at 8 across its models;
MiniMax remains capped at 4. A larger client timeout does not override upstream
timeouts. No further repair is automatically authorized by this amendment.

All 12,114 already valid codes remain untouched. Original and amended budget
groups must independently pass the frozen parser and provenance checks, then
form an exact disjoint union of 12,120 codes and 32,320 consensus item-events.
Original failed records, forecasts, models, and analysis code remain unchanged.
The six-request run is an explicit protocol deviation, not part of the original
frozen repair allowance and not an independent replication.

Only two affected answers are in the canonical prediction panel; one is in a
neutral wording arm, and three are in the missing-information opportunity panel.
This classification was read from design metadata, without examining their
event labels or primary effects. The completed paper must identify these panels
and disclose whether substantive claims depend on the amended codes.

Before paper completion, enumerate both possible binary values for each of the
two originally missing canonical GLM codes, separately for each primary event,
while keeping the other two coders and all locked forecasts fixed. This gives at
most four assignments per event and exact ranges for the six primary paired
effect estimates and raw p-values. Apply Holm to the vector of per-test maximum
raw p-values as a conservative joint sensitivity check, and label it supplemental.
This cannot test the semantic truth of any coder. The other affected panels must
receive corresponding bounded descriptive sensitivity checks. No sensitivity
result replaces or refits the frozen primary analysis.

Full empirical synthesis, content sensitivity, bilingual results, resource
accounting, and scientific/visual artifact review remain required after recovery.
