# Executive Summary: Checkout Redesign A/B Test

**Prepared for:** Product & Growth stakeholders
**Prepared by:** Venkata Kurella
**Experiment window:** 21 days, 38,166 users (after data cleaning)

## The question

We replaced the existing 3-step checkout with a single-page checkout for a
random half of visitors, and asked: does the new checkout get more people to
actually complete a purchase?

## The result

**Yes. The new checkout increased purchase conversion by about 15%, and we're
confident this wasn't a fluke.**

| | Old checkout (control) | New checkout (treatment) |
|---|---|---|
| Purchase conversion rate | 9.91% | 11.37% |

That's a **1.46 percentage point** improvement — roughly **15 more purchases
for every 1,000 visitors** who would previously have left without buying.

We ran the statistics to rule out random noise as the explanation: the
probability of seeing a gap this large by chance alone is well under 1 in
10,000. We're 95% confident the true improvement is somewhere between 0.85
and 2.08 percentage points — even the low end of that range is a solid win.

We also checked the result separately for desktop, mobile, and tablet users.
The new checkout came out ahead in every segment, which tells us this isn't
an artifact of one device type skewing the numbers.

## What we'd flag before a full rollout

- **Tablet traffic is a smaller slice of the experiment**, so our confidence
  in that specific segment is lower than for desktop/mobile. Worth a quick
  recheck after a broader rollout rather than treating it as unproven.
- **Cleaning the raw data removed about 6% of rows** — mostly users who
  ended up logged into both the old and new checkout (a tracking issue, not
  a checkout problem) and a handful of duplicate event logs. None of this
  changes the conclusion, but the tracking issue is worth a look so future
  experiments don't need this cleanup step.

## Recommendation

**Ship the single-page checkout to 100% of traffic.** The effect is real,
meaningfully sized, and consistent across the segments we can measure with
confidence.

---
*Full statistical methodology, data cleaning steps, and code:
see `notebooks/ab_test_analysis.ipynb`.*
