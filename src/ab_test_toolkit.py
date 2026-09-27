"""
ab_test_toolkit.py
-------------------
Reusable functions for analyzing a two-group (control vs. treatment) A/B test
on a binary conversion metric. Built for the checkout-redesign case study in
this project, but every function here is generic - drop in any control/
treatment conversion counts and it works.

Covers the four things a stakeholder-ready A/B test readout needs:
  1. Hypothesis test (two-proportion z-test) + p-value
  2. Confidence interval + effect size for the difference in conversion rates
  3. Sample-size / power calculation (both directions: achieved power for the
     sample you have, and required sample size for a target effect + power)
  4. Simple plain-language interpretation of the result

Dependencies: numpy, scipy, statsmodels
"""

from dataclasses import dataclass

import numpy as np
from scipy import stats
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize, proportions_ztest


@dataclass
class ABTestResult:
    n_control: int
    n_treatment: int
    conversions_control: int
    conversions_treatment: int
    rate_control: float
    rate_treatment: float
    absolute_lift: float
    relative_lift_pct: float
    z_stat: float
    p_value: float
    ci_low: float
    ci_high: float
    effect_size_h: float
    alpha: float
    significant: bool

    def p_value_display(self) -> str:
        """Never print a literal 0.0000 - p-values are never exactly zero."""
        if self.p_value < 0.0001:
            return "p < 0.0001"
        return f"p = {self.p_value:.4f}"

    def summary(self) -> str:
        sig_word = "IS" if self.significant else "is NOT"
        return (
            f"Control:   {self.conversions_control:,} / {self.n_control:,} "
            f"= {self.rate_control:.2%}\n"
            f"Treatment: {self.conversions_treatment:,} / {self.n_treatment:,} "
            f"= {self.rate_treatment:.2%}\n"
            f"Absolute lift: {self.absolute_lift:+.2%} pts  "
            f"(relative: {self.relative_lift_pct:+.1f}%)\n"
            f"95% CI on absolute lift: [{self.ci_low:.2%}, {self.ci_high:.2%}]\n"
            f"z = {self.z_stat:.3f}, {self.p_value_display()}  "
            f"(alpha = {self.alpha})\n"
            f"Effect size (Cohen's h): {self.effect_size_h:.3f}\n"
            f"Result {sig_word} statistically significant at alpha={self.alpha}."
        )


def run_ab_test(
    n_control: int,
    conversions_control: int,
    n_treatment: int,
    conversions_treatment: int,
    alpha: float = 0.05,
) -> ABTestResult:
    """
    Two-proportion z-test comparing conversion rate between control and
    treatment groups. Returns a full ABTestResult with p-value, CI, and
    effect size.
    """
    rate_c = conversions_control / n_control
    rate_t = conversions_treatment / n_treatment

    count = np.array([conversions_treatment, conversions_control])
    nobs = np.array([n_treatment, n_control])
    z_stat, p_value = proportions_ztest(count, nobs, alternative="two-sided")

    # 95% CI on the DIFFERENCE in proportions (Wald interval with pooled-free SE,
    # standard approach for reporting a lift with uncertainty bounds)
    se_diff = np.sqrt(
        rate_c * (1 - rate_c) / n_control + rate_t * (1 - rate_t) / n_treatment
    )
    z_crit = stats.norm.ppf(1 - alpha / 2)
    diff = rate_t - rate_c
    ci_low = diff - z_crit * se_diff
    ci_high = diff + z_crit * se_diff

    effect_size_h = proportion_effectsize(rate_t, rate_c)

    return ABTestResult(
        n_control=n_control,
        n_treatment=n_treatment,
        conversions_control=conversions_control,
        conversions_treatment=conversions_treatment,
        rate_control=rate_c,
        rate_treatment=rate_t,
        absolute_lift=diff,
        relative_lift_pct=(diff / rate_c) * 100 if rate_c else float("nan"),
        z_stat=z_stat,
        p_value=p_value,
        ci_low=ci_low,
        ci_high=ci_high,
        effect_size_h=effect_size_h,
        alpha=alpha,
        significant=p_value < alpha,
    )


def achieved_power(
    n_control: int,
    n_treatment: int,
    rate_control: float,
    rate_treatment: float,
    alpha: float = 0.05,
) -> float:
    """
    Post-hoc statistical power: given the sample sizes and rates actually
    observed, what was the probability of detecting this effect if it's real?
    Uses the smaller of the two group sizes (conservative) with the ratio
    between groups accounted for.
    """
    effect_size = proportion_effectsize(rate_treatment, rate_control)
    analysis = NormalIndPower()
    ratio = n_treatment / n_control
    power = analysis.power(
        effect_size=abs(effect_size),
        nobs1=n_control,
        alpha=alpha,
        ratio=ratio,
    )
    return power


def required_sample_size(
    baseline_rate: float,
    minimum_detectable_effect_relative: float,
    alpha: float = 0.05,
    power: float = 0.80,
) -> int:
    """
    Standard pre-experiment sample size calculation: given a baseline
    conversion rate and the smallest RELATIVE lift you want to be able to
    detect (e.g. 0.10 = 10% relative lift), how many users per group do you
    need for the requested power?
    """
    target_rate = baseline_rate * (1 + minimum_detectable_effect_relative)
    effect_size = proportion_effectsize(target_rate, baseline_rate)
    analysis = NormalIndPower()
    n_per_group = analysis.solve_power(
        effect_size=abs(effect_size), alpha=alpha, power=power, ratio=1.0
    )
    return int(np.ceil(n_per_group))


def interpret(result: ABTestResult) -> str:
    """Plain-language, non-technical interpretation of a test result."""
    direction = "higher" if result.absolute_lift > 0 else "lower"
    if result.significant:
        return (
            f"The treatment group's conversion rate was {abs(result.relative_lift_pct):.1f}% "
            f"{direction} than control's, and this difference is unlikely to be due to chance "
            f"({result.p_value_display()}, below the {result.alpha} significance threshold). "
            f"We are 95% confident the true lift is between "
            f"{result.ci_low:.2%} and {result.ci_high:.2%} percentage points."
        )
    return (
        f"The treatment group's conversion rate was {abs(result.relative_lift_pct):.1f}% "
        f"{direction} than control's, but this difference could plausibly be due to chance "
        f"({result.p_value_display()}, above the {result.alpha} significance threshold). "
        f"We cannot conclude the treatment had a real effect based on this sample."
    )
