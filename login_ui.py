import base64
import io
import re
from pathlib import Path

import streamlit as st

from auth_session import create_auth_token, set_auth_cookie

APP_DIR = Path(__file__).resolve().parent

# ============================================================
# LOGIN / SIGNUP UI (full-screen truck photo + branded left panel)
# Replace your existing login() function with everything below.
# Keeps: load_users, save_users, session_state keys, approval flow.
# Usage in main file:  from login_ui import login ;  login(load_users, save_users)
# Image: fuso_canter_background.png in the same folder as the app.
# ============================================================

def _login_css(truck_background: str) -> str:
    return """
<style>
:root{
  --brand:#c8102e; --brand-dark:#a30d25; --navy:#0b1624;
  --text:#ffffff; --soft:#b9c5d4; --line:rgba(255,255,255,.16);
}

/* ---------- Backdrop and left panel ---------- */
header[data-testid="stHeader"], [data-testid="stSidebar"], [data-testid="collapsedControl"],
#MainMenu, footer{display:none !important;}
.stApp{
  background-color:#dbe3ec !important;
}
.stApp::before{
  content:""; position:fixed; inset:0; width:100vw; z-index:0; pointer-events:none;
  background:""" + truck_background + """ no-repeat right center / auto 100%;
}
.stApp::after{
  content:""; position:fixed; inset:0 auto 0 0; width:clamp(420px,46vw,620px);
  z-index:0; pointer-events:none;
  background:linear-gradient(90deg,rgba(39,48,61,.82) 0%,rgba(48,58,72,.76) 68%,rgba(48,58,72,.5) 84%,rgba(48,58,72,0) 100%);
}
[data-testid="stAppViewContainer"]{background:transparent !important;}
[data-testid="stAppViewContainer"], [data-testid="stMain"]{position:relative; z-index:1;}
.block-container{
  max-width:100% !important; min-height:100vh; min-height:100dvh;
  padding:18px 0 !important;
  display:flex; flex-direction:column; justify-content:center;
}
div[data-testid="stHorizontalBlock"]:has(.login-card-marker){align-items:center; gap:0 !important;}

/* ---------- Login panel ---------- */
div[data-testid="stColumn"]:has(.login-card-marker){
  box-sizing:border-box;
  flex:0 0 clamp(380px,38vw,460px) !important;
  width:clamp(380px,38vw,460px) !important; max-width:100%;
  padding:clamp(26px,4vh,40px) clamp(34px,6.2vw,72px) !important;
  background:transparent;
  border:0; border-radius:0;
  box-shadow:none;
}
div[data-testid="stColumn"]:has(.login-spacer){flex:1 1 auto !important;}

/* ---------- Brand ---------- */
.brand{padding-bottom:18px; margin-bottom:24px; border-bottom:1px solid var(--line); text-align:center;}
.brand-prepared{font-size:22px !important; font-weight:800; letter-spacing:1.2px; color:#f4f6f9; text-transform:uppercase;}
.brand-department{font-size:18px !important; font-weight:700; letter-spacing:.6px; color:#ff9baa; text-transform:uppercase; margin-top:7px;}
.brand-company{margin-top:24px; color:#f04b61; font-size:20px !important; font-weight:800; letter-spacing:1.2px; text-transform:uppercase;}
.brand-row{display:flex; align-items:center; justify-content:space-between; gap:12px; margin-top:10px;}
.brand-mark{
  width:40px; height:40px; flex:0 0 40px; border-radius:11px; display:grid; place-items:center;
  background:rgba(9,18,29,.72); color:#36d783; font-weight:800; font-size:22px;
  border:2px solid #e24a5d; box-shadow:0 0 12px rgba(200,16,46,.3);
}
.brand-identity{flex:1; text-align:center; min-width:0;}
.brand-name{font-size:21px; font-weight:800; color:#fff; letter-spacing:-.5px; line-height:1.15;}
.brand-name span{color:#ff6b81;}
.brand-desc{font-size:9px; font-weight:700; letter-spacing:1px; color:#9fb0c4; text-transform:uppercase; margin-top:5px;}
.brand-tag{flex:0 0 44px; text-align:center; line-height:1.3;}
.brand-tag b{display:block; font-size:11px; color:#f04b61; letter-spacing:1px;}
.brand-tag small{font-size:8px; font-weight:800; letter-spacing:1px; color:#34d399;}
.brand-tag small::before{content:"\\25CF\\00a0";}

.form-title{font-size:22px; font-weight:800; color:#ffffff !important; letter-spacing:-.3px; margin:0; text-align:center;}
.form-sub{font-size:12px; color:var(--soft); margin:8px 0 20px; line-height:1.5; text-align:center;}

/* ---------- Inputs (white, readable) ---------- */
div[data-testid="stColumn"]:has(.login-card-marker){color-scheme:light;}
div[data-testid="stColumn"]:has(.login-card-marker) label p{
  color:#dbe4ef !important; font-size:13px !important; font-weight:600 !important;
}
div[data-testid="stColumn"]:has(.login-card-marker) div[data-baseweb="base-input"],
div[data-testid="stColumn"]:has(.login-card-marker) div[data-baseweb="input"],
div[data-testid="stColumn"]:has(.login-card-marker) div[data-baseweb="input"] > div{
  background:#ffffff !important; background-color:#ffffff !important;
}
div[data-testid="stColumn"]:has(.login-card-marker) div[data-baseweb="input"] > div{
  border:1.5px solid transparent !important; border-radius:8px !important;
  min-height:44px !important; box-shadow:none !important; transition:border-color .15s, box-shadow .15s;
}
div[data-testid="stColumn"]:has(.login-card-marker) div[data-baseweb="input"] > div:focus-within{
  border-color:var(--brand) !important; box-shadow:0 0 0 4px rgba(200,16,46,.28) !important; outline:none !important;
}
div[data-testid="stColumn"]:has(.login-card-marker) input{
  color:#0f1b2d !important; -webkit-text-fill-color:#0f1b2d !important; caret-color:#c8102e; font-size:14px !important;
}
div[data-testid="stColumn"]:has(.login-card-marker) input::placeholder{
  color:#98a2b3 !important; -webkit-text-fill-color:#98a2b3 !important; opacity:1;
}
div[data-testid="stColumn"]:has(.login-card-marker) div[data-baseweb="input"] button{
  background:transparent !important; border:0 !important; box-shadow:none !important; color:#667085 !important;
}
div[data-testid="stColumn"]:has(.login-card-marker) div[data-baseweb="input"] svg{fill:#667085 !important;}
div[data-testid="stColumn"]:has(.login-card-marker) input:-webkit-autofill{
  -webkit-box-shadow:0 0 0 40px #ffffff inset !important; -webkit-text-fill-color:#0f1b2d !important;
}
div[data-testid="stColumn"]:has(.login-card-marker) [data-testid="stForm"]{
  border:0 !important; padding:0 !important; background:transparent !important;
}

/* ---------- Buttons ---------- */
div[data-testid="stColumn"]:has(.login-card-marker) button[kind="primary"],
div[data-testid="stColumn"]:has(.login-card-marker) button[kind="primaryFormSubmit"]{
  background:#c93449 !important;
  border:0 !important; border-radius:8px !important; min-height:40px;
  color:#fff !important; font-weight:700 !important; letter-spacing:.4px;
  box-shadow:none !important;
  transition:transform .15s, filter .15s, box-shadow .15s;
}
div[data-testid="stColumn"]:has(.login-card-marker) button[kind="primary"]:hover,
div[data-testid="stColumn"]:has(.login-card-marker) button[kind="primaryFormSubmit"]:hover{
  transform:translateY(-1px); filter:brightness(1.08);
}
div[data-testid="stColumn"]:has(.login-card-marker) button[kind="secondary"]{
  background:rgba(255,255,255,.06) !important; color:#fff !important;
  border:1px solid rgba(255,255,255,.42) !important; border-radius:7px !important;
  min-height:40px; font-weight:600 !important; transition:background .15s, border-color .15s;
}
div[data-testid="stColumn"]:has(.login-card-marker) button[kind="secondary"]:hover{
  background:rgba(255,255,255,.14) !important; border-color:#fff !important;
}
div[data-testid="stColumn"]:has(.login-card-marker) button p{color:inherit !important;}

.switch-row{display:block; margin:22px 0 8px; color:#9fb0c4; font-size:11px; text-align:center;}
.switch-row::before,.switch-row::after{display:none;}
.card-foot{margin-top:24px; text-align:center; color:#aab5c4; font-size:9px; line-height:1.6;}
.card-foot b{color:#d0d7e0; letter-spacing:.5px; font-size:9px; text-transform:none;}

/* ---------- Tablet ---------- */
@media (max-width:1100px){
  div[data-testid="stColumn"]:has(.login-card-marker){flex-basis:clamp(380px,38vw,440px) !important; width:clamp(380px,38vw,440px) !important;}
}

/* ---------- Mobile / small tablet: truck on top, form below ---------- */
@media (max-width:860px){
  .stApp{
    background-color:#dbe3ec !important;
  }
  .stApp::after{
    inset:0; width:auto;
    background:linear-gradient(180deg,rgba(39,48,61,0) 0%,rgba(39,48,61,.12) 25%,rgba(39,48,61,.86) 38%,rgba(39,48,61,.9) 100%);
  }
  .stApp::before{
    inset:0 0 auto; width:100%; height:36vh;
    background-position:center top; background-size:100% auto;
  }
  .block-container{justify-content:flex-start; padding:34vh 16px 28px !important;}
  div[data-testid="stHorizontalBlock"]:has(.login-card-marker){flex-direction:column; gap:0 !important;}
  div[data-testid="stColumn"]:has(.login-spacer){display:none !important;}
  div[data-testid="stColumn"]:has(.login-card-marker){
    flex:1 1 100% !important; width:100% !important; max-width:540px; margin:0 auto;
    padding:22px 24px !important; background:rgba(39,48,61,.94);
  }
}
@media (max-width:520px){
  div[data-testid="stColumn"]:has(.login-card-marker){padding:22px 18px !important;}
  .brand-company{margin-top:18px;}
  .brand-prepared{font-size:19px !important;}
  .brand-department{display:block; font-size:15px !important;}
  .brand-company{font-size:17px !important;}
  .brand-tag{display:none;}
  .brand-mark{width:36px; height:36px; flex-basis:36px; font-size:20px;}
  .brand-name{font-size:20px;}
  .form-title{font-size:22px;}
  .form-sub{font-size:13px; margin-bottom:16px;}
  /* stack the two-column signup fields */
  div[data-testid="stColumn"]:has(.login-card-marker) [data-testid="stForm"] div[data-testid="stHorizontalBlock"]{
    flex-direction:column; gap:0 !important;
  }
  div[data-testid="stColumn"]:has(.login-card-marker) [data-testid="stForm"] div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]{
    width:100% !important; flex:1 1 100% !important; min-width:100% !important;
  }
}
/* Short laptop / landscape screens */
@media (max-height:700px) and (min-width:861px){
  .block-container{padding-top:12px !important; padding-bottom:12px !important;}
  .brand{margin-bottom:12px; padding-bottom:12px;}
  .brand-desc,.card-foot{display:none;}
}
@media (prefers-reduced-motion:reduce){*{transition:none !important;}}
</style>
"""


