from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from balance_check import CONTROL_LABEL
from feature_engineering import TREATMENT_COL

QUADRANT_PERSUADABLE = "Persuadable"
QUADRANT_SURE_THING = "Sure Thing"
QUADRANT_LOST_CAUSE = "Lost Cause"
QUADRANT_SLEEPING_DOG = "Sleeping Dog"

QUADRANT_ORDER = (
    QUADRANT_PERSUADABLE,
    QUADRANT_SURE_THING,
    QUADRANT_LOST_CAUSE,
    QUADRANT_SLEEPING_DOG,
)


@dataclass
class ArmQuadrantResult:
    arm: str
    threshold_control: float
    threshold_treatment: float
    mu0_hat: np.ndarray
    mu1_hat: np.ndarray
    quadrant: pd.Categorical
    counts: pd.Series


def base_rate_thresholds(
    holdout_df: pd.DataFrame,
    arm: str,
    treatment_col: str = TREATMENT_COL,
    control_label: str = CONTROL_LABEL,
    outcome_col: str = "conversion",
) -> tuple[float, float]:
    control_mask = holdout_df[treatment_col] == control_label
    arm_mask = holdout_df[treatment_col] == arm

    if control_mask.sum() == 0:
        raise ValueError(f"no control ('{control_label}') rows found in holdout_df -- can't derive threshold_control")
    if arm_mask.sum() == 0:
        raise ValueError(f"no '{arm}' rows found in holdout_df -- can't derive threshold_treatment")

    threshold_control = float(holdout_df.loc[control_mask, outcome_col].mean())
    threshold_treatment = float(holdout_df.loc[arm_mask, outcome_col].mean())
    return threshold_control, threshold_treatment


def _quadrant_from_flags(would_convert_treatment: np.ndarray, would_convert_control: np.ndarray) -> np.ndarray:
    quadrant = np.empty(would_convert_treatment.shape[0], dtype=object)
    quadrant[would_convert_treatment & ~would_convert_control] = QUADRANT_PERSUADABLE
    quadrant[would_convert_treatment & would_convert_control] = QUADRANT_SURE_THING
    quadrant[~would_convert_treatment & ~would_convert_control] = QUADRANT_LOST_CAUSE
    quadrant[~would_convert_treatment & would_convert_control] = QUADRANT_SLEEPING_DOG
    return quadrant


def assign_quadrants(
    xlearner,
    X_holdout: pd.DataFrame,
    arm: str,
    threshold_control: float,
    threshold_treatment: float,
) -> ArmQuadrantResult:
    if arm not in xlearner.models_mu_t:
        raise KeyError(
            f"'{arm}' is not one of this xlearner's fitted treatment arms {list(xlearner.models_mu_t.keys())} "
            "-- pass the same arm label used at fit time (e.g. from `t_groups`)."
        )

    X = X_holdout.to_numpy() if hasattr(X_holdout, "to_numpy") else X_holdout

    mu0_hat = xlearner.model_mu_c.predict(X)
    mu1_hat = xlearner.models_mu_t[arm].predict(X)

    would_convert_control = mu0_hat > threshold_control
    would_convert_treatment = mu1_hat > threshold_treatment
    quadrant = _quadrant_from_flags(would_convert_treatment, would_convert_control)

    quadrant_cat = pd.Categorical(quadrant, categories=list(QUADRANT_ORDER))
    counts = quadrant_cat.value_counts().reindex(QUADRANT_ORDER, fill_value=0)

    return ArmQuadrantResult(
        arm=arm,
        threshold_control=threshold_control,
        threshold_treatment=threshold_treatment,
        mu0_hat=mu0_hat,
        mu1_hat=mu1_hat,
        quadrant=quadrant_cat,
        counts=counts,
    )


def assign_quadrants_all_arms(
    xlearner,
    X_holdout: pd.DataFrame,
    holdout_df: pd.DataFrame,
    arms: list[str] | None = None,
    treatment_col: str = TREATMENT_COL,
    control_label: str = CONTROL_LABEL,
    outcome_col: str = "conversion",
    threshold_fn=base_rate_thresholds,
) -> dict[str, ArmQuadrantResult]:
    if arms is None:
        arms = list(xlearner.t_groups)

    results = {}
    for arm in arms:
        threshold_control, threshold_treatment = threshold_fn(holdout_df, arm, treatment_col, control_label, outcome_col)
        results[arm] = assign_quadrants(xlearner, X_holdout, arm, threshold_control, threshold_treatment)
    return results


def quadrant_count_table(results: dict[str, ArmQuadrantResult]) -> pd.DataFrame:
    """One row per quadrant, one column per arm: counts, all four quadrants always present."""
    table = pd.DataFrame({arm: res.counts for arm, res in results.items()})
    return table.reindex(QUADRANT_ORDER)


def mu_summary(results: dict[str, ArmQuadrantResult]) -> pd.DataFrame:
    rows = []
    for arm, res in results.items():
        rows.append(
            {
                "arm": arm,
                "threshold_control": res.threshold_control,
                "threshold_treatment": res.threshold_treatment,
                "mu0_hat_mean": res.mu0_hat.mean(),
                "mu0_hat_max": res.mu0_hat.max(),
                "mu1_hat_mean": res.mu1_hat.mean(),
                "mu1_hat_max": res.mu1_hat.max(),
                "pct_above_threshold_control": (res.mu0_hat > res.threshold_control).mean() * 100,
                "pct_above_threshold_treatment": (res.mu1_hat > res.threshold_treatment).mean() * 100,
            }
        )
    return pd.DataFrame(rows)
