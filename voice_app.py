import os
import re
import html
import json
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import plotly.express as px
import plotly.graph_objects as go

# Cloud AI
from openai import OpenAI
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

# OpenAI models. API key is read from Streamlit Secrets / environment.
AI_MODEL = "gpt-5.6-luna"
TRANSCRIBE_MODEL = "gpt-4o-mini-transcribe"

# Login is also read from Streamlit Secrets.
# If you do not create these secrets, the app will show a clear message.
LOGIN_EMAIL = st.secrets.get("LOGIN_EMAIL", os.getenv("LOGIN_EMAIL", ""))
LOGIN_PASSWORD = st.secrets.get("LOGIN_PASSWORD", os.getenv("LOGIN_PASSWORD", ""))

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False


# ============================================================
# STYLING
# ============================================================
st.markdown(
    """
<style>
#MainMenu,header,footer{visibility:hidden}
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
    padding:22px 28px 28px;
    text-align:center;
    box-shadow:0 7px 22px rgba(15,23,42,.05);
    margin-bottom:20px
}
.brand-title{
    font-size:13px;
    font-weight:900;
    letter-spacing:2.5px;
    color:#2563eb;
    margin-top:7px
}
.main-title{
    font-size:36px;
    font-weight:900;
    color:#243447;
    margin-top:5px
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
    margin:70px auto 20px;
    background:#fff;
    padding:38px;
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
    font-size:32px;
    font-weight:900;
    margin-top:7px
}
.login-subtitle{
    color:#64748b;
    margin-bottom:24px
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
# HELPERS
# ============================================================
def login():
    st.markdown(
        """
        <div class="login-box">
            <div class="login-logo">MASTER MOTOR • QFL4</div>
            <div class="login-title">Audit Intelligence</div>
            <div class="login-subtitle">
                Sign in to access AI-powered audit analytics
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not LOGIN_EMAIL or not LOGIN_PASSWORD:
        st.error(
            "Login credentials are not configured. Add LOGIN_EMAIL and "
            "LOGIN_PASSWORD to Streamlit Secrets."
        )
        return

    e = st.text_input("📧 Email")
    p = st.text_input("🔒 Password", type="password")

    if st.button("Login →", type="primary", use_container_width=True):
        if e.strip().lower() == LOGIN_EMAIL.lower() and p == LOGIN_PASSWORD:
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Invalid email or password.")


def get_openai_client():
    api_key = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", ""))
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


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
    c = find_col(
        d,
        [
            "Chassis No",
            "Chassis",
            "Chassis Number",
            "Vehicle",
            "Vehicle No",
            "Vehicle Number",
        ],
    )
    if not c:
        return len(d)
    s = d[c].dropna().astype(str).str.strip()
    s = s[s != ""]
    return int(s.nunique())


def class_total(d, label):
    return nsum(
        d,
        find_col(
            d,
            [
                f"CLASS {label}",
                f"Class {label}",
                f"CLASS_{label}",
            ],
        ),
    )


def zone_total(d, label):
    return nsum(
        d,
        find_col(
            d,
            [
                f"ZONE {label}",
                f"Zone {label}",
                f"ZONE_{label}",
            ],
        ),
    )


def ab_total(d):
    c = find_col(d, ["A+B", "A + B", "AB", "A B"])
    return nsum(d, c) if c else class_total(d, "A") + class_total(d, "B")


def total_defects(d):
    c = find_col(
        d,
        [
            "Total",
            "Total Defects",
            "Defect Quantity",
            "Defects",
        ],
    )
    if c:
        return nsum(d, c)

    s = sum(class_total(d, x) for x in "ABCD")
    if s:
        return s

    return nsum(
        d,
        find_col(
            d,
            ["QTY", "Quantity", "Defect Qty", "Defect Quantity"],
        ),
    )


@st.cache_data(ttl=30)
def load_excel():
    d = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME)
    d.columns = (
        d.columns.astype(str)
        .str.strip()
        .str.replace("\n", " ", regex=False)
        .str.replace(r"\s+", " ", regex=True)
    )

    date_col = next(
        (x for x in d.columns if str(x).strip().lower() == "date"),
        None,
    )
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


