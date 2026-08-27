# Confirmatory educational-character panel: results

Snapshot: 2026-08-26. Status: **complete frozen-split analysis**. The formal
sample, decision thresholds, judge-family leaveout gates, and scale-revision
limit were fixed before formal scores were inspected. The result is a
construct-boundary result, not a preregistered population claim.

## Bottom line

The formal experiment does **not** add a new cross-task educational-character
axis. It instead sharpens the repository's existing conclusion:

> The most defensible object is a prompt-contingent pedagogical policy response
> surface. Models have different defaults and different steering elasticity,
> but most intuitively named teaching “personalities” do not survive strict
> measurement, cross-task, nonredundancy, and behavioral-grounding gates.

The six-axis framework remains useful as an audit map, but its axes have
different evidential status:

| Axis | Final status in this repository |
|---|---|
| Assistance directness | Validated behavioral character axis; strongest positive result |
| Epistemic commitment | Expressed confidence is a finite-panel signature; revision and abstention remain separate mixed facets |
| Instructional agency | Exploratory only; the replacement four-family pilot missed its frozen judge-profile gate, so formal recovery cannot promote it |
| Relational communion | Reliably scored, but not a new signature: no Socratic model variance and formal rho=0.805 with old `affective_warmth` |
| Next-step actionability | Strong, uniform prompt response but not a stable model axis; formal judge-profile and cross-task gates fail |
| Learner contingency | Negative boundary; existing factorial, LongTutor, personalization, and routing tests do not support learner-responsive policy |

Normative permissiveness remains rejected as a unified seventh axis: its two
stable safety profiles correlate in the wrong direction across tasks.

## Completed formal panel

The eligible formal set contains 290 public/synthetic MathTutorBench slates:
74 standard generic, 74 matched standard pedagogy, 34 hard generic, 34 matched
hard pedagogy, and 74 Socratic. Four blinded judge families scored the same six
candidate configurations:

- GLM-5.2;
- DeepSeek-V4-Pro;
- Doubao-Seed-2.0-Lite; and
- MiniMax-M2.7.

Coverage is 1,160/1,160 unique formal judge calls, 290 per judge, with zero
failed or invalid rows and a durable exit code of zero. The 34 formal LongTutor
slates were excluded because renewed external transmission of those histories
was not authorized. The payload audit records 290 execution batches and 1,160
judge calls and excludes candidate identities, prompt-arm labels, gold answers,
reasoning traces, and credentials.

## Frozen decision outcomes

| Dimension | ICC(3,k) | Score SD | Minimum judge model-profile rho | Cross-task ICC | Median task rho | Max abs old-scale rho | Formal decision |
|---|---:|---:|---:|---:|---:|---:|---|
| Instructional agency | 0.900 | 0.893 | 1.000 | 0.639 | 0.600 | 0.755 | Exploratory only because pilot gate was 0.657 < 0.70; no formal override |
| Relational communion | 0.945 | 0.836 | 0.899 | 0.478 | 1.000 | 0.805 with warmth | Reliable measurement, but no new cross-task signature |
| Next-step actionability | 0.871 | 1.139 | 0.600 | -0.111 | -0.771 | 0.308 | Formal measurement and cross-task signature fail |

Agency's formal agreement is strong, but promoting it would violate the
predeclared pilot lock. Its registered transparent anchors also fail the 0.30
magnitude gate: question rate rho=-0.189 and imperative rate rho=-0.121, with
the latter in the unexpected direction.

Communion is consistently scored and its standard/hard model ranking is
stable, but every candidate has the same exact-item-centered Socratic mean.
Consequently the Socratic model-variance estimate is undefined rather than
positive. It also crosses the fixed nonredundancy boundary with
`affective_warmth` (rho=0.805 versus the required value below 0.80), while praise
(0.236) and encouragement (0.039) miss behavioral-anchor magnitude. The right
interpretation is a reliable refinement/relabeling of warmth in the paired
tasks, not an additional character axis.

Actionability is the clearest separation between *steerability* and
*disposition*. Response-level judge ICC is high, but three of six judge-pair
model-profile correlations are 0.600 and its model ordering reverses across
tasks (cross-task ICC=-0.111; median rho=-0.771). Every leave-one-judge-family
panel retains that cross-task failure. It is therefore a useful prompt outcome,
not a stable default model characteristic.

## Prompt influence

The matched pedagogy instruction has large, context-controlled effects:

