# X-Learner Results Report

**Scope note:**\
 This report presents the X-Learner results (through `causalml`, multi-arm treatment), with No Email as the baseline arm.

**Dataset:**\
 Hillstrom MineThatData Email Dataset, three-arm treatment (Mens Email / Womens Email / No Email control).

**Model**:\
causalml (X-Learner), GradientBoostingRegressor (random_state=42). Evaluated on a held-out 20% stratified split never used for fitting.

---

## 1. Naive-Baseline Sanity Check


### Training split

Control (No Email) conversion rate: **0.00516** (n=17,045)

| Arm | Top decile naive uplift | Top decile model CATE | Bottom decile naive uplift | Bottom decile model CATE | Naive ranks top > bottom? | Model ranks top > bottom? |
|---|---|---|---|---|---|---|
| Mens Email | 0.04510 | 0.01505 | -0.01662 | 0.00097 | **True** | **True** |
| Womens Email | 0.03159 | 0.01248 | -0.01887 | -0.00504 | **True** | **True** |

### Holdout split

Control (No Email) conversion rate: **0.00798** (n=4,261)

| Arm | Top decile naive uplift | Top decile model CATE | Bottom decile naive uplift | Bottom decile model CATE | Naive ranks top > bottom? | Model ranks top > bottom? |
|---|---|---|---|---|---|---|
| Mens Email | 0.00524 | 0.01614 | -0.00022 | 0.00163 | **True** | **True** |
| Womens Email | 0.00511 | 0.01282 | -0.00039 | -0.00445 | **True** | **True** |

---

## 2. Qini Coefficient, AUUC, Uplift@K%


<table>
<tr>
<th>Mens Email vs. Control (n_arm=4,262, n_control=4,261)</th>
<th>Womens Email vs. Control (n_arm=4,277, n_control=4,261)</th>
</tr>
<tr>
<td>

| Metric | X-Learner | Random (sanity baseline) |
|---|---|---|
| Qini coefficient | **0.06861** | -0.15416 |
| AUUC | **0.57284** | 0.34618 |

**Uplift@K%:**

| K% | n in bucket | Uplift (X-Learner) | Uplift (Random) |
|---|---|---|---|
| 10 | 852 | 0.005284 | -0.002331 |
| 20 | 1,705 | 0.006071 | -0.000309 |
| 30 | 2,557 | 0.006757 | 0.002892 |
| 40 | 3,410 | 0.004221 | 0.000905 |
| 50 | 4,262 | 0.005978 | 0.003709 |
| 60 | 5,114 | 0.006358 | 0.004322 |
| 70 | 5,967 | 0.005007 | 0.004152 |
| 80 | 6,819 | 0.004553 | 0.004394 |
| 90 | 7,672 | 0.005500 | 0.004463 |
| 100 | 8,524 | 0.004925 | 0.004925 |

</td>
<td>

| Metric | X-Learner | Random (sanity baseline) |
|---|---|---|
| Qini coefficient | **0.26601** | -0.06803 |
| AUUC | **0.76675** | 0.43198 |

**Uplift@K%:**

| K% | n in bucket | Uplift (X-Learner) | Uplift (Random) |
|---|---|---|---|
| 10 | 854 | 0.005110 | 0.004905 |
| 20 | 1,708 | 0.002417 | 0.000503 |
| 30 | 2,562 | 0.000712 | -0.001438 |
| 40 | 3,416 | 0.001024 | -0.000046 |
| 50 | 4,270 | 0.001294 | 0.000051 |
| 60 | 5,123 | 0.001403 | 0.000749 |
| 70 | 5,977 | 0.001186 | 0.001568 |
| 80 | 6,831 | 0.001382 | 0.001118 |
| 90 | 7,685 | 0.001033 | 0.001199 |
| 100 | 8,539 | 0.000905 | 0.000905 |

</td>
</tr>
</table>

---

## 3. Quadrant Breakdown (Holdout)

**per-arm base-rate thresholds**:\
 `threshold_control`= observed holdout control conversion rate (shared across arms, since it's the same physical control pool)\
 `threshold_treatment`= each arm's own observed holdout conversion rate.

`threshold_control = 0.00798` (both arms), `threshold_treatment` = 0.01290 (Mens), 0.00888 (Womens).

| Quadrant | Mens Email (n) | Mens Email (%) | Womens Email (n) | Womens Email (%) |
|---|---|---|---|---|
| Persuadable | 4,445 | 34.73% | 4,756 | 37.16% |
| Sure Thing | 246 | 1.92% | 645 | 5.04% |
| Lost Cause | 7,344 | 57.38% | 7,033 | 54.95% |
| Sleeping Dog | 765 | 5.98% | 366 | 2.86% |

---

## Summary

- Naive-baseline sanity check: passes on both arms. The CATE model's ranking is consistent with a model-free check.
- Qini/AUUC: both arms beat random targeting, Womens Email ranks uplift meaningfully better than Mens Email by both metrics on holdout.
- Quadrant sizes are real and non-degenerate under the base-rate threshold (unlike under a naive 0.5 cutoff), but cross-arm quadrant-rate comparisons require controlling for the per-arm threshold difference first.