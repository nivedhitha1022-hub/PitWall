import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from theme import F1_CSS, F1_RED, F1_BLACK, F1_WHITE, F1_SILVER, F1_GREY
from data_loader import load_data
from pages import tab1_descriptive, tab2_diagnostic, tab3_predictive, tab4_prescriptive

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PitWall Analytics",
    page_icon="🏎",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(F1_CSS, unsafe_allow_html=True)

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data
def get_data():
    return load_data()

with st.spinner("Loading race data..."):
    subs, sess, mrr, rfm = get_data()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="
    background: linear-gradient(135deg, #0A0A0A 0%, #1C1C1C 50%, #0A0A0A 100%);
    border-bottom: 3px solid #E8002D;
    padding: 20px 28px 16px 28px;
    margin: -1rem -1rem 1rem -1rem;
    display: flex;
    align-items: center;
    gap: 16px;
">
    <div>
        <div style="font-size:11px; letter-spacing:3px; color:#E8002D; font-weight:700; text-transform:uppercase; margin-bottom:4px;">
            F1 PERFORMANCE ANALYTICS PLATFORM
        </div>
        <div style="font-size:28px; font-weight:900; color:#F5F5F5; letter-spacing:1px; font-family:'Titillium Web',Arial Black,sans-serif;">
            🏎&nbsp; PITWALL ANALYTICS
        </div>
        <div style="font-size:13px; color:#9B9B9B; margin-top:4px;">
            Subscriber Retention Intelligence &nbsp;·&nbsp; Season 2023–2024 &nbsp;·&nbsp; 800 Subscribers &nbsp;·&nbsp; 29,240 Sessions
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📋  Descriptive",
    "🔍  Diagnostic",
    "🔮  Predictive",
    "🎯  Prescriptive",
])

with tab1:
    tab1_descriptive.render(subs, sess, mrr, rfm)

with tab2:
    tab2_diagnostic.render(subs, sess, mrr, rfm)

with tab3:
    tab3_predictive.render(subs, sess, mrr, rfm)

with tab4:
    tab4_prescriptive.render(subs, sess, mrr, rfm)
