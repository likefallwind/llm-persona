# Targeted affiliation stability pilot

The prospective five-model panel is complete: 280 generator calls
and 144 blinded judge calls, with no failed final records.

## Frozen-gate result

- Judge reliability ICC(3,k): 0.931
- Default education/non-education model-profile rho: 0.900
- Default/irrelevant-context profile rho: 0.718
- Mean irrelevant-context displacement: -0.050
- Default between-model SD: 0.445
- High-minus-low prompt effect: 1.689; positive models: 5/5
- Self-report/open-behavior rho: -0.200
- Scenario-choice/open-behavior rho: undefined (default choice ceiling)

All five stability gates pass, as do both prompt-steerability gates. Neither
general-personality convergence gate passes. The primary open-behavior profile
is invariant to leaving out any one judge (minimum rho
1.000).

## Interpretation

The fixed model configurations have a distinguishable default affiliation
behavior profile that transports across the two scenario domains and survives
the tested irrelevant context. The explicit high/low instruction moves behavior
strongly and in the same direction for every model, but elasticity differs.

This is not Big Five validation. Default IPIP-like self-reports are compressed
near the socially desirable end and correlate -0.200 with open behavior.
Every model chooses the affiliative option in every default forced-choice item,
so choice/behavior correlation is undefined. Open affiliation also correlates
0.900 with
surface warmth and 0.800
with costly benevolence. Thus the supported object is a behavioral cluster with
substantial warmth overlap, not a construct-equivalent human trait.

## Gate table

```json
{
  "stability_gates": {
    "judge_reliability": true,
    "cross_domain_transport": true,
    "irrelevant_rank_stability": true,
    "irrelevant_mean_stability": true,
    "default_model_dispersion": true
  },
  "prompt_gates": {
    "high_low_mean_effect": true,
    "all_models_directional": true
  },
  "convergence_gates": {
    "self_report_to_behavior": false,
    "scenario_choice_to_behavior": false
  }
}
```
