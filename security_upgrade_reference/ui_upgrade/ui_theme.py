"""Optional modern visual theme helpers for Streamlit."""
import streamlit as st

CSS = """
<style>
:root{--pa-bg:#0b1020;--pa-panel:#121a2b;--pa-text:#f2f5fb;--pa-muted:#a8b4c8;--pa-accent:#7c9cff;--pa-teal:#52d6c7;--pa-border:rgba(164,184,220,.18)}
.stApp{background:radial-gradient(ellipse at 12% 0%,rgba(83,112,218,.15),transparent 35%),radial-gradient(ellipse at 90% 5%,rgba(55,196,182,.09),transparent 28%),var(--pa-bg);color:var(--pa-text)}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#10192b,#0d1424);border-right:1px solid var(--pa-border)}
.block-container{max-width:1220px;padding-top:2rem;padding-bottom:3rem}
h1,h2,h3{letter-spacing:-.025em}
div[data-testid="stMetric"]{background:rgba(23,34,56,.76);border:1px solid var(--pa-border);padding:1rem;border-radius:16px}
div[data-testid="stButton"]>button{border-radius:10px;border:1px solid var(--pa-border);min-height:2.6rem}
div[data-testid="stTextInput"] input,div[data-testid="stTextArea"] textarea{border-radius:10px}
.pa-hero{padding:2rem 2.2rem;border-radius:22px;border:1px solid var(--pa-border);background:linear-gradient(135deg,rgba(124,156,255,.16),rgba(82,214,199,.08));margin-bottom:1.2rem}
.pa-eyebrow{color:var(--pa-teal);text-transform:uppercase;letter-spacing:.13em;font-size:.76rem;font-weight:700}
.pa-muted{color:var(--pa-muted)}
.pa-card{padding:1.1rem 1.2rem;border-radius:16px;background:rgba(18,26,43,.8);border:1px solid var(--pa-border);height:100%}
@media(max-width:700px){.block-container{padding-left:1rem;padding-right:1rem}.pa-hero{padding:1.3rem;border-radius:16px}}
</style>"""

def apply_theme():
    st.markdown(CSS, unsafe_allow_html=True)

def render_hero(title, subtitle, eyebrow="PREDICTAI WORKSPACE"):
    st.markdown(f'<section class="pa-hero"><div class="pa-eyebrow">{eyebrow}</div><h1>{title}</h1><p class="pa-muted">{subtitle}</p></section>',unsafe_allow_html=True)

def render_feature_cards():
    items=[("Document intelligence","Upload documents and get structured, explainable insights."),
           ("Dataset analysis","Explore patterns, statistics, relationships, and predictions."),
           ("AI workspace","Ask follow-up questions and turn findings into useful reports.")]
    cols=st.columns(3)
    for col,(title,body) in zip(cols,items):
        with col: st.markdown(f'<div class="pa-card"><h3>{title}</h3><p class="pa-muted">{body}</p></div>',unsafe_allow_html=True)
