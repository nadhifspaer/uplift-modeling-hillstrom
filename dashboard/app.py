from __future__ import annotations

import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

# Path
APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent
REPORTS_DIR = PROJECT_ROOT / "reports"
DATA_DIR = PROJECT_ROOT / "data"
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))
from balance_check import CONTROL_LABEL, TREATMENT_LABELS  # ("No E-Mail", ("Mens E-Mail", "Womens E-Mail"))
from evaluate_qini import evaluate_arm  # Read, bukan untuk predict

MODEL_COMPARISON_PATH = REPORTS_DIR / "X-Learner_results_report.md"
BALANCE_REPORT_PATH = REPORTS_DIR / "covariate_balance_report.md"
BUSINESS_IMPACT_PATH = REPORTS_DIR / "business_impact.md"
HOLDOUT_SCORED_PATH = DATA_DIR / "holdout_scored.parquet"
QINI_CURVES_PATH = REPORTS_DIR / "qini_curves_holdout.parquet"

MENS_LABEL, WOMENS_LABEL = TREATMENT_LABELS


MODEL_COL = "X-Learner"
RANDOM_COL = "Random"
SERIES_COLORS = {MODEL_COL: "#2a78d6", RANDOM_COL: "#eb6834"}
SERIES_DASH = {MODEL_COL: [1, 0], RANDOM_COL: [6, 3]}

alt.data_transformers.disable_max_rows()


def _cate_col(arm: str) -> str:
    return f"cate_{arm.replace(' ', '_').replace('-', '')}"

st.set_page_config(page_title="Hillstrom Uplift Dashboard", layout="wide")

st.sidebar.title("Campaign Arm")
selected_arm = st.sidebar.radio(
    "Compare against control:",
    TREATMENT_LABELS,
)


# Header
st.title("Uplift Modeling Dashboard")
st.caption(
    "Hillstrom MineThatData email campaign: "
    f"({MENS_LABEL} / {WOMENS_LABEL} / {CONTROL_LABEL})"
)
st.markdown(f"{selected_arm} vs. Control ({CONTROL_LABEL})")

st.divider()

# Section 1
st.header("Qini Curve")

if QINI_CURVES_PATH.exists():
    qini_long = pd.read_parquet(QINI_CURVES_PATH)
    arm_curve = qini_long[qini_long["arm"] == selected_arm]

    plot_df = arm_curve.melt(
        id_vars=["population"], value_vars=[MODEL_COL, RANDOM_COL], var_name="series", value_name="cumulative_gain"
    )

    max_points_per_series = 1000
    if len(arm_curve) > max_points_per_series:
        step = len(arm_curve) // max_points_per_series
        keep_population = set(arm_curve["population"].iloc[::step]) | {
            arm_curve["population"].iloc[0], arm_curve["population"].iloc[-1]
        }
        plot_df = plot_df[plot_df["population"].isin(keep_population)]

    base = alt.Chart(plot_df).encode(
        x=alt.X("population:Q", title="Population (ranked by predicted CATE, descending)"),
    )
    lines = base.mark_line(strokeWidth=2, point=alt.OverlayMarkDef(opacity=0)).encode(
        y=alt.Y("cumulative_gain:Q", title="Cumulative Gain"),
        color=alt.Color(
            "series:N",
            scale=alt.Scale(domain=list(SERIES_COLORS), range=list(SERIES_COLORS.values())),
            legend=alt.Legend(title=None),
        ),
        strokeDash=alt.StrokeDash(
            "series:N", scale=alt.Scale(domain=list(SERIES_DASH), range=list(SERIES_DASH.values())), legend=None
        ),
        tooltip=[
            alt.Tooltip("series:N", title="Series"),
            alt.Tooltip("population:Q", title="Population"),
            alt.Tooltip("cumulative_gain:Q", title="Cumulative Gain", format=".3f"),
        ],
    )
    zero_rule = alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(color="#c3c2b7", strokeWidth=1).encode(y="y:Q")

    st.altair_chart((zero_rule + lines).properties(height=380), use_container_width=True)
else:
    st.warning(
        f"Not found: `{QINI_CURVES_PATH.relative_to(PROJECT_ROOT)}` : run notebook 03's Stage 6.2 export cell first."
    )

st.divider()

# Section 2
st.header("Uplift Score Distribution")

