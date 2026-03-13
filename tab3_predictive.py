import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import (roc_auc_score, roc_curve, confusion_matrix,
                              classification_report, precision_recall_curve)
from sklearn.pipeline import Pipeline
from theme import (base_layout, F1_RED, F1_WHITE, F1_SILVER, F1_GREY, F1_DGREY,
                   F1_GOLD, F1_LGREY, ACCENT_BLUE, ACCENT_GREEN, ACCENT_AMBER,
                   PLAN_COLORS, insight, section_label)


@st.cache_data
def build_features(subs, sess):
    eng = sess.groupby("subscriber_id").agg(
        avg_engagement=("engagement_score","mean"),
        total_sessions=("subscriber_id","count"),
        avg_duration=("session_duration_min","mean"),
        mobile_pct=("device", lambda x: (x=="Mobile").mean()),
    ).reset_index()

    df = subs.merge(eng, on="subscriber_id", how="left")
    df["avg_engagement"]  = df["avg_engagement"].fillna(0)
    df["total_sessions"]  = df["total_sessions"].fillna(0)
    df["avg_duration"]    = df["avg_duration"].fillna(0)
    df["mobile_pct"]      = df["mobile_pct"].fillna(0.5)

    le_plan = LabelEncoder()
    le_reg  = LabelEncoder()
    le_ch   = LabelEncoder()
    df["plan_enc"]    = le_plan.fit_transform(df["plan"])
    df["region_enc"]  = le_reg.fit_transform(df["region"])
    df["channel_enc"] = le_ch.fit_transform(df["acquisition_channel"])

    features = ["plan_enc","region_enc","channel_enc","monthly_price_usd",
                "age","tenure_months","renewal_count","nps_score",
                "avg_engagement","total_sessions","avg_duration","mobile_pct"]
    feat_labels = ["Plan","Region","Acq. Channel","Monthly Price",
                   "Age","Tenure (months)","Renewals","NPS Score",
                   "Avg Engagement","Total Sessions","Avg Duration","Mobile %"]

    X = df[features].fillna(0)
    y = df["churned_bool"]
    return X, y, df, features, feat_labels, le_plan


@st.cache_data
def train_model(X, y):
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
    rf = RandomForestClassifier(n_estimators=200, max_depth=8, min_samples_leaf=5,
                                 class_weight="balanced", random_state=42)
    rf.fit(X_tr, y_tr)
    probs = rf.predict_proba(X_te)[:,1]
    cv    = cross_val_score(rf, X, y, cv=5, scoring="roc_auc")
    return rf, X_tr, X_te, y_tr, y_te, probs, cv


