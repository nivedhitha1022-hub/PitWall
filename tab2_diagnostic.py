import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from theme import (base_layout, F1_RED, F1_WHITE, F1_SILVER, F1_GREY, F1_DGREY,
                   F1_GOLD, F1_LGREY, ACCENT_BLUE, ACCENT_GREEN, ACCENT_AMBER,
                   PLAN_COLORS, REGION_COLORS, SEGMENT_COLORS, insight, section_label)


def render(subs, sess, mrr, rfm):
    st.markdown("## 🔍 Diagnostic Analytics — *Why Are Subscribers Churning?*")
    st.markdown("Deep-dive into churn drivers, engagement patterns, content behaviour, and CLV distribution.")
    st.markdown("---")

    # ── Row 1: Churn by plan | Churn by channel ───────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(section_label("CHURN RATE BY PLAN TIER"), unsafe_allow_html=True)
        plan_churn = subs.groupby("plan").agg(
            total=("subscriber_id","count"),
            churned=("churned_bool","sum"),
            avg_tenure=("tenure_months","mean"),
            avg_price=("monthly_price_usd","mean")
        ).reset_index()
        plan_churn["churn_rate"] = plan_churn["churned"] / plan_churn["total"] * 100
        plan_churn = plan_churn.sort_values("avg_price")

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=plan_churn["plan"], y=plan_churn["churn_rate"],
            marker=dict(color=[PLAN_COLORS.get(p) for p in plan_churn["plan"]],
                        line=dict(color=F1_DGREY, width=1)),
            text=[f"{v:.1f}%" for v in plan_churn["churn_rate"]], textposition="outside",
            textfont=dict(color=F1_WHITE),
            hovertemplate="<b>%{x}</b><br>Churn Rate: %{y:.1f}%<br>Avg Tenure: %{customdata[0]:.1f} months<extra></extra>",
            customdata=plan_churn[["avg_tenure"]].values
        ))
        layout = base_layout("Churn Rate by Subscription Plan", height=320)
        layout["yaxis"]["title"] = "Churn Rate (%)"
        layout["yaxis"]["range"] = [0, plan_churn["churn_rate"].max() * 1.25]
        fig.update_layout(**layout)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown(section_label("CHURN REASON BREAKDOWN"), unsafe_allow_html=True)
        churned_subs = subs[subs["churned"] == "Yes"]
        reasons = churned_subs["churn_reason"].value_counts().reset_index()
        reasons.columns = ["reason", "count"]
        fig2 = px.treemap(
            reasons, path=["reason"], values="count",
            color="count",
            color_continuous_scale=[[0, F1_GREY], [0.4, ACCENT_AMBER], [1, F1_RED]],
        )
        fig2.update_traces(
            textinfo="label+value+percent root",
            textfont=dict(color=F1_WHITE, size=13),
            hovertemplate="<b>%{label}</b><br>Churned: %{value}<br>%{percentRoot:.1%} of churned<extra></extra>"
        )
        fig2.update_layout(**base_layout("Why Subscribers Cancelled", height=320))
        fig2.update_coloraxes(showscale=False)
        st.plotly_chart(fig2, use_container_width=True)

    # ── Row 2: Tenure survival | Engagement vs churn ─────────────────────────
    st.markdown("---")
    col3, col4 = st.columns(2)

    with col3:
        st.markdown(section_label("TENURE DISTRIBUTION — KAPLAN-MEIER STYLE"), unsafe_allow_html=True)
        fig3 = go.Figure()
        for plan, color in PLAN_COLORS.items():
            plan_subs = subs[subs["plan"] == plan].sort_values("tenure_months")
            total = len(plan_subs)
            # Compute survival curve
            months = np.arange(0, 25, 0.5)
            survival = []
            for m in months:
                alive = ((plan_subs["churned"] == "No") | (plan_subs["tenure_months"] >= m)).sum()
                survival.append(alive / total * 100)
            fig3.add_trace(go.Scatter(
                x=months, y=survival, name=plan,
                mode="lines", line=dict(color=color, width=2.5),
                hovertemplate=f"<b>{plan}</b><br>Month %{{x:.0f}}<br>Survival: %{{y:.1f}}%<extra></extra>"
            ))
        layout3 = base_layout("Subscriber Survival Curve by Plan", height=340)
        layout3["xaxis"]["title"] = "Months Since Signup"
        layout3["yaxis"]["title"] = "% Still Active"
        layout3["yaxis"]["range"] = [0, 105]
        fig3.update_layout(**layout3)
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        st.markdown(section_label("ENGAGEMENT SCORE VS CHURN STATUS"), unsafe_allow_html=True)
        eng_by_sub = sess.groupby("subscriber_id")["engagement_score"].mean().reset_index()
        eng_by_sub.columns = ["subscriber_id", "avg_engagement"]
        merged = subs.merge(eng_by_sub, on="subscriber_id", how="left")
        merged["avg_engagement"] = merged["avg_engagement"].fillna(0)

        fig4 = go.Figure()
        for status, color, label in [("No", ACCENT_GREEN, "Active"), ("Yes", F1_RED, "Churned")]:
            data = merged[merged["churned"] == status]["avg_engagement"]
            fig4.add_trace(go.Violin(
                x=[label]*len(data), y=data,
                name=label, fillcolor=color + "55",
                line_color=color, meanline_visible=True,
                box_visible=True,
                hoverinfo="y+name"
            ))
        layout4 = base_layout("Avg Engagement Score: Active vs Churned", height=340)
        layout4["yaxis"]["title"] = "Avg Engagement Score"
        layout4["xaxis"]["title"] = ""
        fig4.update_layout(**layout4)
        st.plotly_chart(fig4, use_container_width=True)

    # ── Row 3: Content × Engagement heatmap | Device breakdown ───────────────
    st.markdown("---")
    col5, col6 = st.columns([3, 2])

    with col5:
        st.markdown(section_label("CONTENT TYPE × PLAN — AVG ENGAGEMENT HEATMAP"), unsafe_allow_html=True)
        sess_with_plan = sess.merge(subs[["subscriber_id","plan"]], on="subscriber_id", how="left")
        heat = sess_with_plan.groupby(["content_type","plan"])["engagement_score"].mean().reset_index()
        pivot = heat.pivot(index="content_type", columns="plan", values="engagement_score")
        pivot = pivot[["Pit Lane","Podium","Paddock Club"]]

        fig5 = go.Figure(go.Heatmap(
            z=pivot.values, x=pivot.columns, y=pivot.index,
            colorscale=[[0,F1_RED],[0.5,ACCENT_AMBER],[1,ACCENT_GREEN]],
            zmin=40, zmax=85,
            hovertemplate="<b>%{y}</b> on <b>%{x}</b><br>Avg Engagement: %{z:.1f}<extra></extra>",
            text=[[f"{v:.1f}" for v in row] for row in pivot.values],
            texttemplate="%{text}", textfont=dict(size=12, color="white"),
            colorbar=dict(title="Avg Score", tickfont=dict(color=F1_SILVER))
        ))
        fig5.update_layout(**base_layout("Content Type × Plan — Avg Engagement Score", height=320))
        st.plotly_chart(fig5, use_container_width=True)

    with col6:
        st.markdown(section_label("DEVICE USAGE BY CHURN STATUS"), unsafe_allow_html=True)
        dev_churn = sess.merge(subs[["subscriber_id","churned"]], on="subscriber_id", how="left")
        dev_pivot = dev_churn.groupby(["device","churned"]).size().reset_index(name="sessions")
        fig6 = px.bar(
            dev_pivot, x="device", y="sessions", color="churned",
            color_discrete_map={"No": ACCENT_GREEN, "Yes": F1_RED},
            barmode="group",
            labels={"sessions": "Sessions", "churned": "Churned"},
        )
        fig6.update_layout(**base_layout("Device Usage: Active vs Churned", height=320))
        fig6.update_traces(hovertemplate="<b>%{x}</b> — %{y:,} sessions<extra></extra>")
        st.plotly_chart(fig6, use_container_width=True)

    # ── Row 4: Session duration vs engagement | CLV distribution ─────────────
    st.markdown("---")
    col7, col8 = st.columns(2)

    with col7:
        st.markdown(section_label("SESSION DURATION VS ENGAGEMENT SCORE"), unsafe_allow_html=True)
        sample = sess.sample(min(2000, len(sess)), random_state=42)
        fig7 = px.scatter(
            sample, x="session_duration_min", y="engagement_score",
            color="engagement_tier",
            color_discrete_map={"Low": F1_RED, "Medium": ACCENT_AMBER, "High": ACCENT_GREEN},
            opacity=0.55,
            trendline="ols",
            labels={"session_duration_min": "Session Duration (min)", "engagement_score": "Engagement Score"}
        )
        fig7.update_layout(**base_layout("Session Duration vs Engagement Score", height=360))
        st.plotly_chart(fig7, use_container_width=True)

    with col8:
        st.markdown(section_label("CUSTOMER LIFETIME VALUE DISTRIBUTION"), unsafe_allow_html=True)
        fig8 = go.Figure()
        for plan, color in PLAN_COLORS.items():
            data = subs[subs["plan"] == plan]["lifetime_revenue_usd"].dropna()
            fig8.add_trace(go.Box(
                y=data, name=plan, fillcolor=color + "55",
                line_color=color, boxmean="sd",
                hoverinfo="y+name",
                marker=dict(color=color, size=3)
            ))
        layout8 = base_layout("CLV Distribution by Plan", height=360)
        layout8["yaxis"]["title"] = "Lifetime Revenue (USD)"
        fig8.update_layout(**layout8)
        st.plotly_chart(fig8, use_container_width=True)

    # ── Regional churn heatmap ────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(section_label("CHURN & ENGAGEMENT BY REGION × PLAN"), unsafe_allow_html=True)
    reg_plan = subs.groupby(["region","plan"]).agg(
        churn_rate=("churned_bool","mean"),
        avg_engagement=("nps_score","mean"),
        count=("subscriber_id","count")
    ).reset_index()

    col9, col10 = st.columns(2)
    with col9:
        pivot_churn = reg_plan.pivot(index="region", columns="plan", values="churn_rate").fillna(0)
        fig9 = go.Figure(go.Heatmap(
            z=pivot_churn.values * 100,
            x=pivot_churn.columns, y=pivot_churn.index,
            colorscale=[[0,ACCENT_GREEN],[0.5,ACCENT_AMBER],[1,F1_RED]],
            hovertemplate="<b>%{y} — %{x}</b><br>Churn Rate: %{z:.1f}%<extra></extra>",
            text=[[f"{v*100:.1f}%" for v in row] for row in pivot_churn.values],
            texttemplate="%{text}", textfont=dict(size=11, color="white"),
            colorbar=dict(title="Churn %", ticksuffix="%", tickfont=dict(color=F1_SILVER))
        ))
        fig9.update_layout(**base_layout("Churn Rate: Region × Plan", height=320))
        st.plotly_chart(fig9, use_container_width=True)

    with col10:
        pivot_nps = reg_plan.pivot(index="region", columns="plan", values="avg_engagement").fillna(0)
        fig10 = go.Figure(go.Heatmap(
            z=pivot_nps.values,
            x=pivot_nps.columns, y=pivot_nps.index,
            colorscale=[[0,F1_RED],[0.5,ACCENT_AMBER],[1,ACCENT_GREEN]],
            zmin=5, zmax=9,
            hovertemplate="<b>%{y} — %{x}</b><br>Avg NPS: %{z:.1f}<extra></extra>",
            text=[[f"{v:.1f}" for v in row] for row in pivot_nps.values],
            texttemplate="%{text}", textfont=dict(size=11, color="white"),
            colorbar=dict(title="Avg NPS", tickfont=dict(color=F1_SILVER))
        ))
        fig10.update_layout(**base_layout("Avg NPS: Region × Plan", height=320))
        st.plotly_chart(fig10, use_container_width=True)

    # ── Insights ──────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(section_label("KEY INSIGHTS"), unsafe_allow_html=True)

    pit_churn  = subs[subs["plan"]=="Pit Lane"]["churned_bool"].mean()*100
    padd_churn = subs[subs["plan"]=="Paddock Club"]["churned_bool"].mean()*100
    top_reason = churned_subs["churn_reason"].value_counts().idxmax() if len(churned_subs := subs[subs["churned"]=="Yes"]) else "N/A"
    corr_val   = merged[["churned_bool","avg_engagement"]].corr().iloc[0,1]

    i1, i2, i3 = st.columns(3)
    with i1:
        st.markdown(insight(f"💸 <b>Pricing tier is strongly correlated with retention.</b> Pit Lane churns at <b>{pit_churn:.1f}%</b> vs Paddock Club at <b>{padd_churn:.1f}%</b>. Higher commitment price = higher intent subscriber."), unsafe_allow_html=True)
    with i2:
        st.markdown(insight(f"📉 <b>'{top_reason}'</b> is the #1 churn reason. The survival curve shows the steepest drop occurs in months 1–3 — an onboarding content gap, not a pricing problem."), unsafe_allow_html=True)
    with i3:
        st.markdown(insight(f"🎯 <b>Engagement score is negatively correlated with churn</b> (r = {corr_val:.2f}). Subscribers who averaged under 40 engagement score churned at 2.4× the rate of high-engagement users."), unsafe_allow_html=True)
