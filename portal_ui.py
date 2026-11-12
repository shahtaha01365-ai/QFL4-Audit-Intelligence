"""
QFL4 AI Audit Intelligence - portal UI module
=============================================
Design system, sidebar, KPI cards, chart styling, page renderers and footer.
Put this file in the SAME folder as your main Streamlit file.
"""
import html
import json
import numbers
import re
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

from auth_session import clear_auth_cookie
from loading_ui import FUSO_LOGO_DATA_URI, PORTAL_LOADING_HTML

# ------------------------------------------------------------
# PALETTE
# ------------------------------------------------------------
NAVY = "#0f1b2d"
BRAND = "#c8102e"
CLASS_COLORS = {"A": "#c8102e", "B": "#e8890c", "C": "#2f7bbf", "D": "#2e9e6b"}
ZONE_COLORS = {"A": "#1f4e79", "B": "#2f7bbf", "C": "#6aa6d6", "D": "#9bbfdc"}
DONUT = ["#c8102e", "#e8890c", "#2f7bbf", "#2e9e6b", "#7c5cbf", "#94a3b8"]
FONT = "Inter, Segoe UI, system-ui, sans-serif"

# ------------------------------------------------------------
# GLOBAL CSS
# ------------------------------------------------------------
PORTAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
:root{
  --navy:#0f1b2d; --ink:#1c2b3f; --muted:#64748b; --line:#e3e8ef; --bg:#f3f5f9;
  --brand:#c8102e; --brand-2:#a30d25;
  --shadow:0 1px 2px rgba(15,27,45,.04), 0 8px 24px rgba(15,27,45,.05);
}
html, body, .stApp{font-family:'Inter','Segoe UI',system-ui,-apple-system,sans-serif;}
.stApp{background:var(--bg) !important; color:var(--ink); color-scheme:light;}
.stApp button, .stApp input, .stApp textarea{font-family:inherit;}
#MainMenu, footer, [data-testid="stStatusWidget"], .stAppDeployButton{visibility:hidden !important; display:none !important;}
header[data-testid="stHeader"]{background:transparent !important; box-shadow:none !important; height:3rem !important;}
.block-container{padding:1.2rem clamp(1rem,2.6vw,2.4rem) 3rem !important; max-width:1600px;}
div[data-testid="stColumn"]{min-width:0;}

