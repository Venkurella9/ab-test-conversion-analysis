"""
Generates a synthetic, intentionally messy A/B test dataset simulating a
checkout redesign experiment for a fictitious e-commerce site.

Business scenario: The product team replaced a 3-step checkout flow (control)
with a single-page checkout (treatment) and wants to know whether it improved
purchase conversion.

The data is deliberately messy in ways real experiment logs actually are:
  - ~3% of user_ids appear in BOTH groups (cross-contamination from a
    randomization bug / repeat visits with a stale assignment cookie)
  - ~1% fully duplicated rows (double-fired analytics event)
  - ~4% missing device_type
  - timestamps logged in two different formats (two logging systems)
  - a handful of negative / impossibly large session_duration values
  - a mild group-size imbalance (imperfect randomization)

Run: python3 generate_data.py
Output: ab_test_raw.csv in this directory
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

rng = np.random.default_rng(seed=42)

N_CONTROL = 19800
N_TREATMENT = 20400
N_TOTAL = N_CONTROL + N_TREATMENT

# True underlying conversion probabilities (unknown to the "analyst" -
# this is what the experiment is trying to recover).
TRUE_P_CONTROL = 0.100
TRUE_P_TREATMENT = 0.114  # ~14% relative lift

DEVICE_TYPES = ["desktop", "mobile", "tablet"]
DEVICE_WEIGHTS = [0.46, 0.44, 0.10]
COUNTRIES = ["US", "US", "US", "CA", "UK", "IN", "AU", "DE"]

START_DATE = datetime(2026, 6, 1)
EXPERIMENT_DAYS = 21


def make_group(n, group_label, true_p):
    user_ids = rng.integers(100000, 999999, size=n)
    days_offset = rng.integers(0, EXPERIMENT_DAYS, size=n)
    seconds_offset = rng.integers(0, 86400, size=n)
    timestamps = [START_DATE + timedelta(days=int(d), seconds=int(s))
                  for d, s in zip(days_offset, seconds_offset)]

    device = rng.choice(DEVICE_TYPES, size=n, p=DEVICE_WEIGHTS)
    country = rng.choice(COUNTRIES, size=n)

    # Funnel: viewed_product -> added_to_cart -> started_checkout -> completed_purchase
    viewed = np.ones(n, dtype=int)
    add_to_cart_p = 0.42 if group_label == "control" else 0.44
    added = rng.binomial(1, add_to_cart_p, size=n)

    started_checkout_p = 0.55  # of those who added to cart
    started = added * rng.binomial(1, started_checkout_p, size=n)

    # Purchase conversion is defined over the WHOLE assigned group (intent-to-treat),
    # not just those who reached checkout - this is the metric the business question
    # actually cares about. We back it into the funnel so downstream stages stay
    # internally consistent (can't purchase without starting checkout).
    purchased = np.zeros(n, dtype=int)
    target_conversions = int(round(true_p * n))
    eligible = np.where(started == 1)[0]
    # If funnel-eligible pool is smaller than target (shouldn't be, but guard anyway)
    n_purchase = min(target_conversions, len(eligible))
    purchase_idx = rng.choice(eligible, size=n_purchase, replace=False)
    purchased[purchase_idx] = 1

    session_duration = rng.gamma(shape=2.2, scale=55, size=n).round(1)

    df = pd.DataFrame({
        "user_id": user_ids,
        "group": group_label,
        "timestamp": timestamps,
        "device_type": device,
        "country": country,
        "session_duration_sec": session_duration,
        "viewed_product": viewed,
        "added_to_cart": added,
        "started_checkout": started,
        "completed_purchase": purchased,
    })
    return df


control_df = make_group(N_CONTROL, "control", TRUE_P_CONTROL)
treatment_df = make_group(N_TREATMENT, "treatment", TRUE_P_TREATMENT)

df = pd.concat([control_df, treatment_df], ignore_index=True)

# ---- Inject realistic messiness ----

# 1. Cross-contamination: ~3% of rows get user_ids re-used from the OTHER group
#    (simulates a stale assignment cookie / randomization leak)
n_contam = int(0.03 * len(df))
contam_idx = rng.choice(df.index, size=n_contam, replace=False)
swap_ids = rng.choice(df["user_id"].values, size=n_contam, replace=False)
df.loc[contam_idx, "user_id"] = swap_ids

# 2. Fully duplicated rows (~1%) - double-fired analytics event
dup_rows = df.sample(n=int(0.01 * len(df)), random_state=7)
df = pd.concat([df, dup_rows], ignore_index=True)

# 3. Missing device_type (~4%)
missing_idx = rng.choice(df.index, size=int(0.04 * len(df)), replace=False)
df.loc[missing_idx, "device_type"] = np.nan

# 4. Two timestamp formats - convert ~12% of rows to US-style string format,
#    leave the rest as ISO. Both get written to CSV as text, which is exactly
#    how this shows up in real exports.
def fmt_ts(ts, style):
    if style == "us":
        return ts.strftime("%m/%d/%Y %H:%M")
    return ts.strftime("%Y-%m-%dT%H:%M:%S")

us_style_idx = set(rng.choice(df.index, size=int(0.12 * len(df)), replace=False))
df["timestamp"] = [
    fmt_ts(ts, "us") if i in us_style_idx else fmt_ts(ts, "iso")
    for i, ts in zip(df.index, df["timestamp"])
]

# 5. Bad session_duration values: a few negative, a few absurd outliers
bad_neg_idx = rng.choice(df.index, size=25, replace=False)
df.loc[bad_neg_idx, "session_duration_sec"] = -rng.uniform(1, 50, size=25).round(1)

bad_outlier_idx = rng.choice(df.index, size=15, replace=False)
df.loc[bad_outlier_idx, "session_duration_sec"] = rng.uniform(15000, 40000, size=15).round(1)

# 6. Shuffle row order (real exports aren't sorted by group)
df = df.sample(frac=1.0, random_state=99).reset_index(drop=True)

out_path = "ab_test_raw.csv"
df.to_csv(out_path, index=False)
print(f"Wrote {len(df):,} rows to {out_path}")
print(df["group"].value_counts())
