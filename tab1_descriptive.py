import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from theme import (base_layout, F1_RED, F1_WHITE, F1_SILVER, F1_GREY, F1_DGREY,
                   F1_GOLD, F1_LGREY, ACCENT_BLUE, ACCENT_GREEN, ACCENT_AMBER,
                   PLAN_COLORS, REGION_COLORS, SEGMENT_COLORS, insight, section_label)


def render(subs, sess, mrr, rfm):
    st.markdown("## 📋 Descriptive Analytics — *Who Are Our Subscribers?*")
    st.markdown("High-level snapshot of the subscriber base, revenue trajectory, and RFM segmentation.")
    st.markdown("---")

    # ── KPI Row ───────────────────────────────────────────────────────────────
    active  = subs[subs["churned"] == "No"]
    total_mrr = mrr.groupby("month_dt")["mrr_usd"].sum().sort_index().iloc[-1]
    avg_tenure = subs[subs["churned"] == "No"]["tenure_months"].mean()
    churn_rate = subs["churned_bool"].mean() * 100
    avg_nps    = subs["nps_score"].mean()

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Total Subscribers",  f"{len(subs):,}")
    k2.metric("Active Subscribers", f"{len(active):,}", f"{len(active)/len(subs)*100:.1f}% active")
    k3.metric("Latest MRR",         f"${total_mrr:,.0f}")
    k4.metric("Overall Churn Rate", f"{churn_rate:.1f}%")
    k5.metric("Avg NPS Score",      f"{avg_nps:.1f}/10")

    st.markdown("---")

    # ── Row 1: MRR over time | Plan mix ──────────────────────────────────────
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(section_label("REVENUE GROWTH"), unsafe_allow_html=True)
        mrr_pivot = mrr.pivot_table(index="month_dt", columns="plan", values="mrr_usd", aggfunc="sum").fillna(0)
        fig = go.Figure()
        for plan, color in PLAN_COLORS.items():
            if plan in mrr_pivot.columns:
                fig.add_trace(go.Scatter(
                    x=mrr_pivot.index, y=mrr_pivot[plan],
                    name=plan, fill="tonexty", mode="lines",
                    line=dict(color=color, width=2),
                    fillcolor=color.replace(")", ",0.15)").replace("rgb", "rgba") if "rgb" in color else color + "26",
                    hovertemplate=f"<b>{plan}</b><br>%{{x|%b %Y}}<br>MRR: $%{{y:,.0f}}<extra></extra>"
                ))
        layout = base_layout("Monthly Recurring Revenue by Plan", height=340)
        layout["xaxis"]["title"] = "Month"
        layout["yaxis"]["title"] = "MRR (USD)"
        fig.update_layout(**layout)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown(section_label("PLAN DISTRIBUTION"), unsafe_allow_html=True)
        plan_counts = subs["plan"].value_counts()
        fig2 = go.Figure(go.Pie(
            labels=plan_counts.index,
            values=plan_counts.values,
            hole=0.55,
            marker=dict(colors=[PLAN_COLORS.get(p, F1_SILVER) for p in plan_counts.index],
                        line=dict(color=F1_DGREY, width=2)),
            textinfo="label+percent",
            textfont=dict(color=F1_WHITE, size=11),
            hovertemplate="<b>%{label}</b><br>%{value} subscribers (%{percent})<extra></extra>"
        ))
        fig2.update_layout(**base_layout("Subscriber Split", height=340))
        fig2.add_annotation(text=f"<b>{len(subs)}</b><br>subs", x=0.5, y=0.5,
                            font=dict(color=F1_WHITE, size=14), showarrow=False)
        st.plotly_chart(fig2, use_container_width=True)

    # ── Row 2: Region | Acquisition channel ──────────────────────────────────
    col3, col4 = st.columns(2)

    with col3:
        st.markdown(section_label("SUBSCRIBERS BY REGION"), unsafe_allow_html=True)
        reg = subs.groupby("region").agg(
            subscribers=("subscriber_id", "count"),
            churn_rate=("churned_bool", "mean")
        ).reset_index().sort_values("subscribers", ascending=True)
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(
            y=reg["region"], x=reg["subscribers"],
            orientation="h", name="Subscribers",
            marker=dict(color=reg["churn_rate"], colorscale=[[0,ACCENT_GREEN],[0.5,ACCENT_AMBER],[1,F1_RED]],
                        showscale=True, colorbar=dict(title="Churn Rate", tickformat=".0%",
                        tickfont=dict(color=F1_SILVER))),
            hovertemplate="<b>%{y}</b><br>Subscribers: %{x}<br>Churn: %{marker.color:.1%}<extra></extra>"
        ))
        layout3 = base_layout("Subscribers & Churn Rate by Region", height=320)
        layout3["xaxis"]["title"] = "Subscribers"
        fig3.update_layout(**layout3)
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        st.markdown(section_label("ACQUISITION CHANNEL PERFORMANCE"), unsafe_allow_html=True)
        ch = subs.groupby("acquisition_channel").agg(
            count=("subscriber_id","count"),
            churn=("churned_bool","mean"),
            avg_ltv=("lifetime_revenue_usd","mean")
        ).reset_index()
        fig4 = go.Figure()
        fig4.add_trace(go.Bar(
            x=ch["acquisition_channel"], y=ch["count"],
            name="Subscribers", marker_color=ACCENT_BLUE,
            yaxis="y", hovertemplate="<b>%{x}</b><br>Subs: %{y}<extra></extra>"
        ))
        fig4.add_trace(go.Scatter(
            x=ch["acquisition_channel"], y=ch["churn"]*100,
            name="Churn %", mode="lines+markers",
            line=dict(color=F1_RED, width=2), marker=dict(size=8),
            yaxis="y2", hovertemplate="Churn: %{y:.1f}%<extra></extra>"
        ))
        layout4 = base_layout("Channel: Volume vs Churn Rate", height=320)
        layout4["yaxis2"] = dict(title="Churn %", overlaying="y", side="right",
                                  gridcolor="rgba(0,0,0,0)", tickfont=dict(color=F1_RED))
        layout4["yaxis"]["title"] = "Subscribers"
        layout4["legend"] = dict(bgcolor="rgba(0,0,0,0)", x=0.01, y=0.99)
        fig4.update_layout(**layout4)
        st.plotly_chart(fig4, use_container_width=True)

    # ── Cohort Retention Heatmap ──────────────────────────────────────────────
    st.markdown("---")
    st.markdown(section_label("COHORT RETENTION ANALYSIS"), unsafe_allow_html=True)
    st.markdown("##### Percentage of subscribers still active N months after signup")

    cohort_data = subs[["subscriber_id","signup_date","churn_date","churned"]].copy()
    cohort_data["cohort"] = cohort_data["signup_date"].dt.to_period("M")
    today = pd.Timestamp("2024-12-31")
    rows = []
    for cohort, group in cohort_data.groupby("cohort"):
        for m in range(0, 13):
            cutoff = cohort.to_timestamp() + pd.DateOffset(months=m)
            if cutoff > today: break
            alive = group[(group["churned"]=="No") | (group["churn_date"] > cutoff)]
            rows.append({"cohort": str(cohort), "month": m, "retained": len(alive)/len(group)*100})
    cohort_df = pd.DataFrame(rows)
    pivot = cohort_df.pivot(index="cohort", columns="month", values="retained").tail(18)
    fig5 = go.Figure(go.Heatmap(
        z=pivot.values, x=[f"M+{m}" for m in pivot.columns], y=pivot.index,
        colorscale=[[0,F1_RED],[0.5,ACCENT_AMBER],[1,ACCENT_GREEN]],
        zmin=0, zmax=100,
        hovertemplate="Cohort: %{y}<br>Month: %{x}<br>Retained: %{z:.1f}%<extra></extra>",
        text=[[f"{v:.0f}%" if not np.isnan(v) else "" for v in row] for row in pivot.values],
        texttemplate="%{text}", textfont=dict(size=9, color="white"),
        colorbar=dict(title="% Retained", ticksuffix="%", tickfont=dict(color=F1_SILVER))
    ))
    layout5 = base_layout("Cohort Retention Heatmap (Last 18 Cohorts)", height=480)
    layout5["xaxis"]["title"] = "Months Since Signup"
    layout5["yaxis"]["title"] = "Signup Cohort"
    fig5.update_layout(**layout5)
    st.plotly_chart(fig5, use_container_width=True)

    # ── RFM Segmentation ──────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(section_label("RFM CUSTOMER SEGMENTATION"), unsafe_allow_html=True)
    st.markdown("##### Subscribers scored on Recency, Frequency & Monetary value — segmented into 7 behavioural groups")

    col5, col6 = st.columns([1, 2])

    with col5:
        seg_summary = rfm.groupby("segment").agg(
            count=("subscriber_id","count"),
            avg_ltv=("monetary","mean"),
            avg_recency=("recency_days","mean"),
            churn_rate=("churned_bool","mean")
        ).reset_index().sort_values("avg_ltv", ascending=False)
        seg_summary["color"] = seg_summary["segment"].map(SEGMENT_COLORS)

        fig6 = go.Figure(go.Bar(
            x=seg_summary["count"], y=seg_summary["segment"],
            orientation="h",
            marker=dict(color=seg_summary["color"]),
            text=seg_summary["count"], textposition="outside",
            textfont=dict(color=F1_WHITE),
            hovertemplate="<b>%{y}</b><br>Subscribers: %{x}<br>Avg LTV: $%{customdata[0]:.0f}<br>Churn: %{customdata[1]:.1%}<extra></extra>",
            customdata=seg_summary[["avg_ltv","churn_rate"]].values
        ))
        layout6 = base_layout("Segment Size", height=380)
        layout6["xaxis"]["title"] = "Subscribers"
        layout6["margin"]["r"] = 60
        fig6.update_layout(**layout6)
        st.plotly_chart(fig6, use_container_width=True)

    with col6:
        fig7 = px.scatter(
            rfm, x="recency_days", y="frequency",
            size="monetary", color="segment",
            color_discrete_map=SEGMENT_COLORS,
            hover_data={"subscriber_id": True, "monetary": ":.2f", "plan": True, "churned": True},
            size_max=28,
            labels={"recency_days": "Recency (days since last session)",
                    "frequency": "Frequency (total sessions)",
                    "monetary": "LTV (USD)"}
        )
        layout7 = base_layout("RFM Scatter — Recency vs Frequency (bubble = LTV)", height=380)
        fig7.update_layout(**layout7)
        fig7.update_traces(marker=dict(line=dict(width=0.5, color=F1_DGREY)))
        st.plotly_chart(fig7, use_container_width=True)

    # ── Insights ──────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(section_label("KEY INSIGHTS"), unsafe_allow_html=True)
    champions = rfm[rfm["segment"]=="Champion"]
    lost      = rfm[rfm["segment"]=="Lost"]
    top_region = subs.groupby("region")["subscriber_id"].count().idxmax()
    best_channel = subs.groupby("acquisition_channel")["churned_bool"].mean().idxmin()

    i1, i2 = st.columns(2)
    with i1:
        st.markdown(insight(f"🏆 <b>{len(champions)} Champions</b> ({len(champions)/len(rfm)*100:.1f}% of base) drive disproportionate LTV averaging <b>${champions['monetary'].mean():,.0f}</b> — these are the subscribers to protect first."), unsafe_allow_html=True)
        st.markdown(insight(f"🌍 <b>{top_region}</b> is the largest regional market. Cohort retention shows months 2–4 are the highest-risk dropout window across all regions."), unsafe_allow_html=True)
    with i2:
        st.markdown(insight(f"⚠️ <b>{len(lost)} Lost subscribers</b> have RFM scores indicating they are unrecoverable through standard re-engagement. Prescriptive tab models win-back ROI."), unsafe_allow_html=True)
        st.markdown(insight(f"📣 <b>{best_channel}</b> is the lowest-churn acquisition channel — directing budget here maximises retention ROI before a single session is watched."), unsafe_allow_html=True)
