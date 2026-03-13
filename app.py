import streamlit as st
from data_loader import load_data
import tab1_descriptive

st.set_page_config(page_title="PitWall Analytics", page_icon="🏎", layout="wide")

st.title("PitWall Analytics")

@st.cache_data
def get_data():
    return load_data()

subs, sess, mrr, rfm = get_data()

tab1_descriptive.render(subs, sess, mrr, rfm)
