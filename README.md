# A/B Test Analysis Framework: Checkout Redesign

**Business question:** Did a new single-page checkout improve purchase
conversion rate over the existing 3-step checkout, and is the result
statistically significant?

**TL;DR result:** Yes — conversion rose from **9.91% to 11.37%** (a 14.8%
relative lift), p < 0.0001, 95% CI [0.85%, 2.08%] on the absolute lift,
consistent across desktop/mobile/tablet segments. Full writeup in
[`reports/executive_summary.md`](reports/executive_summary.md).

## Why this project

Most portfolio A/B test projects run a t-test on a clean, pre-packaged
Kaggle CSV and call it done. That skips the part of the job that's actually
hard: real experiment logs are messy, and knowing *what to do about the
mess* (and being able to explain that decision to a stakeholder) is the
actual skill. So this project uses a synthetic dataset built to include the
same problems a real experiment log has — and the cleaning process is
documented, not hidden.

## What's in here

```
data/
  generate_data.py       # generates the synthetic messy dataset
  ab_test_raw.csv         # the raw (messy) data
src/
  ab_test_toolkit.py       # reusable stats functions - see below
notebooks/
  ab_test_analysis.ipynb   # the full analysis, executed end-to-end
reports/
  executive_summary.md     # non-technical writeup for stakeholders
visuals/
  conversion_funnel.png
  conversion_rate_comparison.png
examples/
  quickstart_example.py    # proves the toolkit works on a DIFFERENT experiment
requirements.txt
```

## Data quality issues found (and how they were handled)

The raw log (40,602 rows) had five realistic problems, each investigated and
cleaned with a documented decision rather than silently dropped:

| Issue | Scale | Decision |
|---|---|---|
| user_ids appearing in both groups | ~3% of ids (2,152 rows) | Dropped — can't attribute conversion to either arm without bias |
| Fully duplicated rows | 1.5% | Dropped duplicates, kept first occurrence |
| Missing `device_type` | 4.0% | Kept as `"unknown"` — verified missingness isn't correlated with conversion, so dropping would lose signal for no benefit |
| Two timestamp formats mixed in one column | ~12% | Parsed both formats explicitly |
| Impossible `session_duration` values (negative / >10,000 sec) | 40 rows | Clipped to a valid range, flagged rather than silently overwritten |

Net: 6% of rows removed, all justified in the notebook (Section 2) with the
before/after counts shown, not just asserted.

## The reusable toolkit (`src/ab_test_toolkit.py`)

This isn't analysis code wired to one dataset — it's a small library:

- `run_ab_test()` — two-proportion z-test, p-value, 95% CI on the lift, Cohen's h effect size
- `achieved_power()` — post-hoc power for the sample size you actually have
- `required_sample_size()` — pre-experiment sample size calculator (baseline rate + minimum detectable effect + power -> N per group)
- `interpret()` — plain-language, non-technical result summary

`examples/quickstart_example.py` runs the exact same functions against a
completely different (hypothetical) email subject-line test to prove it's
not hardcoded to the checkout scenario.

## How to reproduce

```bash
pip install -r requirements.txt
python3 data/generate_data.py          # regenerate the raw dataset (optional, already included)
jupyter nbconvert --to notebook --execute --inplace notebooks/ab_test_analysis.ipynb
python3 examples/quickstart_example.py # see the toolkit run on a different scenario
```

## Tools

Python (pandas, NumPy, SciPy, statsmodels), Jupyter, matplotlib.

## What this demonstrates

Experimental design and pre-registration thinking (sample size/power
calculated before results, not just after), statistical rigor (proper
hypothesis test, CI, effect size — not just "which number is bigger"),
real-world data cleaning judgment, and stakeholder communication (technical
notebook + separate non-technical executive summary).