/* ---------- Typography ---------- */
.stApp h1,.stApp h2,.stApp h3,.stApp h4{color:var(--navy); letter-spacing:-.3px; font-weight:800;}
.stApp h3{font-size:1.08rem; display:flex; align-items:center; gap:10px; margin-top:.4rem;}
.stApp h3::before{content:""; width:4px; height:18px; border-radius:4px; background:var(--brand); flex:0 0 4px;}
[data-testid="stWidgetLabel"] p, .stApp label p{color:#334155 !important; font-weight:600 !important; font-size:.82rem !important;}
[data-testid="stCaptionContainer"]{color:var(--muted);}

/* ---------- Form controls ---------- */
.stApp div[data-baseweb="select"] > div,
.stApp div[data-baseweb="input"] > div,
.stApp div[data-baseweb="textarea"] > div{
  background:#fff !important; border:1.5px solid #d7deea !important; border-radius:10px !important;
  min-height:44px; box-shadow:none !important; transition:border-color .15s, box-shadow .15s;
}
.stApp div[data-baseweb="select"] > div:hover,
.stApp div[data-baseweb="input"] > div:hover,
.stApp div[data-baseweb="textarea"] > div:hover{border-color:#a9b6c9 !important;}
.stApp div[data-baseweb="select"] > div:focus-within,
.stApp div[data-baseweb="input"] > div:focus-within,
.stApp div[data-baseweb="textarea"] > div:focus-within{border-color:var(--brand) !important; box-shadow:0 0 0 3px rgba(200,16,46,.12) !important;}
.stApp div[data-baseweb="base-input"]{background:transparent !important;}
.stApp input, .stApp textarea, .stApp div[data-baseweb="select"] span{color:var(--navy) !important;}
span[data-baseweb="tag"]{background:#fdecef !important; border-radius:8px !important;}
span[data-baseweb="tag"] span{color:#a30d25 !important; font-weight:600;}

/* ---------- Buttons ---------- */
.stApp button[kind="primary"], .stApp button[kind="primaryFormSubmit"]{
  background:linear-gradient(180deg,#d9223f,var(--brand-2)) !important; border:0 !important; color:#fff !important;
  border-radius:10px !important; font-weight:700 !important; min-height:44px;
  box-shadow:0 8px 18px rgba(200,16,46,.24) !important; transition:transform .15s, filter .15s;
}
.stApp button[kind="primary"]:hover, .stApp button[kind="primaryFormSubmit"]:hover{transform:translateY(-1px); filter:brightness(1.07);}
.stApp button[kind="secondary"], .stApp button[kind="secondaryFormSubmit"]{
  background:#fff !important; border:1.5px solid #d7deea !important; color:var(--ink) !important;
  border-radius:10px !important; font-weight:650 !important; min-height:42px; transition:border-color .15s, background .15s;
}
.stApp button[kind="secondary"]:hover, .stApp button[kind="secondaryFormSubmit"]:hover{border-color:var(--brand) !important; color:var(--brand) !important; background:#fff7f8 !important;}
.stApp button p{color:inherit !important;}

/* ---------- Alerts / dataframes / forms ---------- */
div[data-testid="stAlert"]{border-radius:12px; border:1px solid var(--line);}
div[data-testid="stDataFrame"]{border:1px solid var(--line); border-radius:14px; overflow:hidden; box-shadow:var(--shadow); background:#fff;}
div[data-testid="stForm"]{background:#fff; border:1px solid var(--line) !important; border-radius:16px; padding:20px 22px; box-shadow:var(--shadow);}
div[data-testid="stPlotlyChart"]{background:#fff; border:1px solid var(--line); border-radius:16px; padding:8px 10px; box-shadow:var(--shadow); overflow:hidden;}
div[data-testid="stVerticalBlockBorderWrapper"]{border-radius:14px;}

/* ---------- Filter bar (any row that contains a multiselect) ---------- */
div[data-testid="stHorizontalBlock"]:has(div[data-testid="stMultiSelect"]){
  background:#fff; border:1px solid var(--line); border-radius:16px; padding:14px 16px 6px; box-shadow:var(--shadow);
}

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#0f1b2d 0%,#0b1624 100%) !important; border-right:1px solid rgba(255,255,255,.06);}
section[data-testid="stSidebar"][aria-expanded="true"]{min-width:276px !important; max-width:min(276px,86vw) !important;}
section[data-testid="stSidebar"] > div:first-child{padding:.9rem .85rem 1rem;}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p, [data-testid="stSidebar"] label p{color:#c7d2e0 !important;}
[data-testid="stSidebarHeader"] button, [data-testid="stSidebarCollapseButton"] button{color:#c7d2e0 !important;}
[data-testid="stSidebarCollapsedControl"] button, [data-testid="collapsedControl"] button{
  background:var(--navy) !important; color:#fff !important; border-radius:12px !important; box-shadow:0 6px 16px rgba(15,27,45,.25);
}
[data-testid="stSidebarCollapsedControl"], [data-testid="collapsedControl"]{z-index:999999 !important;}
.side-brand{display:flex; flex-direction:column; align-items:center; gap:9px; padding:14px; border-radius:16px; margin-bottom:6px;
  background:linear-gradient(145deg,rgba(255,255,255,.08),rgba(255,255,255,.03)); border:1px solid rgba(255,255,255,.10);}
.side-fuso-logo{display:block; width:142px; max-width:80%; height:auto; border-radius:7px; box-shadow:0 5px 14px rgba(0,0,0,.2);}
.side-mark{width:42px; height:42px; flex:0 0 42px; border-radius:11px; display:grid; place-items:center; color:#36d783; font-weight:800; font-size:25px; line-height:1;
  background:rgba(9,18,29,.92); box-shadow:0 0 12px rgba(200,16,46,.3), 0 8px 18px rgba(200,16,46,.24); border:2px solid #e24a5d;}
.side-brand-copy{text-align:center;}
.side-kicker{font-size:9px; font-weight:800; letter-spacing:1.6px; color:#ff6b81; text-transform:uppercase;}
.side-title{font-size:17px; font-weight:800; color:#fff; letter-spacing:-.3px; line-height:1.2;}
.side-title span{color:#ff6b81;}
.nav-section{color:#7f91a7; font-size:10px; font-weight:800; letter-spacing:1.6px; padding:16px 8px 8px;}
[data-testid="stSidebar"] label[data-baseweb="radio"] > div:first-child{display:none !important;}
[data-testid="stSidebar"] div[role="radiogroup"]{gap:3px;}
[data-testid="stSidebar"] div[role="radiogroup"] label{
  width:100%; min-height:42px; padding:9px 12px; border-radius:11px; border:1px solid transparent; cursor:pointer;
  transition:background .15s, border-color .15s;
}
[data-testid="stSidebar"] div[role="radiogroup"] label:hover{background:rgba(255,255,255,.07);}
[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked){
  background:linear-gradient(90deg,rgba(200,16,46,.34),rgba(200,16,46,.10)); border-color:rgba(255,107,129,.28);
  box-shadow:inset 3px 0 0 #ff4d6a;
}
[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) p{color:#fff !important; font-weight:700;}
.side-user{display:flex; align-items:center; gap:11px; padding:12px; margin-top:14px; border-radius:14px; background:rgba(255,255,255,.05); border:1px solid rgba(255,255,255,.09);}
.side-avatar{width:38px; height:38px; flex:0 0 38px; border-radius:50%; display:grid; place-items:center; font-weight:800; color:#fff; background:linear-gradient(145deg,#2f7bbf,#1f4e79);}
.side-info{min-width:0; flex:1;}
.side-name{color:#fff; font-size:13px; font-weight:700; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;}
.side-mail{color:#8fa1b8; font-size:10.5px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;}
.role-pill{font-size:9px; font-weight:800; letter-spacing:1px; padding:4px 8px; border-radius:99px; color:#ffb3bd; background:rgba(200,16,46,.22); border:1px solid rgba(255,107,129,.3);}
.side-status{margin-top:10px; padding:10px 12px; border-radius:12px; background:rgba(255,255,255,.04); border:1px solid rgba(255,255,255,.07); font-size:11px; color:#9fb0c4; line-height:2;}
.side-status div{display:flex; align-items:center; justify-content:space-between; gap:8px;}
.side-status b{color:#e2e8f0; font-weight:600;}
.dot{display:inline-block; width:7px; height:7px; border-radius:50%; margin-right:8px; background:#34d399; box-shadow:0 0 0 3px rgba(52,211,153,.16);}
.dot.warn{background:#f59e0b; box-shadow:0 0 0 3px rgba(245,158,11,.16);}
[data-testid="stSidebar"] button[kind="secondary"]{
  background:rgba(255,255,255,.06) !important; border:1.5px solid rgba(255,255,255,.18) !important; color:#fff !important;
}
[data-testid="stSidebar"] button[kind="secondary"]:hover{background:rgba(200,16,46,.25) !important; border-color:#ff6b81 !important; color:#fff !important;}

/* ---------- Page header ---------- */
.ph{display:flex; align-items:center; gap:16px; margin:4px 0 20px;}
.ph-ico{width:48px; height:48px; flex:0 0 48px; border-radius:14px; display:grid; place-items:center; font-size:22px; background:#fff; border:1px solid var(--line); box-shadow:var(--shadow);}
.ph-text{min-width:0; flex:1;}
.ph-title{font-size:clamp(22px,2.4vw,28px); font-weight:800; color:var(--navy); letter-spacing:-.6px; line-height:1.15;}
.ph-desc{font-size:13px; color:var(--muted); margin-top:3px;}
.ph-date{font-size:11px; font-weight:700; color:#475569; background:#fff; border:1px solid var(--line); border-radius:99px; padding:7px 13px; white-space:nowrap;}

/* ---------- Overview masthead ---------- */
.mast{position:relative; overflow:hidden; border-radius:20px; padding:clamp(22px,3vw,36px); margin:4px 0 22px;
  background:radial-gradient(700px 300px at 90% 0%, rgba(200,16,46,.30), transparent 60%), radial-gradient(600px 300px at 0% 100%, rgba(47,123,191,.25), transparent 60%), linear-gradient(120deg,#0f1b2d 0%,#16293f 60%,#1b3550 100%);
  box-shadow:0 18px 40px rgba(15,27,45,.18); display:flex; justify-content:space-between; align-items:flex-end; gap:22px; flex-wrap:wrap;}
.mast::after{content:""; position:absolute; inset:0; pointer-events:none; opacity:.5;
  background-image:linear-gradient(rgba(255,255,255,.04) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.04) 1px,transparent 1px); background-size:44px 44px;
  -webkit-mask-image:linear-gradient(90deg,transparent,#000); mask-image:linear-gradient(90deg,transparent,#000);}
.mast > *{position:relative; z-index:1;}
.mast-kicker{font-size:10px; font-weight:800; letter-spacing:1.8px; color:#ff8fa0; text-transform:uppercase;}
.mast-title{font-size:clamp(26px,3.2vw,38px); font-weight:800; color:#fff; letter-spacing:-1px; line-height:1.1; margin-top:8px;}
.mast-title span{color:#ff6b81;}
.mast-desc{font-size:13px; color:#b9c8d8; margin-top:8px; max-width:560px; line-height:1.6;}
.mast-chips{display:flex; gap:10px; flex-wrap:wrap;}
.chip{display:inline-flex; align-items:center; gap:8px; padding:9px 14px; border-radius:12px; font-size:12px; font-weight:600; color:#e2e8f0; background:rgba(255,255,255,.08); border:1px solid rgba(255,255,255,.14); backdrop-filter:blur(6px);}
.chip b{color:#fff;}

/* ---------- Section headers / panels ---------- */
.sec{margin:28px 0 12px; display:flex; align-items:baseline; gap:12px; flex-wrap:wrap;}
.sec-title{font-size:15px; font-weight:800; color:var(--navy); display:flex; align-items:center; gap:10px; letter-spacing:.2px;}
.sec-title::before{content:""; width:4px; height:18px; border-radius:4px; background:var(--brand);}
.sec-sub{font-size:12px; color:var(--muted);}
.section-title{font-size:15px; font-weight:800; color:var(--navy); margin:20px 0 10px;}
.panel{background:#fff; border:1px solid var(--line); border-radius:16px; padding:16px 18px; box-shadow:var(--shadow); height:100%;}
.panel-title{font-size:11px; font-weight:800; letter-spacing:1px; color:var(--muted); text-transform:uppercase; margin-bottom:12px;}

/* ---------- KPI cards ---------- */
.tone-blue{--accent:#2563a8; --soft:#eaf2fb;} .tone-red{--accent:#c8102e; --soft:#fdecef;}
.tone-orange{--accent:#d97706; --soft:#fff4e5;} .tone-green{--accent:#15803d; --soft:#e8f6ee;}
.tone-dark{--accent:#0f1b2d; --soft:#eaeef4;} .tone-slate{--accent:#475569; --soft:#eef1f5;}
.kpi-grid{display:grid; grid-template-columns:repeat(auto-fit,minmax(var(--min,190px),1fr)); gap:14px; margin:6px 0 4px;}
.kpi-card{position:relative; overflow:hidden; background:#fff; border:1px solid var(--line); border-radius:16px; padding:16px 18px 16px 20px; box-shadow:var(--shadow); transition:transform .15s, box-shadow .15s;}
.kpi-card:hover{transform:translateY(-2px); box-shadow:0 14px 30px rgba(15,27,45,.09);}
.kpi-card::before{content:""; position:absolute; left:0; top:0; bottom:0; width:4px; background:var(--accent);}
.kpi-top{display:flex; justify-content:space-between; align-items:center; gap:8px;}
.kpi-label{font-size:11px; font-weight:700; letter-spacing:.9px; color:var(--muted); text-transform:uppercase;}
.kpi-ico{width:34px; height:34px; flex:0 0 34px; border-radius:10px; display:grid; place-items:center; font-size:16px; background:var(--soft);}
.kpi-value{font-size:clamp(28px,2.6vw,36px); font-weight:800; color:var(--accent); letter-spacing:-1px; margin-top:10px; line-height:1;}
.kpi-hint{font-size:12px; color:var(--muted); margin-top:8px;}
.tile-grid{display:grid; grid-template-columns:repeat(auto-fit,minmax(92px,1fr)); gap:10px;}
.tile{background:var(--soft); border-radius:12px; padding:12px 10px; text-align:center; border:1px solid rgba(15,27,45,.05);}
.tile-label{font-size:10px; font-weight:800; letter-spacing:.8px; color:var(--muted); text-transform:uppercase;}
.tile-value{font-size:26px; font-weight:800; color:var(--accent); margin-top:4px; letter-spacing:-.6px;}

/* ---------- Tables ---------- */
.dtable{width:100%; border-collapse:collapse; font-size:13px;}
.dtable th{text-align:left; color:var(--muted); font-size:10px; font-weight:800; letter-spacing:.8px; text-transform:uppercase; padding:8px 8px; border-bottom:1px solid var(--line);}
.dtable td{padding:12px 8px; border-bottom:1px solid #eef1f5; color:#334155; font-weight:600; vertical-align:middle;}
.dtable tr:last-child td{border-bottom:0;}
.rank{display:inline-grid; place-items:center; width:26px; height:26px; border-radius:8px; background:#fdecef; color:#a30d25; font-weight:800; font-size:12px;}
.share{display:flex; align-items:center; gap:10px; min-width:110px;}
.share-track{flex:1; height:7px; border-radius:99px; background:#eef1f5; overflow:hidden;}
.share-bar{height:100%; border-radius:99px; background:linear-gradient(90deg,#c8102e,#ff6b81);}
.share span{font-size:12px; color:#475569; min-width:42px; text-align:right;}

/* ---------- Insight (Pareto) ---------- */
.insight{display:flex; gap:16px; align-items:flex-start; background:linear-gradient(135deg,#fff 0%,#fff6f7 100%); border:1px solid #f5c9d0; border-left:5px solid var(--brand); border-radius:16px; padding:18px 20px; margin:6px 0 14px; box-shadow:var(--shadow);}
.insight-ico{width:44px; height:44px; flex:0 0 44px; border-radius:12px; display:grid; place-items:center; background:#fdecef; font-size:20px;}
.insight-kicker{font-size:10px; font-weight:800; letter-spacing:1.5px; color:#a30d25; text-transform:uppercase;}
.insight-main{font-size:clamp(17px,2vw,21px); font-weight:800; color:var(--navy); margin-top:4px; letter-spacing:-.3px;}
.insight-text{font-size:13px; color:#475569; margin-top:6px; line-height:1.55;}
.insight-chips{display:flex; gap:8px; flex-wrap:wrap; margin-top:10px;}
.pill{font-size:11px; font-weight:700; padding:5px 11px; border-radius:99px; background:#fff; border:1px solid #f0c3cb; color:#a30d25;}
.pill.neutral{border-color:var(--line); color:#475569;}

/* ---------- Vision & mission ---------- */
.vision-card{background:#fff; border:1px solid var(--line); border-radius:18px; padding:26px 28px; margin:0 0 16px; box-shadow:var(--shadow);}
.vision-heading{display:flex; align-items:center; gap:12px; color:var(--navy); font-size:18px; font-weight:800; letter-spacing:.6px; margin-bottom:12px;}
.vision-icon{width:34px; height:34px; flex:0 0 34px; border-radius:10px; display:inline-grid; place-items:center; font-size:15px; font-weight:800;}
.vision-icon-red{background:#fdecef; color:#c8102e;} .vision-icon-blue{background:#eaf2fb; color:#2563a8;} .vision-icon-gold{background:#fff4e5; color:#b45309;}
.vision-text{color:#53657a; font-size:15px; line-height:1.85;}
.approach-text{font-weight:700; color:#334e68;}
.leader-photo-wrap{background:#fff; border:1px solid var(--line); border-radius:18px; padding:12px; box-shadow:var(--shadow);}
.leader-photo-wrap img{border-radius:12px;}
.leader-caption{text-align:center; padding:14px 6px 6px;}
.leader-name{font-size:18px; font-weight:800; color:var(--navy);}
.leader-role{font-size:12px; font-weight:700; color:var(--muted); letter-spacing:.6px; margin-top:3px;}

/* ---------- AI assistant ---------- */
.voice-card{border-radius:20px; padding:clamp(20px,3vw,30px); margin:6px 0 18px; color:#fff;
  background:radial-gradient(500px 240px at 95% 0%, rgba(200,16,46,.35), transparent 60%), linear-gradient(130deg,#0f1b2d,#1b3550); box-shadow:0 16px 36px rgba(15,27,45,.16);}
.voice-title{font-size:clamp(20px,2.4vw,26px); font-weight:800; letter-spacing:-.5px;}
.voice-subtitle{font-size:13px; color:#b9c8d8; margin-top:6px; line-height:1.6;}
div[data-testid="stHorizontalBlock"]:has(input[aria-label="POWERED BY FQCM"]){
  background:#fff; border:1.5px solid #d7deea !important; border-radius:16px; padding:6px 12px; box-shadow:var(--shadow); align-items:center;
}
div[data-testid="stHorizontalBlock"]:has(input[aria-label="POWERED BY FQCM"]):focus-within{border-color:var(--brand) !important;}
div[data-testid="stHorizontalBlock"]:has(input[aria-label="POWERED BY FQCM"]) [data-baseweb="input"] > div{border:0 !important; box-shadow:none !important; background:transparent !important;}
.answer-card{background:#fff; border:1px solid var(--line); border-left:5px solid var(--brand); border-radius:16px; padding:18px 22px; margin-top:14px; box-shadow:var(--shadow);}
.answer-label{font-size:10px; color:var(--brand); font-weight:800; letter-spacing:1.5px;}
.answer-text{font-size:16px; color:var(--navy); font-weight:600; margin-top:8px; line-height:1.65;}

/* ---------- User cards ---------- */
.ucard{display:flex; align-items:center; gap:14px;}
.uavatar{width:44px; height:44px; flex:0 0 44px; border-radius:50%; display:grid; place-items:center; font-weight:800; color:#fff; background:linear-gradient(145deg,#2f7bbf,#1f4e79);}
.uname{font-size:15px; font-weight:700; color:var(--navy);} .umail{font-size:12px; color:var(--muted);}

/* ---------- Footer ---------- */
.pf{background:linear-gradient(180deg,#0f1b2d,#0b1624); border-top:4px solid var(--brand); border-radius:18px; padding:28px clamp(18px,3vw,32px) 18px; margin-top:36px; color:#b9c5d4;}
.pf-grid{display:grid; grid-template-columns:minmax(0,1.4fr) repeat(3,minmax(0,1fr)); gap:26px; padding-bottom:20px; border-bottom:1px solid rgba(255,255,255,.12);}
.pf-brand{color:#fff; font-size:15px; font-weight:800; letter-spacing:.5px; line-height:1.45; margin-bottom:10px;}
.pf-head{color:#fff; font-size:13px; font-weight:750; letter-spacing:.6px; text-transform:uppercase; line-height:1.45; margin-bottom:10px;}
.pf-text{font-size:14px; line-height:1.75; color:#b9c5d4; overflow-wrap:normal; word-break:normal;}
.pf-text b{color:#d6dfeb;}
.pf-list{list-style:none; padding:0; margin:0; font-size:14px; line-height:1.75; overflow-wrap:normal; word-break:normal;}
.pf-bottom{display:flex; justify-content:space-between; gap:10px 20px; flex-wrap:wrap; padding-top:14px; font-size:12px; line-height:1.6; color:#9fb0c4;}

/* ---------- Responsive ---------- */
@media (max-width:1000px){
  div[data-testid="stHorizontalBlock"]:has(div[data-testid="stMultiSelect"]){flex-wrap:wrap;}
  div[data-testid="stHorizontalBlock"]:has(div[data-testid="stMultiSelect"]) > div[data-testid="stColumn"]{flex:1 1 calc(50% - 12px) !important; min-width:calc(50% - 12px) !important;}
  .pf-grid{grid-template-columns:1fr 1fr;}
}
@media (max-width:768px){
  .block-container{padding-top:3.4rem !important;}
  .ph-date{display:none;}
}
@media (max-width:640px){
  .block-container{padding-left:.9rem !important; padding-right:.9rem !important;}
  .ph-ico{width:42px; height:42px; flex-basis:42px; font-size:19px;}
  .kpi-grid{grid-template-columns:repeat(2,1fr); gap:10px;}
  .kpi-card{padding:14px 14px 14px 16px;}
  .kpi-ico{display:none;}
  .insight{flex-direction:column; gap:10px;}
  .pf-grid{grid-template-columns:1fr;}
  .mast-chips .chip{font-size:11px; padding:8px 11px;}
  div[data-testid="stHorizontalBlock"]:has(div[data-testid="stMultiSelect"]) > div[data-testid="stColumn"]{flex:1 1 100% !important; min-width:100% !important;}
}
@media (prefers-reduced-motion:reduce){*{transition:none !important;}}
</style>
"""


def inject_portal_css():
    st.session_state["_fig_n"] = 0  # reset the per-run chart counter
    st.markdown(PORTAL_CSS, unsafe_allow_html=True)


# ------------------------------------------------------------
# SMALL HELPERS
# ------------------------------------------------------------
def _now_pk():
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("Asia/Karachi"))
    except Exception:
        return datetime.utcnow() + timedelta(hours=5)


def _fmt(v):
    if isinstance(v, bool):
        return html.escape(str(v))
    if isinstance(v, numbers.Integral):
        return f"{int(v):,}"
    if isinstance(v, numbers.Real):
        return f"{float(v):,.2f}"
    return html.escape(str(v))


def _find(df, names):
    low = {re.sub(r"[^a-z0-9]+", "", str(c).lower()): c for c in df.columns}
    for n in names:
        key = re.sub(r"[^a-z0-9]+", "", n.lower())
        if key in low:
            return low[key]
    return None


def page_title(title, description="", icon=""):
    today = _now_pk().strftime("%a, %d %b %Y")
    ico = f'<div class="ph-ico">{icon}</div>' if icon else ""
    st.markdown(
        f'<div class="ph">{ico}<div class="ph-text"><div class="ph-title">{html.escape(title)}</div>'
        f'<div class="ph-desc">{html.escape(description)}</div></div><div class="ph-date">{today}</div></div>',
        unsafe_allow_html=True,
    )


def section_header(title, subtitle=""):
    sub = f'<div class="sec-sub">{html.escape(subtitle)}</div>' if subtitle else ""
    st.markdown(f'<div class="sec"><div class="sec-title">{html.escape(title)}</div>{sub}</div>', unsafe_allow_html=True)


def kpi_grid(items, min_width=190):
    """items: (label, value, tone, icon, hint)"""
    cards = []
    for it in items:
        label, value, tone = it[0], it[1], it[2]
        icon = it[3] if len(it) > 3 else ""
        hint = it[4] if len(it) > 4 else ""
        cards.append(
            f'<div class="kpi-card tone-{tone}"><div class="kpi-top"><span class="kpi-label">{html.escape(label)}</span>'
            f'<span class="kpi-ico">{icon}</span></div><div class="kpi-value">{_fmt(value)}</div>'
            f'<div class="kpi-hint">{html.escape(hint)}</div></div>'
        )
    st.markdown(f'<div class="kpi-grid" style="--min:{min_width}px">{"".join(cards)}</div>', unsafe_allow_html=True)


def tile_grid(title, items):
    """items: (label, value, tone)"""
    tiles = "".join(
        f'<div class="tile tone-{t}"><div class="tile-label">{html.escape(l)}</div><div class="tile-value">{_fmt(v)}</div></div>'
        for l, v, t in items
    )
    st.markdown(
        f'<div class="panel"><div class="panel-title">{html.escape(title)}</div><div class="tile-grid">{tiles}</div></div>',
        unsafe_allow_html=True,
    )


def insight_card(kicker, headline, qty, pct, text, extra=""):
    chips = f'<span class="pill">{qty:,} units</span><span class="pill">{pct}% of total</span>'
    if extra:
        chips += f'<span class="pill neutral">{html.escape(extra)}</span>'
    st.markdown(
        f'<div class="insight"><div class="insight-ico">🚨</div><div><div class="insight-kicker">{html.escape(kicker)}</div>'
        f'<div class="insight-main">{html.escape(headline)}</div><div class="insight-text">{html.escape(text)}</div>'
        f'<div class="insight-chips">{chips}</div></div></div>',
        unsafe_allow_html=True,
    )


# ------------------------------------------------------------
# CHART HELPERS
# ------------------------------------------------------------
def style_fig(fig, height=360, title=None):
    layout = dict(
        height=height, autosize=True,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, size=12, color="#475569"),
        margin=dict(l=14, r=14, t=62 if title else 18, b=14),
        hoverlabel=dict(bgcolor=NAVY, bordercolor=NAVY, font=dict(color="#ffffff", family=FONT, size=12)),
        legend=dict(orientation="h", y=1.1, x=1, xanchor="right", font=dict(size=11)),
        bargap=0.35,
    )
    if title:
        layout["title"] = dict(text=title, x=0.01, xanchor="left", y=0.96, font=dict(size=15, color=NAVY, family=FONT))
    fig.update_layout(**layout)
    fig.update_xaxes(showgrid=False, linecolor="#e2e8f0", tickfont=dict(size=11), automargin=True)
    fig.update_yaxes(gridcolor="#eef1f5", zeroline=False, tickfont=dict(size=11), automargin=True)
    return fig


def show_fig(fig):
    n = st.session_state.get("_fig_n", 0) + 1
    st.session_state["_fig_n"] = n
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key=f"qfl_fig_{n}")


def simple_bar(labels, values, colors, title, height=320):
    fig = go.Figure(go.Bar(
        x=labels, y=values, marker_color=colors, text=[f"{int(v):,}" for v in values],
        textposition="outside", cliponaxis=False, hovertemplate="%{x}: %{y:,}<extra></extra>",
    ))
    style_fig(fig, height=height, title=title)
    fig.update_layout(showlegend=False, yaxis=dict(range=[0, max([float(v) for v in values] + [1]) * 1.22]))
    return fig


def donut_fig(data, label_col, qty_col, title, height=380):
    total = float(data[qty_col].sum())
    fig = px.pie(data, names=label_col, values=qty_col, hole=0.64, color_discrete_sequence=DONUT)
    fig.update_traces(textinfo="none", sort=False, domain=dict(x=[0.08, 0.92], y=[0.24, 0.92]),
                      marker=dict(line=dict(color="#ffffff", width=2)),
                      hovertemplate="%{label}<br>%{value:,} (%{percent})<extra></extra>")
    style_fig(fig, height=height, title=title)
    fig.update_layout(
        legend=dict(orientation="h", y=0.02, x=0.5, xanchor="center", font=dict(size=11)),
        annotations=[dict(text=f"<b>{int(total):,}</b><br><span style='font-size:11px;color:#64748b'>defects</span>",
                          x=0.5, y=0.58, showarrow=False, font=dict(size=24, color=NAVY, family=FONT))],
    )
    return fig


def pareto_fig(data, label_col, qty_col, title, bar="#2f7bbf", line="#e8890c", height=450):
    d = data.copy()
    total = float(d[qty_col].sum())
    d["cum"] = d[qty_col].cumsum() / total * 100
    colors = [BRAND] + [bar] * (len(d) - 1)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=d[label_col], y=d[qty_col], name="Quantity", marker_color=colors,
                         text=[f"{int(v):,}" for v in d[qty_col]], textposition="outside", cliponaxis=False,
                         hovertemplate="%{x}<br>Qty: %{y:,}<extra></extra>"))
    fig.add_trace(go.Scatter(x=d[label_col], y=d["cum"], name="Cumulative %", mode="lines+markers", yaxis="y2",
                             line=dict(color=line, width=2.6), marker=dict(size=7, line=dict(color="#fff", width=1.5)),
                             hovertemplate="%{x}<br>%{y:.1f}%<extra></extra>"))
    if len(d) >= 2:
        fig.add_trace(go.Scatter(x=[d[label_col].iloc[0], d[label_col].iloc[-1]], y=[80, 80], name="80% line", mode="lines",
                                 yaxis="y2", line=dict(dash="dash", color="#15803d", width=1.6), hoverinfo="skip"))
    style_fig(fig, height=height, title=title)
    fig.update_layout(
        yaxis=dict(title="Quantity", range=[0, float(d[qty_col].max()) * 1.2]),
        yaxis2=dict(overlaying="y", side="right", range=[0, 105], ticksuffix="%", showgrid=False, title="Cumulative %"),
        xaxis=dict(tickangle=-30),
        margin=dict(l=14, r=14, t=70, b=14),
    )
    return fig


def _has_data(df, qty):
    return df is not None and not df.empty and qty in df.columns and df[qty].sum() > 0


# ------------------------------------------------------------
# PAGE HEADERS
# ------------------------------------------------------------
PAGE_META = {
    "🎙️ AI Assistant": ("AI Voice Assistant", "Ask audit questions in English using voice or text."),
    "⚠️ Total Defects": ("Total Defects", "Defect performance and class distribution."),
    "📈 Pareto Analysis": ("Pareto Analysis", "Identify the highest-impact defect types and defect categories."),
    "🚗 Vehicle Audit": ("Vehicle Audit", "Vehicle and chassis-level audit information."),
    "🧩 Class & Zone": ("Class & Zone Analysis", "Compare quality classes and audit zones."),
    "📋 Audit Data": ("Audit Data", "Records from the connected Google Sheet used by the analytics engine."),
}


def overview_masthead(user_email, df):
    now = _now_pk()
    hour = now.hour
    greet = "Good morning" if hour < 12 else ("Good afternoon" if hour < 17 else "Good evening")
    user_name = st.session_state.get("user_name", "")
    name = user_name or (user_email or "").split("@")[0].replace(".", " ").replace("_", " ").title() or "there"
    records = len(df) if df is not None else 0
    date_col = _find(df, ["Date"]) if df is not None and not df.empty else None
    last = ""
    if date_col is not None:
        mx = pd.to_datetime(df[date_col], errors="coerce").max()
        if pd.notna(mx):
            last = mx.strftime("%d %b %Y")
    chips = '<span class="chip"><span class="dot"></span>Live &middot; <b>Google Sheets</b></span>'
    chips += f'<span class="chip">Records <b>{records:,}</b></span>'
    if last:
        chips += f'<span class="chip">Last audit <b>{last}</b></span>'
    st.markdown(
        f'<div class="mast"><div><div class="mast-kicker">Master Motors &middot; FUSO / Quality operations</div>'
        f'<div class="mast-title">{greet}, <span>{html.escape(name)}</span></div>'
        f'<div class="mast-desc">{now.strftime("%A, %d %B %Y")} &mdash; vehicle audit performance, defect concentration and quality classification at a glance.</div></div>'
        f'<div class="mast-chips">{chips}</div></div>',
        unsafe_allow_html=True,
    )


def render_page_header(page, df, user_email=""):
    if page == "🏠 Overview":
        overview_masthead(user_email, df)
    elif page in PAGE_META:
        title, desc = PAGE_META[page]
        page_title(title, desc, page.split(" ")[0])


# ------------------------------------------------------------
# SIDEBAR
# ------------------------------------------------------------
_MOBILE_NAV_JS = """
<script>
const doc = window.parent.document;
const loaderMarkup = __QFL4_PORTAL_LOADING_HTML__;
const loaderId = "qfl4-navigation-loader";
function showLoader(timeoutMs){
  if(doc.getElementById(loaderId)) return;
  const overlay = doc.createElement("div");
  overlay.id = loaderId;
  overlay.innerHTML = loaderMarkup;
  doc.body.appendChild(overlay);
  const main = doc.querySelector('[data-testid="stMain"]');
  if(main){
    let removeTimer;
    const observer = new MutationObserver(function(){
      window.clearTimeout(removeTimer);
      removeTimer = window.setTimeout(function(){
        const activeOverlay = doc.getElementById(loaderId);
        if(activeOverlay) activeOverlay.remove();
        observer.disconnect();
      }, 350);
    });
    observer.observe(main, {childList:true, subtree:true, characterData:true});
  }
  window.setTimeout(function(){
    const activeOverlay = doc.getElementById(loaderId);
    if(activeOverlay) activeOverlay.remove();
  }, timeoutMs || 60000);
}
function bindNav(){
  doc.querySelectorAll('[data-testid="stSidebar"] label[data-testid="stRadioOption"]').forEach(function(l){
    if(l.dataset.qfl) return; l.dataset.qfl = "1";
    l.addEventListener('click', function(){
      const input = l.querySelector('input[type="radio"]');
      if(!input || !input.checked) showLoader();
    }, true);
    l.addEventListener('click', function(){
      if(window.parent.innerWidth <= 768){
        setTimeout(function(){
          var b = doc.querySelector('[data-testid="stSidebarCollapseButton"] button') || doc.querySelector('[data-testid="stSidebarHeader"] button');
          if(b) b.click();
        }, 180);
      }
    });
  });
  doc.querySelectorAll('button[kind="primary"],button[kind="primaryFormSubmit"]').forEach(function(button){
    if(button.dataset.qflLoading) return;
    button.dataset.qflLoading = "1";
    button.addEventListener('click', function(){ showLoader(12000); }, true);
  });
}
const priorLoader = doc.getElementById(loaderId);
if(priorLoader){
  window.setTimeout(function(){
    const activeOverlay = doc.getElementById(loaderId);
    if(activeOverlay) activeOverlay.remove();
  }, 2500);
}
bindNav();
new MutationObserver(bindNav).observe(doc.body, {childList:true, subtree:true});
</script>
""".replace("__QFL4_PORTAL_LOADING_HTML__", json.dumps(PORTAL_LOADING_HTML))

_PAGE_LABELS = {
    "Vision & Mission": "Vision & mission",
    "🏠 Overview": "Overview",
    "🎙️ AI Assistant": "AI assistant",
    "⚠️ Total Defects": "Total defects",
    "📈 Pareto Analysis": "Pareto analysis",
    "🚗 Vehicle Audit": "Vehicle audit",
    "📄 Download Chassis Sheet": "Download chassis sheet",
    "🧩 Class & Zone": "Class & zone",
    "📋 Audit Data": "Audit data",
    "➕ Add Audit Data": "Add audit data",
    "🗑️ Delete Audit Entry": "Delete audit entry",
    "👥 Manage Users": "Manage users",
}


def render_sidebar(nav_pages, user_email, role, ai_ready, records=0):
    name = (user_email or "user").split("@")[0].replace(".", " ").replace("_", " ").title()
    initial = html.escape(name[:1].upper() or "U")
    with st.sidebar:
        st.markdown(
            f'<div class="side-brand"><img class="side-fuso-logo" src="{FUSO_LOGO_DATA_URI}" alt="FUSO logo">'
            '<div class="side-mark" role="img" aria-label="QFL4 logo">&#10003;</div>'
            '<div class="side-brand-copy"><div class="side-kicker">Master Motors &middot; FUSO</div>'
            '<div class="side-title">QFL4 <span>AI</span></div></div></div>'
            '<div class="nav-section">NAVIGATION</div>',
            unsafe_allow_html=True,
        )
        page = st.radio(
            "Pages",
            nav_pages,
            index=nav_pages.index("🏠 Overview"),
            format_func=lambda value: _PAGE_LABELS.get(value, value),
            label_visibility="collapsed",
        )
        ai_dot = "dot" if ai_ready else "dot warn"
        ai_txt = "Ready" if ai_ready else "Key required"
        st.markdown(
            f'<div class="nav-section">ACCOUNT</div>'
            f'<div class="side-user"><div class="side-avatar">{initial}</div><div class="side-info">'
            f'<div class="side-name">{html.escape(name)}</div><div class="side-mail">{html.escape(user_email or "")}</div></div>'
            f'<span class="role-pill">{html.escape(str(role).upper())}</span></div>'
            f'<div class="side-status"><div><span><i class="dot"></i>Google Sheets</span><b>{records:,} rows</b></div>'
            f'<div><span><i class="{ai_dot}"></i>Gemini AI</span><b>{ai_txt}</b></div></div>',
            unsafe_allow_html=True,
        )
        st.write("")
        if st.button("Sign out", use_container_width=True, key="logout_btn"):
            clear_auth_cookie()
            st.session_state.logged_in = False
            st.session_state.role = "user"
            st.session_state.user_email = ""
            st.session_state.user_name = ""
            st.session_state.show_signup = False
            st.session_state.auth_cookie_revoked = True
            st.stop()
        components.html(_MOBILE_NAV_JS, height=0)
    return page


# ------------------------------------------------------------
# PAGE RENDERERS
#   C: columns (defect, category, qty, model, chassis)
#   F: functions (vehicle_count, total_defects, ab_total, calculate_dpu,
#                 class_total, zone_total, build_pareto_summary)
# ------------------------------------------------------------
def _class_zone_values(filtered, F):
    cls = {k: F.class_total(filtered, k) for k in "ABCD"}
    zone = {k: F.zone_total(filtered, k) for k in "ABCD"}
    return cls, zone


def _class_zone_charts(filtered, F):
    cls, zone = _class_zone_values(filtered, F)
    a, b = st.columns(2, gap="medium")
    with a:
        show_fig(simple_bar([f"Class {k}" for k in cls], list(cls.values()), [CLASS_COLORS[k] for k in cls], "Class-wise defect distribution"))
    with b:
        show_fig(simple_bar([f"Zone {k}" for k in zone], list(zone.values()), [ZONE_COLORS[k] for k in zone], "Zone-wise defect distribution"))


def render_overview(filtered, C, F):
    kpi_grid([
        ("Vehicles audited", F.vehicle_count(filtered), "blue", "🚗", "Unique chassis in view"),
        ("Total defects", F.total_defects(filtered), "red", "⚠️", "All classes combined"),
        ("A + B defects", F.ab_total(filtered), "orange", "🔥", "Critical & major findings"),
        ("DPU", F.calculate_dpu(filtered), "dark", "📊", "Defects per unit"),
    ])

    section_header("Class & zone performance", "Defect counts by class and audit zone")
    cls, zone = _class_zone_values(filtered, F)
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        tile_grid("Defect class", [(f"Class {k}", v, {"A": "red", "B": "orange", "C": "blue", "D": "green"}[k]) for k, v in cls.items()])
    with c2:
        tile_grid("Audit zone", [(f"Zone {k}", v, "slate") for k, v in zone.items()])

    ov = F.build_pareto_summary(filtered, C.defect) if C.defect and C.qty else None
    ok = _has_data(ov, C.qty)

    section_header("Defect focus", "Where the quality losses are concentrated")
    left, right = st.columns([1.15, 1], gap="medium")
    with left:
        if ok:
            total = float(ov[C.qty].sum())
            rows = []
            for rank, (_, r) in enumerate(ov.head(5).iterrows(), 1):
                q = int(r[C.qty]); pct = q / total * 100 if total else 0
                rows.append(
                    f'<tr><td><span class="rank">{rank}</span></td><td>{html.escape(str(r[C.defect]))}</td><td><b>{q:,}</b></td>'
                    f'<td><div class="share"><div class="share-track"><div class="share-bar" style="width:{min(pct,100):.1f}%"></div></div><span>{pct:.1f}%</span></div></td></tr>'
                )
            st.markdown(
                '<div class="panel"><div class="panel-title">Top 5 defect types</div><table class="dtable"><thead><tr><th>#</th><th>Defect</th><th>Qty</th><th>Share</th></tr></thead>'
                f'<tbody>{"".join(rows)}</tbody></table></div>', unsafe_allow_html=True)
        else:
            st.info("No defect type data available for the selected filters.")
    with right:
        if ok:
            mix = ov.copy()
            if len(mix) > 5:
                other = pd.DataFrame({C.defect: ["Other"], C.qty: [mix.iloc[5:][C.qty].sum()]})
                mix = pd.concat([mix.head(5), other], ignore_index=True)
            show_fig(donut_fig(mix, C.defect, C.qty, "Defect mix", height=360))
        else:
            st.info("No defect mix available for the selected filters.")

    section_header("Pareto & model performance", "Vital few vs. trivial many, and defects by model")
    p1, p2 = st.columns([1.4, 1], gap="medium")
    with p1:
        if ok:
            show_fig(pareto_fig(ov, C.defect, C.qty, "Pareto - defect types", height=400))
        else:
            st.info("No Pareto data available.")
    with p2:
        if C.model and not filtered.empty:
            m = filtered.copy()
            if C.qty:
                m[C.qty] = pd.to_numeric(m[C.qty], errors="coerce").fillna(0)
                ms = m.groupby(C.model, as_index=False)[C.qty].sum().sort_values(C.qty, ascending=False)
            else:
                ms = m.groupby(C.model).size().reset_index(name="qty").sort_values("qty", ascending=False)
            ms.columns = ["Model", "Total"]
            ms = ms.head(10)
            show_fig(simple_bar(ms["Model"].astype(str).tolist(), ms["Total"].tolist(), ["#2f7bbf"] * len(ms), "Defects by model", height=400))
        else:
            st.info("Model column not available.")

    section_header("Class & zone distribution")
    _class_zone_charts(filtered, F)

    section_header("Chassis-level defect summary", "Top 15 chassis by total defect quantity")
    if C.chassis and not filtered.empty:
        v = filtered.copy()
        v[C.chassis] = v[C.chassis].astype(str)
        if C.qty:
            v[C.qty] = pd.to_numeric(v[C.qty], errors="coerce").fillna(0)
            summ = v.groupby(C.chassis, as_index=False)[C.qty].sum().sort_values(C.qty, ascending=False)
            summ.rename(columns={C.qty: "Total Defects"}, inplace=True)
        else:
            summ = v.groupby(C.chassis).size().reset_index(name="Total Defects").sort_values("Total Defects", ascending=False)
        if C.defect:
            v[C.defect] = v[C.defect].astype(str)
            top = v.groupby(C.chassis)[C.defect].apply(lambda s: ", ".join(pd.Series(s.dropna().astype(str).unique()).head(3))).reset_index(name="Top Defects")
            summ = summ.merge(top, on=C.chassis, how="left")
        summ = summ.head(15)
        mx = max(int(summ["Total Defects"].max()), 1)
        st.dataframe(
            summ, use_container_width=True, hide_index=True, height=min(60 + 36 * len(summ), 600),
            column_config={"Total Defects": st.column_config.ProgressColumn("Total Defects", format="%d", min_value=0, max_value=mx)},
        )
    else:
        st.info("No chassis data available for the selected filters.")


def render_total_defects(filtered, C, F):
    section_header("Key performance indicators")
    kpi_grid([
        ("Vehicles audited", F.vehicle_count(filtered), "blue", "🚗", "Unique chassis"),
        ("Total defects", F.total_defects(filtered), "red", "⚠️", "All classes"),
        ("Class A", F.class_total(filtered, "A"), "red", "🔴", "Critical"),
        ("A + B", F.ab_total(filtered), "orange", "🟠", "Critical & major"),
        ("Class C", F.class_total(filtered, "C"), "blue", "🔵", "Minor"),
        ("Class D", F.class_total(filtered, "D"), "green", "🟢", "Cosmetic"),
        ("DPU", F.calculate_dpu(filtered), "dark", "📊", "Defects per unit"),
    ], min_width=165)
    section_header("Quality distribution", "Class-wise and zone-wise defect totals")
    _class_zone_charts(filtered, F)


def render_class_zone(filtered, C, F):
    cls, zone = _class_zone_values(filtered, F)
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        tile_grid("Defect class", [(f"Class {k}", v, {"A": "red", "B": "orange", "C": "blue", "D": "green"}[k]) for k, v in cls.items()])
    with c2:
        tile_grid("Audit zone", [(f"Zone {k}", v, "slate") for k, v in zone.items()])
    section_header("Quality distribution", "Compare quality classes and audit zones")
    _class_zone_charts(filtered, F)


def _pareto_block(data, label_col, qty, noun, kicker, bar, line):
    if not _has_data(data, qty):
        st.info(f"No {noun} Pareto data available for the current filters.")
        return
    d = data.copy()
    total = float(d[qty].sum())
    top = d.iloc[0]
    q = int(top[qty]); pct = round(q / total * 100, 1) if total else 0
    cum = d[qty].cumsum() / total * 100
    vital = min(int((cum < 80).sum()) + 1, len(d))
    insight_card(kicker, f"Target {noun}: {top[label_col]}", q, pct,
                 f"Immediate corrective action is recommended because this {noun} accounts for the largest share of defects.",
                 extra=f"{vital} of {len(d)} {noun}(s) drive ~80%")
    show_fig(pareto_fig(d, label_col, qty, f"Pareto analysis by {noun}", bar=bar, line=line, height=470))


def render_pareto(filtered, C, F):
    pareto = F.build_pareto_summary(filtered, C.defect) if C.defect and C.qty else None
    pareto_cat = F.build_pareto_summary(filtered, C.category) if C.category and C.qty else None
    section_header("Pareto by defect type", "Highest-priority action item (80/20 focus)")
    _pareto_block(pareto, C.defect, C.qty, "defect type", "Priority action - defect type", "#2f7bbf", "#e8890c")
    section_header("Pareto by defect category", "The vital categories driving most defect occurrences")
    _pareto_block(pareto_cat, C.category, C.qty, "defect category", "Priority action - defect category", "#0ea5e9", "#7c5cbf")


def render_audit_records(filtered, sheet_name):
    section_header("Audit records", f"Showing {len(filtered):,} records from {sheet_name}")
    view = filtered.copy()
    for c in view.columns:
        if pd.api.types.is_datetime64_any_dtype(view[c]):
            view[c] = view[c].dt.strftime("%d %b %Y")
    st.dataframe(view, use_container_width=True, hide_index=True, height=520)
    st.download_button(
        "Download filtered records (CSV)",
        data=filtered.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"QFL4_audit_records_{_now_pk():%Y%m%d}.csv",
        mime="text/csv",
    )


# ------------------------------------------------------------
# USER APPROVALS (admin)
# ------------------------------------------------------------
def render_user_approvals(users, save_users):
    pending = [e for e, i in users.items() if i.get("status") == "pending"]
    approved = [e for e, i in users.items() if i.get("status") == "approved"]
    kpi_grid([
        ("Pending requests", len(pending), "orange", "⏳", "Waiting for approval"),
        ("Approved users", len(approved), "green", "✅", "Active accounts"),
        ("Total accounts", len(users), "blue", "👥", "All registered"),
    ], min_width=200)

    section_header("Pending requests", "Approve or reject new account registrations")
    if not pending:
        st.info("No pending user registration requests right now.")
    for email in pending:
        info = users[email]
        name = info.get("name", "N/A")
        with st.container(border=True):
            c1, c2, c3 = st.columns([4, 1.2, 1.2], vertical_alignment="center")
            with c1:
                st.markdown(
                    f'<div class="ucard"><div class="uavatar">{html.escape(name[:1].upper() or "U")}</div>'
                    f'<div><div class="uname">{html.escape(name)}</div><div class="umail">{html.escape(email)}</div></div></div>',
                    unsafe_allow_html=True)
            with c2:
                if st.button("Approve", key=f"app_{email}", type="primary", use_container_width=True):
                    users[email]["status"] = "approved"
                    save_users(users)
                    st.rerun()
            with c3:
                if st.button("Reject", key=f"rej_{email}", use_container_width=True):
                    del users[email]
                    save_users(users)
                    st.rerun()

    if approved:
        section_header("Approved users")
        rows = [{"Name": users[e].get("name", ""), "Email": e, "Role": str(users[e].get("role", "user")).title()} for e in approved]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# ------------------------------------------------------------
# FOOTER
# ------------------------------------------------------------
def render_footer():
    st.markdown(
        '<div class="pf"><div class="pf-grid">'
        '<div><div class="pf-brand">MASTER MOTORS &bull; FUSO QFL4</div>'
        '<div class="pf-text">Final Quality Control Management &amp; Assembly Plant Intelligence.<br>'
        '<b>Plant:</b> Port Qasim Authority, Karachi<br><b>Dept:</b> Quality Assurance, Health, Safety &amp; Environment</div></div>'
        '<div><div class="pf-head">Commercial vehicles</div><ul class="pf-list"><li>FUSO Canter Light Duty</li><li>FUSO Heavy Trucks</li><li>Master Bus Series</li><li>Specialized Chassis</li></ul></div>'
        '<div><div class="pf-head">Quality standards</div><ul class="pf-list"><li>QFL4 Inspection Protocol</li><li>MFTBC Product Audit</li><li>Defect Class (A, B, C, D)</li><li>DPU Performance Benchmarks</li></ul></div>'
        '<div><div class="pf-head">System &amp; support</div><ul class="pf-list"><li>Gemini AI Assistant</li><li>Pareto Defect Analytics</li><li>Audit Records Dashboard</li><li>User Access Controls</li></ul></div>'
        '</div><div class="pf-bottom"><div>&copy; 2026 Master Motor Corporation Ltd. All rights reserved.</div>'
        '<div>Powered by Google Gemini AI &amp; Streamlit &middot; QFL4 Portal</div></div></div>',
        unsafe_allow_html=True,
    )