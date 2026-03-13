import streamlit as st
import plotly.express as px


def render(subs, sess, mrr, rfm):
    st.subheader("Descriptive Analytics")

    active = subs[subs["churned"] == "No"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Subscribers", int(len(subs)))
    c2.metric("Active Subscribers", int(len(active)))
    c3.metric("Churn Rate %", round(float(subs["churned_bool"].mean() * 100), 2))
    c4.metric("Avg NPS", round(float(subs["nps_score"].mean()), 2))

    st.markdown("---")

    plan_counts = subs["plan"].value_counts().reset_index()
    plan_counts.columns = ["plan", "count"]
    fig1 = px.bar(plan_counts, x="plan", y="count", title="Subscribers by Plan")
    st.plotly_chart(fig1, use_container_width=True)

    st.markdown("---")

    seg_counts = rfm["segment"].value_counts().reset_index()
    seg_counts.columns = ["segment", "count"]
    fig2 = px.bar(seg_counts, x="segment", y="count", title="RFM Segments")
    st.plotly_chart(fig2, use_container_width=True)
