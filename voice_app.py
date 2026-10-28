import os
import re
import html
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import plotly.express as px
import plotly.graph_objects as go
import gspread
from google.oauth2.service_account import Credentials

# Google Gemini AI
import google.generativeai as genai
from streamlit_mic_recorder import mic_recorder

# Persistent black borders for all Streamlit form controls
st.markdown(
    """
    <style>
    div[data-baseweb="select"] > div,
    div[data-baseweb="input"] > div,
    div[data-baseweb="textarea"] > div,
    div[data-testid="stNumberInput"] [data-baseweb="input"] > div,
    div[data-testid="stTextInput"] [data-baseweb="input"] > div,
    div[data-testid="stTextArea"] [data-baseweb="textarea"] > div,
    div[data-testid="stDateInput"] [data-baseweb="input"] > div {
        border: 1.5px solid #000000 !important;
        border-radius: 6px !important;
        background-color: #ffffff !important;
        box-shadow: none !important;
    }
    div[data-baseweb="select"] > div:hover,
    div[data-baseweb="input"] > div:hover,
    div[data-baseweb="textarea"] > div:hover,
    div[data-baseweb="select"] > div:focus-within,
    div[data-baseweb="input"] > div:focus-within,
    div[data-baseweb="textarea"] > div:focus-within {
        border: 1.5px solid #000000 !important;
        outline: none !important;
        box-shadow: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)



# ============================================================
# PAGE / APP CONFIG
# ============================================================
st.set_page_config(
    page_title="QFL4 AI Audit Intelligence",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_DIR = Path(__file__).resolve().parent
EXCEL_FILE = str(APP_DIR / "audit_data.xlsx")  # Optional local backup/import file
SHEET_NAME = "Audit Entries"
GOOGLE_SHEET_ID = st.secrets.get("GOOGLE_SHEET_ID", "1ADGSkAzFDxvj2GPQ0P8mJb1_u3BVGVYdBFREAy0rdmM")
USERS_FILE = str(APP_DIR / "users.json")
TEMPLATE_FILENAME = "QFL 4-Product Audit Sheet (Fuso) Revised.xlsx"
TEMPLATE_PATH = APP_DIR / TEMPLATE_FILENAME



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

/* Strong black outlines for every Streamlit input/control */
div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div,
div[data-baseweb="textarea"] > div,
div[data-baseweb="datepicker"] > div,
div[data-baseweb="timepicker"] > div,
div[data-testid="stNumberInput"] div[data-baseweb="input"] > div,
div[data-testid="stDateInput"] div[data-baseweb="input"] > div,
div[data-testid="stTextInput"] div[data-baseweb="input"] > div,
div[data-testid="stTextArea"] div[data-baseweb="textarea"] > div {
    border: 2px solid #000000 !important;
    border-radius: 6px !important;
    background-color: #ffffff !important;
    box-shadow: none !important;
}
div[data-baseweb="select"] > div:hover,
div[data-baseweb="input"] > div:hover,
div[data-baseweb="textarea"] > div:hover {
    border-color: #000000 !important;
}
div[data-baseweb="select"] > div:focus-within,
div[data-baseweb="input"] > div:focus-within,
div[data-baseweb="textarea"] > div:focus-within {
    border: 2px solid #000000 !important;
    outline: 1px solid #000000 !important;
    outline-offset: 1px !important;
}
div[data-testid="stCheckbox"] label > div:first-child,
div[data-testid="stRadio"] label > div:first-child {
    border: 2px solid #000000 !important;
}
div[data-testid="stButton"] > button,
button[kind="primary"],
div[data-testid="stDownloadButton"] > button {
    border: 2px solid #000000 !important;
}

    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
<style>
#MainMenu, footer, [data-testid="stStatusWidget"], .stAppDeployButton {
    visibility: hidden !important;
    display: none !important;
}

/* Keep the header visible so the sidebar toggle remains accessible. */
header[data-testid="stHeader"] {
    background: transparent !important;
    box-shadow: none !important;
    height: 3rem !important;
}

/* Keep the sidebar expand/collapse control visible and clickable. */
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
.sidebar-note { color: #94a3b8; font-size: 11px; padding: 8px; }

.page-title { font-size: 30px; font-weight: 900; color: #243447; margin-bottom: 2px; }
.page-desc { font-size: 13px; color: #718096; margin-bottom: 20px; }

.main-title { font-size: 36px; font-weight: 900; color: #243447; margin-top: 10px; }
.main-subtitle { color: #64748b; font-size: 15px; margin-top: 6px; }
.online-badge { display: inline-block; margin-top: 12px; padding: 6px 14px; border-radius: 20px; background: #edf8f1; color: #15803d; border: 1px solid #ccebd7; font-size: 10px; font-weight: 900; }
.section-title { font-size: 20px; font-weight: 900; color: #243447; margin: 24px 0 12px; }

.kpi { background: #fff; border: 1px solid #e0e6ec; border-radius: 14px; padding: 18px; min-height: 105px; box-shadow: 0 5px 16px rgba(15,23,42,.04); }
.kpi-label { font-size: 11px; color: #718096; font-weight: 800; }
.kpi-value { font-size: 30px; color: #243447; font-weight: 900; margin-top: 7px; }

.kpi-dpu { background: linear-gradient(135deg, #fff5f5, #fed7d7); border: 1px solid #feb2b2; border-radius: 14px; padding: 18px; min-height: 105px; box-shadow: 0 6px 18px rgba(220, 38, 38, 0.08); }
.kpi-dpu .kpi-label { font-size: 11px; color: #9b2c2c; font-weight: 800; letter-spacing: 0.5px; }
.kpi-dpu .kpi-value { font-size: 34px; color: #dc2626; font-weight: 900; margin-top: 7px; }

/* ACTION ALERT BOX FOR PARETO */
.pareto-alert-box {
    background: linear-gradient(135deg, #fff1f2, #ffe4e6);
    border: 2px solid #f43f5e;
    border-radius: 14px;
    padding: 18px 22px;
    margin-bottom: 20px;
    box-shadow: 0 6px 20px rgba(244, 63, 94, 0.12);
}
.pareto-alert-title {
    color: #be123c;
    font-size: 12px;
    font-weight: 900;
    letter-spacing: 1.5px;
    text-transform: uppercase;
}
.pareto-alert-main {
    color: #881337;
    font-size: 20px;
    font-weight: 900;
    margin-top: 4px;
}
.pareto-alert-desc {
    color: #9f1239;
    font-size: 13px;
    margin-top: 4px;
    font-weight: 600;
}

.voice-card { padding: 25px; border-radius: 16px; background: linear-gradient(135deg,#f8fbff,#e7f0fb); border: 1px solid #d8e4f2; margin: 20px 0; box-shadow: 0 7px 22px rgba(37,99,235,.06); }
.voice-title { font-size: 25px; font-weight: 900; color: #243447; }
.voice-subtitle { font-size: 13px; color: #64748b; margin-top: 5px; }

div[data-testid="stHorizontalBlock"]:has(input[aria-label="POWERED BY FQCM"]) {
    background: #ffffff; border: 2px solid #ff4b4b !important; border-radius: 14px; padding: 4px 12px; box-shadow: 0 4px 20px rgba(255, 75, 75, 0.1); align-items: center;
}
div[data-testid="stHorizontalBlock"]:has(input[aria-label="POWERED BY FQCM"]) [data-baseweb="input"] { background: transparent !important; border: none !important; box-shadow: none !important; }
div[data-testid="stHorizontalBlock"]:has(input[aria-label="POWERED BY FQCM"]) fieldset { border: none !important; }

.answer-card { background: #fff; border: 1px solid #dce5ef; border-left: 4px solid #ff1a40; border-radius: 12px; padding: 17px 20px; margin-top: 12px; }
.answer-label { font-size: 10px; color: #ff1a40; font-weight: 900; letter-spacing: 1.4px; }
.answer-text { font-size: 18px; color: #243447; font-weight: 650; margin-top: 6px; line-height: 1.5; }

.top-header-banner {
    max-width: 520px;
    margin: 25px auto 10px auto;
    background: #ffffff;
    border: 1.5px solid #e2e8f0;
    border-radius: 14px;
    padding: 14px 20px;
    text-align: center;
    box-shadow: 0 6px 20px rgba(15, 23, 42, 0.06);
}
.top-header-text {
    color: #1e293b;
    font-size: 16px;
    font-weight: 900;
    letter-spacing: 1.5px;
    text-transform: uppercase;
}
.top-header-sub {
    color: #dc2626;
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 2px;
    margin-top: 3px;
}

.login-brand-box {
    background: linear-gradient(135deg, #182030, #0f172a);
    border: 1px solid #2a374c;
    border-radius: 16px;
    padding: 22px 26px;
    margin-bottom: 18px;
    box-shadow: 0 10px 30px rgba(15, 23, 42, 0.25);
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.brand-left {
    display: flex;
    align-items: center;
    gap: 18px;
}
.brand-hex {
    width: 56px;
    height: 56px;
    background: linear-gradient(135deg, #1f2937, #111827);
    border: 2px solid #ef4444;
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    box-shadow: 0 4px 14px rgba(239, 68, 68, 0.3);
}
.brand-check {
    color: #22c55e;
    font-size: 24px;
    font-weight: 900;
}
.brand-texts {
    display: flex;
    flex-direction: column;
}
.brand-top-sub {
    color: #ef4444;
    font-size: 10px;
    font-weight: 900;
    letter-spacing: 1.8px;
    margin-bottom: 3px;
}
.brand-main-title {
    display: flex;
    align-items: baseline;
    gap: 8px;
    margin-bottom: 3px;
}
.brand-qfl {
    color: #ffffff;
    font-size: 26px;
    font-weight: 900;
    letter-spacing: 0.5px;
}
.brand-ai {
    color: #ef4444;
    font-size: 26px;
    font-weight: 900;
}
.brand-desc {
    color: #94a3b8;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.9px;
}
.brand-fqcm-box {
    border: 1.5px solid #475569;
    border-radius: 10px;
    padding: 8px 14px;
    text-align: center;
    background: rgba(255, 255, 255, 0.04);
}
.brand-fqcm-text {
    color: #ef4444;
    font-size: 16px;
    font-weight: 900;
    letter-spacing: 1.2px;
}
.brand-fqcm-active {
    color: #22c55e;
    font-size: 9px;
    font-weight: 800;
    letter-spacing: 1.2px;
    margin-top: 2px;
}

.login-title {
    color: #243447;
    font-size: 26px;
    font-weight: 900;
    margin-bottom: 6px;
    text-align: center;
}
.login-subtitle {
    color: #64748b;
    font-size: 13.5px;
    margin-bottom: 22px;
    text-align: center;
}
.stTextInput input {
    background-color: #f8fafc !important;
    border: 1.5px solid #cbd5e1 !important;
    border-radius: 10px !important;
    padding: 12px 14px !important;
    color: #243447 !important;
    transition: all 0.3s;
}
.stTextInput input:focus {
    background-color: #ffffff !important;
    border-color: #2563eb !important;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15) !important;
}

/* VISION & MISSION */
.vision-card {
    background: #ffffff;
    border: 1px solid #dce3ea;
    border-radius: 16px;
    padding: 28px 30px;
    margin: 14px 0;
    box-shadow: 0 6px 20px rgba(15,23,42,.05);
}
.vision-heading {
    color: #243447;
    font-size: 22px;
    font-weight: 900;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 10px;
    letter-spacing: .3px;
}
.vision-icon {
    width: 30px;
    height: 30px;
    border-radius: 8px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    font-weight: 900;
    flex: 0 0 30px;
}
.vision-icon-red { background: #fff1f2; color: #dc2626; border: 1px solid #fecdd3; }
.vision-icon-blue { background: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe; }
.vision-icon-gold { background: #fffbeb; color: #b45309; border: 1px solid #fde68a; }
.vision-text {
    color: #53657a;
    font-size: 15px;
    line-height: 1.8;
    font-weight: 500;
}
.leader-photo-wrap {
    background: #ffffff;
    border: 1px solid #dce3ea;
    border-radius: 16px;
    padding: 12px;
    box-shadow: 0 6px 20px rgba(15,23,42,.05);
}
.leader-photo-wrap img {
    border-radius: 10px;
}
.leader-caption {
    text-align: center;
    padding: 14px 6px 5px;
}
.leader-name {
    color: #243447;
    font-size: 18px;
    font-weight: 900;
}
.leader-role {
    color: #64748b;
    font-size: 12px;
    font-weight: 700;
    margin-top: 3px;
    letter-spacing: .6px;
}
.approach-card {
    margin-top: 16px;
}
.approach-text {
    font-weight: 700;
    color: #334e68;
}


/* EXECUTIVE QUALITY DASHBOARD */
.dashboard-title { font-size: 28px; font-weight: 950; color: #243447; margin: 4px 0 2px; }
.dashboard-subtitle { color: #64748b; font-size: 12px; margin-bottom: 14px; }
.dashboard-card { background:#fff; border:1px solid #d8dee7; border-radius:12px; padding:14px 16px; box-shadow:0 3px 12px rgba(15,23,42,.06); height:100%; }
.dashboard-card-title { color:#334155; font-size:12px; font-weight:900; letter-spacing:.5px; text-transform:uppercase; margin-bottom:6px; }
.dashboard-card-value { color:#1f2937; font-size:30px; line-height:1; font-weight:950; }
.dashboard-card-value.red { color:#dc3b45; }
.dashboard-card-value.orange { color:#d97706; }
.dashboard-card-value.green { color:#15803d; }
.dashboard-card-value.blue { color:#2563a8; }
.mini-kpi { background:#fff; border:1px solid #d8dee7; border-radius:10px; padding:10px 12px; text-align:center; box-shadow:0 2px 8px rgba(15,23,42,.05); }
.mini-kpi-label { font-size:10px; color:#64748b; font-weight:850; text-transform:uppercase; }
.mini-kpi-value { font-size:24px; color:#1f2937; font-weight:950; margin-top:3px; }
.dashboard-section { font-size:17px; font-weight:950; color:#243447; margin:18px 0 9px; }
.top-defect-table { width:100%; border-collapse:collapse; font-size:12px; }
.top-defect-table th { text-align:left; background:#f1f5f9; color:#475569; padding:9px 10px; font-weight:900; }
.top-defect-table td { border-top:1px solid #e5e7eb; padding:9px 10px; color:#334155; font-weight:650; }
.rank-badge { display:inline-block; min-width:24px; padding:3px 6px; border-radius:6px; background:#eef2f7; text-align:center; font-weight:900; }


/* HIGH VISIBILITY INPUTS GLOBALLY: Streamlit widgets may be outside stForm. */
/* Selectboxes, text inputs, number inputs, date inputs, and textareas */
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
div[data-testid="stMultiSelect"] div[data-baseweb="select"] > div,
div[data-testid="stTextInput"] div[data-baseweb="input"] > div,
div[data-testid="stNumberInput"] div[data-baseweb="input"] > div,
div[data-testid="stDateInput"] div[data-baseweb="input"] > div,
div[data-testid="stTextArea"] div[data-baseweb="textarea"] > div {
    background-color: #ffffff !important;
    border: 2px solid #64748b !important;
    border-radius: 9px !important;
    box-shadow: 0 1px 4px rgba(15, 23, 42, 0.12) !important;
    min-height: 44px !important;
}
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div:hover,
div[data-testid="stMultiSelect"] div[data-baseweb="select"] > div:hover,
div[data-testid="stTextInput"] div[data-baseweb="input"] > div:hover,
div[data-testid="stNumberInput"] div[data-baseweb="input"] > div:hover,
div[data-testid="stDateInput"] div[data-baseweb="input"] > div:hover,
div[data-testid="stTextArea"] div[data-baseweb="textarea"] > div:hover {
    border-color: #2563eb !important;
}
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div:focus-within,
div[data-testid="stMultiSelect"] div[data-baseweb="select"] > div:focus-within,
div[data-testid="stTextInput"] div[data-baseweb="input"] > div:focus-within,
div[data-testid="stNumberInput"] div[data-baseweb="input"] > div:focus-within,
div[data-testid="stDateInput"] div[data-baseweb="input"] > div:focus-within,
div[data-testid="stTextArea"] div[data-baseweb="textarea"] > div:focus-within {
    border: 2px solid #1d4ed8 !important;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.22) !important;
}
div[data-testid="stSelectbox"] div[data-baseweb="select"] span,
div[data-testid="stMultiSelect"] div[data-baseweb="select"] span,
div[data-testid="stTextInput"] input,
div[data-testid="stNumberInput"] input,
div[data-testid="stDateInput"] input,
div[data-testid="stTextArea"] textarea {
    color: #172554 !important;
}

/* CLEAR, HIGH-CONTRAST FORM FIELDS (especially Add Audit Data) */
div[data-testid="stForm"] div[data-baseweb="select"] > div,
div[data-testid="stForm"] div[data-baseweb="input"] > div,
div[data-testid="stForm"] div[data-baseweb="textarea"] > div,
div[data-testid="stForm"] [data-testid="stDateInput"] div[data-baseweb="input"] > div,
div[data-testid="stForm"] [data-testid="stNumberInput"] div[data-baseweb="input"] > div {
    background: #ffffff !important;
    border: 1.5px solid #94a3b8 !important;
    border-radius: 9px !important;
    box-shadow: 0 1px 3px rgba(15, 23, 42, 0.07) !important;
    min-height: 42px !important;
    transition: border-color .18s ease, box-shadow .18s ease !important;
}
div[data-testid="stForm"] div[data-baseweb="select"] > div:hover,
div[data-testid="stForm"] div[data-baseweb="input"] > div:hover,
div[data-testid="stForm"] div[data-baseweb="textarea"] > div:hover {
    border-color: #2563eb !important;
}
div[data-testid="stForm"] div[data-baseweb="select"] > div:focus-within,
div[data-testid="stForm"] div[data-baseweb="input"] > div:focus-within,
div[data-testid="stForm"] div[data-baseweb="textarea"] > div:focus-within {
    border-color: #2563eb !important;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.17) !important;
}
div[data-testid="stForm"] div[data-baseweb="select"] span,
div[data-testid="stForm"] div[data-baseweb="input"] input,
div[data-testid="stForm"] textarea {
    color: #172554 !important;
}
div[data-testid="stForm"] label {
    color: #1e293b !important;
    font-weight: 650 !important;
}
/* Fluid check controls get a subtle green tint so they stand out clearly. */
div[data-testid="stForm"] div[data-testid="stHorizontalBlock"] div[data-baseweb="select"] > div {
    border-color: #86a3bd !important;
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# USERS & AUTH HELPERS
# ============================================================
def load_users():
    if not os.path.exists(USERS_FILE):
        default_users = {}
        if LOGIN_EMAIL:
            default_users[LOGIN_EMAIL.strip().lower()] = {
                "name": "Administrator",
                "password": LOGIN_PASSWORD,
                "status": "approved",
                "role": "admin",
            }
        save_users(default_users)
        return default_users
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_users(users_dict):
    with open(USERS_FILE, "w") as f:
        json.dump(users_dict, f, indent=4)


# ============================================================
# PROFESSIONAL LOGIN PAGE
# ============================================================
def login():
    st.markdown(
        """
        <div class="top-header-banner">
            <div class="top-header-text">PREPARED BY TEAM FQCM</div>
            <div class="top-header-sub">FINAL QUALITY CONTROL MANAGEMENT</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2.2, 1])
    
    with col2:
        st.markdown(
            """
            <div class="login-brand-box">
                <div class="brand-left">
                    <div class="brand-hex">
                        <span class="brand-check">✓</span>
                    </div>
                    <div class="brand-texts">
                        <div class="brand-top-sub">MASTER MOTORS • FUSO</div>
                        <div class="brand-main-title">
                            <span class="brand-qfl">QFL4</span>
                            <span class="brand-ai">AI</span>
                        </div>
                        <div class="brand-desc">AUTOMOTIVE QUALITY & AUDIT INTELLIGENCE</div>
                    </div>
                </div>
                <div class="brand-fqcm-box">
                    <div class="brand-fqcm-text">FQCM</div>
                    <div class="brand-fqcm-active">ACTIVE</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        users = load_users()

        if not st.session_state.show_signup:
            st.markdown(
                """
                <div class="login-title">Welcome Back</div>
                <div class="login-subtitle">Sign in to access QFL4 Audit Intelligence</div>
                """,
                unsafe_allow_html=True,
            )
            
            with st.form("login_form"):
                e = st.text_input("Email", placeholder="name@master.com.pk")
                p = st.text_input("Password", type="password", placeholder="••••••••")
                submitted = st.form_submit_button("LOGIN", use_container_width=True, type="primary")

                if submitted:
                    e_clean = e.strip().lower()
                    if e_clean in users:
                        if users[e_clean]["status"] == "approved":
                            if users[e_clean]["password"] == p:
                                st.session_state.logged_in = True
                                st.session_state.user_email = e_clean
                                st.session_state.role = users[e_clean].get("role", "user")
                                st.rerun()
                            else:
                                st.error("Incorrect password.")
                        else:
                            st.warning("Your account is awaiting admin approval ⏳")
                    else:
                        st.error("Email not found. Please create an account.")

            st.markdown("<p style='text-align:center; font-size:13px; color:#718096; margin-top:15px; margin-bottom:5px;'>Don't have an account?</p>", unsafe_allow_html=True)
            if st.button("Create Account", use_container_width=True):
                st.session_state.show_signup = True
                st.rerun()

        else:
            st.markdown(
                """
                <div class="login-title" style="font-size: 24px;">Create Account</div>
                <div class="login-subtitle">Register for audit portal access</div>
                """,
                unsafe_allow_html=True,
            )

            with st.form("signup_form"):
                full_name = st.text_input("Full Name", placeholder="Taha Shahid")
                new_e = st.text_input("Email", placeholder="name@master.com.pk").strip().lower()
                new_p = st.text_input("Password", type="password", placeholder="••••••••")
                confirm_p = st.text_input("Confirm Password", type="password", placeholder="••••••••")
                
                signup_submitted = st.form_submit_button("CREATE ACCOUNT", use_container_width=True, type="primary")

                if signup_submitted:
                    if not full_name or not new_e or not new_p or not confirm_p:
                        st.error("Please fill in all fields.")
                    elif new_p != confirm_p:
                        st.error("Passwords do not match.")
                    elif new_e in users:
                        st.error("This email is already registered or requested.")
                    else:
                        users[new_e] = {
                            "name": full_name,
                            "password": new_p,
                            "status": "pending",
                            "role": "user",
                        }
                        save_users(users)
                        st.success("Account created! Status: PENDING ⏳. Waiting for admin approval.")

            st.markdown("<p style='text-align:center; font-size:13px; color:#718096; margin-top:15px; margin-bottom:5px;'>Already have an account?</p>", unsafe_allow_html=True)
            if st.button("Login", use_container_width=True):
                st.session_state.show_signup = False
                st.rerun()
        
        st.markdown(
            """
            <div style="text-align: center; font-size: 11px; color: #94a3b8; margin-top: 15px;">
                &copy; 2026 Master Motor Corporation Ltd.<br>Powered by AI Audit Intelligence
            </div>
            """,
            unsafe_allow_html=True
        )


# ============================================================
# HELPER FUNCTIONS
# ============================================================
def init_gemini():
    api_key = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", ""))
    if not api_key:
        return False
    genai.configure(api_key=api_key)
    return True

def norm(x):
    return re.sub(r"[^a-z0-9]+", "", str(x).lower())

def find_col(d, names):
    mapping = {norm(c): c for c in d.columns}
    return next((mapping[norm(x)] for x in names if norm(x) in mapping), None)

def nsum(d, c):
    if not c or c not in d.columns:
        return 0
    return int(pd.to_numeric(d[c], errors="coerce").fillna(0).sum())

def vehicle_count(d):
    c = find_col(d, ["Chassis No", "Chassis", "Chassis Number", "Vehicle", "Vehicle No", "Vehicle Number"])
    if not c:
        return len(d)
    s = d[c].dropna().astype(str).str.strip()
    s = s[s != ""]
    return int(s.nunique())

def class_total(d, label):
    return nsum(d, find_col(d, [f"CLASS {label}", f"Class {label}", f"CLASS_{label}"]))

def zone_total(d, label):
    return nsum(d, find_col(d, [f"ZONE {label}", f"Zone {label}", f"ZONE_{label}"]))

def ab_total(d):
    c = find_col(d, ["A+B", "A + B", "AB", "A B"])
    return nsum(d, c) if c else class_total(d, "A") + class_total(d, "B")

def total_defects(d):
    # Prefer the actual quantity entered on the audit form. Some imported
    # workbooks contain a "Total" column that is blank/zero even when QTY > 0.
    qty_col = find_col(d, ["QTY", "Quantity", "Defect Qty", "Defect Quantity", "Qty"])
    qty_total = nsum(d, qty_col)
    if qty_total:
        return qty_total

    # Fall back to class totals when present.
    class_sum = sum(class_total(d, x) for x in "ABCD")
    if class_sum:
        return class_sum

    # Last resort: use a general Total column.
    total_col = find_col(d, ["Total Defects", "Total", "Defects"])
    return nsum(d, total_col)

def calculate_dpu(d):
    v_count = vehicle_count(d)
    if v_count == 0:
        return 0.0
    tot_def = total_defects(d)
    return round(tot_def / v_count, 2)

def get_google_worksheet():
    """Connect to the configured Google Sheet using Streamlit secrets."""
    service_account_info = dict(st.secrets["gcp_service_account"])
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    credentials = Credentials.from_service_account_info(service_account_info, scopes=scopes)
    client = gspread.authorize(credentials)
    spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)
    return spreadsheet.worksheet(SHEET_NAME)


def load_excel():
    """Load audit records from Google Sheets (the authoritative data source)."""
    worksheet = get_google_worksheet()
    values = worksheet.get_all_values()
    if not values:
        return pd.DataFrame()
    headers = [str(value).strip() for value in values[0]]
    rows = values[1:]
    # Pad short rows and trim any extra cells to match the header width.
    normalized_rows = [(row[:len(headers)] + [""] * max(0, len(headers) - len(row))) for row in rows]
    d = pd.DataFrame(normalized_rows, columns=headers)
    d.columns = d.columns.astype(str).str.strip().str.replace("\n", " ", regex=False).str.replace(r"\s+", " ", regex=True)
    date_col = next((x for x in d.columns if str(x).strip().lower() == "date"), None)
    if date_col:
        d[date_col] = pd.to_datetime(d[date_col], errors="coerce")
    return d


def save_google_sheet(dataframe):
    """Replace worksheet contents with the supplied DataFrame."""
    worksheet = get_google_worksheet()
    clean_df = dataframe.copy().fillna("")
    clean_df = clean_df.astype(object).where(pd.notna(clean_df), "")
    rows = [clean_df.columns.astype(str).tolist()]
    for row in clean_df.itertuples(index=False, name=None):
        rows.append([value.isoformat() if isinstance(value, (pd.Timestamp, datetime)) else str(value) if value is not None else "" for value in row])
    worksheet.clear()
    if rows:
        worksheet.update(range_name="A1", values=rows, value_input_option="USER_ENTERED")

def page_title(title, description):
    st.markdown(
        f"""
        <div class="page-title">{html.escape(title)}</div>
        <div class="page-desc">{html.escape(description)}</div>
        """,
        unsafe_allow_html=True,
    )

def make_ai_context(d):
    summary_str = ""
    defect_c = find_col(d, ["Defect Type", "Defect", "Defect Name", "Defect Description", "Problem"])
    qty_c = find_col(d, ["QTY", "Quantity", "Defect Qty", "Defect Quantity", "Qty"])
    
    if defect_c and qty_c:
        agg = d.groupby(defect_c, as_index=False)[qty_c].sum().sort_values(qty_c, ascending=False)
        summary_str = "\n\nCOMPLETE DEFECT TYPE SUMMARY (Total Quantities per Defect Type across all records):\n" + agg.to_string(index=False)

    category_c = find_col(d, ["Defect Category", "Category"])
    if category_c and qty_c:
        agg_cat = d.groupby(category_c, as_index=False)[qty_c].sum().sort_values(qty_c, ascending=False)
        summary_str += "\n\nCOMPLETE DEFECT CATEGORY SUMMARY:\n" + agg_cat.to_string(index=False)

    sample = d.tail(20).copy()
    for c in sample.columns:
        if pd.api.types.is_datetime64_any_dtype(sample[c]):
            sample[c] = sample[c].dt.strftime("%Y-%m-%d")
            
    recent_str = "\n\nRECENT AUDIT ROWS:\n" + sample.to_string(index=False)
    return summary_str + recent_str

def ai_answer(q, d):
    if not init_gemini():
        return "Gemini API key is not configured. Please add GEMINI_API_KEY to Streamlit Secrets."

    context = make_ai_context(d)
    current_date_str = datetime.now().strftime("%Y-%m-%d")
    
    prompt = f"""You are the QFL4 Vehicle Audit Intelligence Assistant for Master Motors FUSO.
CURRENT SYSTEM DATE: {current_date_str}

STRICT DATA RULES:
1. Use the COMPLETE DEFECT TYPE SUMMARY and audit data supplied below to answer questions about defect types, quantities, vehicles, dates, chassis, classes (A, B, C, D), zones, and DPU.
2. Never invent, estimate, assume, or fabricate a number or vehicle detail. Look up the exact numbers from the supplied summaries and rows.
3. RELATIVE TIME AWARENESS: Use the CURRENT SYSTEM DATE above to evaluate relative time queries like "last week", "yesterday", or "today". If there are NO audit records matching that specific time frame in the provided data, you must explicitly state that no vehicles were audited during that period.
4. Respect active dashboard filters.
5. LANGUAGE RULE: Respond in professional English only, regardless of the language used in the question.
6. Keep answers concise, accurate, and fast.

ACTIVE FILTERED AUDIT DATA & SUMMARIES:
Columns: {", ".join(map(str, d.columns))}
{context}

USER QUESTION: {q}"""

    try:
        model = genai.GenerativeModel(AI_MODEL)
        response = model.generate_content(prompt)
        answer = response.text
        return answer.strip() or "I could not generate an answer from the current audit data."
    except Exception as exc:
        return f"Gemini AI request failed: {exc}"

def ai_answer_audio(audio_bytes, d):
    if not init_gemini():
        return "Gemini API key is not configured."

    context = make_ai_context(d)
    current_date_str = datetime.now().strftime("%Y-%m-%d")
    
    prompt = f"""You are the QFL4 Vehicle Audit Intelligence Assistant for Master Motors FUSO.
CURRENT SYSTEM DATE: {current_date_str}

STRICT DATA RULES:
1. Listen to the user's voice question and use the COMPLETE DEFECT TYPE SUMMARY and audit data supplied below to answer questions.
2. Never invent, estimate, assume, or fabricate a number or vehicle detail.
3. LANGUAGE RULE: Respond in professional English only, regardless of the language used in the question.
4. Keep answers concise and clear.

ACTIVE FILTERED AUDIT DATA & SUMMARIES:
Columns: {", ".join(map(str, d.columns))}
{context}"""

    try:
        model = genai.GenerativeModel(AI_MODEL)
        response = model.generate_content([
            {"mime_type": "audio/webm", "data": audio_bytes},
            prompt
        ])
        return response.text.strip() or "I could not understand the audio recording."
    except Exception as exc:
        return f"Voice processing failed: {exc}"

def speak(text):
    safe_text = json.dumps(str(text))
    components.html(f"""<script>speechSynthesis.cancel();const u = new SpeechSynthesisUtterance({safe_text});u.lang='en-US';speechSynthesis.speak(u);</script>""", height=1)


# ============================================================
# AUTHENTICATION CHECK
# ============================================================
if not st.session_state.logged_in:
    login()
    st.stop()


# ============================================================
# REQUIRED FILE CHECK
# ============================================================
# ============================================================
# LOAD DATA FROM GOOGLE SHEETS
# ============================================================
try:
    df = load_excel()
except Exception as exc:
    st.error("Unable to load audit data from Google Sheets.")
    st.caption(f"Details: {type(exc).__name__}: {exc}")
    st.info("Verify that Streamlit Secrets contains [gcp_service_account], GOOGLE_SHEET_ID is correct, the worksheet tab is named 'Audit Entries', and the service account has Editor access to the spreadsheet.")
    st.stop()


# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown(
        """
        <div class="nav-brand">
            <div class="nav-brand-top">MASTER MOTOR • QFL4</div>
            <div class="nav-brand-title">Audit Intelligence</div>
            <div class="nav-caption">Quality analytics portal</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="nav-section">ANALYTICS</div>', unsafe_allow_html=True)

    nav_pages = [
        "Vision & Mission",
        "🏠 Overview",
        "🎙️ AI Assistant",
        "⚠️ Total Defects",
        "📈 Pareto Analysis",
        "🚗 Vehicle Audit",
        "📄 Download Chassis Sheet",
        "🧩 Class & Zone",
        "📋 Audit Data",
    ]

    if st.session_state.get("role") == "admin":
        nav_pages.append("➕ Add Audit Data")
        nav_pages.append("🗑️ Delete Audit Entry")
        nav_pages.append("👥 Manage Users")

    page = st.radio("Pages", nav_pages, label_visibility="collapsed")

    if st.session_state.get("role") == "admin":
        st.markdown('<div class="nav-section">DATA MANAGEMENT</div>', unsafe_allow_html=True)
        st.caption("Audit records are stored in the connected Google Sheet.")

    st.markdown('<div class="nav-section">SYSTEM</div>', unsafe_allow_html=True)
    ai_ready = bool(st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", "")))
    ai_status = '<span class="status-ok">● GEMINI AI READY</span>' if ai_ready else '<span class="status-warn">● GEMINI KEY REQUIRED</span>'

    st.markdown(
        f"""
        <div class="sidebar-note">
            User: {html.escape(st.session_state.get('user_email', ''))}<br>
            Role: {html.escape(st.session_state.get('role', 'user').upper())}<br>
            Source: Google Sheets<br>
            {ai_status}
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.role = "user"
        st.rerun()


# ============================================================
# VISION & MISSION
# ============================================================
if page == "Vision & Mission":
    page_title(
        "Vision & Mission",
        "Leadership vision for digital transformation and AI-driven quality intelligence."
    )

    col_img, col_text = st.columns([1, 2], gap="large")

    with col_img:
        photo_file = "ather_ali_darbari.png"
        if os.path.exists(photo_file):
            st.markdown('<div class="leader-photo-wrap">', unsafe_allow_html=True)
            st.image(photo_file, use_container_width=True)
            st.markdown(
                """
                <div class="leader-caption">
                    <div class="leader-name">Mr. Ather Ali Darbari</div>
                    <div class="leader-role">Senior General Manager</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("Please place the leadership photo in the app folder as: ather_ali_darbari.png")
            st.markdown(
                """
                <div class="leader-caption">
                    <div class="leader-name">Mr. Ather Ali Darbari</div>
                    <div class="leader-role">Senior General Manager</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with col_text:
        st.markdown(
            """
            <div class="vision-card">
                <div class="vision-heading"><span class="vision-icon vision-icon-red">V</span>VISION</div>
                <div class="vision-text">
                    Leverage technology to digitalize quality processes and use
                    Artificial Intelligence to analyse quality data, enabling smarter,
                    faster and data-driven decision-making across the organization.
                </div>
            </div>

            <div class="vision-card">
                <div class="vision-heading"><span class="vision-icon vision-icon-blue">M</span>MISSION</div>
                <div class="vision-text">
                    Transform manual and disconnected quality activities into integrated
                    digital solutions that systematically capture and analyse data,
                    using AI to identify trends, detect problems, prioritize improvement
                    opportunities and drive continuous quality improvement.
                </div>
            </div>

            <div class="vision-card approach-card">
                <div class="vision-heading"><span class="vision-icon vision-icon-gold">→</span>DIGITAL QUALITY APPROACH</div>
                <div class="vision-text approach-text">
                    Digitalize &nbsp;→&nbsp; Collect Data &nbsp;→&nbsp; Analyse with AI
                    &nbsp;→&nbsp; Identify Trends &nbsp;→&nbsp; Take Action &nbsp;→&nbsp; Continuous Improvement
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.stop()

# ============================================================
# ADMIN PAGE: MANAGE USERS
# ============================================================
if page == "👥 Manage Users":
    if st.session_state.get("role") != "admin":
        st.error("Access Denied: You do not have administrator privileges.")
        st.stop()
        
    page_title("User Approvals", "Approve or reject pending account registration requests.")
    users = load_users()
    pending_list = [email for email, info in users.items() if info["status"] == "pending"]

    if not pending_list:
        st.info("No pending user registration requests right now.")
    else:
        st.write(f"Found **{len(pending_list)}** pending account request(s):")
        for email in pending_list:
            c1, c2, c3 = st.columns([3, 1, 1])
            with c1:
                user_name = users[email].get("name", "N/A")
                st.markdown(f"**{user_name}** <br><span style='color:#718096; font-size:12px;'>{email}</span>", unsafe_allow_html=True)
            with c2:
                if st.button("Approve", key=f"app_{email}", type="primary"):
                    users[email]["status"] = "approved"
                    save_users(users)
                    st.success(f"Approved {email}!")
                    st.rerun()
            with c3:
                if st.button("Reject", key=f"rej_{email}"):
                    del users[email]
                    save_users(users)
                    st.warning(f"Rejected and removed {email}.")
                    st.rerun()
    st.stop()


# ============================================================
# ADMIN PAGE: DELETE AUDIT ENTRY
# ============================================================
if page == "🗑️ Delete Audit Entry":
    if st.session_state.get("role") != "admin":
        st.error("Access denied. Administrator privileges are required to access this page.")
        st.stop()

    page_title("Delete Audit Entry", "Select a chassis record to permanently delete it.")
    try:
        df_delete = load_excel()
        chassis_col_delete = find_col(df_delete, ["Chassis No", "Chassis", "Chassis Number"])
        if not chassis_col_delete:
            st.error("The Chassis No. column was not found in the spreadsheet.")
        else:
            chassis_values = (
                df_delete[chassis_col_delete]
                .dropna()
                .astype(str)
                .str.strip()
            )
            chassis_values = chassis_values[chassis_values != ""]
            unique_chassis = sorted(chassis_values.unique().tolist())

            if not unique_chassis:
                st.info("No chassis entries are available to delete.")
            else:
                selected_chassis = st.selectbox("Select Chassis Number", unique_chassis)
                matching_delete_rows = df_delete.index[
                    df_delete[chassis_col_delete].fillna("").astype(str).str.strip().str.casefold()
                    == selected_chassis.casefold()
                ].tolist()
                st.warning(
                    f"Deleting chassis **{selected_chassis}** will permanently remove {len(matching_delete_rows)} row(s) "
                    "and all associated defect details."
                )
                confirm_delete = st.checkbox(
                    "I understand this action cannot be undone.",
                    key="confirm_delete_chassis_entry",
                )
                if st.button(
                    "Delete Selected Chassis Entry",
                    type="primary",
                    use_container_width=True,
                    disabled=not confirm_delete,
                ):
                    df_delete = df_delete.drop(index=matching_delete_rows).reset_index(drop=True)
                    save_google_sheet(df_delete)
                    st.success(f"All audit entries for chassis {selected_chassis} were deleted successfully.")
                    st.rerun()
    except Exception as exc:
        st.error(f"An error occurred while deleting the audit entry: {exc}")
    st.stop()


# ============================================================
# ADMIN PAGE: ADD AUDIT DATA
# ============================================================
if page == "➕ Add Audit Data":
    if st.session_state.get("role") != "admin":
        st.error("Access denied. Administrator privileges are required to access this page.")
        st.stop()

    page_title("Admin Data Entry", "Create a new audit record.")

    # Keep the defect rows horizontal and let the admin choose how many
    # nomenclature entries belong to this chassis.
    defect_rows_count = st.number_input(
        "Number of Defects for this Chassis",
        min_value=1,
        max_value=30,
        value=1,
        step=1,
        key="nomenclature_rows_count",
    )

    # Chassis input intentionally stays OUTSIDE the form so Streamlit reruns
    # on every edit and duplicate feedback appears beside this one field.
    st.markdown("### Vehicle / Audit Details")
    c1, c2 = st.columns(2)
    with c1:
        audit_date = st.date_input("Date", datetime.now(), key="audit_date_live")
        vehicle_name = st.text_input("Vehicle Name", "FUSO Canter", key="vehicle_name_live")
        model_name = st.text_input("Model", "FE84", key="model_name_live")
        chassis_no = st.text_input("Chassis No.", "", key="chassis_no_vehicle_details")
        engine_no = st.text_input("Engine No.", placeholder="Enter engine number", key="engine_no_live")

    def _normalize_chassis(value):
        if pd.isna(value):
            return ""
        return re.sub(r"[^a-z0-9]", "", str(value).strip().casefold())

    chassis_key_live = _normalize_chassis(chassis_no)
    duplicate_chassis_live = False
    if chassis_key_live:
        try:
            df_chassis_live = load_excel()
            chassis_col_live = find_col(df_chassis_live, ["Chassis No", "Chassis Number", "Chassis"])
            if chassis_col_live:
                existing_live = df_chassis_live[chassis_col_live].map(_normalize_chassis)
                duplicate_chassis_live = bool((existing_live.ne("") & existing_live.eq(chassis_key_live)).any())
            else:
                st.error("The Chassis No column was not found. Please verify the column heading.")
        except Exception as exc:
            st.error(f"Unable to check for duplicate chassis numbers: {exc}")
    if duplicate_chassis_live:
        st.error("This chassis number is already entered.")

    with st.form("add_data_form"):

        st.markdown("### Fluid Check")
        st.caption("Select a check mark (✓) or cross (✗) for each item.")
        fc1, fc2, fc3, fc4, fc5 = st.columns(5)
        with fc1:
            fluid_clutch = st.selectbox("CLUTCH", ["✓", "✗"], key="fluid_clutch")
        with fc2:
            fluid_engine = st.selectbox("E/G", ["✓", "✗"], key="fluid_engine")
        with fc3:
            fluid_brake = st.selectbox("BRAKE", ["✓", "✗"], key="fluid_brake")
        with fc4:
            fluid_llc = st.selectbox("LLC", ["✓", "✗"], key="fluid_llc")
        with fc5:
            fluid_washer = st.selectbox("WASHER", ["✓", "✗"], key="fluid_washer")

        fluid_checks = {
            "Fluid Check - Clutch": fluid_clutch,
            "Fluid Check - E/G": fluid_engine,
            "Fluid Check - Brake": fluid_brake,
            "Fluid Check - LLC": fluid_llc,
            "Fluid Check - Washer": fluid_washer,
        }

        st.markdown("### Defect Nomenclature")
        st.caption(
            "Enter Defect Type and Defect Category separately for each entry. Department, Class, Zone, and Quantity "
            "aur nomenclature details bhi record hongi."
        )

        nomenclature_entries = []
        for idx in range(int(defect_rows_count)):
            st.markdown(f"**Defect Entry {idx + 1}**")
            a1, a2 = st.columns(2)
            with a1:
                entry_type = st.selectbox(
                    "Defect Type",
                    ["Safety", "Functional", "Major Aesthetics", "Minor Aesthetics"],
                    key=f"entry_type_{idx}",
                )
            with a2:
                entry_category = st.selectbox(
                    "Defect Category",
                    [
                        "Over Tightening", "Looseness", "Scratch", "Rust",
                        "Improperly installed", "Weld Spot Burr", "Weld Spot Miss",
                        "Sag", "Run", "Dent", "Bump", "Spot Miss", "Seepage",
                        "Leakage", "Crater", "Thin Paint", "Part Miss",
                        "Harness Routing Wrong", "Wrong Part", "Deformation",
                        "Gap NG", "Indicator not work", "Wrinkles",
                        "Torque Mark Miss", "Other",
                    ],
                    key=f"entry_category_{idx}",
                )
            a3, a4, a5 = st.columns([1.2, 1.2, 1])
            with a3:
                department = st.selectbox(
                    "Department",
                    [
                        "Weld Shop", "Paint Shop", "Assembly Shop", "Tester Line",
                        "Final Confirmation", "QA Receiving", "CKD",
                    ],
                    key=f"entry_department_{idx}",
                )
            with a4:
                entry_qty = st.number_input("Total Defect Quantity (QTY)", min_value=1, value=1,
                                            step=1, key=f"entry_qty_{idx}")
            with a5:
                st.caption("Type aur Category alag fields hain.")

            b1, b2, b3 = st.columns(3)
            with b1:
                entry_class = st.selectbox("Defect Class", ["A", "B", "C", "D"],
                                           key=f"entry_class_{idx}")
            with b2:
                entry_zone = st.selectbox("Zone", ["A", "B", "C", "D"],
                                          key=f"entry_zone_{idx}")
            with b3:
                vloc = st.selectbox("Vehicle Location", ["RH", "LH", "FR", "RR"],
                                    key=f"nomenclature_vloc_{idx}")

            v4, v5, v6, v7 = st.columns([1, 1.2, 1, 1.6])
            with v4:
                area = st.selectbox("Area", ["Side", "Upper Side", "Lower Side"],
                                    key=f"nomenclature_area_{idx}")
            with v5:
                part = st.text_input("Part Name", placeholder="Part name",
                                     key=f"nomenclature_part_{idx}")
            with v6:
                ploc = st.selectbox("Part Location", ["RH", "LH", "FR", "RR"],
                                    key=f"nomenclature_ploc_{idx}")
            with v7:
                defect = st.text_input("Defect Description", placeholder="Defect description",
                                       key=f"nomenclature_defect_{idx}")



            nomenclature_entries.append({
                "type": entry_type.strip(), "category": entry_category.strip(),
                "department": department.strip(), "qty": int(entry_qty), "class": entry_class, "zone": entry_zone,
                "vloc": vloc, "area": area, "part": part.strip(),
                "ploc": ploc, "defect": defect.strip()
            })

        submitted = st.form_submit_button(
            "Save All Defects to Google Sheets", type="primary", use_container_width=True
        )

        if submitted:
            if duplicate_chassis_live:
                st.error("This chassis number is already entered.")
                st.stop()
            try:
                if not str(chassis_no).strip():
                    st.error("Please enter a chassis number.")
                    st.stop()
                df_existing = load_excel()
                df_existing.columns = (
                    df_existing.columns.astype(str).str.strip()
                    .str.replace("\\n", " ", regex=False)
                    .str.replace(r"\\s+", " ", regex=True)
                )

                valid_entries = []
                for item in nomenclature_entries:
                    if not item["part"] and not item["defect"] and not item["type"] and not item["category"] and not item["department"]:
                        continue
                    if not item["type"] or not item["category"] or not item["department"] or not item["part"] or not item["defect"]:
                        st.error("Each completed entry must include Defect Type, Defect Category, Department, Part Name, and Defect Description.")
                        st.stop()
                    valid_entries.append(item)

                if not valid_entries:
                    st.error("Please enter at least one complete defect entry.")
                    st.stop()

                # Preserve per-entry details in dedicated Excel columns as well as
                # the existing Defect N nomenclature field.
                # Defect N columns contain ONLY the five-part nomenclature,
                # exactly in the requested format. Other details remain in
                # their own numbered columns (Defect Type N, Department N, etc.).
                nomenclatures = [
                    f'{x["vloc"]} | {x["area"]} | {x["part"]} | {x["ploc"]} | {x["defect"]}'
                    for x in valid_entries
                ]
                total_qty = sum(x["qty"] for x in valid_entries)
                first = valid_entries[0]

                # Assign a sequential control number for each new chassis record.
                control_col_existing = find_col(df_existing, ["Control Number", "Control No", "Control #"])
                control_values = (
                    df_existing[control_col_existing].dropna().astype(str).str.strip().tolist()
                    if control_col_existing else []
                )
                used_numbers = []
                for control_value in control_values:
                    match_control = re.search(r"(\\d+)\\s*$", control_value)
                    if match_control:
                        used_numbers.append(int(match_control.group(1)))
                next_control_number = max(used_numbers or [0]) + 1
                generated_control = f"QFL4-{pd.to_datetime(audit_date):%Y%m%d}-{next_control_number:04d}"

                new_entry = {
                    "Control Number": generated_control,
                    "Date": pd.to_datetime(audit_date),
                    "Vehicle": vehicle_name,
                    "Model": model_name,
                    "Chassis No": str(chassis_no).strip(),
                    "Engine No": str(engine_no).strip(),
                    "Defect Type": first["type"],
                    "Department": first["department"],
                    "Defect Category": first["category"],
                    "QTY": total_qty,
                    **fluid_checks,
                }

                for cls in "ABCD":
                    amount = sum(x["qty"] for x in valid_entries if x["class"] == cls)
                    class_col_name = f"CLASS {cls}"
                    if class_col_name in df_existing.columns:
                        new_entry[class_col_name] = amount
                for zone in "ABCD":
                    amount = sum(x["qty"] for x in valid_entries if x["zone"] == zone)
                    zone_col_name = f"ZONE {zone}"
                    if zone_col_name in df_existing.columns:
                        new_entry[zone_col_name] = amount

                existing_defect_cols = [
                    c for c in df_existing.columns
                    if re.fullmatch(r"Defect\s*\d+", str(c).strip(), flags=re.IGNORECASE)
                ]
                highest_existing = max(
                    [int(re.search(r"\d+", str(c)).group()) for c in existing_defect_cols] or [0]
                )
                required_defect_count = max(highest_existing, len(nomenclatures))
                for n in range(1, required_defect_count + 1):
                    col = f"Defect {n}"
                    if col not in df_existing.columns:
                        df_existing[col] = pd.NA

                # Store separate metadata columns for every nomenclature entry.
                for n, item in enumerate(valid_entries, start=1):
                    for field, value in [
                        ("Defect Type", item["type"]), ("Defect Category", item["category"]),
                        ("Department", item["department"]), ("Defect Class", item["class"]), ("Zone", item["zone"]), ("QTY", item["qty"])
                    ]:
                        col = f"{field} {n}"
                        if col not in df_existing.columns:
                            df_existing[col] = pd.NA

                # Reliable duplicate check: match the chassis-specific column only,
                # normalize case and remove spaces/punctuation on both sides.
                chassis_col = find_col(df_existing, ["Chassis No", "Chassis Number", "Chassis"])
                chassis_key = _normalize_chassis(chassis_no)
                if not chassis_col:
                    st.error("The Chassis No column was not found. Please verify the column heading.")
                    st.stop()
                existing_chassis = df_existing[chassis_col].map(_normalize_chassis)
                matching_rows = df_existing.index[
                    existing_chassis.ne("") & existing_chassis.eq(chassis_key)
                ].tolist()
                if matching_rows:
                    st.error("This chassis number is already entered.")
                    st.stop()


                if matching_rows:
                    target_idx = matching_rows[0]
                    for key, value in new_entry.items():
                        if key not in df_existing.columns:
                            df_existing[key] = pd.NA
                        if key in ["QTY"] or re.fullmatch(r"(CLASS|ZONE) [ABCD]", key):
                            old_value = pd.to_numeric(pd.Series([df_existing.at[target_idx, key]]), errors="coerce").fillna(0).iloc[0]
                            df_existing.at[target_idx, key] = old_value + value
                        elif key == "Control Number":
                            old_control = df_existing.at[target_idx, key]
                            if pd.isna(old_control) or not str(old_control).strip():
                                df_existing.at[target_idx, key] = value
                        elif key in fluid_checks:
                            df_existing.at[target_idx, key] = value
                        elif pd.isna(df_existing.at[target_idx, key]) or str(df_existing.at[target_idx, key]).strip() == "":
                            df_existing.at[target_idx, key] = value

                    for item in valid_entries:
                        for n in range(1, required_defect_count + 1):
                            col = f"Defect {n}"
                            val = df_existing.at[target_idx, col]
                            if pd.isna(val) or not str(val).strip() or str(val).strip().lower() == "nan":
                                df_existing.at[target_idx, col] = nomenclatures.pop(0)
                                break
                    # Fill metadata slots using the first available numbered slot.
                    for item in valid_entries:
                        for n in range(1, required_defect_count + 1):
                            type_col = f"Defect Type {n}"
                            if pd.isna(df_existing.at[target_idx, type_col]) or not str(df_existing.at[target_idx, type_col]).strip():
                                for field, value in [
                                    ("Defect Type", item["type"]), ("Defect Category", item["category"]),
                                    ("Department", item["department"]), ("Defect Class", item["class"]), ("Zone", item["zone"]), ("QTY", item["qty"])
                                ]:
                                    df_existing.at[target_idx, f"{field} {n}"] = value
                                break
                else:
                    for n, nomenclature in enumerate(nomenclatures, start=1):
                        new_entry[f"Defect {n}"] = nomenclature
                    for n, item in enumerate(valid_entries, start=1):
                        for field, value in [
                            ("Defect Type", item["type"]), ("Defect Category", item["category"]),
                            ("Department", item["department"]), ("Defect Class", item["class"]), ("Zone", item["zone"]), ("QTY", item["qty"])
                        ]:
                            new_entry[f"{field} {n}"] = value
                    for col in df_existing.columns:
                        if col not in new_entry:
                            new_entry[col] = pd.NA
                    for col in new_entry:
                        if col not in df_existing.columns:
                            df_existing[col] = pd.NA
                    df_existing = pd.concat(
                        [df_existing, pd.DataFrame([{col: new_entry.get(col, pd.NA) for col in df_existing.columns}])],
                        ignore_index=True,
                    )

                save_google_sheet(df_existing)
                st.success(f"Saved {len(valid_entries)} defect entr{'y' if len(valid_entries) == 1 else 'ies'} successfully. One audit row was maintained for chassis {str(chassis_no).strip()}.")
                st.rerun()
            except Exception as e:
                st.error(f"An error occurred while saving the data: {e}")

    st.stop()


# ============================================================
# PAGE HEADER
# ============================================================
if page == "🏠 Overview":
    st.markdown(
        """
        <div class="main-title">AI AUDIT INTELLIGENCE</div>
        <div class="main-subtitle">Smart Vehicle Quality & Audit Analytics</div>
        <div class="online-badge">● SYSTEM ONLINE</div>
        """,
        unsafe_allow_html=True,
    )
else:
    titles = {
        "🎙️ AI Assistant": ("AI Voice Assistant", "Ask audit questions in English using voice or text."),
        "⚠️ Total Defects": ("Total Defects", "Defect performance and class distribution."),
        "📈 Pareto Analysis": ("Pareto Analysis", "Identify the highest-impact defect types and defect categories."),
        "🚗 Vehicle Audit": ("Vehicle Audit", "Vehicle and chassis-level audit information."),
        "🧩 Class & Zone": ("Class & Zone Analysis", "Compare quality classes and audit zones."),
        "📋 Audit Data": ("Audit Data", "Connected Excel records used by the analytics engine."),
    }
    if page in titles:
        title, description = titles[page]
        page_title(title, description)



# ============================================================
# DOWNLOAD ONE COMPLETED AUDIT SHEET PER CHASSIS
# ============================================================
if page == "📄 Download Chassis Sheet":
    page_title("Download Chassis Audit Sheet", "Select a chassis number to populate and download the original FUSO audit template.")

    chassis_col = find_col(df, ["Chassis No", "Chassis", "Chassis Number"])
    if not chassis_col or df.empty:
        st.warning("The Chassis No. column or audit records could not be found.")
        st.stop()

    chassis_values = sorted(
        df[chassis_col].dropna().astype(str).str.strip().loc[lambda s: s.ne("")].unique().tolist()
    )
    if not chassis_values:
        st.info("No chassis records are currently available.")
        st.stop()

    chosen_chassis = st.selectbox("Select chassis number", chassis_values)
    vehicle_rows = df[df[chassis_col].fillna("").astype(str).str.strip() == chosen_chassis]
    vehicle = vehicle_rows.iloc[0]

    # Resolve the template relative to this Python file, not the current working directory.
    # This is reliable on Streamlit Community Cloud and local runs.
    template_path = APP_DIR / TEMPLATE_FILENAME
    if not template_path.is_file():
        nearby_xlsx = sorted(p.name for p in APP_DIR.glob("*.xlsx"))
        st.error(
            f"Audit template file not found. Expected file: {TEMPLATE_FILENAME} "
            f"\nApp folder: {APP_DIR}"
        )
        if nearby_xlsx:
            st.caption("Available .xlsx files in the application folder: " + ", ".join(nearby_xlsx))
        st.info(
            "Upload the template to the same root folder in the GitHub repository as "
            "Streamlit ki main Python file hai. Filename bilkul exact hona chahiye."
        )
        st.stop()

    st.write("**Vehicle details preview**")
    preview_cols = [c for c in [
        find_col(df, ["Date"]), find_col(df, ["Model", "Model Name"]),
        find_col(df, ["Engine", "Engine No", "Engine Number"]), chassis_col
    ] if c]
    st.dataframe(vehicle_rows[preview_cols].head(1), use_container_width=True, hide_index=True)

    if st.button("Prepare Chassis Sheet", type="primary", use_container_width=True):
        try:
            from io import BytesIO
            import openpyxl
            from copy import copy

            template_wb = openpyxl.load_workbook(str(template_path))
            template_ws = template_wb[template_wb.sheetnames[0]]

            # Updated FUSO templates may have different merged-cell layouts.
            # Always write to the top-left (anchor) cell of a merged range.
            from openpyxl.cell.cell import MergedCell

            def safe_set_cell(ws, coordinate, value):
                cell = ws[coordinate]
                if isinstance(cell, MergedCell):
                    for merged_range in ws.merged_cells.ranges:
                        if coordinate in merged_range:
                            cell = ws.cell(merged_range.min_row, merged_range.min_col)
                            break
                cell.value = value
                return cell

            def cell_value(row, names, default=""):
                col = find_col(vehicle_rows, names)
                if not col:
                    return default
                value = vehicle.get(col, default)
                if pd.isna(value):
                    return default
                if isinstance(value, (pd.Timestamp, datetime)):
                    return value.strftime("%d-%m-%Y")
                return str(value).strip()

            model_value = cell_value(0, ["Model", "Model Name"])
            date_value = cell_value(0, ["Date"])
            engine_value = cell_value(0, ["Engine", "Engine No", "Engine Number", "Engine#"])
            # Write only into existing template header cells; keep all layout/styles unchanged.
            safe_set_cell(template_ws, "A3", f"MODEL: {model_value}")
            safe_set_cell(template_ws, "H3", f"DATE: {date_value}")
            safe_set_cell(template_ws, "A4", f"ENGINE# {engine_value}")
            safe_set_cell(template_ws, "H4", f"CHASSIS NO.: {chosen_chassis}")

            # The template header contains merged cells. Only write the Control Number
            # to the top-left cell I2 of the merged I2:L2 range below; never write J2.

            defect_columns = []
            for col_name in vehicle_rows.columns:
                match = re.fullmatch(r"Defect\s*(\d+)", str(col_name).strip(), flags=re.I)
                if match:
                    defect_columns.append((int(match.group(1)), col_name))
            defect_columns.sort()

            # The uploaded FUSO template has defect rows 7-38, fluid labels on row 39,
            # and the fluid check marks on row 40. Preserve the existing merged layout.
            for r in range(7, 39):
                safe_set_cell(template_ws, f"A{r}", r - 6)
                safe_set_cell(template_ws, f"B{r}", None)
                safe_set_cell(template_ws, f"G{r}", None)
                # Keep the template's printed A/B/C/D checkbox labels in H:K.
                safe_set_cell(template_ws, f"L{r}", None)

            # IMPORTANT: Control Number is permanent in the original template.
            # Do not generate, overwrite, move, restyle, unmerge, or re-merge its cells.

            filled = 0
            for n, defect_col_name in defect_columns:
                defect_text = vehicle.get(defect_col_name)
                if pd.isna(defect_text) or not str(defect_text).strip() or str(defect_text).strip().lower() == "nan":
                    continue
                if filled >= 32:
                    break
                row_num = 7 + filled
                # Defect nomenclature is displayed in the merged B:F field.
                safe_set_cell(template_ws, f"B{row_num}", str(defect_text).strip())

                dept_col = find_col(vehicle_rows, [f"Department {n}", "Department"])
                dept_value = vehicle.get(dept_col, "") if dept_col else ""
                if not pd.isna(dept_value) and str(dept_value).strip():
                    safe_set_cell(template_ws, f"G{row_num}", str(dept_value).strip())

                class_col = find_col(vehicle_rows, [f"Defect Class {n}", f"Class {n}"])
                class_value = vehicle.get(class_col, "") if class_col else ""
                if (pd.isna(class_value) or not str(class_value).strip()) and n == 1:
                    class_col = find_col(vehicle_rows, ["Defect Class", "Class"])
                    class_value = vehicle.get(class_col, "") if class_col else ""
                class_value = str(class_value).strip().upper() if not pd.isna(class_value) else ""
                if class_value in ("A", "B", "C", "D"):
                    class_cell = template_ws.cell(row_num, 8 + "ABCD".index(class_value))
                    safe_set_cell(template_ws, class_cell.coordinate, f"☑{class_value}")
                filled += 1

            # Fluid checks come from Audit Entries; only tick/cross marks are printed.
            fluid_template_columns = [
                ("Fluid Check - Clutch", "B40"),
                ("Fluid Check - E/G", "C40"),
                ("Fluid Check - Brake", "D40"),
                ("Fluid Check - LLC", "E40"),
                ("Fluid Check - Washer", "F40"),
            ]
            for source_name, target_cell in fluid_template_columns:
                # Reflect the saved audit value: tick for ✓, cross for ✗, blank if no value exists.
                # Do not automatically tick every item when the record has no fluid-check value.
                raw_fluid_value = vehicle.get(source_name, "")
                fluid_value = "" if pd.isna(raw_fluid_value) else str(raw_fluid_value).strip()
                mark = "✓" if fluid_value == "✓" else ("✗" if fluid_value == "✗" else "")
                cell = safe_set_cell(template_ws, target_cell, mark)
                from copy import copy as _copy
                from openpyxl.styles import Alignment
                existing_font = _copy(cell.font)
                existing_font.name = "Arial"
                existing_font.sz = 14
                existing_font.bold = True
                cell.font = existing_font
                cell.alignment = Alignment(horizontal="center", vertical="center")

            template_ws.print_area = "A1:L40"
            template_ws.page_setup.fitToWidth = 1
            template_ws.page_setup.fitToHeight = 1
            template_ws.sheet_properties.pageSetUpPr.fitToPage = True
            output = BytesIO()
            template_wb.save(output)
            output.seek(0)
            safe_chassis = re.sub(r"[^A-Za-z0-9_-]+", "_", chosen_chassis)
            st.download_button(
                "⬇️ Download Excel Sheet",
                data=output.getvalue(),
                file_name=f"FUSO_Audit_{safe_chassis}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
            st.success(f"Sheet ready: {filled} defect row(s) filled. Control Number, A/B/C/D classification, fluid tick/cross marks, and signature area are included.")
            st.caption("The coordinator signature field is intentionally left blank.")
        except Exception as exc:
            st.error(f"Unable to prepare the audit sheet: {exc}")
    st.stop()


# ============================================================
# SHARED FILTERS
# ============================================================
st.markdown('<div class="section-title">🔎 Audit Filters</div>', unsafe_allow_html=True)

date_col = find_col(df, ["Date"])
model_col = find_col(df, ["Model", "Model Name"])
chassis_col = find_col(df, ["Chassis No", "Chassis", "Chassis Number"])

# Defect fields are resolved here so the Overview dashboard and all
# downstream analytics can use them before any page-specific rendering.
defect_col = find_col(df, ["Defect Type", "Defect", "Defect Name", "Defect Description", "Problem"])
category_col = find_col(df, ["Defect Category", "Category"])
qty_col = find_col(df, ["QTY", "Quantity", "Defect Qty", "Defect Quantity", "Qty"])

# Month / Year and exact Date filters replace the old Vehicle filter.
# Both filters can be used together; when both are selected, the dashboard
# shows the intersection of the selected month(s) and exact date(s).
f1, f2, f3, f4 = st.columns(4)

with f1:
    if date_col:
        month_periods = (
            df[date_col]
            .dropna()
            .dt.to_period("M")
            .drop_duplicates()
            .sort_values(ascending=False)
            .tolist()
        )
        month_year_options = [p.strftime("%B %Y") for p in month_periods]
        selected_month_year = st.multiselect(
            "📅 Month & Year",
            month_year_options,
            placeholder="Select month / year",
        )
    else:
        month_periods = []
        month_year_options = []
        selected_month_year = []

with f2:
    if date_col:
        exact_dates = (
            df[date_col]
            .dropna()
            .dt.normalize()
            .drop_duplicates()
            .sort_values(ascending=False)
            .tolist()
        )
        date_options = [d.strftime("%d %B %Y") for d in exact_dates]
        selected_dates = st.multiselect(
            "📆 Audit Date",
            date_options,
            placeholder="Select date(s)",
        )
    else:
        exact_dates = []
        date_options = []
        selected_dates = []

with f3:
    model_options = sorted(df[model_col].dropna().astype(str).unique().tolist()) if model_col else []
    selected_model = st.selectbox("🏷️ Model", ["All"] + model_options)

with f4:
    chassis_options = sorted(df[chassis_col].dropna().astype(str).unique().tolist()) if chassis_col else []
    selected_chassis = st.selectbox("🔢 Chassis No.", ["All"] + chassis_options)

filtered = df.copy()

if selected_month_year and date_col:
    selected_periods = {
        pd.Period(value, freq="M")
        for value in selected_month_year
        for value in [pd.to_datetime(value, format="%B %Y").to_period("M")]
    }
    filtered = filtered[
        filtered[date_col].dt.to_period("M").isin(selected_periods)
    ]

if selected_dates and date_col:
    selected_date_values = {
        pd.to_datetime(value, format="%d %B %Y").normalize()
        for value in selected_dates
    }
    filtered = filtered[
        filtered[date_col].dt.normalize().isin(selected_date_values)
    ]

if selected_model != "All" and model_col:
    filtered = filtered[filtered[model_col].astype(str) == selected_model]
if selected_chassis != "All" and chassis_col:
    filtered = filtered[filtered[chassis_col].astype(str) == selected_chassis]


# ============================================================
# SHARED PARETO SUMMARY HELPER (GLOBAL SCOPE)
# ============================================================
def build_pareto_summary(data, label_col):
    """Count each numbered defect entry independently; fallback to base columns for legacy rows."""
    if not label_col or not qty_col:
        return None
    numbered = []
    for c in data.columns:
        m = re.fullmatch(re.escape(label_col) + r"\s+(\d+)", str(c).strip(), flags=re.IGNORECASE)
        if m:
            numbered.append((int(m.group(1)), c))
    numbered.sort()
    rows = []
    if numbered:
        for _, row in data.iterrows():
            found_numbered = False
            for n, c in numbered:
                label = str(row.get(c, "") if pd.notna(row.get(c, pd.NA)) else "").strip()
                qcol = next((x for x in data.columns if str(x).strip().lower() == f"qty {n}".lower()), None)
                q = pd.to_numeric(pd.Series([row.get(qcol, 0) if qcol else 0]), errors="coerce").fillna(0).iloc[0]
                if label and label.lower() not in ("nan", "none"):
                    rows.append({label_col: label, qty_col: float(q)})
                    found_numbered = True
            if not found_numbered:
                label = str(row.get(label_col, "") if pd.notna(row.get(label_col, pd.NA)) else "").strip()
                q = pd.to_numeric(pd.Series([row.get(qty_col, 0)]), errors="coerce").fillna(0).iloc[0]
                if label and label.lower() not in ("nan", "none"):
                    rows.append({label_col: label, qty_col: float(q)})
    else:
        for _, row in data.iterrows():
            label = str(row.get(label_col, "") if pd.notna(row.get(label_col, pd.NA)) else "").strip()
            q = pd.to_numeric(pd.Series([row.get(qty_col, 0)]), errors="coerce").fillna(0).iloc[0]
            if label and label.lower() not in ("nan", "none"):
                rows.append({label_col: label, qty_col: float(q)})
    if not rows:
        return pd.DataFrame(columns=[label_col, qty_col])
    out = pd.DataFrame(rows).groupby(label_col, as_index=False)[qty_col].sum()
    return out.sort_values(qty_col, ascending=False).reset_index(drop=True)

# ============================================================
# EXECUTIVE OVERVIEW DASHBOARD
# ============================================================
if page == "🏠 Overview":
    st.markdown('<div class="dashboard-title">QFL4 QUALITY CONTROL DASHBOARD</div>', unsafe_allow_html=True)
    st.markdown('<div class="dashboard-subtitle">Vehicle audit performance, defect concentration and quality classification based on the active filters.</div>', unsafe_allow_html=True)

    k1, k2, k3, k4 = st.columns(4, gap="small")
    overview_kpis = [
        (k1, "VEHICLES AUDITED", vehicle_count(filtered), "blue"),
        (k2, "TOTAL DEFECTS", total_defects(filtered), "red"),
        (k3, "A+B DEFECTS", ab_total(filtered), "orange"),
        (k4, "DPU (DEFECTS / UNIT)", calculate_dpu(filtered), "red"),
    ]
    for col, label, value, cls in overview_kpis:
        with col:
            st.markdown(f'<div class="dashboard-card"><div class="dashboard-card-title">{label}</div><div class="dashboard-card-value {cls}">{value}</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="dashboard-section">CLASS & ZONE PERFORMANCE</div>', unsafe_allow_html=True)
    strip = st.columns(8, gap="small")
    strip_data = [
        ("CLASS A", class_total(filtered, "A"), "red"), ("CLASS B", class_total(filtered, "B"), "orange"),
        ("CLASS C", class_total(filtered, "C"), "blue"), ("CLASS D", class_total(filtered, "D"), "green"),
        ("ZONE A", zone_total(filtered, "A"), "blue"), ("ZONE B", zone_total(filtered, "B"), "blue"),
        ("ZONE C", zone_total(filtered, "C"), "blue"), ("ZONE D", zone_total(filtered, "D"), "blue"),
    ]
    for col, (label, value, cls) in zip(strip, strip_data):
        with col:
            st.markdown(f'<div class="mini-kpi"><div class="mini-kpi-label">{label}</div><div class="mini-kpi-value {cls}">{value}</div></div>', unsafe_allow_html=True)

    overview_pareto = build_pareto_summary(filtered, defect_col)

    st.markdown('<div class="dashboard-section">DEFECT FOCUS</div>', unsafe_allow_html=True)
    left, right = st.columns([1.15, 1], gap="medium")
    with left:
        if overview_pareto is not None and not overview_pareto.empty:
            top3 = overview_pareto.head(3).copy()
            rows = []
            for rank, (_, row) in enumerate(top3.iterrows(), 1):
                qty = int(row[qty_col])
                total_qty = float(overview_pareto[qty_col].sum())
                pct = (qty / total_qty * 100) if total_qty else 0
                rows.append(f'<tr><td><span class="rank-badge">{rank}</span></td><td>{html.escape(str(row[defect_col]))}</td><td><b>{qty}</b></td><td>{pct:.1f}%</td></tr>')
            rows_html = ''.join(rows)
            st.markdown(f'<div class="dashboard-card"><div class="dashboard-card-title">TOP 3 DEFECT TYPES</div><table class="top-defect-table"><thead><tr><th>#</th><th>Defect</th><th>Qty</th><th>Share</th></tr></thead><tbody>{rows_html}</tbody></table></div>', unsafe_allow_html=True)
        else:
            st.info("No defect type data available for the selected filters.")

    with right:
        if overview_pareto is not None and not overview_pareto.empty and overview_pareto[qty_col].sum() > 0:
            mix = overview_pareto.copy()
            if len(mix) > 5:
                top = mix.head(5).copy()
                other_qty = mix.iloc[5:][qty_col].sum()
                other = pd.DataFrame({defect_col: ["Other"], qty_col: [other_qty]})
                mix = pd.concat([top, other], ignore_index=True)
            fig_mix = px.pie(mix, names=defect_col, values=qty_col, hole=0.42)
            fig_mix.update_layout(height=310, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="v"))
            fig_mix.update_traces(textposition="outside", textinfo="percent+value")
            st.plotly_chart(fig_mix, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("No defect mix available for the selected filters.")

    st.markdown('<div class="dashboard-section">PARETO & MODEL PERFORMANCE</div>', unsafe_allow_html=True)
    p1, p2 = st.columns([1.35, 1], gap="medium")
    with p1:
        if overview_pareto is not None and not overview_pareto.empty and overview_pareto[qty_col].sum() > 0:
            pareto_view = overview_pareto.copy()
            total_qty = pareto_view[qty_col].sum()
            pareto_view["Cumulative %"] = pareto_view[qty_col].cumsum() / total_qty * 100
            fig_p = go.Figure()
            fig_p.add_trace(go.Bar(x=pareto_view[defect_col], y=pareto_view[qty_col], name="Defect Qty", text=pareto_view[qty_col], textposition="outside", marker_color="#2563a8"))
            fig_p.add_trace(go.Scatter(x=pareto_view[defect_col], y=pareto_view["Cumulative %"], name="Cumulative %", mode="lines+markers", yaxis="y2", line=dict(color="#dc3b45", width=2.5)))
            fig_p.update_layout(height=360, margin=dict(l=25,r=60,t=20,b=90), xaxis=dict(tickangle=-35), yaxis=dict(title="Qty"), yaxis2=dict(title="Cumulative %", overlaying="y", side="right", range=[0,100], ticksuffix="%"), legend=dict(orientation="h", y=1.08))
            st.plotly_chart(fig_p, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("No Pareto data available.")
    with p2:
        if model_col:
            model_df = filtered.copy()
            if qty_col:
                model_df[qty_col] = pd.to_numeric(model_df[qty_col], errors="coerce").fillna(0)
                model_summary = model_df.groupby(model_col, as_index=False)[qty_col].sum().sort_values(qty_col, ascending=False)
                model_summary.columns = ["Model", "Total Defects"]
            else:
                model_summary = model_df.groupby(model_col).size().reset_index(name="Total Defects").sort_values("Total Defects", ascending=False)
                model_summary.columns = ["Model", "Total Defects"]
            model_summary["Model"] = model_summary["Model"].astype(str)
            fig_m = px.bar(model_summary.head(10), x="Model", y="Total Defects", text="Total Defects")
            fig_m.update_layout(height=360, margin=dict(l=20,r=20,t=20,b=55), xaxis_tickangle=-25)
            fig_m.update_traces(marker_color="#4b78a8", textposition="outside")
            st.plotly_chart(fig_m, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Model column not available.")

    st.markdown('<div class="dashboard-section">CLASS & ZONE DISTRIBUTION</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        class_df = pd.DataFrame({"Class": list("ABCD"), "Defects": [class_total(filtered, x) for x in "ABCD"]})
        fig_class_overview = px.bar(class_df, x="Class", y="Defects", text="Defects")
        fig_class_overview.update_layout(height=300, margin=dict(l=20,r=20,t=20,b=30))
        fig_class_overview.update_traces(marker_color="#4b78a8", textposition="outside")
        st.plotly_chart(fig_class_overview, use_container_width=True, config={"displayModeBar": False})
    with c2:
        zone_df = pd.DataFrame({"Zone": list("ABCD"), "Defects": [zone_total(filtered, x) for x in "ABCD"]})
        fig_zone_overview = px.bar(zone_df, x="Zone", y="Defects", text="Defects")
        fig_zone_overview.update_layout(height=300, margin=dict(l=20,r=20,t=20,b=30))
        fig_zone_overview.update_traces(marker_color="#64748b", textposition="outside")
        st.plotly_chart(fig_zone_overview, use_container_width=True, config={"displayModeBar": False})

    st.markdown('<div class="dashboard-section">CHASSIS-LEVEL DEFECT SUMMARY</div>', unsafe_allow_html=True)
    if chassis_col and not filtered.empty:
        chassis_view = filtered.copy()
        chassis_view[chassis_col] = chassis_view[chassis_col].astype(str)
        if defect_col:
            chassis_view[defect_col] = chassis_view[defect_col].astype(str)
        if qty_col:
            chassis_view[qty_col] = pd.to_numeric(chassis_view[qty_col], errors="coerce").fillna(0)
            chassis_summary = chassis_view.groupby(chassis_col, as_index=False)[qty_col].sum().sort_values(qty_col, ascending=False)
            chassis_summary.rename(columns={qty_col: "Total Defects"}, inplace=True)
        else:
            chassis_summary = chassis_view.groupby(chassis_col).size().reset_index(name="Total Defects").sort_values("Total Defects", ascending=False)
        if defect_col:
            defect_summary = chassis_view.groupby(chassis_col)[defect_col].apply(lambda s: ", ".join(pd.Series(s.dropna().astype(str).unique()).head(3))).reset_index(name="Top Defects")
            chassis_summary = chassis_summary.merge(defect_summary, on=chassis_col, how="left")
        st.dataframe(chassis_summary.head(15), use_container_width=True, height=300, hide_index=True)
    else:
        st.info("No chassis data available for the selected filters.")


# ============================================================
# KPI CARDS — DETAILED PAGES ONLY
# ============================================================
if page in ["⚠️ Total Defects"]:
    st.markdown('<div class="section-title">📌 Key Performance Indicators</div>', unsafe_allow_html=True)
    kpis_row1 = [
        ("🚗 VEHICLES AUDITED", vehicle_count(filtered)),
        ("⚠️ TOTAL DEFECTS", total_defects(filtered)),
        ("🔴 CLASS A", class_total(filtered, "A")),
        ("🟠 A+B", ab_total(filtered)),
    ]
    for col, (label, value) in zip(st.columns(4), kpis_row1):
        with col:
            st.markdown(f'<div class="kpi"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div></div>', unsafe_allow_html=True)
    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    for col, label, value in [
        (c1, "🟡 CLASS C", class_total(filtered, "C")),
        (c2, "🟢 CLASS D", class_total(filtered, "D")),
        (c3, "📊 DPU (Defects/Unit)", calculate_dpu(filtered)),
    ]:
        with col:
            st.markdown(f'<div class="kpi"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div></div>', unsafe_allow_html=True)

# ============================================================
# QUALITY DISTRIBUTION
# ============================================================
if page in ["⚠️ Total Defects", "🧩 Class & Zone"]:
    st.markdown('<div class="section-title">📊 Quality Distribution</div>', unsafe_allow_html=True)
    a, b = st.columns(2)
    with a:
        class_df = pd.DataFrame({"Class": list("ABCD"), "Defects": [class_total(filtered, x) for x in "ABCD"]})
        fig_class = px.bar(class_df, x="Class", y="Defects", text="Defects", title="Class-wise Defect Distribution")
        fig_class.update_layout(height=380, margin=dict(l=20, r=20, t=55, b=20))
        st.plotly_chart(fig_class, use_container_width=True)
    with b:
        zone_df = pd.DataFrame({"Zone": list("ABCD"), "Defects": [zone_total(filtered, x) for x in "ABCD"]})
        fig_zone = px.bar(zone_df, x="Zone", y="Defects", text="Defects", title="Zone-wise Defect Distribution")
        fig_zone.update_layout(height=380, margin=dict(l=20, r=20, t=55, b=20))
        st.plotly_chart(fig_zone, use_container_width=True)


# ============================================================
# PARETO ANALYSIS (DEFECT TYPE & DEFECT CATEGORY)
# ============================================================
pareto = build_pareto_summary(filtered, defect_col) if defect_col and qty_col else None
pareto_cat = build_pareto_summary(filtered, category_col) if category_col and qty_col else None

if page in ["📈 Pareto Analysis"]:
    st.markdown('<div class="section-title">📈 Defect Pareto Analysis & Action Focus</div>', unsafe_allow_html=True)
    
    # --- FIRST PARETO SECTION: DEFECT TYPE ---
    st.subheader("📊 Pareto Analysis by Defect Type")
    
    # Action focus box for Defect Type
    if pareto is not None and not pareto.empty and pareto[qty_col].sum() > 0:
        top_defect_row = pareto.iloc[0]
        top_defect_name = top_defect_row[defect_col]
        top_defect_qty = int(top_defect_row[qty_col])
        total_all_defects = pareto[qty_col].sum()
        top_defect_pct = round((top_defect_qty / total_all_defects) * 100, 1) if total_all_defects > 0 else 0
        
        st.markdown(
            f"""
            <div class="pareto-alert-box">
                <div class="pareto-alert-title">🚨 HIGHEST PRIORITY ACTION ITEM (DEFECT TYPE 80/20 FOCUS)</div>
                <div class="pareto-alert-main">Target Defect: {html.escape(str(top_defect_name))} ({top_defect_qty} Units / {top_defect_pct}%)</div>
                <div class="pareto-alert-desc">Immediate corrective action is recommended because this defect accounts for the largest share of total defects.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if pareto is not None and not pareto.empty and pareto[qty_col].sum() > 0:
        total = pareto[qty_col].sum()
        pareto["Cumulative %"] = pareto[qty_col].cumsum() / total * 100
        fig_pareto = go.Figure()
        fig_pareto.add_trace(go.Bar(x=pareto[defect_col], y=pareto[qty_col], name="Defect Quantity", text=pareto[qty_col], textposition="outside", marker_color="#2563eb"))
        fig_pareto.add_trace(go.Scatter(x=pareto[defect_col], y=pareto["Cumulative %"], name="Cumulative %", mode="lines+markers", yaxis="y2", line=dict(color="#dc2626", width=2.5)))
        if len(pareto) >= 2:
            fig_pareto.add_trace(go.Scatter(x=[pareto[defect_col].iloc[0], pareto[defect_col].iloc[-1]], y=[80, 80], name="80% Target", mode="lines", line=dict(dash="dash", color="#16a34a"), yaxis="y2"))
        fig_pareto.update_layout(title="Pareto Analysis by Defect Type", height=500, xaxis=dict(tickangle=-45), yaxis=dict(title="Quantity"), yaxis2=dict(title="Cumulative %", overlaying="y", side="right", range=[0, 100], ticksuffix="%"), margin=dict(l=40, r=70, t=65, b=140))
        st.plotly_chart(fig_pareto, use_container_width=True)
    else:
        st.info("No Defect Type Pareto data available for current filters.")

    st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)

    # --- SECOND PARETO SECTION: DEFECT CATEGORY ---
    st.subheader("📈 Dedicated Pareto Analysis by Defect Category")
    st.markdown("Identifies the vital categories driving the majority of defect occurrences.")
    
    # Action focus box for Defect Category
    if pareto_cat is not None and not pareto_cat.empty and pareto_cat[qty_col].sum() > 0:
        top_cat_row = pareto_cat.iloc[0]
        top_cat_name = top_cat_row[category_col]
        top_cat_qty = int(top_cat_row[qty_col])
        total_all_cats = pareto_cat[qty_col].sum()
        top_cat_pct = round((top_cat_qty / total_all_cats) * 100, 1) if total_all_cats > 0 else 0
        
        st.markdown(
            f"""
            <div class="pareto-alert-box">
                <div class="pareto-alert-title">🚨 HIGHEST PRIORITY ACTION ITEM (DEFECT CATEGORY 80/20 FOCUS)</div>
                <div class="pareto-alert-main">Target Category: {html.escape(str(top_cat_name))} ({top_cat_qty} Units / {top_cat_pct}%)</div>
                <div class="pareto-alert-desc">Prioritize this category because it accounts for the largest share of defects.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if pareto_cat is not None and not pareto_cat.empty and pareto_cat[qty_col].sum() > 0:
        total_cat = pareto_cat[qty_col].sum()
        pareto_cat["Cumulative %"] = pareto_cat[qty_col].cumsum() / total_cat * 100
        
        # Table removed completely as requested, showing chart full width nicely
        fig_pareto_cat = go.Figure()
        fig_pareto_cat.add_trace(go.Bar(x=pareto_cat[category_col], y=pareto_cat[qty_col], name="Category Quantity", text=pareto_cat[qty_col], textposition="outside", marker_color="#0ea5e9"))
        fig_pareto_cat.add_trace(go.Scatter(x=pareto_cat[category_col], y=pareto_cat["Cumulative %"], name="Cumulative %", mode="lines+markers", yaxis="y2", line=dict(color="#ea580c", width=2.5)))
        if len(pareto_cat) >= 2:
            fig_pareto_cat.add_trace(go.Scatter(x=[pareto_cat[category_col].iloc[0], pareto_cat[category_col].iloc[-1]], y=[80, 80], name="80% Target", mode="lines", line=dict(dash="dash", color="#16a34a"), yaxis="y2"))
        fig_pareto_cat.update_layout(title="Pareto Trend by Defect Category", height=500, xaxis=dict(tickangle=-30), yaxis=dict(title="Quantity"), yaxis2=dict(title="Cumulative %", overlaying="y", side="right", range=[0, 100], ticksuffix="%"), margin=dict(l=40, r=70, t=65, b=120))
        st.plotly_chart(fig_pareto_cat, use_container_width=True)
    else:
        st.info("No Defect Category column found or no data available for category Pareto.")


# ============================================================
# AI ASSISTANT
# ============================================================
if page in ["🎙️ AI Assistant"]:
    st.markdown(
        """
        <div class="voice-card">
            <div class="voice-title">🎙️ AI Voice & Text Assistant (Gemini Powered)</div>
            <div class="voice-subtitle">Type your question and press Enter, or click the microphone button inside the search bar.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-title">💬 Ask Audit Assistant</div>', unsafe_allow_html=True)
    
    col_txt, col_mic = st.columns([12, 1])
    with col_txt:
        text_question = st.text_input("POWERED BY FQCM", placeholder="POWERED BY FQCM", label_visibility="collapsed")
    with col_mic:
        audio_data = mic_recorder(
            start_prompt="🎙️",
            stop_prompt="⏹️",
            just_once=True,
            key="audit_mic"
        )

    components.html("""
    <script>
    const doc = window.parent.document;
    function setupEnterKey() {
        const inputs = doc.querySelectorAll('input[aria-label="POWERED BY FQCM"]');
        inputs.forEach(input => {
            if (!input.dataset.enterBound) {
                input.dataset.enterBound = "true";
                input.addEventListener('keydown', function(e) {
                    if (e.key === 'Enter') {
                        e.preventDefault();
                        input.dispatchEvent(new Event('input', { bubbles: true }));
                        input.dispatchEvent(new Event('change', { bubbles: true }));
                        
                        setTimeout(() => {
                            const allBtns = doc.querySelectorAll('button');
                            for (let b of allBtns) {
                                if (b.textContent.includes("Send Query")) {
                                    b.click();
                                    break;
                                }
                            }
                        }, 100);
                    }
                });
            }
        });
    }
    const observer = new MutationObserver(setupEnterKey);
    observer.observe(doc.body, { childList: true, subtree: true });
    setupEnterKey();
    </script>
    """, height=0)
    
    ask_clicked = st.button("Send Query →", type="primary", use_container_width=True)

    if audio_data and "bytes" in audio_data:
        with st.spinner("🎙️ Processing voice recording with Gemini..."):
            answer = ai_answer_audio(audio_data["bytes"], filtered)
        st.markdown(f'<div class="answer-card"><div class="answer-label">AI VOICE RESPONSE</div><div class="answer-text">{html.escape(answer)}</div></div>', unsafe_allow_html=True)
        speak(answer)

    if text_question.strip() and (ask_clicked or "last_q" not in st.session_state or st.session_state.last_q != text_question):
        st.session_state.last_q = text_question
        with st.spinner("🤖 Analysing audit data with Gemini..."):
            answer = ai_answer(text_question, filtered)
        st.markdown(f'<div class="answer-card"><div class="answer-label">AI RESPONSE</div><div class="answer-text">{html.escape(answer)}</div></div>', unsafe_allow_html=True)
        speak(answer)


# ============================================================
# AUDIT RECORDS
# ============================================================
if page in ["🚗 Vehicle Audit", "📋 Audit Data"]:
    st.markdown('<div class="section-title">📋 Audit Records</div>', unsafe_allow_html=True)
    st.caption(f"Showing {len(filtered)} records from {SHEET_NAME}")
    st.dataframe(filtered, use_container_width=True, height=430 if page != "🏠 Overview" else 300)


# ============================================================
# PROFESSIONAL CORPORATE FOOTER (SAFE RENDER)
# ============================================================
components.html("""
<style>
.footer-container {
    background-color: #1a1a1a;
    color: #a3a3a3;
    padding: 24px 28px;
    border-radius: 14px;
    overflow: hidden;
    margin-top: 10px;
    margin-bottom: 10px;
    font-family: -apple-system, BlinkMacSystemFont, sans-serif;
    border-top: 4px solid #ff1a40;
}
.footer-grid {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    gap: 20px;
    border-bottom: 1px solid #333333;
    padding-bottom: 16px;
}
.footer-col {
    flex: 1;
    min-width: 150px;
}
.footer-col-brand {
    flex: 1.2;
    min-width: 220px;
}
.footer-brand-title {
    color: #ffffff;
    font-size: 14px;
    font-weight: 900;
    letter-spacing: 1px;
    margin-bottom: 6px;
}
.footer-heading {
    color: #ffffff;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 1.2px;
    margin-bottom: 8px;
    text-transform: uppercase;
}
.footer-text {
    font-size: 10.5px;
    line-height: 1.4;
    color: #9ca3af;
    margin-bottom: 4px;
}
.footer-links {
    list-style: none;
    padding: 0;
    margin: 0;
}
.footer-links li {
    margin-bottom: 4px;
}
.footer-links a {
    color: #9ca3af;
    text-decoration: none;
    font-size: 10.5px;
}
.footer-links a:hover {
    color: #ffffff;
}
.footer-bottom {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 12px;
    font-size: 9.5px;
    color: #6b7280;
    flex-wrap: wrap;
    gap: 10px;
}
</style>

<div class="footer-container">
    <div class="footer-grid">
        <div class="footer-col-brand">
            <div class="footer-brand-title">MASTER MOTORS • FUSO QFL4</div>
            <div class="footer-text">Final Quality Control Management & Assembly Plant Intelligence.</div>
            <div class="footer-text" style="margin-top: 6px;"><b>Plant Location:</b> Port Qasim Authority, Karachi</div>
            <div class="footer-text"><b>Dept:</b> Quality Assurance, Health, Safety & Environment</div>
        </div>
        
        <div class="footer-col">
            <div class="footer-heading">COMMERCIAL VEHICLES</div>
            <ul class="footer-links">
                <li><a href="#">FUSO Canter Light Duty</a></li>
                <li><a href="#">FUSO Heavy Trucks</a></li>
                <li><a href="#">Master Bus Series</a></li>
                <li><a href="#">Specialized Chassis</a></li>
            </ul>
        </div>
        
        <div class="footer-col">
            <div class="footer-heading">QUALITY STANDARDS</div>
            <ul class="footer-links">
                <li><a href="#">QFL4 Inspection Protocol</a></li>
                <li><a href="#">MFTBC Product Audit</a></li>
                <li><a href="#">Defect Class (A, B, C, D)</a></li>
                <li><a href="#">DPU Performance Benchmarks</a></li>
            </ul>
        </div>
        
        <div class="footer-col">
            <div class="footer-heading">SYSTEM &SUPPORT</div>
            <ul class="footer-links">
                <li><a href="#">Gemini AI Assistant</a></li>
                <li><a href="#">Pareto Defect Analytics</a></li>
                <li><a href="#">Audit Records Dashboard</a></li>
                <li><a href="#">User Access Controls</a></li>
            </ul>
        </div>
    </div>
    
    <div class="footer-bottom">
        <div>© 2026 Master Motor Corporation Ltd. All Rights Reserved.</div>
        <div>Powered by Google Gemini AI & Streamlit | QFL4 Portal</div>
    </div>
</div>
""", height=350)
