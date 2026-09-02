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
LOGO_FILE = "qfl4_logos_header.png"
SHEET_NAME = "Sheet1"
USERS_FILE = "users.json"

# Gemini AI Model (Updated to gemini-2.5-flash)
AI_MODEL = "gemini-2.5-flash"

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

[data-testid="stSidebar"]{
    background:#fff!important;
    border-right:1px solid #dce3ea
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

.logo-area{
    background:#fff;
    border:1px solid #e1e7ed;
    border-radius:18px;
    padding:22px 28px;
    text-align:center;
    box-shadow:0 7px 22px rgba(15,23,42,.05);
    margin-bottom:20px
}
.logo-area img {
    max-width: 100%;
    height: auto;
    object-fit: contain;
    max-height: 60px;
    margin-top: 10px;
}
.brand-title{
    font-size:24px;
    font-weight:900;
    letter-spacing:1.5px;
    color:#1d5fa7;
    margin-bottom:2px;
}
.brand-tagline{
    font-size:13px;
    font-weight:600;
    letter-spacing:0.8px;
    color:#64748b;
    margin-bottom:16px;
    font-style:italic;
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

.chat-input-container {
    background: #ffffff;
    border: 2px solid #cbd5e1;
    border-radius: 35px;
    padding: 2px 12px;
    box-shadow: 0 4px 20px rgba(15, 23, 42, 0.06);
    margin-top: 15px;
}
.chat-input-container [data-baseweb="input"] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}

.answer-card{
    background:#fff;
    border:1px solid #dce5ef;
    border-left:4px solid #2563eb;
    border-radius:12px;
    padding:17px 20px;
    margin-top:12px
}
.answer-label{
    font-size:10px;
    color:#2563eb;
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
    margin:50px auto 10px;
    background:#fff;
    padding:32px;
    border-radius:20px;
    border:1px solid #e1e7ed;
    box-shadow:0 18px 50px rgba(15,23,42,.08);
    text-align:center
}
.login-logo{
    color:#2563eb;
    font-size:12px;
    font-weight:900;
    letter-spacing:2px
}
.login-title{
    color:#243447;
    font-size:28px;
    font-weight:900;
    margin-top:5px
}
.login-subtitle{
    color:#64748b;
    font-size:13px;
    margin-bottom:10px
}

.status-ok{
    display:inline-block;
    padding:5px 10px;
    border-radius:14px;
    background:#edf8f1;
    color:#15803d;
    border:1px solid #ccebd7;
    font-size:10px;
    font-weight:900
}
.status-warn{
    display:inline-block;
    padding:5px 10px;
    border-radius:14px;
    background:#fff7ed;
    color:#c2410c;
    border:1px solid #fed7aa;
    font-size:10px;
    font-weight:900
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
    users = load_users()

    if not st.session_state.show_signup:
        st.markdown(
            """
            <div class="login-box">
                <div class="login-logo">MASTER MOTOR • QFL4</div>
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
                <div class="login-logo">MASTER MOTOR • QFL4</div>
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
    sample = d.tail(40).copy()
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
3. RELATIVE TIME AWARENESS: Use the CURRENT SYSTEM DATE above to evaluate relative time queries like "last week", "yesterday", or "today". If there are NO audit records matching that specific time frame in the provided data, you must explicitly state that no vehicles were audited during that period. Do not substitute older data as "last week".
4. Respect active dashboard filters.
5. LANGUAGE MATCHING RULE: Detect the language of the user's question (English, Urdu, or Roman Urdu). You MUST reply in the EXACT SAME language and script/style that the user used.
6. Keep answers accurate, practical, and clear.

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
CURRENT SYSTEM DATE: {current_date_str}

STRICT DATA RULES:
1. Listen to the user's voice question and use ONLY the audit data supplied below to answer questions about vehicles, dates, chassis, classes, zones, DPU, and defect quantities.
2. Never invent, estimate, assume, or fabricate a number or vehicle detail.
3. RELATIVE TIME AWARENESS: Use the CURRENT SYSTEM DATE above to evaluate relative time queries like "last week", "yesterday", or "today". If no records match, state that no vehicles were audited during that period.
4. LANGUAGE MATCHING RULE: Detect the language of the user's question (English, Urdu, or Roman Urdu) and reply in the EXACT SAME language.
5. Keep answers accurate, practical, and clear.

ACTIVE FILTERED AUDIT DATA:
Columns: {", ".join(map(str, d.columns))}
Rows: {context}
"""
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
if not os.path.exists(EXCEL_FILE):
    st.error(f"{EXCEL_FILE} not found. Upload it beside your app file.")
    st.stop()


# ============================================================
# LOAD DATA
# ============================================================
try:
    df = load_excel()
except Exception as exc:
    st.error(f"Could not read {EXCEL_FILE}: {exc}")
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
        "🏠 Overview",
        "🎙️ AI Assistant",
        "⚠️ Total Defects",
        "📈 Pareto Analysis",
        "🚗 Vehicle Audit",
        "🧩 Class & Zone",
        "📋 Audit Data",
    ]

    if st.session_state.role == "admin":
        nav_pages.append("👥 Manage Users")

    page = st.radio("Pages", nav_pages, label_visibility="collapsed")

    st.markdown('<div class="nav-section">SYSTEM</div>', unsafe_allow_html=True)
    ai_ready = bool(st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", "")))
    ai_status = '<span class="status-ok">● GEMINI AI READY</span>' if ai_ready else '<span class="status-warn">● GEMINI KEY REQUIRED</span>'

    st.markdown(
        f"""
        <div class="sidebar-note">
            User: {html.escape(st.session_state.get('user_email', ''))}<br>
            Role: {html.escape(st.session_state.get('role', 'user').upper())}<br>
            Source: {html.escape(EXCEL_FILE)}<br>
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
# ADMIN PAGE: MANAGE USERS
# ============================================================
if page == "👥 Manage Users" and st.session_state.role == "admin":
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
# PAGE HEADER
# ============================================================
if page == "🏠 Overview":
    st.markdown(
        """
        <div class="logo-area">
            <div class="brand-title">FUSO MASTER MOTOR QFL4 AUDIT INTELLIGENCE</div>
            <div class="brand-tagline">A Vision of Mr. Ather Ali Darbari</div>
        """,
        unsafe_allow_html=True,
    )
    if os.path.exists(LOGO_FILE):
        st.image(LOGO_FILE)
    else:
        st.warning(f"{LOGO_FILE} not found.")

    st.markdown(
        """
        <div class="main-title">AI AUDIT INTELLIGENCE</div>
        <div class="main-subtitle">Smart Vehicle Quality & Audit Analytics</div>
        <div class="online-badge">● SYSTEM ONLINE</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    titles = {
        "🎙️ AI Assistant": ("AI Voice Assistant", "Ask audit questions in English, Urdu, or Roman Urdu via voice or text."),
        "⚠️ Total Defects": ("Total Defects", "Defect performance and class distribution."),
        "📈 Pareto Analysis": ("Pareto Analysis", "Identify the highest-impact defect types."),
        "🚗 Vehicle Audit": ("Vehicle Audit", "Vehicle and chassis-level audit information."),
        "🧩 Class & Zone": ("Class & Zone Analysis", "Compare quality classes and audit zones."),
        "📋 Audit Data": ("Audit Data", "Connected Excel records used by the analytics engine."),
    }
    if page in titles:
        title, description = titles[page]
        page_title(title, description)


# ============================================================
# SHARED FILTERS
# ============================================================
st.markdown('<div class="section-title">🔎 Audit Filters</div>', unsafe_allow_html=True)

date_col = find_col(df, ["Date"])
vehicle_col = find_col(df, ["Vehicle", "Vehicle No", "Vehicle Name"])
model_col = find_col(df, ["Model", "Model Name"])
chassis_col = find_col(df, ["Chassis No", "Chassis", "Chassis Number"])

f1, f2, f3, f4 = st.columns(4)

with f1:
    dates = sorted(df[date_col].dropna().dt.date.unique().tolist()) if date_col else []
    selected_dates = st.multiselect("📅 Date", dates)

with f2:
    vehicle_options = sorted(df[vehicle_col].dropna().astype(str).unique().tolist()) if vehicle_col else []
    selected_vehicle = st.selectbox("🚗 Vehicle", ["All"] + vehicle_options)

with f3:
    model_options = sorted(df[model_col].dropna().astype(str).unique().tolist()) if model_col else []
    selected_model = st.selectbox("🏷️ Model", ["All"] + model_options)

with f4:
    chassis_options = sorted(df[chassis_col].dropna().astype(str).unique().tolist()) if chassis_col else []
    selected_chassis = st.selectbox("🔢 Chassis No.", ["All"] + chassis_options)

filtered = df.copy()
if selected_dates and date_col:
    filtered = filtered[filtered[date_col].dt.date.isin(selected_dates)]
if selected_vehicle != "All" and vehicle_col:
    filtered = filtered[filtered[vehicle_col].astype(str) == selected_vehicle]
if selected_model != "All" and model_col:
    filtered = filtered[filtered[model_col].astype(str) == selected_model]
if selected_chassis != "All" and chassis_col:
    filtered = filtered[filtered[chassis_col].astype(str) == selected_chassis]


# ============================================================
# KPI CARDS
# ============================================================
if page in ["🏠 Overview", "⚠️ Total Defects"]:
    st.markdown('<div class="section-title">📌 Key Performance Indicators</div>', unsafe_allow_html=True)
    
    kpis_row1 = [
        ("🚗 VEHICLES AUDITED", vehicle_count(filtered)),
        ("⚠️ TOTAL DEFECTS", total_defects(filtered)),
        ("🔴 CLASS A", class_total(filtered, "A")),
        ("🟠 A+B", ab_total(filtered)),
    ]
    for col, (label, value) in zip(st.columns(4), kpis_row1):
        with col:
            st.markdown(
                f"""
                <div class="kpi">
                    <div class="kpi-label">{label}</div>
                    <div class="kpi-value">{value}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f"""
            <div class="kpi">
                <div class="kpi-label">🟡 CLASS C</div>
                <div class="kpi-value">{class_total(filtered, "C")}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""
            <div class="kpi">
                <div class="kpi-label">🟢 CLASS D</div>
                <div class="kpi-value">{class_total(filtered, "D")}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"""
            <div class="kpi-dpu">
                <div class="kpi-label">📊 DPU (Defects/Unit)</div>
                <div class="kpi-value">{calculate_dpu(filtered)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c4:
        pass


# ============================================================
# QUALITY DISTRIBUTION
# ============================================================
if page in ["🏠 Overview", "⚠️ Total Defects", "🧩 Class & Zone"]:
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
# PARETO ANALYSIS
# ============================================================
defect_col = find_col(filtered, ["Defect Type", "Defect", "Defect Name", "Defect Description", "Problem"])
qty_col = find_col(filtered, ["QTY", "Quantity", "Defect Qty", "Defect Quantity", "Qty"])
pareto = None

if defect_col and qty_col:
    pareto = filtered[[defect_col, qty_col]].copy()
    pareto[defect_col] = pareto[defect_col].astype(str).str.strip()
    pareto[qty_col] = pd.to_numeric(pareto[qty_col], errors="coerce").fillna(0)
    pareto = pareto[~pareto[defect_col].isin(["", "nan", "None", "NaN"])]
    pareto = pareto.groupby(defect_col, as_index=False)[qty_col].sum().sort_values(qty_col, ascending=False).reset_index(drop=True)

if page in ["🏠 Overview", "📈 Pareto Analysis"]:
    st.markdown('<div class="section-title">📈 Defect Pareto Analysis</div>', unsafe_allow_html=True)
    if pareto is not None and not pareto.empty and pareto[qty_col].sum() > 0:
        total = pareto[qty_col].sum()
        pareto["Cumulative %"] = pareto[qty_col].cumsum() / total * 100
        fig_pareto = go.Figure()
        fig_pareto.add_trace(go.Bar(x=pareto[defect_col], y=pareto[qty_col], name="Defect Quantity", text=pareto[qty_col], textposition="outside"))
        fig_pareto.add_trace(go.Scatter(x=pareto[defect_col], y=pareto["Cumulative %"], name="Cumulative %", mode="lines+markers", yaxis="y2"))
        if len(pareto) >= 2:
            fig_pareto.add_trace(go.Scatter(x=[pareto[defect_col].iloc[0], pareto[defect_col].iloc[-1]], y=[80, 80], name="80% Target", mode="lines", line=dict(dash="dash"), yaxis="y2"))
        fig_pareto.update_layout(title="Defect Quantity Pareto", height=520, xaxis=dict(tickangle=-45), yaxis=dict(title="Quantity"), yaxis2=dict(title="Cumulative %", overlaying="y", side="right", range=[0, 100], ticksuffix="%"), margin=dict(l=40, r=70, t=65, b=140))
        st.plotly_chart(fig_pareto, use_container_width=True)
    else:
        st.info("No Pareto data available for the current filters.")


# ============================================================
# AI ASSISTANT
# ============================================================
if page in ["🏠 Overview", "🎙️ AI Assistant"]:
    st.markdown(
        """
        <div class="voice-card">
            <div class="voice-title">🎙️ AI Voice & Text Assistant (Gemini Powered)</div>
            <div class="voice-subtitle">Type your question and press Enter, or click the microphone button inside the bar below.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-title">💬 Ask Audit Assistant</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="chat-input-container">', unsafe_allow_html=True)
    col_txt, col_mic = st.columns([11, 1])
    with col_txt:
        text_question = st.text_input("Ask anything", placeholder="Ask anything...", label_visibility="collapsed")
    with col_mic:
        audio_data = mic_recorder(
            start_prompt="🎙️",
            stop_prompt="⏹️",
            just_once=True,
            key="audit_mic"
        )
    st.markdown('</div>', unsafe_allow_html=True)

    components.html("""
    <script>
    const doc = window.parent.document;
    function setupEnterKey() {
        const inputs = doc.querySelectorAll('input[aria-label="Ask anything"]');
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
if page in ["🏠 Overview", "🚗 Vehicle Audit", "📋 Audit Data"]:
    st.markdown('<div class="section-title">📋 Audit Records</div>', unsafe_allow_html=True)
    st.caption(f"Showing {len(filtered)} records from {SHEET_NAME}")
    st.dataframe(filtered, use_container_width=True, height=430 if page != "🏠 Overview" else 300)


# ============================================================
# FOOTER
# ============================================================
st.markdown('<div style="text-align:center;color:#94a3b8;font-size:11px;margin-top:40px">QFL4 AI Audit Intelligence • Master Motor • FUSO • Powered by Google Gemini</div>', unsafe_allow_html=True)
