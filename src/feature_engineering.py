from __future__ import annotations

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder

from balance_check import TREATMENT_COL, CONTROL_LABEL, TREATMENT_LABELS

DROPPED_COLUMNS = ["history_segment"]

OUTCOME_COLUMNS = ["visit", "conversion", "spend"]

ONE_HOT_FEATURES = ["zip_code", "channel"]

PASSTHROUGH_FEATURES = ["recency", "history", "mens", "womens", "newbie"]


def build_feature_matrix(
    df: pd.DataFrame,
    encoder: OneHotEncoder | None = None,
) -> tuple[pd.DataFrame, OneHotEncoder]:
    for col in OUTCOME_COLUMNS:
        assert col not in PASSTHROUGH_FEATURES + ONE_HOT_FEATURES, (
            f"'{col}' is an outcome column and must never enter the feature matrix (temporal leakage)"
        )

    if encoder is None:
        encoder = OneHotEncoder(sparse_output=False, handle_unknown="ignore")
        encoded = encoder.fit_transform(df[ONE_HOT_FEATURES])
    else:
        encoded = encoder.transform(df[ONE_HOT_FEATURES])

    encoded_df = pd.DataFrame(
        encoded,
        columns=encoder.get_feature_names_out(ONE_HOT_FEATURES),
        index=df.index,
    )

    X = pd.concat([df[PASSTHROUGH_FEATURES], encoded_df], axis=1)
    return X, encoder


def validate_segment(
    df: pd.DataFrame,
    treatment_col: str = TREATMENT_COL,
    control_label: str = CONTROL_LABEL,
    treatment_labels: tuple[str, ...] = TREATMENT_LABELS,
) -> None:
    expected = {control_label, *treatment_labels}
    actual = set(df[treatment_col].dropna().unique())

    if len(actual) != 3:
        raise ValueError(
            f"'{treatment_col}' has {len(actual)} distinct value(s) {sorted(actual)}, expected exactly "
            f"3 ({sorted(expected)}). This looks like an upstream collapse into a binary "
            "'any email vs. no email' flag -- check preprocessing before this point."
        )

    if actual != expected:
        raise ValueError(
            f"'{treatment_col}' has 3 distinct values {sorted(actual)} but they don't match the "
            f"expected labels {sorted(expected)} -- check for typos or relabeling upstream."
        )

    if control_label not in actual:
        raise ValueError(f"control label '{control_label}' not found in '{treatment_col}' values: {sorted(actual)}")


def split_train_holdout(
    df: pd.DataFrame,
    test_size: float = 0.2,
    random_state: int = 42,
    treatment_col: str = TREATMENT_COL,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    train_df, holdout_df = train_test_split(
        df,
        test_size=test_size,
        stratify=df[treatment_col],
        random_state=random_state,
    )
    return train_df, holdout_df
