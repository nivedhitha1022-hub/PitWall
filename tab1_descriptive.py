import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

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
    SEGMENT_COLORS,
    insight,
    section_label,
)


def rgba_fill(color, alpha=0.15):
    if isinstance(color, str) and "rgb(" in color:
        return color.replace("rgb(", "rgba(").replace(")", f", {alpha})")
    return f"rgba(155, 155, 155, {alpha})"


def render(subs, sess, mrr, rfm):
    st.markdown("## 📋 Descriptive Analytics — *Who Are Our Subscribers?*")
    st.markdown(
        "High-level snapshot of the subscriber base, revenue trajectory, and RFM segmentation."
    )
    st.markdown("---")

    active = subs[subs["churned"] == "No"].copy()

    total_mrr_series = mrr.groupby("month_dt")["mrr_usd"].sum().sort_index()
    total_mrr = total_mrr_series.iloc[-1] if not total_mrr_series.empty else 0

    churn_rate = subs["churned_bool"].mean() * 100 if len(subs) else 0
    avg_nps = subs["nps_score"].mean() if "nps_score" in subs.columns else 0

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Total Subscribers", f"{len(subs):,}")
    k2.metric(
        "Active Subscribers",
        f"{len(active):,}",
        f"{(len(active) / len(subs) * 100):.1f}% active" if len(subs) else "0.0% active",
    )
    k3.metric("Latest MRR", f"${total_mrr:,.0f}")
    k4.metric("Overall Churn Rate", f"{churn_rate:.1f}%")
    k5.metric("Avg NPS Score", f"{avg_nps:.1f}/10" if pd.notna(avg_nps) else "N/A")

    st.markdown("---")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(section_label("REVENUE GROWTH"), unsafe_allow_html=True)

        mrr_plot = mrr.copy()
        if "plan" not in mrr_plot.columns:
            mrr_plot["plan"] = "Total"

        mrr_pivot = (
            mrr_plot.pivot_table(
                index="month_dt",
                columns="plan",
                values="mrr_usd",
                aggfunc="sum",
            )
            .fillna(0)
            .sort_index()
        )

        fig = go.Figure()
        first_trace = True

        for plan, color in PLAN_COLORS.items():
            if plan in mrr_pivot.columns:
                fig.add_trace(
                    go.Scatter(
                        x=mrr_pivot.index,
                        y=mrr_pivot[plan],
                        name=plan,
                        mode="lines",
                        fill="tozeroy" if first_trace else "tonexty",
                        line=dict(color=color, width=2),
                        fillcolor=rgba_fill(color),
                        hovertemplate=f"<b>{plan}</b><br>%{{x|%b %Y}}<br>MRR: $%{{y:,.0f}}<extra></extra>",
                    )
                )
                first_trace = False

        if len(fig.data) == 0 and not total_mrr_series.empty:
            fig.add_trace(
                go.Scatter(
                    x=total_mrr_series.index,
                    y=total_mrr_series.values,
                    name="Total",
                    mode="lines",
                    fill="tozeroy",
                    line=dict(color=ACCENT_BLUE, width=2),
                    fillcolor=rgba_fill("rgb(0, 102, 204)"),
                    hovertemplate="<b>Total</b><br>%{x|%b %Y}<br>MRR: $%{y:,.0f}<extra></extra>",
                )
            )

        layout = base_layout("Monthly Recurring Revenue by Plan", height=340)
        layout["xaxis"]["title"] = "Month"
        layout["yaxis"]["title"] = "MRR (USD)"
        fig.update_layout(**layout)

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown(section_label("PLAN DISTRIBUTION"), unsafe_allow_html=True)

        plan_counts = subs["plan"].fillna("Unknown").value_counts()

        fig2 = go.Figure(
            go.Pie(
                labels=plan_counts.index,
                values=plan_counts.values,
                hole=0.55,
                marker=dict(
                    colors=[PLAN_COLORS.get(p, F1_SILVER) for p in plan_counts.index],
                    line=dict(color=F1_DGREY, width=2),
                ),
                textinfo="label+percent",
                textfont=dict(color=F1_WHITE, size=11),
                hovertemplate="<b>%{label}</b><br>Subscribers: %{value}<br>%{percent}<extra></extra>",
            )
        )

        fig2.update_layout(**base_layout("Subscriber Split", height=340))
        fig2.add_annotation(
            text=f"<b>{len(subs)}</b><br>subs",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(color=F1_WHITE, size=14),
        )

        st.plotly_chart(fig2, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        st.markdown(section_label("SUBSCRIBERS BY REGION"), unsafe_allow_html=True)

        reg = (
            subs.groupby("region", dropna=False)
            .agg(
                subscribers=("subscriber_id", "count"),
                churn_rate=("churned_bool", "mean"),
            )
            .reset_index()
            .sort_values("subscribers")
        )

        reg["region"] = reg["region"].fillna("Unknown")

        fig3 = go.Figure()
        fig3.add_trace(
            go.Bar(
                y=reg["region"],
                x=reg["subscribers"],
                orientation="h",
                marker=dict(
                    color=reg["churn_rate"],
                    colorscale=[
                        [0, ACCENT_GREEN],
                        [0.5, ACCENT_AMBER],
                        [1, F1_RED],
                    ],
                    showscale=True,
                    colorbar=dict(title="Churn Rate"),
                ),
                hovertemplate="<b>%{y}</b><br>Subscribers: %{x}<br>Churn: %{marker.color:.1%}<extra></extra>",
            )
        )

        layout3 = base_layout("Subscribers & Churn Rate by Region", height=320)
        layout3["xaxis"]["title"] = "Subscribers"
        fig3.update_layout(**layout3)

        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        st.markdown(section_label("ACQUISITION CHANNEL PERFORMANCE"), unsafe_allow_html=True)

        ch = (
            subs.groupby("acquisition_channel", dropna=False)
            .agg(
                count=("subscriber_id", "count"),
                churn=("churned_bool", "mean"),
            )
            .reset_index()
        )

        ch["acquisition_channel"] = ch["acquisition_channel"].fillna("Unknown")

        fig4 = go.Figure()

        fig4.add_trace(
            go.Bar(
                x=ch["acquisition_channel"],
                y=ch["count"],
                marker_color=ACCENT_BLUE,
                name="Subscribers",
                hovertemplate="<b>%{x}</b><br>Subscribers: %{y}<extra></extra>",
            )
        )

        fig4.add_trace(
            go.Scatter(
                x=ch["acquisition_channel"],
                y=ch["churn"] * 100,
                name="Churn %",
                mode="lines+markers",
                line=dict(color=F1_RED, width=2),
                marker=dict(size=8),
                yaxis="y2",
                hovertemplate="<b>%{x}</b><br>Churn: %{y:.1f}%<extra></extra>",
            )
        )

        layout4 = base_layout("Channel: Volume vs Churn Rate", height=320)
        layout4["yaxis"]["title"] = "Subscribers"
        layout4["yaxis2"] = dict(
            title="Churn %",
            overlaying="y",
            side="right",
            showgrid=False,
        )
        fig4.update_layout(**layout4)

        st.plotly_chart(fig4, use_container_width=True)

    st.markdown("---")
    st.markdown(section_label("RFM CUSTOMER SEGMENTATION"), unsafe_allow_html=True)

    col5, col6 = st.columns([1, 2])

    with col5:
        seg_summary = (
            rfm.groupby("segment", dropna=False)
            .agg(
                count=("subscriber_id", "count"),
                avg_ltv=("monetary", "mean"),
            )
            .reset_index()
            .sort_values("avg_ltv", ascending=False)
        )

        fig6 = go.Figure(
            go.Bar(
                x=seg_summary["count"],
                y=seg_summary["segment"],
                orientation="h",
                marker=dict(color=seg_summary["segment"].map(SEGMENT_COLORS).fillna(F1_SILVER)),
                hovertemplate="<b>%{y}</b><br>Subscribers: %{x}<extra></extra>",
            )
        )

        fig6.update_layout(**base_layout("Segment Size", height=380))
        st.plotly_chart(fig6, use_container_width=True)

    with col6:
        fig7 = px.scatter(
            rfm,
            x="recency_days",
            y="frequency",
            size="monetary",
            color="segment",
            color_discrete_map=SEGMENT_COLORS,
            size_max=28,
            hover_data=["subscriber_id", "plan", "region", "churned"],
        )

        fig7.update_layout(**base_layout("RFM Scatter", height=380))
        st.plotly_chart(fig7, use_container_width=True)

    st.markdown("---")
    st.markdown(section_label("KEY INSIGHTS"), unsafe_allow_html=True)

    champions = rfm[rfm["segment"] == "Champion"]
    lost = rfm[rfm["segment"] == "Lost"]

    i1, i2 = st.columns(2)

    with i1:
        champion_avg = champions["monetary"].mean() if len(champions) else 0
        st.markdown(
            insight(
                f"🏆 <b>{len(champions)} Champions</b> drive the majority of lifetime value averaging "
                f"<b>${champion_avg:,.0f}</b>."
            ),
            unsafe_allow_html=True,
        )

    with i2:
        st.markdown(
            insight(
                f"⚠️ <b>{len(lost)} Lost subscribers</b> have extremely low recency and engagement."
            ),
            unsafe_allow_html=True,
        )