def direct_answer(q, d):
    raw = q.lower()

    vehicle = any(
        x in raw
        for x in [
            "vehicle",
            "vehicles",
            "gari",
            "gariyan",
            "gaari",
            "gaariyan",
            "car",
            "cars",
        ]
    )

    count = any(
        x in raw
        for x in [
            "how many",
            "number of",
            "kitni",
            "kitne",
            "total kitni",
            "total kitne",
        ]
    )

    if vehicle and count:
        n = vehicle_count(d)
        return (
            f"{n} vehicles were audited. "
            f"Roman Urdu: {n} gariyan audit hui hain."
        )

    if any(
        x in raw
        for x in [
            "total defect",
            "total defects",
            "kitne defects",
            "defects kitne",
        ]
    ):
        n = total_defects(d)
        return (
            f"The total number of defects is {n}. "
            f"Roman Urdu: total {n} defects hain."
        )

    if any(x in raw for x in ["a+b", "a + b", "a plus b"]):
        return f"The total A+B defects are {ab_total(d)}."

    for label in "ABCD":
        if f"class {label.lower()}" in raw:
            return f"There are {class_total(d, label)} Class {label} defects."
        if f"zone {label.lower()}" in raw:
            return f"There are {zone_total(d, label)} defects in Zone {label}."

    return None


def make_ai_context(d):
    # Keep the prompt reasonably small for cloud usage.
    sample = d.head(300).copy()

    # Convert datetime values to strings for a clean prompt.
    for c in sample.columns:
        if pd.api.types.is_datetime64_any_dtype(sample[c]):
            sample[c] = sample[c].dt.strftime("%Y-%m-%d")

    return sample.to_string(index=False)


def ai_answer(q, d):
    # Deterministic answers for common KPI questions.
    fast_answer = direct_answer(q, d)
    if fast_answer:
        return fast_answer

    client = get_openai_client()
    if client is None:
        return (
            "OpenAI API key is not configured. "
            "Please add OPENAI_API_KEY to Streamlit Secrets."
        )

    context = make_ai_context(d)

    prompt = f"""
You are the QFL4 Vehicle Audit Intelligence Assistant.

STRICT DATA RULES:
1. Use ONLY the audit data supplied below.
2. Never invent, estimate, assume, or fabricate a number.
3. If the supplied data does not contain enough information to answer,
   say that the information is not available in the current audit data.
4. Respect the active dashboard filters. The data below is already filtered.
5. Understand English, Urdu, and Roman Urdu.
6. If the user asks in Roman Urdu, answer in clear Roman Urdu.
7. If the user asks in Urdu, you may answer in Urdu.
8. Keep answers short and practical.
9. When giving a number, make it clear what the number represents.

ACTIVE FILTERED AUDIT DATA:
Columns:
{", ".join(map(str, d.columns))}

Rows:
{context}

USER QUESTION:
{q}
"""

    try:
        response = client.responses.create(
            model=AI_MODEL,
            input=prompt,
        )
        answer = getattr(response, "output_text", "") or ""
        answer = answer.strip()

        if answer:
            return answer

        return "I could not generate an answer from the current audit data."

    except Exception as exc:
        msg = str(exc)
        if "api_key" in msg.lower() or "authentication" in msg.lower():
            return "OpenAI authentication failed. Please check OPENAI_API_KEY in Streamlit Secrets."
        return f"Cloud AI request failed: {msg}"


def speech_to_text(audio_bytes):
    client = get_openai_client()
    if client is None:
        return None, (
            "OpenAI API key is not configured. "
            "Please add OPENAI_API_KEY to Streamlit Secrets."
        )

    temp_file = "voice_input.wav"

    try:
        with open(temp_file, "wb") as f:
            f.write(audio_bytes)

        with open(temp_file, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model=TRANSCRIBE_MODEL,
                file=audio_file,
            )

        text = getattr(transcript, "text", "") or ""
        return text.strip(), None

    except Exception as exc:
        return None, f"Voice transcription failed: {exc}"

    finally:
        try:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        except Exception:
            pass


def speak(text):
    safe_text = json.dumps(str(text))
    components.html(
        f"""
        <script>
        speechSynthesis.cancel();
        const u = new SpeechSynthesisUtterance({safe_text});
        u.lang = 'en-US';
        u.rate = 1.08;
        speechSynthesis.speak(u);
        </script>
        """,
        height=1,
    )


# ============================================================
# AUTHENTICATION
# ============================================================
if not st.session_state.logged_in:
    login()
    st.stop()