| Dimension | Standard mean delta (95% cluster CI) | Hard mean delta (95% cluster CI) | Prompt movement / default model range | Direction across all six models |
|---|---:|---:|---:|---|
| Instructional agency | -0.995 [-1.124, -0.859] | -1.039 [-1.218, -0.850] | 0.679 / 0.942 | Negative for every model in both tasks |
| Next-step actionability | +1.047 [0.824, 1.252] | +0.880 [0.522, 1.196] | 0.856 / 0.787 | Positive for every model in both tasks |
| Relational communion | -0.172 [-0.233, -0.115] | -0.194 [-0.294, -0.098] | 0.202 / 0.199 | Model signs are mixed |

These effects survive every judge-family leaveout in direction. Agency's pooled
model-specific deltas range from -0.378 for GLM-5.2 to -1.407 for MiniMax-M2.7;
actionability ranges from +0.364 to +1.646 for the same two models. Together
with the previously validated help-directness deltas (-0.851 to -2.096), this
shows both a shared prompt deformation and large model-specific elasticity.

The decisive asymmetry is that actionability is highly steerable but not a
cross-task model signature, whereas assistance directness is both highly
steerable and the only axis that passes the full existing behavioral-character
chain. Prompt responsiveness alone is therefore insufficient evidence of model
“personality.”

## Default, or “unprompted,” differences

“Default” here means the generic system-policy arm, not an intrinsic or
prompt-free model essence. The strongest supported default contrast remains
assistance directness: exact-item-centered means range from GLM-5.2 at -0.845
and DeepSeek-V4-Pro at -0.324 to MiniMax-M3 at +0.408 and MiniMax-M2.7 at
+0.803. MiniMax configurations therefore reveal/explain more by default, while
GLM leaves more work with the learner.

The objective epistemic profile is crossed rather than one-dimensional.
Doubao-Seed-2.0-Pro has the highest expressed confidence (0.977) and almost no
answer revision (0.019). Qwen3.5-4B also reports high confidence (0.956) but has
the highest unanswerable-item abstention (0.912). MiniMax-M3 reports the lowest
confidence (0.878) but abstains much less often (0.748). These are observable
policy tendencies, not calibration or correctness claims.

The new formal scores can be used only as exploratory descriptions. They place
MiniMax-M2.7 toward greater tutor control (+0.594) and GLM toward lower tutor
control (-0.758); GLM is most action-oriented by default (+0.609) while
MiniMax-M2.7 is least (-0.581); Doubao is warmest (+0.513), while DeepSeek
(-0.376) and MiniMax-M2.7 (-0.343) are more transactional. The formal failures
above prohibit treating those three columns as stable personality traits.

## Ability boundary

In leave-one-model-out prediction of the existing judged MathTutorBench quality
outcome, adding all three confirmatory scores to transparent features changes
mean AUC from 0.9030 to 0.9065 (+0.0035; positive in six of six folds).
Actionability alone adds +0.0029, agency +0.0028, and communion -0.0006. These
small descriptive associations do not upgrade any failed measurement,
cross-task, nonredundancy, or judge-family gate and are not learner gains.

## Stopping decision

The high-value uncertainty raised by this research question is now resolved:

1. a literature-grounded dimension map was constructed instead of importing
   human Big Five self-report scales;
2. all existing frozen evidence was mapped into six axes plus prompt elasticity;
3. the two plausible new confirmatory candidates were tested on an untouched
   split with four judge families;
4. prompt effects were quantified against default model ranges; and
5. nonredundancy, behavioral anchors, quality association, and judge-family
   sensitivity were checked.

No additional generic judge-panel or wording iteration is justified. The
failed actionability stability and communion nonredundancy results are not
plausibly repaired by more scoring of the same contexts, and wording revisions
were explicitly capped after the pilot split. A new experiment would be a new
research question only if it adds one of the missing identification layers:
prospective learner outcomes, independently sampled model families/provider
routes, learner-state interventions that genuinely vary evidence, or matched
epistemic-policy prompts. None is required to stabilize the current conclusion.

## Reproducibility pointers

- Protocol and fixed gates: `research/34_theory_grounded_panel_protocol.md`
- Formal aggregate report: `artifacts/confirmatory_character_panel_v1/formal/report.md`
- Formal machine decision: `artifacts/confirmatory_character_panel_v1/formal/decision.json`
- Judge-family sensitivity: `artifacts/confirmatory_character_panel_v1/formal/judge_family_sensitivity.json`
- Six-axis synthesis: `artifacts/educational_character_framework_v1/decision.json`
- Payload scope audit: `artifacts/confirmatory_character_judge_v3/payload_audit.json`

Raw annotations remain ignored and are not required for the public aggregate
claim package.
