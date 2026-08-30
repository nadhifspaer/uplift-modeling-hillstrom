# Uplift Modeling for Email Campaign Effectiveness: Hillstrom MineThatData

Causal inference / uplift modeling project on the Hillstrom MineThatData email dataset. The business question isn't "who will buy" (predictive), it's **"whose purchase was actually caused by the email"** (causal), so campaign budget goes toward customers who convert specifically because of the email, rather than customers who would have bought anyway or customers the email actively discourages.

---

## 1. Project Overview

**Dataset:** ~64,000 customers. `recency`, `history`, `mens`/`womens` (prior category purchase indicators), `zip_code`, `newbie`, `channel` as covariates; `segment` as the randomized treatment; `visit`, `conversion`, `spend` as outcomes (measured *after* treatment; never used as model inputs, since that would be temporal leakage).

**Goal:** find the *Persuadables*, customers who convert only because of the email, without wasting spend on *Sure Things* (would convert anyway), *Lost Causes* (won't convert regardless), or damaging outcomes by emailing *Sleeping Dogs* (conversion drops because of the email). All four quadrants are used and reported consistently, not just the three most commonly discussed.

**Stack:** Python, Pandas, scikit-learn (preprocessing/splitting), `causalml` (modeling), Streamlit (dashboard).

**Evaluation:** Qini Curve, Qini Coefficient, AUUC, and Uplift@K%

---

## 2. Three Arms, Not Binary

`segment` has three values: **Mens E-Mail**, **Womens E-Mail**, **No E-Mail** (control).

- Every metric (Qini, AUUC, Uplift@K%, quadrant breakdown) is computed **separately** for Mens E-Mail vs. Control and Womens E-Mail vs. Control.
- `feature_engineering.py`'s `validate_segment()` runs as an explicit guard immediately before fitting, raising an error (not returning a bool that could be silently ignored) if `segment` doesn't carry exactly the three expected values.

---

## 3. Balance Check

Before modeling, Balance check verifies the randomization is actually balanced across covariates.
- **Numeric** (`recency`, `history`): one-way ANOVA across all three arms, run first, with pairwise Tukey HSD post-hoc only if the ANOVA is significant. Neither feature was significant (p=0.76, p=0.70), so no post-hoc ran.
- **Categorical/binary** (`zip_code`, `channel`, `newbie`, `mens`, `womens`, all 5): chi-square across all three arms. None significant.
- **SMD**, pairwise vs. control, all 28 feature/arm/level combinations: max |SMD| = 0.0137, an order of magnitude below the 0.1 flag threshold.

**Verdict: the randomization looks clean.** No evidence of a randomization bug or covariate imbalance requiring stratification or reweighting.


---

## 4. Modeling Safeguards

**Before fitting:**\
A group-size and stability check reports the size of all three groups (Mens E-Mail, Womens E-Mail, No E-Mail) and checks the control group against a control-to-combined-treatment ratio threshold of 0.3, a project-specific choice rather than one derived from a formula, since a stable baseline estimate needs a reasonably sized control group. This runs alongside the three-arm validation guard described above (`validate_segment()`), immediately before fitting.

**After fitting:**\
A naive-baseline sanity check buckets customers into deciles by model-predicted CATE, then checks whether the naive uplift also ranks the top decile above the bottom decile. Run before any Qini or AUUC number is trusted. It passed on both splits, for both arms.

---

## 5. Method

The model uses `causalml`'s X-Learner method with a Gradient Boosting as its base. Since this is a randomized experiment, the exact probability of each customer receiving a given email arm is already known (it was set by random assignment itself), so that value is provided directly to the model instead of having the model estimate it from the data. Estimating it would only add unnecessary noise, since the true value is already known with certainty.

Thhe data was split 80/20 into a training set and a holdout set, using a fixed random seed for consistency. All results reported are based only on the holdout set, data the model never saw while being traineed.

---

## 6. Results Highlights, Per Arm (Holdout)


| Metric | Mens E-Mail | Womens E-Mail |
|---|---|---|
| Qini coefficient (vs. Random) | 0.06861 (vs. -0.15416) | **0.26601** (vs. -0.06803) |
| AUUC (vs. Random) | 0.57284 (vs. 0.34618) | **0.76675** (vs. 0.43198) |
| Naive-baseline sanity check | **Passes** (train + holdout) | **Passes** (train + holdout) |

**Womens E-Mail ranks uplift meaningfully better than Mens E-Mail:** its Qini coefficient is roughly 4x Mens', and its AUUC is also higher. Both arms clear their random-targeting baseline on both metrics, so both are distinguishable from a random ranking.

**Quadrant breakdown** (base-rate thresholds, holdout, n=12,800 customers per arm):

| Quadrant | Mens E-Mail | Womens E-Mail |
|---|---|---|
| Persuadable | 34.73% | 37.16% |
| Sure Thing | 1.92% | 5.04% |
| Lost Cause | 57.38% | 54.95% |
| Sleeping Dog | 5.98% | 2.86% |

Cross-arm comparisons of this table need care, since `threshold_treatment` is per-arm by design (each arm's own observed holdout conversion rate), so raw percentage-point gaps between arms aren't automatically a pure behavioral difference.

---

## 7. Business Impact Conclusion

- **Mens E-Mail**\
**Mens E-Mail has the larger absolute effect** (~42 incremental conversions across the holdout comparison, the larger raw ATE) but the **weaker targeting precision** (Qini 0.069): most of its value looks broad-based rather than concentrated in an identifiable subgroup, so uplift-based sub-targeting is a modest optimization here, not the primary lever.
- **Womens E-Mail**\
**Womens E-Mail has the smaller absolute effect** (~7.7 incremental conversions) but the **stronger targeting precision** (Qini 0.266), a meaningfully larger share of that smaller effect concentrates in an identifiable high-uplift subgroup, making uplift-based targeting the higher-value lever for this specific campaign.

---

## 8. Repository Structure

```
uplift-modeling-hillstrom/
├── data/
│   ├── hillstrom_email_data.csv
│   └── holdout_scored.parquet
├── notebooks/
│   ├── eda.ipynb                        # EDA and data cleaning
│   ├── 02_covariate_balance_check.ipynb # covariate balance check
│   └── 03_level4_x_learner_causal_forest.ipynb  # X-Learner fit, evaluation, dashboard export
├── src/
│   ├── balance_check.py
│   ├── feature_engineering.py
│   ├── evaluate_qini.py
│   └── quadrant_segmentation.py
├── dashboard/
│   └── app.py                           # Streamlit: Qini curve, uplift distribution, targeting simulator
├── reports/
│   ├── covariate_balance_report.md
│   ├── X-Learner_results_report.md              # X-Learner results write-up
│   ├── business_impact.md
│   ├── qini_curves_holdout.parquet
│   └── figures/                         # balance-check and Qini-curve PNGs
└── requirements.txt
```

---

## 9. Running the Dashboard

```
streamlit run dashboard/app.py
```

Live Demo Link: https://uplift-modeling-hillstrom-2dsckuwyn9bjzgzprkhdtf.streamlit.app/

Sidebar selects the campaign arm (Mens E-Mail / Womens E-Mail vs. the fixed No E-Mail control). Qini Curve and Uplift Score Distribution are wired to the real evaluation outputs described above. the Targeting Simulator slider reuses `evaluate_qini.evaluate_arm(...).uplift_at_k` at an arbitrary percentage, with no refit and no new metric.