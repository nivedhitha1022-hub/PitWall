import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from scipy import stats

from theme import (
    base_layout,
    F1_RED,
    F1_WHITE,
    F1_SILVER,
    F1_DGREY,
    ACCENT_BLUE,
    ACCENT_GREEN,
    ACCENT_AMBER,
    PLAN_COLORS,
    insight,
    section_label,
)


@st.cache_data
def get_model_and_active(subs, sess):
    eng = (
        sess.groupby("subscriber_id")
        .agg(
            avg_engagement=("engagement_score", "mean"),
            total_sessions=("subscriber_id", "count"),
            avg_duration=("session_duration_min", "mean") if "session_duration_min" in sess.columns else ("engagement_score", "size"),
            mobile_pct=("device", lambda x: (x == "Mobile").mean()) if "device" in sess.columns else ("engagement_score", lambda x: 0.5),
        )
        .reset_index()
    )

    df = subs.merge(eng, on="subscriber_id", how="left")
    for col in ["avg_engagement", "total_sessions", "avg_duration"]:
        df[col] = df[col].fillna(0)
    df["mobile_pct"] = df["mobile_pct"].fillna(0.5)

    if "renewal_count" not in df.columns:
        df["renewal_count"] = 0

    for col, enc in [
        ("plan", "plan_enc"),
        ("region", "region_enc"),
        ("acquisition_channel", "channel_enc"),
    ]:
        df[enc] = LabelEncoder().fit_transform(df[col].fillna("Unknown"))

    features = [
        "plan_enc",
        "region_enc",
        "channel_enc",
        "monthly_price_usd",
        "age",
        "tenure_months",
        "renewal_count",
        "nps_score",
        "avg_engagement",
        "total_sessions",
        "avg_duration",
        "mobile_pct",
    ]

    X = df[features].fillna(0)
    y = df["churned_bool"]

    rf = RandomForestClassifier(
        n_estimators=200,
        max_depth=8,
        min_samples_leaf=5,
        class_weight="balanced",
        random_state=42,
    )
    rf.fit(X, y)

    df["churn_prob"] = rf.predict_proba(X)[:, 1]
    df["predicted_clv_6m"] = (df["monthly_price_usd"] * 6 * (1 - df["churn_prob"])).round(2)

    active = df[df["churned"] == "No"].copy()

    rng = np.random.default_rng(42)
    n = len(active)

    active["treatment_uplift"] = np.clip(
        active["churn_prob"].values * 0.6
        + (active["avg_engagement"].values / 100) * 0.4
        + rng.normal(0, 0.08, n),
        0,
        1,
    )

    active["control_response"] = np.clip(
        1 - active["churn_prob"].values + rng.normal(0, 0.05, n),
        0,
        1,
    )

    def _seg(row):
        t, c = row["treatment_uplift"], row["control_response"]
        if t > 0.5 and c < 0.5:
            return "Persuadable"
        if t > 0.5 and c > 0.5:
            return "Sure Thing"
        if t < 0.5 and c < 0.5:
            return "Lost Cause"
        return "Sleeping Dog"

    active["uplift_segment"] = active.apply(_seg, axis=1)
    active["churn_risk_label"] = pd.cut(
        active["churn_prob"],
        bins=[0, 0.33, 0.66, 1.0],
        labels=["Low Risk", "Medium Risk", "High Risk"],
    )
    active["priority_score"] = (active["churn_prob"] * active["predicted_clv_6m"]).round(2)

    return active


