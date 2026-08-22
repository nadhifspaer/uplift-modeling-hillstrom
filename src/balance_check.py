from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multicomp import pairwise_tukeyhsd

TREATMENT_COL = "segment"
CONTROL_LABEL = "No E-Mail"
TREATMENT_LABELS = ("Mens E-Mail", "Womens E-Mail")
NUMERIC_FEATURES = ["recency", "history"]
CATEGORICAL_FEATURES = ["zip_code", "channel", "newbie", "mens", "womens"]
ALPHA = 0.05
SMD_THRESHOLD = 0.1


@dataclass
class SMDResult:
    feature: str
    arm: str
    smd: float
    flagged: bool


@dataclass
class NumericFeatureResult:
    feature: str
    anova_f: float
    anova_p: float
    anova_significant: bool
    posthoc: Optional[pd.DataFrame]
    smd: list[SMDResult]


@dataclass
class CategoricalFeatureResult:
    feature: str
    chi2: float
    chi2_p: float
    chi2_dof: int
    chi2_significant: bool
    smd: list[SMDResult]


def _smd_numeric(treated: pd.Series, control: pd.Series) -> float:
    mean_diff = treated.mean() - control.mean()
    pooled_std = np.sqrt((treated.var(ddof=1) + control.var(ddof=1)) / 2)
    return 0.0 if pooled_std == 0 else mean_diff / pooled_std


def _smd_binary(treated: pd.Series, control: pd.Series) -> float:
    p1, p2 = treated.mean(), control.mean()
    pooled = np.sqrt((p1 * (1 - p1) + p2 * (1 - p2)) / 2)
    return 0.0 if pooled == 0 else (p1 - p2) / pooled


def compute_numeric_smd(
    df: pd.DataFrame,
    feature: str,
    treatment_col: str = TREATMENT_COL,
    control_label: str = CONTROL_LABEL,
    treatment_labels: tuple[str, ...] = TREATMENT_LABELS,
) -> list[SMDResult]:
    control = df.loc[df[treatment_col] == control_label, feature]
    results = []
    for arm in treatment_labels:
        treated = df.loc[df[treatment_col] == arm, feature]
        smd = _smd_numeric(treated, control)
        results.append(SMDResult(feature=feature, arm=arm, smd=smd, flagged=abs(smd) >= SMD_THRESHOLD))
    return results


def compute_categorical_smd(
    df: pd.DataFrame,
    feature: str,
    treatment_col: str = TREATMENT_COL,
    control_label: str = CONTROL_LABEL,
    treatment_labels: tuple[str, ...] = TREATMENT_LABELS,
) -> list[SMDResult]:
    """SMD per category level (each level treated as a 0/1 indicator), pairwise vs. control."""
    control_mask = df[treatment_col] == control_label
    results = []
    for arm in treatment_labels:
        arm_mask = df[treatment_col] == arm
        for level in sorted(df[feature].unique(), key=str):
            treated = (df.loc[arm_mask, feature] == level).astype(int)
            control = (df.loc[control_mask, feature] == level).astype(int)
            smd = _smd_binary(treated, control)
            results.append(
                SMDResult(feature=f"{feature}={level}", arm=arm, smd=smd, flagged=abs(smd) >= SMD_THRESHOLD)
            )
    return results


def run_anova(
    df: pd.DataFrame,
    feature: str,
    treatment_col: str = TREATMENT_COL,
    group_labels: tuple[str, ...] = (CONTROL_LABEL,) + TREATMENT_LABELS,
) -> tuple[float, float]:
    groups = [df.loc[df[treatment_col] == label, feature] for label in group_labels]
    f_stat, p_value = stats.f_oneway(*groups)
    return f_stat, p_value


def run_tukey_posthoc(
    df: pd.DataFrame,
    feature: str,
    treatment_col: str = TREATMENT_COL,
    control_label: str = CONTROL_LABEL,
    treatment_labels: tuple[str, ...] = TREATMENT_LABELS,
) -> pd.DataFrame:
    """Tukey HSD across all three arms, filtered down to Mens-vs-Control and Womens-vs-Control."""
    tukey = pairwise_tukeyhsd(endog=df[feature].to_numpy(), groups=df[treatment_col].to_numpy(), alpha=ALPHA)
    table = tukey._results_table.data
    summary = pd.DataFrame(data=table[1:], columns=table[0])
    relevant = summary[
        ((summary["group1"] == control_label) & (summary["group2"].isin(treatment_labels)))
        | ((summary["group2"] == control_label) & (summary["group1"].isin(treatment_labels)))
    ].reset_index(drop=True)
    return relevant


def check_numeric_feature(
    df: pd.DataFrame,
    feature: str,
    treatment_col: str = TREATMENT_COL,
    control_label: str = CONTROL_LABEL,
    treatment_labels: tuple[str, ...] = TREATMENT_LABELS,
    alpha: float = ALPHA,
) -> NumericFeatureResult:
    group_labels = (control_label,) + tuple(treatment_labels)
    f_stat, p_value = run_anova(df, feature, treatment_col, group_labels)
    significant = p_value < alpha
    posthoc = (
        run_tukey_posthoc(df, feature, treatment_col, control_label, treatment_labels) if significant else None
    )
    smd = compute_numeric_smd(df, feature, treatment_col, control_label, treatment_labels)
    return NumericFeatureResult(
        feature=feature,
        anova_f=f_stat,
        anova_p=p_value,
        anova_significant=significant,
        posthoc=posthoc,
        smd=smd,
    )


def run_chi_square(
    df: pd.DataFrame,
    feature: str,
    treatment_col: str = TREATMENT_COL,
    group_labels: tuple[str, ...] = (CONTROL_LABEL,) + TREATMENT_LABELS,
) -> tuple[float, float, int]:
    subset = df[df[treatment_col].isin(group_labels)]
    contingency = pd.crosstab(subset[feature], subset[treatment_col])
    chi2, p_value, dof, _ = stats.chi2_contingency(contingency)
    return chi2, p_value, dof


def check_categorical_feature(
    df: pd.DataFrame,
    feature: str,
    treatment_col: str = TREATMENT_COL,
    control_label: str = CONTROL_LABEL,
    treatment_labels: tuple[str, ...] = TREATMENT_LABELS,
    alpha: float = ALPHA,
) -> CategoricalFeatureResult:
    group_labels = (control_label,) + tuple(treatment_labels)
    chi2, p_value, dof = run_chi_square(df, feature, treatment_col, group_labels)
    smd = compute_categorical_smd(df, feature, treatment_col, control_label, treatment_labels)
    return CategoricalFeatureResult(
        feature=feature,
        chi2=chi2,
        chi2_p=p_value,
        chi2_dof=dof,
        chi2_significant=p_value < alpha,
        smd=smd,
    )


def run_balance_check(
    df: pd.DataFrame,
    numeric_features: list[str] = NUMERIC_FEATURES,
    categorical_features: list[str] = CATEGORICAL_FEATURES,
    treatment_col: str = TREATMENT_COL,
    control_label: str = CONTROL_LABEL,
    treatment_labels: tuple[str, ...] = TREATMENT_LABELS,
    alpha: float = ALPHA,
) -> tuple[dict[str, NumericFeatureResult], dict[str, CategoricalFeatureResult]]:
    numeric_results = {
        feature: check_numeric_feature(df, feature, treatment_col, control_label, treatment_labels, alpha)
        for feature in numeric_features
    }
    categorical_results = {
        feature: check_categorical_feature(df, feature, treatment_col, control_label, treatment_labels, alpha)
        for feature in categorical_features
    }
    return numeric_results, categorical_results
