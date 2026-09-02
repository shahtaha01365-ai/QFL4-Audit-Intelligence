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

# Gemini AI Model
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
# STYLING
# ============================================================
st.markdown(
    """
<style>
#MainMenu, footer{visibility:hidden}
.stApp{background:#eef1f5}
.block-container{max-width:1500px;padding:24px 32px 50px}

/* Hide Streamlit Cloud Floating Manage App / Status Widget */
[data-testid="stStatusWidget"] {
    display: none !important;
}

[data-testid="stSidebar"]{
    background:#fff!important;
    border-right:1px solid #dce3ea
}

/* === LOGIN & SIGNUP TEXT BOX BORDER FIX === */
.stTextInput input {
    background-color: #ffffff !important;
    border: 1.5px solid #cbd5e1 !important;
    border-radius: 8px !important;
    padding: 10px 14px !important;
    color: #243447 !important;
}
.stTextInput input:focus {
    border-color: #2563eb !important;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15) !important;
}

.nav-brand{
    padding:8px 8px 18px;
    border-bottom:1px solid #edf1f5;
    margin-bottom:10px
}
.nav-brand-top{
    color:#1d5fa7;
    font-size:10px;
    font-weight:900;
    letter-spacing:1.8px
}
.nav-brand-title{
    color:#243447;
    font-size:21px;
    font-weight:900;
    margin-top:5px
}
.nav-caption{
    color:#94a3b8;
    font-size:11px;
    margin-top:3px
}
.nav-section{
    color:#94a3b8;
    font-size:10px;
    font-weight:900;
    letter-spacing:1.2px;
    padding:13px 8px 6px
}
.sidebar-note{
    color:#94a3b8;
    font-size:11px;
    padding:8px
}

.page-title{
    font-size:30px;
    font-weight:900;
    color:#243447;
    margin-bottom:2px
}
.page-desc{
    font-size:13px;
    color:#718096;
    margin-bottom:20px
}

.main-title{
    font-size:36px;
    font-weight:900;
    color:#243447;
    margin-top:10px
}
.main-subtitle{
    color:#64748b;
    font-size:15px;
    margin-top:6px
}
.online-badge{
    display:inline-block;
    margin-top:12px;
    padding:6px 14px;
    border-radius:20px;
    background:#edf8f1;
    color:#15803d;
    border:1px solid #ccebd7;
    font-size:10px;
    font-weight:900
}

.section-title{
    font-size:20px;
    font-weight:900;
    color:#243447;
    margin:24px 0 12px
}

.kpi{
    background:#fff;
    border:1px solid #e0e6ec;
    border-radius:14px;
    padding:18px;
    min-height:105px;
    box-shadow:0 5px 16px rgba(15,23,42,.04)
}
.kpi-label{
    font-size:11px;
    color:#718096;
    font-weight:800
}
.kpi-value{
    font-size:30px;
    color:#243447;
    font-weight:900;
    margin-top:7px
}

.kpi-dpu{
    background:linear-gradient(135deg, #fff5f5, #fed7d7);
    border:1px solid #feb2b2;
    border-radius:14px;
    padding:18px;
    min-height:105px;
    box-shadow:0 6px 18px rgba(220, 38, 38, 0.08)
}
.kpi-dpu .kpi-label{
    font-size:11px;
    color:#9b2c2c;
    font-weight:800;
    letter-spacing:0.5px
}
.kpi-dpu .kpi-value{
    font-size:34px;
    color:#dc2626;
    font-weight:900;
    margin-top:7px
}

.voice-card{
    padding:25px;
    border-radius:16px;
    background:linear-gradient(135deg,#f8fbff,#e7f0fb);
    border:1px solid #d8e4f2;
    margin:20px 0;
    box-shadow:0 7px 22px rgba(37,99,235,.06)
}
.voice-title{
    font-size:25px;
    font-weight:900;
    color:#243447
}
.voice-subtitle{
    font-size:13px;
    color:#64748b;
    margin-top:5px
}

div[data-testid="stHorizontalBlock"]:has(input[aria-label="Ask anything"]) {
    background: #ffffff;
    border: 2px solid #ff4b4b !important;
    border-radius: 14px;
    padding: 4px 12px;
    box-shadow: 0 4px 20px rgba(255, 75, 75, 0.1);
    align-items: center;
}
div[data-testid="stHorizontalBlock"]:has(input[aria-label="Ask anything"]) [data-baseweb="input"] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}
div[data-testid="stHorizontalBlock"]:has(input[aria-label="Ask anything"]) fieldset {
    border: none !important;
}

.answer-card{
    background:#fff;
    border:1px solid #dce5ef;
    border-left:4px solid #ff1a40;
    border-radius:12px;
    padding:17px 20px;
    margin-top:12px
}
.answer-label{
    font-size:10px;
    color:#ff1a40;
    font-weight:900;
    letter-spacing:1.4px
}
.answer-text{
    font-size:18px;
    color:#243447;
    font-weight:650;
    margin-top:6px;
    line-height:1.5
}

.login-box{
    max-width:440px;
    margin:10px auto 10px;
    background:#fff;
    padding:28px 32px;
    border-radius:20px;
    border:1px solid #e1e7ed;
    box-shadow:0 18px 50px rgba(15,23,42,.08);
    text-align:center
}
.login-title{
    color:#243447;
    font-size:26px;
    font-weight:900;
    margin-top:5px
}
.login-subtitle{
    color:#64748b;
    font-size:13px;
    margin-bottom:10px
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


def login():
    # Perfectly scaled SVG with correct viewBox (0 0 500 170) and height=170 to avoid any clipping
    components.html("""
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 170" width="100%" height="100%">
      <defs>
        <linearGradient id="cardBg" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#0f172a" />
          <stop offset="100%" stop-color="#1e293b" />
        </linearGradient>
        <linearGradient id="masterRedGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#ff1a40" />
          <stop offset="100%" stop-color="#cc0029" />
        </linearGradient>
        <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
          <feGaussianBlur stdDeviation="3" result="blur" />
          <feComposite in="SourceGraphic" in2="blur" operator="over" />
        </filter>
      </defs>
      <rect width="500" height="162" rx="16" fill="url(#cardBg)" stroke="#334155" stroke-width="1.5"/>
      <g transform="translate(24, 38)">
        <polygon points="42,2 78,22 78,62 42,82 6,62 6,22" fill="#1e293b" stroke="url(#masterRedGrad)" stroke-width="2.5" filter="url(#glow)"/>
        <circle cx="42" cy="42" r="16" fill="#0f172a" stroke="#ff1a40" stroke-width="1.5" stroke-dasharray="3 2"/>
        <path d="M32 43 L39 50 L53 33" fill="none" stroke="#22c55e" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round"/>
      </g>
      <g transform="translate(125, 48)">
        <text x="0" y="10" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="10.5" font-weight="800" fill="#ff1a40" letter-spacing="2.5">MASTER MOTORS • FUSO</text>
        <text x="0" y="42" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="26" font-weight="900" fill="#ffffff" letter-spacing="0.8">QFL4 <tspan fill="#ff1a40">AI</tspan></text>
        <text x="0" y="65" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="9.5" font-weight="600" fill="#94a3b8" letter-spacing="1.2">AUTOMOTIVE QUALITY &amp; AUDIT INTELLIGENCE</text>
      </g>
      <g transform="translate(410, 41)">
        <rect width="66" height="80" rx="10" fill="#1e293b" stroke="#475569" stroke-width="1"/>
        <text x="33" y="38" text-anchor="middle" font-family="sans-serif" font-size="15" font-weight="900" fill="#ff1a40" letter-spacing="1">FQCM</text>
        <text x="33" y="60" text-anchor="middle" font-family="sans-serif" font-size="8" font-weight="700" fill="#22c55e" letter-spacing="0.5">ACTIVE</text>
      </g>
    </svg>
    """, height=170)

    users = load_users()

    if not st.session_state.show_signup:
        st.markdown(
            """
            <div class="login-box">
                <div class="login-title">Welcome Back</div>
                <div class="login-subtitle">Sign in to access Audit Intelligence</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        with st.form("login_form"):
            e = st.text_input("Email", placeholder="name@master.com.pk")
            p = st.text_input("Password", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("LOGIN", use_container_width=True)

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

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("<p style='text-align:center; font-size:13px; color:#718096; margin-top:8px;'>Don't have an account?</p>", unsafe_allow_html=True)
            if st.button("Create Account", use_container_width=True):
                st.session_state.show_signup = True
                st.rerun()

    else:
        st.markdown(
            """
            <div class="login-box">
                <div class="login-title">Create QFL4 Account</div>
                <div class="login-subtitle">Register for audit portal access</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("signup_form"):
            full_name = st.text_input("Full Name", placeholder="Taha Shahid")
            new_e = st.text_input("Email", placeholder="name@master.com.pk").strip().lower()
            new_p = st.text_input("Password", type="password", placeholder="••••••••")
            confirm_p = st.text_input("Confirm Password", type="password", placeholder="••••••••")
            
            signup_submitted = st.form_submit_button("CREATE ACCOUNT", use_container_width=True)

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

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("<p style='text-align:center; font-size:13px; color:#718096; margin-top:8px;'>Already have an account?</p>", unsafe_allow_html=True)
            if st.button("Login", use_container_width=True):
                st.session_state.show_signup = False
                st.rerun()


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
    c = find_col(d, ["Total", "Total Defects", "Defect Quantity", "Defects"])
    if c:
        return nsum(d, c)
    s = sum(class_total(d, x) for x in "ABCD")
    if s:
        return s
    return nsum(d, find_col(d, ["QTY", "Quantity", "Defect Qty", "Defect Quantity"]))


def calculate_dpu(d):
    v_count = vehicle_count(d)
    if v_count == 0:
        return 0.0
    tot_def = total_defects(d)
    return round(tot_def / v_count, 2)


@st.cache_data(ttl=30)
def load_excel():
    d = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME)
    d.columns = d.columns.astype(str).str.strip().str.replace("\n", " ", regex=False).str.replace(r"\s+", " ", regex=True)
    date_col = next((x for x in d.columns if str(x).strip().lower() == "date"), None)
    if date_col:
        d[date_col] = pd.to_datetime(d[date_col], errors="coerce")
    return d


def page_title(title, description):
    st.markdown(
        f"""
        <div class="page-title">{html.escape(title)}</div>
        <div class="page-desc">{html.escape(description)}</div>
        """,
        unsafe_allow_html=True,
    )


def make_ai_context(d):
    sample = d.tail(15).copy()
    for c in sample.columns:
        if pd.api.types.is_datetime64_any_dtype(sample[c]):
            sample[c] = sample[c].dt.strftime("%Y-%m-%d")
    return sample.to_string(index=False)


def ai_answer(q, d):
    if not init_gemini():
        return "Gemini API key is not configured. Please add GEMINI_API_KEY to Streamlit Secrets."

    context = make_ai_context(d)
    current_date_str = datetime.now().strftime("%Y-%m-%d")
    
    prompt = f"""
You are the QFL4 Vehicle Audit Intelligence Assistant for Master Motors FUSO.
CURRENT SYSTEM DATE: {current_date_str}

STRICT DATA RULES:
1. Use ONLY the audit data supplied below to answer questions about vehicles, dates, chassis, classes (A, B, C, D), zones, DPU, and defect quantities.
2. Never invent, estimate, assume, or fabricate a number or vehicle detail.
3. RELATIVE TIME AWARENESS: Use the CURRENT SYSTEM DATE above to evaluate relative time queries like "last week", "yesterday", or "today". If there are NO audit records matching that specific time frame in the provided data, you must explicitly state that no vehicles were audited during that period.
4. Respect active dashboard filters.
5. LANGUAGE MATCHING RULE: Detect the language of the user's question (English, Urdu, or Roman Urdu). You MUST reply in the EXACT SAME language and script/style that the user used.
6. Keep answers concise, accurate, and fast.

ACTIVE FILTERED AUDIT DATA:
Columns: {", ".join(map(str, d.columns))}
Rows: {context}

USER QUESTION: {q}
"""
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
    
    prompt = f"""
You are the QFL4 Vehicle Audit Intelligence Assistant for Master Motors FUSO.
CURRENT SYSTEM DATE: {current_date
