import streamlit as st

def apply_theme():
    st.markdown('''<style>
    :root { color-scheme: dark; }
    [data-testid="stAppViewContainer"] { background: radial-gradient(ellipse at 10% 0%, #182343 0%, #0b1020 44%, #090d18 100%); }
    [data-testid="stHeader"] { background: rgba(0,0,0,0); }
    [data-testid="stSidebar"] { background: linear-gradient(180deg,#111a30,#0b1020); border-right:1px solid rgba(148,163,184,.18); }
    .main .block-container { max-width: 1440px; padding-top: 2rem; padding-bottom: 4rem; }
    h1,h2,h3 { letter-spacing:-.025em; }
    div[data-testid="stMetric"] { background:rgba(21,31,54,.72); border:1px solid rgba(148,163,184,.18); padding:16px; border-radius:16px; }
    div[data-testid="stForm"], div[data-testid="stExpander"] { border-color:rgba(148,163,184,.24)!important; border-radius:16px!important; }
    .stButton > button, .stFormSubmitButton > button { border-radius:11px; min-height:2.6rem; font-weight:600; }
    .pauth-wrap { max-width:780px; margin:3vh auto; padding:clamp(20px,4vw,42px); border:1px solid rgba(148,163,184,.24); border-radius:24px; background:rgba(15,23,42,.72); box-shadow:0 20px 80px rgba(0,0,0,.24); }
    .pauth-pill { font-size:.65rem; vertical-align:middle; padding:6px 10px; border-radius:999px; color:#c4b5fd; background:rgba(139,92,246,.14); border:1px solid rgba(167,139,250,.28); letter-spacing:.12em; }
    div[data-testid="stDataFrame"] { border:1px solid rgba(148,163,184,.2); border-radius:12px; overflow:hidden; }
    </style>''', unsafe_allow_html=True)
