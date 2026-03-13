import streamlit as st
import plotly.express as px


def render(subs, sess, mrr, rfm):

    st.markdown("## 📋 Descriptive Analytics")

    st.markdown("---")

    active = subs[subs["churned"] == "No"]

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Subscribers", len(subs))
    col2.metric("Active Subscribers", len(active))
    col3.metric("Churn Rate %", round(subs["churned_bool"].mean() * 100, 2))
    col4.metric("Avg NPS", round(subs["nps_score"].mean(), 2))

    st.markdown("---")

    st.subheader("Subscribers by Plan")

    plan_counts = subs["plan"].value_counts().reset_index()
    plan_counts.columns = ["plan", "count"]

    fig = px.bar(plan_counts, x="plan", y="count", color="plan")

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    st.subheader("RFM Segments")

    seg = rfm["segment"].value_counts().reset_index()
    seg.columns = ["segment", "count"]

    fig2 = px.bar(seg, x="segment", y="count", color="segment")

    st.plotly_chart(fig2, use_container_width=True)