def render(subs, sess, mrr, rfm):
    st.markdown("## 🎯 Prescriptive Analytics — *What Should We Do About It?*")
    st.markdown("Uplift modelling, A/B test simulation, and prioritised intervention strategy.")
    st.markdown("---")

    active = get_model_and_active(subs, sess)
    persuadables = active[active["uplift_segment"] == "Persuadable"]

    uplift_colors = {
        "Persuadable": ACCENT_GREEN,
        "Sure Thing": ACCENT_BLUE,
        "Lost Cause": F1_RED,
        "Sleeping Dog": F1_SILVER,
    }

    st.markdown(section_label("UPLIFT MODELLING"), unsafe_allow_html=True)
    st.markdown("##### Which subscribers should receive retention offers?")

    col1, col2 = st.columns([2, 1])

    with col1:
        sample = active.sample(min(600, len(active)), random_state=42) if len(active) else active

        fig = px.scatter(
            sample,
            x="control_response",
            y="treatment_uplift",
            color="uplift_segment",
            color_discrete_map=uplift_colors,
            size="predicted_clv_6m",
            size_max=18,
            hover_data={
                "subscriber_id": True,
                "plan": True,
                "churn_prob": ":.1%",
                "predicted_clv_6m": ":.2f",
            },
            labels={
                "control_response": "Control Response (no offer)",
                "treatment_uplift": "Treatment Response (with offer)",
            },
        )

        fig.add_hline(y=0.5, line_dash="dash", line_color=F1_SILVER, line_width=1)
        fig.add_vline(x=0.5, line_dash="dash", line_color=F1_SILVER, line_width=1)

        fig.update_layout(**base_layout("Uplift Model — Intervention Map", height=420))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        seg_counts = active["uplift_segment"].value_counts()

        fig2 = go.Figure(
            go.Bar(
                x=seg_counts.values,
                y=seg_counts.index,
                orientation="h",
                marker=dict(color=[uplift_colors.get(s, F1_SILVER) for s in seg_counts.index]),
                text=seg_counts.values,
                textposition="outside",
                textfont=dict(color=F1_WHITE),
            )
        )
        fig2.update_layout(**base_layout("Segment Counts", height=240))
        st.plotly_chart(fig2, use_container_width=True)

        st.markdown(
            insight(
                f"🎯 <b>{len(persuadables)} Persuadables</b> identified. These are the subscribers most likely to respond positively to targeted retention action."
            ),
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown(section_label("A/B TEST SIMULATOR"), unsafe_allow_html=True)
    st.markdown("Configure a hypothetical retention offer and estimate its business impact.")

    s1, s2, s3, s4 = st.columns(4)

    discount_pct = s1.slider("Discount Offered (%)", 5, 50, 20, step=5)
    target_segment = s2.selectbox(
        "Target Segment",
        ["All At-Risk", "Pit Lane", "Podium", "Paddock Club", "Persuadables Only"],
    )
    sample_size = s3.slider("Sample Size (per group)", 50, 400, 150, step=25)
    baseline_churn = s4.slider("Baseline Churn Rate (%)", 10, 60, 32, step=1)

    effect_map = {
        "All At-Risk": 0.08,
        "Pit Lane": 0.10,
        "Podium": 0.07,
        "Paddock Club": 0.05,
        "Persuadables Only": 0.15,
    }

    effect = effect_map.get(target_segment, 0.08) * (discount_pct / 20)
    treated_cr = max(0.02, (baseline_churn / 100) - effect)
    ctrl_cr = baseline_churn / 100

    rng2 = np.random.default_rng(99)
    ctrl_churned = int(rng2.binomial(sample_size, ctrl_cr))
    treat_churned = int(rng2.binomial(sample_size, treated_cr))
    ctrl_retained = sample_size - ctrl_churned
    treat_retained = sample_size - treat_churned

    contingency = np.array([[ctrl_churned, ctrl_retained], [treat_churned, treat_retained]])
    chi2, p_val, _, _ = stats.chi2_contingency(contingency)

    lift_pct = ((ctrl_cr - treated_cr) / ctrl_cr * 100) if ctrl_cr > 0 else 0

    avg_price_map = {
        "All At-Risk": 15,
        "Pit Lane": 9.99,
        "Podium": 19.99,
        "Paddock Club": 39.99,
        "Persuadables Only": 15,
    }

    avg_price = avg_price_map.get(target_segment, 15)
    saved_subs = max(0, ctrl_churned - treat_churned)
    mrr_saved = saved_subs * avg_price
    campaign_cost = sample_size * avg_price * (discount_pct / 100) * 0.5
    net_benefit = mrr_saved - campaign_cost

    r1, r2, r3, r4, r5 = st.columns(5)
    r1.metric("Baseline Churn", f"{ctrl_cr:.1%}")
    r2.metric("Treated Churn", f"{treated_cr:.1%}", f"-{lift_pct:.1f}%")
    r3.metric("Subscribers Saved", f"{saved_subs}")
    r4.metric("Net MRR Benefit", f"${net_benefit:,.0f}")
    r5.metric("p-value", f"{p_val:.3f}", "Significant" if p_val < 0.05 else "Not significant")

    col3, col4 = st.columns(2)

    with col3:
        fig3 = go.Figure(
            go.Bar(
                x=[
                    "Control\nChurned",
                    "Control\nRetained",
                    "Treated\nChurned",
                    "Treated\nRetained",
                ],
                y=[ctrl_churned, ctrl_retained, treat_churned, treat_retained],
                marker_color=[F1_RED, ACCENT_GREEN, "#FF6B6B", "#06D6A0"],
                text=[ctrl_churned, ctrl_retained, treat_churned, treat_retained],
                textposition="auto",
                textfont=dict(color=F1_WHITE),
            )
        )
        layout3 = base_layout("A/B Test Outcome Simulation", height=320)
        layout3["yaxis"]["title"] = "Subscribers"
        fig3.update_layout(**layout3)
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        months = list(range(1, 7))
        fig4 = go.Figure()

        fig4.add_trace(
            go.Scatter(
                x=months,
                y=[net_benefit * m for m in months],
                name="Cumulative Benefit",
                mode="lines+markers",
                line=dict(color=ACCENT_GREEN, width=2.5),
            )
        )

        fig4.add_trace(
            go.Scatter(
                x=months,
                y=[campaign_cost * 0.3 * m for m in months],
                name="Cumulative Cost",
                mode="lines+markers",
                line=dict(color=F1_RED, width=2.5),
            )
        )

        layout4 = base_layout("Projected 6-Month ROI", height=320)
        layout4["xaxis"]["title"] = "Month"
        layout4["yaxis"]["title"] = "Cumulative USD"
        fig4.update_layout(**layout4)
        st.plotly_chart(fig4, use_container_width=True)

    st.markdown("---")
    st.markdown(section_label("TOP PRIORITY INTERVENTION TARGETS"), unsafe_allow_html=True)

    top30 = persuadables.sort_values("priority_score", ascending=False).head(30)
    if len(top30) == 0:
        top30 = active.sort_values("priority_score", ascending=False).head(30)

    display = top30[
        [
            "subscriber_id",
            "plan",
            "region",
            "tenure_months",
            "churn_prob",
            "predicted_clv_6m",
            "uplift_segment",
            "avg_engagement",
        ]
    ].copy()

    display.columns = [
        "Subscriber",
        "Plan",
        "Region",
        "Tenure (mo)",
        "Churn Prob",
        "Pred. CLV 6m",
        "Uplift Segment",
        "Avg Engagement",
    ]

    display["Churn Prob"] = display["Churn Prob"].map("{:.1%}".format)
    display["Pred. CLV 6m"] = display["Pred. CLV 6m"].map("${:,.2f}".format)
    display["Avg Engagement"] = display["Avg Engagement"].map("{:.1f}".format)
    display["Tenure (mo)"] = display["Tenure (mo)"].map("{:.1f}".format)

    st.dataframe(display, use_container_width=True, height=340)

    st.markdown("---")
    st.markdown(section_label("STRATEGIC RECOMMENDATIONS"), unsafe_allow_html=True)

    pit_churn = subs.loc[subs["plan"] == "Pit Lane", "churned_bool"].mean() * 100 if (subs["plan"] == "Pit Lane").any() else 0
    padd_churn = subs.loc[subs["plan"] == "Paddock Club", "churned_bool"].mean() * 100 if (subs["plan"] == "Paddock Club").any() else 0
    best_ch = subs.groupby("acquisition_channel")["churned_bool"].mean().idxmin()

    rec1, rec2 = st.columns(2)

    with rec1:
        st.markdown(
            insight(
                f"<b>🏎 REC 1 — Upgrade Conversion Campaign</b><br>"
                f"Pit Lane churns at {pit_churn:.1f}% versus {padd_churn:.1f}% for Paddock Club. Use upgrade nudges for high-risk Pit Lane users before they spin off the track."
            ),
            unsafe_allow_html=True,
        )

        st.markdown(
            insight(
                "<b>📅 REC 2 — First 90-Day Onboarding Sequence</b><br>"
                "The steepest attrition typically happens early. Build a structured welcome journey tied to preferred content and race-week engagement prompts."
            ),
            unsafe_allow_html=True,
        )

        st.markdown(
            insight(
                "<b>🌍 REC 3 — Regional Offer Calibration</b><br>"
                "Use region-level churn and NPS differences to tailor pricing intensity, discount depth, and messaging rather than using one-size-fits-all retention offers."
            ),
            unsafe_allow_html=True,
        )

    with rec2:
        st.markdown(
            insight(
                f"<b>📣 REC 4 — Reallocate Budget to {best_ch}</b><br>"
                f"{best_ch} currently shows the best retention profile. Shift acquisition spend toward channels that bring in subscribers with stronger long-term value."
            ),
            unsafe_allow_html=True,
        )

        st.markdown(
            insight(
                "<b>🎮 REC 5 — Raise the Engagement Floor</b><br>"
                "Users with weak engagement are the rip current underneath churn. Introduce gamified race-week challenges, predictions, and streak mechanics."
            ),
            unsafe_allow_html=True,
        )

        st.markdown(
            insight(
                f"<b>💡 REC 6 — Uplift-Guided Discounting</b><br>"
                f"Target only the {len(persuadables)} persuadable users where discounts can actually change behaviour, instead of giving margin away to users who would stay anyway."
            ),
            unsafe_allow_html=True,
        )