# ============================================================
# REQUIRED FILE CHECK
# ============================================================
if not os.path.exists(EXCEL_FILE):
    st.error(
        f"{EXCEL_FILE} not found. Upload it beside voice_app.py "
        "in your Streamlit/GitHub repository."
    )
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

    st.markdown(
        '<div class="nav-section">ANALYTICS</div>',
        unsafe_allow_html=True,
    )

    page = st.radio(
        "Pages",
        [
            "🏠 Overview",
            "🎙️ AI Assistant",
            "⚠️ Total Defects",
            "📈 Pareto Analysis",
            "🚗 Vehicle Audit",
            "🧩 Class & Zone",
            "📋 Audit Data",
        ],
        label_visibility="collapsed",
    )

    st.markdown(
        '<div class="nav-section">SYSTEM</div>',
        unsafe_allow_html=True,
    )

    ai_ready = get_openai_client() is not None
    ai_status = (
        '<span class="status-ok">● CLOUD AI READY</span>'
        if ai_ready
        else '<span class="status-warn">● API KEY REQUIRED</span>'
    )

    st.markdown(
        f"""
        <div class="sidebar-note">
            Source: {html.escape(EXCEL_FILE)}<br>
            AI: {html.escape(AI_MODEL)}<br>
            Voice: Cloud transcription<br>
            <br>
            {ai_status}<br>
            <br>
            Excel auto-refresh: ON
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()


# ============================================================
# PAGE HEADER
# ============================================================
if page == "🏠 Overview":
    st.markdown('<div class="logo-area">', unsafe_allow_html=True)

    if os.path.exists(LOGO_FILE):
        st.image(LOGO_FILE, width=320)
    else:
        st.warning(f"{LOGO_FILE} not found.")

    st.markdown(
        """
        <div class="brand-title">MASTER MOTOR • QFL4</div>
        <div class="main-title">AI AUDIT INTELLIGENCE</div>
        <div class="main-subtitle">
            Smart Vehicle Quality & Audit Analytics
        </div>
        <div class="online-badge">● SYSTEM ONLINE</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

else:
    titles = {
        "🎙️ AI Assistant": (
            "AI Voice Assistant",
            "Ask audit questions in English, Urdu, or Roman Urdu.",
        ),
        "⚠️ Total Defects": (
            "Total Defects",
            "Defect performance and class distribution.",
        ),
        "📈 Pareto Analysis": (
            "Pareto Analysis",
            "Identify the highest-impact defect types.",
        ),
        "🚗 Vehicle Audit": (
            "Vehicle Audit",
            "Vehicle and chassis-level audit information.",
        ),
        "🧩 Class & Zone": (
            "Class & Zone Analysis",
            "Compare quality classes and audit zones.",
        ),
        "📋 Audit Data": (
            "Audit Data",
            "Connected Excel records used by the analytics engine.",
        ),
    }

    title, description = titles[page]
    page_title(title, description)


# ============================================================
# SHARED FILTERS
# ============================================================
st.markdown(
    '<div class="section-title">🔎 Audit Filters</div>',
    unsafe_allow_html=True,
)

date_col = find_col(df, ["Date"])
vehicle_col = find_col(df, ["Vehicle", "Vehicle No", "Vehicle Name"])
model_col = find_col(df, ["Model", "Model Name"])
chassis_col = find_col(
    df,
    ["Chassis No", "Chassis", "Chassis Number"],
)

f1, f2, f3, f4 = st.columns(4)

with f1:
    if date_col:
        dates = sorted(
            df[date_col].dropna().dt.date.unique().tolist()
        )
    else:
        dates = []

    selected_dates = st.multiselect("📅 Date", dates)

with f2:
    vehicle_options = (
        sorted(
            df[vehicle_col]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )
        if vehicle_col
        else []
    )
    selected_vehicle = st.selectbox(
        "🚗 Vehicle",
        ["All"] + vehicle_options,
    )

with f3:
    model_options = (
        sorted(
            df[model_col]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )
        if model_col
        else []
    )
    selected_model = st.selectbox(
        "🏷️ Model",
        ["All"] + model_options,
    )

with f4:
    chassis_options = (
        sorted(
            df[chassis_col]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )
        if chassis_col
        else []
    )
    selected_chassis = st.selectbox(
        "🔢 Chassis No.",
        ["All"] + chassis_options,
    )


filtered = df.copy()

if selected_dates and date_col:
    filtered = filtered[
        filtered[date_col].dt.date.isin(selected_dates)
    ]

if selected_vehicle != "All" and vehicle_col:
    filtered = filtered[
        filtered[vehicle_col].astype(str) == selected_vehicle
    ]

if selected_model != "All" and model_col:
    filtered = filtered[
        filtered[model_col].astype(str) == selected_model
    ]

if selected_chassis != "All" and chassis_col:
    filtered = filtered[
        filtered[chassis_col].astype(str) == selected_chassis
    ]


# ============================================================
# KPI CARDS
# ============================================================
if page in ["🏠 Overview", "⚠️ Total Defects"]:
    st.markdown(
        '<div class="section-title">📌 Key Performance Indicators</div>',
        unsafe_allow_html=True,
    )

    kpis = [
        ("🚗 VEHICLES AUDITED", vehicle_count(filtered)),
        ("⚠️ TOTAL DEFECTS", total_defects(filtered)),
        ("🔴 CLASS A", class_total(filtered, "A")),
        ("🟠 A+B", ab_total(filtered)),
    ]

    for col, (label, value) in zip(st.columns(4), kpis):
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


# ============================================================
# QUALITY DISTRIBUTION
# ============================================================
if page in ["🏠 Overview", "⚠️ Total Defects", "🧩 Class & Zone"]:
    st.markdown(
        '<div class="section-title">📊 Quality Distribution</div>',
        unsafe_allow_html=True,
    )

    a, b = st.columns(2)

    with a:
        class_df = pd.DataFrame(
            {
                "Class": list("ABCD"),
                "Defects": [
                    class_total(filtered, x)
                    for x in "ABCD"
                ],
            }
        )

        fig_class = px.bar(
            class_df,
            x="Class",
            y="Defects",
            text="Defects",
            title="Class-wise Defect Distribution",
        )
        fig_class.update_layout(
            height=380,
            margin=dict(l=20, r=20, t=55, b=20),
        )
        st.plotly_chart(
            fig_class,
            use_container_width=True,
        )

    with b:
        zone_df = pd.DataFrame(
            {
                "Zone": list("ABCD"),
                "Defects": [
                    zone_total(filtered, x)
                    for x in "ABCD"
                ],
            }
        )

        fig_zone = px.bar(
            zone_df,
            x="Zone",
            y="Defects",
            text="Defects",
            title="Zone-wise Defect Distribution",
        )
        fig_zone.update_layout(
            height=380,
            margin=dict(l=20, r=20, t=55, b=20),
        )
        st.plotly_chart(
            fig_zone,
            use_container_width=True,
        )


# ============================================================
# PARETO DATA
# ============================================================
defect_col = find_col(
    filtered,
    [
        "Defect Type",
        "Defect",
        "Defect Name",
        "Defect Description",
        "Problem",
    ],
)

qty_col = find_col(
    filtered,
    [
        "QTY",
        "Quantity",
        "Defect Qty",
        "Defect Quantity",
        "Qty",
    ],
)

pareto = None

if defect_col and qty_col:
    pareto = filtered[[defect_col, qty_col]].copy()
    pareto[defect_col] = (
        pareto[defect_col]
        .astype(str)
        .str.strip()
    )
    pareto[qty_col] = pd.to_numeric(
        pareto[qty_col],
        errors="coerce",
    ).fillna(0)

    pareto = pareto[
        ~pareto[defect_col].isin(
            ["", "nan", "None", "NaN"]
        )
    ]

    pareto = (
        pareto.groupby(
            defect_col,
            as_index=False,
        )[qty_col]
        .sum()
        .sort_values(
            qty_col,
            ascending=False,
        )
        .reset_index(drop=True)
    )


# ============================================================
# PARETO PAGE
# ============================================================
if page in ["🏠 Overview", "📈 Pareto Analysis"]:
    st.markdown(
        '<div class="section-title">📈 Defect Pareto Analysis</div>',
        unsafe_allow_html=True,
    )

    if (
        pareto is not None
        and not pareto.empty
        and pareto[qty_col].sum() > 0
    ):
        total = pareto[qty_col].sum()
        pareto["Cumulative %"] = (
            pareto[qty_col].cumsum()
            / total
            * 100
        )

        fig_pareto = go.Figure()

        fig_pareto.add_trace(
            go.Bar(
                x=pareto[defect_col],
                y=pareto[qty_col],
                name="Defect Quantity",
                text=pareto[qty_col],
                textposition="outside",
            )
        )

        fig_pareto.add_trace(
            go.Scatter(
                x=pareto[defect_col],
                y=pareto["Cumulative %"],
                name="Cumulative %",
                mode="lines+markers",
                yaxis="y2",
            )
        )

        if len(pareto) >= 2:
            fig_pareto.add_trace(
                go.Scatter(
                    x=[
                        pareto[defect_col].iloc[0],
                        pareto[defect_col].iloc[-1],
                    ],
                    y=[80, 80],
                    name="80% Target",
                    mode="lines",
                    line=dict(dash="dash"),
                    yaxis="y2",
                )
            )

        fig_pareto.update_layout(
            title="Defect Quantity Pareto",
            height=520,
            xaxis=dict(tickangle=-45),
            yaxis=dict(title="Quantity"),
            yaxis2=dict(
                title="Cumulative %",
                overlaying="y",
                side="right",
                range=[0, 100],
                ticksuffix="%",
            ),
            margin=dict(
                l=40,
                r=70,
                t=65,
                b=140,
            ),
        )

        st.plotly_chart(
            fig_pareto,
            use_container_width=True,
        )

    else:
        st.info(
            "No Pareto data available for the current filters."
        )


# ============================================================
# AI VOICE ASSISTANT
# ============================================================
if page in ["🏠 Overview", "🎙️ AI Assistant"]:
    st.markdown(
        """
        <div class="voice-card">
            <div class="voice-title">
                🎙️ AI Voice Audit Assistant
            </div>
            <div class="voice-subtitle">
                Speak in English, Urdu or Roman Urdu.
                Stop recording and the answer appears as text and voice.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not get_openai_client():
        st.warning(
            "Cloud AI is not configured yet. Add OPENAI_API_KEY "
            "to Streamlit Secrets to enable text and voice AI."
        )

    audio = mic_recorder(
        start_prompt="🎤 Start Speaking",
        stop_prompt="⏹️ Stop Recording",
        just_once=True,
        format="wav",
        key="audit_voice",
    )

    if audio:
        with st.spinner("🎧 Understanding your question..."):
            question, error = speech_to_text(audio["bytes"])

        if error:
            st.error(error)
        elif question:
            st.markdown(
                f"""
                <div class="answer-card">
                    <div class="answer-label">YOU SAID</div>
                    <div class="answer-text">
                        {html.escape(question)}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            with st.spinner("🤖 Analysing audit data..."):
                answer = ai_answer(
                    question,
                    filtered,
                )

            st.markdown(
                f"""
                <div class="answer-card">
                    <div class="answer-label">AI RESPONSE</div>
                    <div class="answer-text">
                        {html.escape(answer)}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            speak(answer)

    st.markdown(
        '<div class="section-title">⌨️ Ask by Text</div>',
        unsafe_allow_html=True,
    )

    text_question = st.text_input(
        "Question",
        placeholder="Example: kitni gari audit hui hy?",
        label_visibility="collapsed",
    )

    if (
        st.button(
            "Ask Assistant →",
            type="primary",
            use_container_width=True,
        )
        and text_question.strip()
    ):
        with st.spinner("🤖 Analysing audit data..."):
            answer = ai_answer(
                text_question,
                filtered,
            )

        st.markdown(
            f"""
            <div class="answer-card">
                <div class="answer-label">AI RESPONSE</div>
                <div class="answer-text">
                    {html.escape(answer)}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        speak(answer)


# ============================================================
# AUDIT RECORDS
# ============================================================
if page in [
    "🏠 Overview",
    "🚗 Vehicle Audit",
    "📋 Audit Data",
]:
    st.markdown(
        '<div class="section-title">📋 Audit Records</div>',
        unsafe_allow_html=True,
    )

    st.caption(
        f"Showing {len(filtered)} records from {SHEET_NAME}"
    )

    st.dataframe(
        filtered,
        use_container_width=True,
        height=430 if page != "🏠 Overview" else 300,
    )


# ============================================================
# FOOTER
# ============================================================
st.markdown(
    """
    <div style="
        text-align:center;
        color:#94a3b8;
        font-size:11px;
        margin-top:40px
    ">
        QFL4 AI Audit Intelligence • Master Motor • FUSO •
        AI-Powered Quality Analytics
    </div>
    """,
    unsafe_allow_html=True,
)
