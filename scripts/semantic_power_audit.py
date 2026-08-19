#!/usr/bin/env python3
"""Power and resolution audit for the frozen semantic-coding design.

This script deliberately distinguishes response-level precision from the number
of independently sampled model systems. Thousands of responses do not turn six
models into thousands of model-level observations.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm
from statsmodels.stats.power import TTestPower


def detectable_paired_effect(n_pairs: int, alpha: float, power: float = 0.80) -> float:
    solver = TTestPower()
    result = solver.solve_power(
        effect_size=None, nobs=n_pairs, alpha=alpha, power=power, alternative="two-sided"
    )
    return float(np.asarray(result).reshape(-1)[0])


def correlation_sample_size(rho: float, alpha: float = 0.05, power: float = 0.80) -> int:
    """Approximate two-sided Pearson-correlation sample size via Fisher z."""
    z_alpha = norm.ppf(1 - alpha / 2)
    z_power = norm.ppf(power)
    estimate = 3 + ((z_alpha + z_power) / math.atanh(rho)) ** 2
    return math.ceil(estimate)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    contexts = {
        "hard prompt pair per model": 40,
        "standard prompt pair per model": 80,
        "pooled standard + hard per model": 120,
    }
    paired_rows = []
    for design, n_pairs in contexts.items():
        for label, alpha in (("single planned contrast", 0.05), ("six-model Bonferroni", 0.05 / 6)):
            paired_rows.append({
                "design": design,
                "n_independent_context_pairs": n_pairs,
                "multiplicity_rule": label,
                "alpha": alpha,
                "minimum_dz_for_80pct_power": detectable_paired_effect(n_pairs, alpha),
            })
    paired = pd.DataFrame(paired_rows)

    correlation = pd.DataFrame([
        {"target_absolute_correlation": rho, "models_needed_for_80pct_power": correlation_sample_size(rho)}
        for rho in (0.3, 0.5, 0.7, 0.8)
    ])

    resolution = pd.DataFrame([
        {
            "claim_unit": "direction shared across six models",
            "independent_units": 6,
            "smallest_one_sided_exact_sign_p": 1 / (2**6),
            "smallest_two_sided_exact_sign_p": 2 / (2**6),
        },
        {
            "claim_unit": "direction shared across four named family pairs",
            "independent_units": 4,
            "smallest_one_sided_exact_sign_p": 1 / (2**4),
            "smallest_two_sided_exact_sign_p": 2 / (2**4),
        },
    ])

    paired.to_csv(args.output_dir / "paired_effect_power.csv", index=False)
    correlation.to_csv(args.output_dir / "model_correlation_power.csv", index=False)
    resolution.to_csv(args.output_dir / "exact_test_resolution.csv", index=False)

    report = "\n".join([
        "# Semantic design power and inferential-resolution audit",
        "",
        "## Paired prompt effects",
        "",
        paired.to_markdown(index=False, floatfmt=".3f"),
        "",
        "The unit is a distinct conversation context, not a response and not a judge rating. The calculation is a paired-t approximation for a standardized within-context effect (`dz`); ordinal mixed models may differ slightly.",
        "",
        "## Model-level correlations",
        "",
        correlation.to_markdown(index=False, floatfmt=".1f"),
        "",
        "The current six-model core panel is not powered for aggregate trait--outcome correlations. Such correlations must remain exploratory. The defensible confirmatory route is item-level held-out-model prediction with context clustering, plus a larger model panel for population-level claims.",
        "",
        "## Exact-test resolution",
        "",
        resolution.to_markdown(index=False, floatfmt=".4f"),
        "",
        "Thousands of item responses estimate conditional behavior precisely, but they do not increase the number of independently sampled model systems. Claims about the population of models must use the model count, whereas prompt effects within a fixed model may use paired contexts.",
        "",
        "## Design decision",
        "",
        "The frozen 80-context standard arm is adequate for moderate within-model semantic prompt effects; the 40-context hard arm is only sensitive to moderate-to-large effects after six-model multiplicity correction. For the paper, pool standard and hard only under a preregistered shared-effect model, otherwise report the hard arm as a lower-powered robustness test. Do not use the six model means to claim a general latent-trait correlation.",
        "",
    ])
    (args.output_dir / "power_audit.md").write_text(report, encoding="utf-8")
    print(args.output_dir / "power_audit.md")


if __name__ == "__main__":
    main()