if HOLDOUT_SCORED_PATH.exists():
    holdout_scored = pd.read_parquet(HOLDOUT_SCORED_PATH)
    cate_col = _cate_col(selected_arm)

    if cate_col in holdout_scored.columns:
        hist = (
            alt.Chart(holdout_scored)
            .mark_bar(color=SERIES_COLORS[MODEL_COL])
            .encode(
                x=alt.X(f"{cate_col}:Q", bin=alt.Bin(maxbins=40), title=f"Predicted CATE: {selected_arm} vs. Control"),
                y=alt.Y("count():Q", title="Customers (holdout)"),
                tooltip=[
                    alt.Tooltip(f"{cate_col}:Q", bin=alt.Bin(maxbins=40), title="CATE bin"),
                    alt.Tooltip("count():Q", title="Customers"),
                ],
            )
        )
        zero_rule = (
            alt.Chart(pd.DataFrame({"x": [0]}))
            .mark_rule(color="#c3c2b7", strokeWidth=1, strokeDash=[4, 2])
            .encode(x="x:Q")
        )
        st.altair_chart((hist + zero_rule).properties(height=350), use_container_width=True)
    else:
        st.warning(f"Column `{cate_col}` not found in `{HOLDOUT_SCORED_PATH.relative_to(PROJECT_ROOT)}`.")
else:
    st.warning(
        f"Not found: `{HOLDOUT_SCORED_PATH.relative_to(PROJECT_ROOT)}` : run notebook 03's Stage 6.2 export cell first."
    )

st.divider()

# Section
st.header("Targeting Simulator")

if HOLDOUT_SCORED_PATH.exists():
    holdout_scored_sim = pd.read_parquet(HOLDOUT_SCORED_PATH)
    cate_col = _cate_col(selected_arm)

    if cate_col in holdout_scored_sim.columns:
        x_pct = st.slider(
            "Target top X% of customers by predicted uplift",
            min_value=1,
            max_value=100,
            value=20,
            step=1,
        )

        sim = evaluate_arm(holdout_scored_sim, arm=selected_arm, cate_col=cate_col, k_percents=(x_pct,))
        row = sim.uplift_at_k.iloc[0]
        n_in_bucket = int(row["n_in_bucket"])
        uplift_model = row[f"uplift_{MODEL_COL}"]
        uplift_random = row[f"uplift_{RANDOM_COL}"]
        est_incremental_model = uplift_model * n_in_bucket
        est_incremental_random = uplift_random * n_in_bucket

        col1, col2, col3 = st.columns(3)
        col1.metric(f"Customers in top {x_pct}%", f"{n_in_bucket:,}")
        col2.metric("Est. incremental conversions: model targeting", f"{est_incremental_model:,.1f}")
        col3.metric(
            "Est. incremental conversions: random targeting",
            f"{est_incremental_random:,.1f}",
            delta=f"{est_incremental_model - est_incremental_random:+.1f} vs. random",
        )
    else:
        st.warning(f"Column `{cate_col}` not found in `{HOLDOUT_SCORED_PATH.relative_to(PROJECT_ROOT)}`.")
else:
    st.warning(
        f"Not found: `{HOLDOUT_SCORED_PATH.relative_to(PROJECT_ROOT)}` : run notebook 03's Stage 6.2 export cell first."
    )

st.divider()

st.header("Reports Already Produced")

with st.expander("Results Report"):
    if MODEL_COMPARISON_PATH.exists():
        st.markdown(MODEL_COMPARISON_PATH.read_text(encoding="utf-8"))
    else:
        st.warning(f"Not found: `{MODEL_COMPARISON_PATH.relative_to(PROJECT_ROOT)}`")

with st.expander("Covariate Balance Report"):
    if BALANCE_REPORT_PATH.exists():
        st.markdown(BALANCE_REPORT_PATH.read_text(encoding="utf-8"))
    else:
        st.warning(f"Not found: `{BALANCE_REPORT_PATH.relative_to(PROJECT_ROOT)}`")

with st.expander("Business Impact Report"):
    if BUSINESS_IMPACT_PATH.exists():
        st.markdown(BUSINESS_IMPACT_PATH.read_text(encoding="utf-8"))
    else:
        st.warning(f"Not found: `{BUSINESS_IMPACT_PATH.relative_to(PROJECT_ROOT)}`")