@st.cache_resource(show_spinner=False)
def _truck_data_uri():
    """Load the truck photo once, shrink it to a web-sized JPEG and return a CSS url()."""
    path = APP_DIR / "fuso_canter_background.png"
    if not path.is_file():
        return "none"
    try:
        from PIL import Image
        img = Image.open(path).convert("RGB")
        img.thumbnail((1800, 1800))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85, optimize=True)
        encoded = base64.b64encode(buf.getvalue()).decode("ascii")
        return f'url("data:image/jpeg;base64,{encoded}")'
    except Exception:
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        return f'url("data:image/png;base64,{encoded}")'


def login(load_users, save_users):
    truck_background = _truck_data_uri()

    st.markdown(_login_css(truck_background), unsafe_allow_html=True)

    form_col, spacer_col = st.columns([1, 1.5], gap="small", vertical_alignment="center")

    # Right side stays empty so the truck photo is fully visible
    with spacer_col:
        st.markdown('<div class="login-spacer"></div>', unsafe_allow_html=True)

    with form_col:
        users = load_users()

        st.markdown(
            """
            <span class="login-card-marker"></span>
            <div class="brand">
                <div class="brand-prepared">Prepared by Team FQCM</div>
                <div class="brand-department">Final Quality Control Management</div>
                <div class="brand-company">Master Motors &bull; FUSO</div>
                <div class="brand-row">
                    <div class="brand-mark" aria-hidden="true">&#10003;</div>
                    <div class="brand-identity">
                        <div class="brand-name">QFL4 <span>AI</span></div>
                        <div class="brand-desc">Automotive quality &amp; audit intelligence</div>
                    </div>
                    <div class="brand-tag"><b>FQCM</b><small>ACTIVE</small></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ----------------- SIGN IN -----------------
        if not st.session_state.show_signup:
            st.markdown(
                """
                <div class="form-title">Welcome back</div>
                <div class="form-sub">Sign in to access the QFL4 quality portal.</div>
                """,
                unsafe_allow_html=True,
            )

            with st.form("login_form", border=False):
                e = st.text_input("Email", placeholder="name@master.com.pk")
                p = st.text_input("Password", type="password", placeholder="Enter your password")
                submitted = st.form_submit_button("LOGIN", width="stretch", type="primary")

                if submitted:
                    e_clean = e.strip().lower()
                    if not e_clean or not p:
                        st.error("Please enter your email and password.")
                    elif e_clean in users:
                        if users[e_clean]["status"] == "approved":
                            if users[e_clean]["password"] == p:
                                st.session_state.logged_in = True
                                st.session_state.user_email = e_clean
                                st.session_state.role = users[e_clean].get("role", "user")
                                st.session_state.auth_cookie_revoked = False
                                st.session_state.portal_loading = True
                                set_auth_cookie(create_auth_token(e_clean))
                            else:
                                st.error("Incorrect password.")
                        else:
                            st.warning("Your account is awaiting admin approval ⏳")
                    else:
                        st.error("Email not found. Please create an account.")

            st.markdown('<div class="switch-row">Don\'t have an account?</div>', unsafe_allow_html=True)
            if st.button("Create Account", width="stretch", key="goto_signup"):
                st.session_state.show_signup = True
                st.rerun()

        # ----------------- SIGN UP -----------------
        else:
            st.markdown(
                """
                <div class="form-title">Create account</div>
                <div class="form-sub">Register for audit portal access. An admin will approve your request.</div>
                """,
                unsafe_allow_html=True,
            )

            with st.form("signup_form", border=False):
                n_col, m_col = st.columns(2, gap="small")
                with n_col:
                    full_name = st.text_input("Full Name", placeholder="Taha Shahid")
                with m_col:
                    new_e = st.text_input("Email", placeholder="name@master.com.pk").strip().lower()
                p_col, c_col = st.columns(2, gap="small")
                with p_col:
                    new_p = st.text_input("Password", type="password", placeholder="Min. 6 characters")
                with c_col:
                    confirm_p = st.text_input("Confirm Password", type="password", placeholder="Repeat password")

                signup_submitted = st.form_submit_button("CREATE ACCOUNT", width="stretch", type="primary")

                if signup_submitted:
                    if not full_name.strip() or not new_e or not new_p or not confirm_p:
                        st.error("Please fill in all fields.")
                    elif not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", new_e):
                        st.error("Please enter a valid email address.")
                    elif len(new_p) < 6:
                        st.error("Password must be at least 6 characters.")
                    elif new_p != confirm_p:
                        st.error("Passwords do not match.")
                    elif new_e in users:
                        st.error("This email is already registered or requested.")
                    else:
                        users[new_e] = {
                            "name": full_name.strip(),
                            "password": new_p,
                            "status": "pending",
                            "role": "user",
                        }
                        save_users(users)
                        st.success("Account created! Status: PENDING ⏳ — waiting for admin approval.")

            st.markdown('<div class="switch-row">Already have an account?</div>', unsafe_allow_html=True)
            if st.button("Login", width="stretch", key="goto_login"):
                st.session_state.show_signup = False
                st.rerun()

        st.markdown(
            """
            <div class="card-foot">
                <b>Prepared by Team FQCM</b><br>
                Final Quality Control Management<br>
                &copy; 2026 Master Motor Corporation Ltd. &middot; Powered by AI Audit Intelligence
            </div>
            """,
            unsafe_allow_html=True,
        )