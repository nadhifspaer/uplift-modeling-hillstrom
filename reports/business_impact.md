# Business Impact Report: Uplift-Based Targeting vs. Sending to Everyone

This report translates the Qini, AUUC, and Uplift@K% results into a business-facing answer on whether uplift-based targeting is worth pursuing. Everything below is expressed in email volume reduction versus incremental conversions captured, computed directly from the project's evaluation outputs. Mens E-Mail and Womens E-Mail are reported separately, each with its own verdict, table, and recommendation, since averaging them together would hide that they tell very different stories.

- **This is a historical, holdout-based estimate, not a live-deployment forecast,** the same limitation that applies to the dashboard's Targeting Simulator.

---

## 1. Headline verdict, per campaign

| | Mens E-Mail | Womens E-Mail |
|---|---|---|
| Qini coefficient (vs. Random) | 0.06861 (vs. -0.15416) | **0.26601** (vs. -0.06803) |
| AUUC (vs. Random) | 0.57284 (vs. 0.34618) | **0.76675** (vs. 0.43198) |
| Beats random targeting? | Yes, by a small margin | **Yes, clearly** |

**Womens E-Mail:**\
Womens E-mail shows real meaningfully better incremental-targeting value. Its Qini coefficient is roughly 4x Mens' and its AUUC is well clear of the random baseline.

 **Mens E-Mail:**\
 Mens E-Mail shows a real but much weaker signal. It does beat random on both metrics, with a genuine effect present, but the edge is small and noisier at the per-decile level. Neither result substitutes for the other.

---

## 2. Campaign volume vs capture tables

### Mens E-Mail vs. Control

| Volume targeted (top K%) | Volume reduction vs. targeting everyone | Cumulative incremental conversions (model) | % of total achievable captured |
|---|---|---|---|
| 10% | 90% fewer emails | 4.5 | 10.7% |
| 20% | 80% fewer emails | 10.4 | 24.7% |
| 30% | 70% fewer emails | 17.3 | 41.2% |
| 40% | 60% fewer emails | 14.4 | 34.3% |
| 50% | 50% fewer emails | 25.5 | 60.7% |
| 60% | 40% fewer emails | 32.5 | 77.4% |
| 70% | 30% fewer emails | 29.9 | 71.2% |
| 80% | 20% fewer emails | 31.0 | 74.0% |
| 90% | 10% fewer emails | 42.2 | 100.5% |
| 100% | baseline (send to everyone) | 42.0 | 100.0% |

### Womens E-Mail vs. Control

| Volume targeted (top K%) | Volume reduction vs. targeting everyone | Cumulative incremental conversions (model) | % of total achievable captured |
|---|---|---|---|
| 10% | 90% fewer emails | 4.4 | 56.4% |
| 20% | 80% fewer emails | 4.1 | 53.4% |
| 30% | 70% fewer emails | 1.8 | 23.6% |
| 40% | 60% fewer emails | 3.5 | 45.2% |
| 50% | 50% fewer emails | 5.5 | 71.5% |
| 60% | 40% fewer emails | 7.2 | 93.0% |
| 70% | 30% fewer emails | 7.1 | 91.7% |
| 80% | 20% fewer emails | 9.4 | **122.1%** |
| 90% | 10% fewer emails | 7.9 | 102.7% |
| 100% | baseline (send to everyone) | 7.7 | 100.0% |

---

## 3. Founding & Summary

**Higher Qini/AUUC turned out to reflect ranking quality, not campaign size.**

- **Mens E-Mail has the larger absolute effect:**\
 Roughly 42.0 incremental conversions across the 8,524-person holdout comparison, about **5.4x more incremental conversions in absolute terms** than Womens.
- **Womens E-Mail has the better targeting precision:**\
 Its Qini/AUUC advantage means the model can much more reliably identify which Womens-eligible customers are worth targeting, even though the total pool of achievable incremental conversions is smaller.

These are two different levers:
- For **Mens E-Mail**, most of the campaign's value seems spread evenly across most customers rather than concentrated in one clear group (Qini 0.069 is real but small), so targeting only a subset doesn't gain much. Sending to everyone is a reasonable approach here, and using the model to target specific customers only adds a small improvement.
- For **Womens E-Mail**, a much bigger share of the available effect comes from one clear high-uplift group of customers (Qini 0.266), so choosing the right customers matters a lot more here. This makes uplift-based targeting the more valuable approach specifically for this campaign.

---

## 4. Recommendation

- **Do not commit to a specific cutoff for either campaign**\
 Based on this data alone, the results are too noisy for that level of detail. A safer, more general point: **targeting the top 50%** captures roughly 61% Mens / 72% Womens of the extra conversions available while cutting email volume in half for both. This is a good starting point because it doesn't depend on one specific, unreliable number.
- **Mens E-Mail:**\
**Treat targeting as a small improvement, not the main strategy**. THe model does better than random, but the case for cutting email volume aggressively is weak given how small and inconsistent the advantage is. 
- **Womens E-Mail:**\
**The strogner case, aggressive targeting.** The advantage here is consistent and reliable, and a large portion of the available benefit comes form one clear, identifiable group of customers,
- **Re-check before making any decision.**\
Both tables would be more trustworthy with more data (more converters) before picking an exact voolume threshold to act on. This report points toward a general direction, not an exact number to use.
