import os
import re
import html
import json
from datetime import datetime
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import plotly.express as px
import plotly.graph_objects as go

# Google Gemini AI
import google.generativeai as genai
from streamlit_mic_recorder import mic_recorder


# ============================================================
# PAGE / APP CONFIG
# ============================================================
st.set_page_config(
    page_title="QFL4 AI Audit Intelligence",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

EXCEL_FILE = "audit_data.xlsx"
SHEET_NAME = "Sheet1"
USERS_FILE = "users.json"

AI_MODEL = "gemini-3.6-flash"

LOGIN_EMAIL = st.secrets.get("LOGIN_EMAIL", os.getenv("LOGIN_EMAIL", ""))
LOGIN_PASSWORD = st.secrets.get("LOGIN_PASSWORD", os.getenv("LOGIN_PASSWORD", ""))

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "role" not in st.session_state:
    st.session_state.role = "user"
if "show_signup" not in st.session_state:
    st.session_state.show_signup = False


# ============================================================
# GLOBAL STYLING & SECURITY HIDE (MANAGE APP / FOOTER)
# ============================================================
st.markdown(
    """
<style>
#MainMenu, footer, [data-testid="stStatusWidget"], .stAppDeployButton {
    visibility: hidden !important;
    display: none !important;
}

/* Header ko poora hide nahi karna - warna sidebar ka open/close arrow bhi ghayab ho jata hai */
header[data-testid="stHeader"] {
    background: transparent !important;
    box-shadow: none !important;
    height: 3rem !important;
}

/* Sidebar collapse/expand ka arrow hamesha visible aur clickable rahe */
[data-testid="collapsedControl"] {
    visibility: visible !important;
    display: flex !important;
    z-index: 999999 !important;
}
button[kind="header"] {
    visibility: visible !important;
    display: flex !important;
}

.stApp {
    background: #eef1f5;
}

.block-container {
    padding-top: 0rem !important;
    padding-bottom: 3.5rem !important;
    max-width: 1500px;
}

[data-testid="stSidebar"] {
    background: #fff !important;
    border-right: 1px solid #dce3ea;
}

.nav-brand {
    padding: 8px 8px 18px;
    border-bottom: 1px solid #edf1f5;
    margin-bottom: 10px;
}
.nav-brand-top { color: #1d5fa7; font-size: 10px; font-weight: 900; letter-spacing: 1.8px; }
.nav-brand-title { color: #243447; font-size: 21px; font-weight: 900; margin-top: 5px; }
.nav-caption { color: #94a3b8; font-size: 11px; margin-top: 3px; }
.nav-section { color: #94a3b8; font-size: 10px; font-weight: 900; letter-spacing: 1.2px; padding: 13px 8px 6px; }
