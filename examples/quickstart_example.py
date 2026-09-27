"""
quickstart_example.py
----------------------
Proves the toolkit is actually reusable, not just wired to the checkout case
study: same functions, a completely different experiment (an email subject
line test), zero changes to ab_test_toolkit.py.

Run: python3 examples/quickstart_example.py
"""
import sys
sys.path.insert(0, "../src")

from ab_test_toolkit import run_ab_test, achieved_power, required_sample_size, interpret

# --- Scenario: marketing wants to know if a new email subject line ---
# --- increases open-to-click rate. Numbers below are hypothetical.  ---

N_CONTROL, CLICKS_CONTROL = 5000, 310      # original subject line
N_TREATMENT, CLICKS_TREATMENT = 5000, 365  # new subject line

result = run_ab_test(N_CONTROL, CLICKS_CONTROL, N_TREATMENT, CLICKS_TREATMENT, alpha=0.05)
print(result.summary())
print()
print(interpret(result))
print()

power = achieved_power(N_CONTROL, N_TREATMENT, result.rate_control, result.rate_treatment)
print(f"Achieved power at this sample size: {power:.1%}")

n_needed = required_sample_size(
    baseline_rate=result.rate_control,
    minimum_detectable_effect_relative=0.10,
    alpha=0.05,
    power=0.80,
)
print(f"Sample size needed per group to reliably detect a 10% relative lift: {n_needed:,}")
