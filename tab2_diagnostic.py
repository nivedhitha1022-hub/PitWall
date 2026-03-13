import streamlit as st

from theme import F1_CSS
from data_loader import load_data
import tab1_descriptive
import tab2_diagnostic
import tab3_predictive
import tab4_prescriptive


st.set_page_config(
    page_title="PitWall Analytics",
    page_icon="🏎",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(F1_CSS, unsafe_allow_html=True)


@st.cache_data
def get_data():
    return load_data()


with st.spinner("Loading race data..."):
    subs, sess, mrr, rfm = get_data()

st.markdown(
    """
    <div style="
        background: linear-gradient(135deg, #0A0A0A 0%, #1C1C1C 50%, #0A0A0A 100%);
        border-bottom: 3px solid #E8002D;
        padding: 20px 28px 16px 28px;
        margin: -1rem -1rem 1rem -1rem;
    ">
        <div style="font-size:11px; letter-spacing:3px; color:#E8002D; font-weight:700; text-transform:uppercase; margin-bottom:4px;">
            F1 PERFORMANCE ANALYTICS PLATFORM
        </div>
        <div style="font-size:28px; font-weight:900; color:#F5F5F5; letter-spacing:1px; font-family:'Titillium Web',Arial Black,sans-serif;">
            🏎&nbsp; PITWALL ANALYTICS
        </div>
        <div style="font-size:13px; color:#9B9B9B; margin-top:4px;">
            Subscriber Retention Intelligence · Season 2023–2024
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "📋 Descriptive",
        "🔍 Diagnostic",
        "🔮 Predictive",
        "🎯 Prescriptive",
    ]
)

with tab1:
    tab1_descriptive.render(subs, sess, mrr, rfm)

with tab2:
    tab2_diagnostic.render(subs, sess, mrr, rfm)

with tab3:
    tab3_predictive.render(subs, sess, mrr, rfm)

with tab4:
    tab4_prescriptive.render(subs, sess, mrr, rfm)
