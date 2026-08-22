from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from causalml.metrics import auuc_score, get_cumlift, get_qini, qini_score

from balance_check import CONTROL_LABEL
from feature_engineering import TREATMENT_COL

MODEL_COL = "X-Learner"
RANDOM_COL = "Random"
RANDOM_SEED = 42

DEFAULT_K_PERCENTS = (10, 20, 30, 40, 50, 60, 70, 80, 90, 100)


@dataclass
class ArmEvaluationResult:
    arm: str
    n_arm: int
    n_control: int
    qini_coefficient: float
    qini_coefficient_random: float
    auuc: float
    auuc_random: float
    uplift_at_k: pd.DataFrame
    qini_curve: pd.DataFrame


def _build_eval_frame(
    df: pd.DataFrame,
    arm: str,
    control_label: str,
    cate_col: str,
    outcome_col: str,
    treatment_col: str,
    random_seed: int,
) -> tuple[pd.DataFrame, int, int]:
    subset = df[df[treatment_col].isin([arm, control_label])]
    w = (subset[treatment_col] == arm).astype(int)
    rng = np.random.RandomState(random_seed)

    eval_df = pd.DataFrame(
        {
            "y": subset[outcome_col].to_numpy(),
            "w": w.to_numpy(),
            MODEL_COL: subset[cate_col].to_numpy(),
            RANDOM_COL: rng.rand(len(subset)),
        }
    )
    return eval_df, int(w.sum()), int((1 - w).sum())


def uplift_at_k(
    eval_df: pd.DataFrame,
    k_percents: tuple[int, ...] = DEFAULT_K_PERCENTS,
) -> pd.DataFrame:
    cumlift = get_cumlift(eval_df, outcome_col="y", treatment_col="w")
    n = cumlift.shape[0]

    rows = []
    for k in k_percents:
        row_idx = min(max(1, round(n * k / 100)), n)
        rows.append(
            {
                "k_pct": k,
                "n_in_bucket": row_idx,
                f"uplift_{MODEL_COL}": cumlift[MODEL_COL].iloc[row_idx - 1],
                f"uplift_{RANDOM_COL}": cumlift[RANDOM_COL].iloc[row_idx - 1],
            }
        )
    return pd.DataFrame(rows)


def evaluate_arm(
    df: pd.DataFrame,
    arm: str,
    cate_col: str,
    control_label: str = CONTROL_LABEL,
    outcome_col: str = "conversion",
    treatment_col: str = TREATMENT_COL,
    k_percents: tuple[int, ...] = DEFAULT_K_PERCENTS,
    random_seed: int = RANDOM_SEED,
) -> ArmEvaluationResult:
    eval_df, n_arm, n_control = _build_eval_frame(
        df, arm, control_label, cate_col, outcome_col, treatment_col, random_seed
    )

    qini = qini_score(eval_df, outcome_col="y", treatment_col="w")
    auuc = auuc_score(eval_df, outcome_col="y", treatment_col="w")
    uplift_k = uplift_at_k(eval_df, k_percents=k_percents)
    qini_curve = get_qini(eval_df, outcome_col="y", treatment_col="w")

    return ArmEvaluationResult(
        arm=arm,
        n_arm=n_arm,
        n_control=n_control,
        qini_coefficient=float(qini[MODEL_COL]),
        qini_coefficient_random=float(qini[RANDOM_COL]),
        auuc=float(auuc[MODEL_COL]),
        auuc_random=float(auuc[RANDOM_COL]),
        uplift_at_k=uplift_k,
        qini_curve=qini_curve,
    )
