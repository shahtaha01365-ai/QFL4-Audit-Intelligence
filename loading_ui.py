import base64
from contextlib import contextmanager
from html import escape
from pathlib import Path

import streamlit as st

_FUSO_LOGO_BASE64 = base64.b64encode(
    Path(__file__).with_name("fuso_logo.png").read_bytes()
).decode("ascii")
FUSO_LOGO_DATA_URI = f"data:image/png;base64,{_FUSO_LOGO_BASE64}"

# ============================================================
# PORTAL LOADING SCREEN  (shown right after a successful login)
# 1) Paste PORTAL_LOADING_HTML anywhere ABOVE the
#    "LOAD DATA FROM GOOGLE SHEETS" section (e.g. in HELPER FUNCTIONS).
# 2) In that section, replace the whole big loading_overlay.markdown("""...""")
#    string with:  loading_overlay.markdown(PORTAL_LOADING_HTML, unsafe_allow_html=True)
# ============================================================

PORTAL_LOADING_HTML = """<style>
.pl-overlay{
  position:fixed; inset:0; z-index:999999; display:grid; place-items:center; padding:24px; overflow:hidden;
  background:
    radial-gradient(900px 520px at 12% 8%, rgba(200,16,46,.24), transparent 60%),
    radial-gradient(800px 520px at 92% 96%, rgba(58,112,172,.24), transparent 60%),
    linear-gradient(160deg,#08111d 0%,#0e1b2c 55%,#0a1522 100%);
  animation:pl-fade .4s ease both;
}
.pl-overlay::before{
  content:""; position:absolute; inset:0; pointer-events:none;
  background-image:
    linear-gradient(rgba(255,255,255,.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,.035) 1px, transparent 1px);
  background-size:48px 48px;
  -webkit-mask-image:radial-gradient(circle at center,#000 0%,transparent 72%);
  mask-image:radial-gradient(circle at center,#000 0%,transparent 72%);
}
.pl-card{position:relative; display:flex; flex-direction:column; align-items:center; text-align:center; width:min(380px,100%);}
.pl-brand-logo{display:block;width:clamp(150px,34vw,220px);height:auto;margin:0 auto 24px;
  border-radius:10px;box-shadow:0 10px 28px rgba(0,0,0,.2);}

/* ---- Spinner ---- */
.pl-spinner{position:relative; width:clamp(104px,28vw,132px); aspect-ratio:1;}
.pl-track{position:absolute; inset:0; border-radius:50%; border:3px solid rgba(255,255,255,.07);}
.pl-ring{
  position:absolute; inset:0; border-radius:50%;
  background:conic-gradient(from 0deg, rgba(255,90,115,0) 0deg, rgba(255,90,115,0) 50deg, #ff5a73 360deg);
  -webkit-mask:radial-gradient(farthest-side, transparent calc(100% - 4px), #000 calc(100% - 3px));
  mask:radial-gradient(farthest-side, transparent calc(100% - 4px), #000 calc(100% - 3px));
  animation:pl-spin 1.2s linear infinite;
  filter:drop-shadow(0 0 8px rgba(255,90,115,.55));
}
.pl-ring.two{
  inset:9%;
  background:conic-gradient(from 0deg, rgba(255,255,255,0) 0deg, rgba(255,255,255,0) 70deg, rgba(255,255,255,.8) 360deg);
  -webkit-mask:radial-gradient(farthest-side, transparent calc(100% - 3px), #000 calc(100% - 2px));
  mask:radial-gradient(farthest-side, transparent calc(100% - 3px), #000 calc(100% - 2px));
  animation:pl-spin 1.9s linear infinite reverse;
  filter:none;
}
.pl-mark{
  position:absolute; inset:22%; border:2px solid #e24a5d; border-radius:24%; display:grid; place-items:center;
  background:rgba(9,18,29,.88); color:#36d783;
  font-weight:800; font-size:clamp(30px,7vw,38px); line-height:1;
  box-shadow:0 0 12px rgba(200,16,46,.3), 0 12px 34px rgba(200,16,46,.35);
  animation:pl-pulse 2s ease-in-out infinite;
}

/* ---- Text ---- */
.pl-kicker{margin-top:30px; color:#ff6b81; font-size:10px; font-weight:800; letter-spacing:2px; text-transform:uppercase;}
.pl-title{margin-top:6px; color:#fff; font-size:clamp(26px,6vw,32px); font-weight:800; letter-spacing:-.8px; line-height:1.1;}
.pl-title span{color:#ff6b81;}
.pl-status{position:relative; height:22px; width:100%; margin-top:14px; color:#b9c5d4; font-size:13px; font-weight:500;}
.pl-status span{position:absolute; left:0; right:0; opacity:0; animation:pl-cycle 6s ease-in-out infinite;}
.pl-status span:nth-child(2){animation-delay:2s;}
.pl-status span:nth-child(3){animation-delay:4s;}

/* ---- Progress bar ---- */
.pl-bar{position:relative; width:min(240px,70%); height:4px; margin-top:18px; border-radius:99px; overflow:hidden; background:rgba(255,255,255,.1);}
.pl-bar::after{
  content:""; position:absolute; top:0; bottom:0; width:42%; border-radius:99px;
  background:linear-gradient(90deg,transparent,#ff5a73,#ffffff,#ff5a73,transparent);
  animation:pl-slide 1.5s ease-in-out infinite;
}
.pl-foot{margin-top:34px; color:#7f91a7; font-size:10px; font-weight:700; letter-spacing:1.6px; text-transform:uppercase;}

@keyframes pl-spin{to{transform:rotate(360deg);}}
@keyframes pl-pulse{0%,100%{transform:scale(1);} 50%{transform:scale(1.06);}}
@keyframes pl-slide{0%{left:-45%;} 100%{left:105%;}}
@keyframes pl-fade{from{opacity:0;} to{opacity:1;}}
@keyframes pl-cycle{
  0%{opacity:0; transform:translateY(6px);}
  6%,28%{opacity:1; transform:translateY(0);}
  34%,100%{opacity:0; transform:translateY(-6px);}
}
@media (max-width:520px){
  .pl-kicker{margin-top:24px;}
  .pl-foot{margin-top:26px;}
}
@media (prefers-reduced-motion:reduce){
  .pl-ring,.pl-mark,.pl-bar::after{animation-duration:4s;}
}
</style>
<div class="pl-overlay" role="status" aria-live="polite">
<div class="pl-card">
<img class="pl-brand-logo" src="__FUSO_LOGO_DATA_URI__" alt="FUSO">
<div class="pl-spinner">
<div class="pl-track"></div>
<div class="pl-ring"></div>
<div class="pl-ring two"></div>
<div class="pl-mark" aria-hidden="true">&#10003;</div>
</div>
<div class="pl-kicker">Master Motors &bull; FUSO</div>
<div class="pl-title">QFL4 <span>AI</span></div>
<div class="pl-status">
<span>Connecting to Google Sheets&hellip;</span>
<span>Loading audit records&hellip;</span>
<span>Preparing your dashboard&hellip;</span>
</div>
<div class="pl-bar"></div>
<div class="pl-foot">Secure session &middot; Quality Intelligence</div>
</div>
</div>""".replace("__FUSO_LOGO_DATA_URI__", FUSO_LOGO_DATA_URI)


@contextmanager
def qfl4_spinner(message):
    """Show the branded full-screen loader while a page section is processing."""
    placeholder = st.empty()
    status_messages = (
        "Connecting to Google Sheets&hellip;",
        "Loading audit records&hellip;",
        "Preparing your dashboard&hellip;",
    )
    loader_html = PORTAL_LOADING_HTML
    for status_message in status_messages:
        loader_html = loader_html.replace(status_message, escape(str(message)))
    placeholder.markdown(loader_html, unsafe_allow_html=True)
    try:
        yield
    finally:
        placeholder.empty()