def render(subs, sess, mrr, rfm):
    st.markdown("## 🔮 Predictive Analytics — *Who Will Churn Next?*")
    st.markdown("Random Forest churn model, CLV forecasting, and 30-day at-risk identification.")
    st.markdown("---")

    X, y, df, features, feat_labels, le_plan = build_features(subs, sess)
    rf, X_tr, X_te, y_tr, y_te, probs, cv = train_model(X, y)

    # ── Model scorecard ───────────────────────────────────────────────────────
    auc  = roc_auc_score(y_te, probs)
    preds = (probs >= 0.5).astype(int)
    cm   = confusion_matrix(y_te, preds)
    acc  = (cm[0,0]+cm[1,1]) / cm.sum()

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("ROC-AUC Score",    f"{auc:.3f}", "Target: >0.75")
    m2.metric("Model Accuracy",   f"{acc:.1%}")
    m3.metric("5-Fold CV AUC",    f"{cv.mean():.3f}", f"±{cv.std():.3f}")
    m4.metric("Training Samples", f"{len(X_tr):,}")

    st.markdown("---")

    # ── ROC Curve | Feature Importance ───────────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(section_label("ROC CURVE — CHURN PREDICTION MODEL"), unsafe_allow_html=True)
        fpr, tpr, _ = roc_curve(y_te, probs)

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=fpr, y=tpr, name=f"Random Forest (AUC={auc:.3f})",
            mode="lines", line=dict(color=F1_RED, width=3),
            fill="tozeroy", fillcolor="rgba(232,0,45,0.12)"
        ))
        fig.add_trace(go.Scatter(
            x=[0,1], y=[0,1], name="Random Classifier",
            mode="lines", line=dict(color=F1_SILVER, width=1, dash="dash")
        ))
        layout = base_layout("ROC Curve — Churn Classifier", height=360)
        layout["xaxis"]["title"] = "False Positive Rate"
        layout["yaxis"]["title"] = "True Positive Rate"
        fig.update_layout(**layout)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown(section_label("FEATURE IMPORTANCE — WHAT DRIVES CHURN?"), unsafe_allow_html=True)
        importance = pd.Series(rf.feature_importances_, index=feat_labels).sort_values()
        colors = [F1_RED if v > importance.median() else F1_SILVER for v in importance.values]

        fig2 = go.Figure(go.Bar(
            x=importance.values, y=importance.index,
            orientation="h",
            marker=dict(color=colors, line=dict(color=F1_DGREY, width=0.5)),
            hovertemplate="<b>%{y}</b><br>Importance: %{x:.4f}<extra></extra>",
            text=[f"{v:.3f}" for v in importance.values], textposition="outside",
            textfont=dict(color=F1_WHITE, size=10)
        ))
        layout2 = base_layout("Feature Importance (Random Forest)", height=360)
        layout2["xaxis"]["title"] = "Gini Importance"
        layout2["margin"]["r"] = 60
        fig2.update_layout(**layout2)
        st.plotly_chart(fig2, use_container_width=True)

    # ── Confusion Matrix | Precision-Recall ──────────────────────────────────
    col3, col4 = st.columns(2)

    with col3:
        st.markdown(section_label("CONFUSION MATRIX"), unsafe_allow_html=True)
        labels = ["Active (0)", "Churned (1)"]
        fig3 = go.Figure(go.Heatmap(
            z=cm, x=labels, y=labels,
            colorscale=[[0, F1_GREY],[1, F1_RED]],
            text=cm, texttemplate="<b>%{text}</b>",
            textfont=dict(size=20, color=F1_WHITE),
            hovertemplate="Actual: %{y}<br>Predicted: %{x}<br>Count: %{z}<extra></extra>",
            showscale=False
        ))
        layout3 = base_layout("Confusion Matrix (Test Set)", height=300)
        layout3["xaxis"]["title"] = "Predicted"
        layout3["yaxis"]["title"] = "Actual"
        fig3.update_layout(**layout3)
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        st.markdown(section_label("PRECISION-RECALL CURVE"), unsafe_allow_html=True)
        prec, rec, _ = precision_recall_curve(y_te, probs)
        fig4 = go.Figure(go.Scatter(
            x=rec, y=prec, mode="lines",
            line=dict(color=ACCENT_BLUE, width=2.5),
            fill="tozeroy", fillcolor="rgba(0,180,216,0.12)",
            hovertemplate="Recall: %{x:.2f}<br>Precision: %{y:.2f}<extra></extra>"
        ))
        baseline = y_te.mean()
        fig4.add_hline(y=baseline, line_dash="dash", line_color=F1_SILVER,
                       annotation_text=f"Baseline: {baseline:.2f}", annotation_font_color=F1_SILVER)
        layout4 = base_layout("Precision-Recall Curve", height=300)
        layout4["xaxis"]["title"] = "Recall"
        layout4["yaxis"]["title"] = "Precision"
        fig4.update_layout(**layout4)
        st.plotly_chart(fig4, use_container_width=True)

    # ── CLV Prediction ────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(section_label("CUSTOMER LIFETIME VALUE — 6-MONTH FORECAST"), unsafe_allow_html=True)
    st.markdown("Predicted future revenue per active subscriber using retention probability × expected tenure.")

    active_df = df[df["churned"] == "No"].copy()
    active_df["churn_prob"]     = rf.predict_proba(active_df[features].fillna(0))[:,1]
    active_df["retention_prob"] = 1 - active_df["churn_prob"]
    active_df["predicted_clv_6m"] = (
        active_df["monthly_price_usd"] * 6 * active_df["retention_prob"]
    ).round(2)
    active_df["churn_risk_label"] = pd.cut(
        active_df["churn_prob"], bins=[0, 0.33, 0.66, 1.0],
        labels=["Low Risk", "Medium Risk", "High Risk"]
    )

    col5, col6 = st.columns(2)
    with col5:
        fig5 = px.histogram(
            active_df, x="predicted_clv_6m", color="plan",
            color_discrete_map=PLAN_COLORS, nbins=30, barmode="overlay",
            opacity=0.75,
            labels={"predicted_clv_6m": "Predicted 6-Month CLV (USD)"}
        )
        layout5 = base_layout("Predicted 6-Month CLV Distribution", height=340)
        layout5["xaxis"]["title"] = "Predicted CLV (USD)"
        layout5["yaxis"]["title"] = "Subscribers"
        fig5.update_layout(**layout5)
        st.plotly_chart(fig5, use_container_width=True)

    with col6:
        clv_region = active_df.groupby("region")["predicted_clv_6m"].agg(["mean","sum","count"]).reset_index()
        clv_region.columns = ["region","avg_clv","total_clv","subscribers"]
        fig6 = go.Figure(go.Bar(
            x=clv_region["region"], y=clv_region["total_clv"],
            marker=dict(
                color=clv_region["avg_clv"],
                colorscale=[[0,F1_GREY],[0.4,ACCENT_AMBER],[1,ACCENT_GREEN]],
                showscale=True,
                colorbar=dict(title="Avg CLV", tickfont=dict(color=F1_SILVER))
            ),
            text=[f"${v:,.0f}" for v in clv_region["total_clv"]], textposition="outside",
            textfont=dict(color=F1_WHITE, size=10),
            hovertemplate="<b>%{x}</b><br>Total CLV: $%{y:,.0f}<br>Avg per Sub: $%{marker.color:.0f}<extra></extra>"
        ))
        layout6 = base_layout("Total Predicted CLV by Region (6-Month)", height=340)
        layout6["yaxis"]["title"] = "Total Predicted CLV (USD)"
        fig6.update_layout(**layout6)
        st.plotly_chart(fig6, use_container_width=True)

    # ── 30-Day At-Risk Table ──────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(section_label("30-DAY AT-RISK SUBSCRIBER WATCHLIST"), unsafe_allow_html=True)
    st.markdown("Active subscribers ranked by churn probability × CLV — highest value at risk shown first.")

    at_risk = active_df[active_df["churn_prob"] >= 0.45].copy()
    at_risk["priority_score"] = (at_risk["churn_prob"] * at_risk["predicted_clv_6m"]).round(2)
    at_risk = at_risk.sort_values("priority_score", ascending=False).head(50)

    display_cols = {
        "subscriber_id": "Subscriber",
        "plan": "Plan",
        "region": "Region",
        "tenure_months": "Tenure (mo)",
        "avg_engagement": "Avg Engagement",
        "churn_prob": "Churn Prob",
        "predicted_clv_6m": "Pred. CLV (6m)",
        "priority_score": "Priority Score",
        "churn_risk_label": "Risk Level"
    }
    table = at_risk[list(display_cols.keys())].rename(columns=display_cols).copy()
    table["Churn Prob"]    = table["Churn Prob"].map("{:.1%}".format)
    table["Avg Engagement"]= table["Avg Engagement"].map("{:.1f}".format)
    table["Pred. CLV (6m)"]= table["Pred. CLV (6m)"].map("${:,.2f}".format)
    table["Priority Score"]= table["Priority Score"].map("${:,.2f}".format)

    st.dataframe(
        table,
        use_container_width=True,
        height=380,
        column_config={
            "Risk Level": st.column_config.Column(width="small"),
            "Plan":       st.column_config.Column(width="small"),
        }
    )

    total_at_risk_clv = at_risk["predicted_clv_6m"].sum()
    st.markdown(insight(f"🚨 <b>{len(at_risk)} high-risk active subscribers</b> represent <b>${total_at_risk_clv:,.0f}</b> in predicted 6-month revenue at risk. Intervening on the top 20 by priority score alone could protect <b>${at_risk.head(20)['predicted_clv_6m'].sum():,.0f}</b> in MRR."), unsafe_allow_html=True)

    # ── Churn probability distribution ───────────────────────────────────────
    st.markdown("---")
    st.markdown(section_label("CHURN PROBABILITY DISTRIBUTION — ACTIVE BASE"), unsafe_allow_html=True)
    col7, col8 = st.columns(2)

    with col7:
        fig7 = px.histogram(
            active_df, x="churn_prob", color="plan",
            color_discrete_map=PLAN_COLORS, nbins=25, barmode="overlay", opacity=0.75,
            labels={"churn_prob": "Predicted Churn Probability"}
        )
        layout7 = base_layout("Churn Probability by Plan (Active Subs)", height=320)
        layout7["xaxis"]["tickformat"] = ".0%"
        fig7.update_layout(**layout7)
        st.plotly_chart(fig7, use_container_width=True)

    with col8:
        risk_counts = active_df["churn_risk_label"].value_counts()
        colors_risk = {"Low Risk": ACCENT_GREEN, "Medium Risk": ACCENT_AMBER, "High Risk": F1_RED}
        fig8 = go.Figure(go.Pie(
            labels=risk_counts.index, values=risk_counts.values,
            hole=0.5,
            marker=dict(colors=[colors_risk.get(l, F1_SILVER) for l in risk_counts.index],
                        line=dict(color=F1_DGREY, width=2)),
            textinfo="label+percent+value",
            textfont=dict(color=F1_WHITE, size=11)
        ))
        fig8.update_layout(**base_layout("Active Subscriber Risk Breakdown", height=320))
        st.plotly_chart(fig8, use_container_width=True)
