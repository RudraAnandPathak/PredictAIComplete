"""Illustrative UI only. Do not replace your existing app.py with this file."""
import streamlit as st
from auth_security import init_auth_db, create_pending_user, authenticate_user, require_active_session
from user_management import list_users, block_user, unblock_user, audit_log
from ui_theme import apply_theme, render_hero, render_feature_cards

st.set_page_config(page_title="PredictAI",page_icon="🔮",layout="wide")
apply_theme()
init_auth_db()

def sign_out():
    for key in ("user_id","username","email","full_name","role","authenticated"): st.session_state.pop(key,None)
    st.rerun()

def login_page():
    render_hero("Your AI workspace, made clearer.","Analyse documents, explore data, and turn questions into insights.")
    a,b=st.tabs(["Sign in","Create account"])
    with a:
        with st.form("login"):
            key=st.text_input("Username or email"); password=st.text_input("Password",type="password")
            go=st.form_submit_button("Sign in",use_container_width=True)
        if go:
            ok,msg,user=authenticate_user(key,password)
            if ok:
                st.session_state.update({"user_id":user["id"],"username":user["username"],"email":user["email"],"full_name":user["full_name"],"role":user["role"],"authenticated":True})
                st.rerun()
            else: st.error(msg)
    with b:
        st.info("New accounts stay pending until real email verification is configured.")
        with st.form("register"):
            name=st.text_input("Full name"); email=st.text_input("Email address"); username=st.text_input("Username")
            password=st.text_input("Password (12+ characters)",type="password"); confirm=st.text_input("Confirm password",type="password")
            accepted=st.checkbox("I agree to the terms and privacy notice")
            go=st.form_submit_button("Create account",use_container_width=True)
        if go:
            if password!=confirm: st.error("Passwords do not match.")
            elif not accepted: st.error("Please accept the terms and privacy notice.")
            else:
                ok,msg=create_pending_user(name,email,username,password)
                (st.success if ok else st.error)(msg)

def protected_page():
    valid,msg=require_active_session()
    if not valid: sign_out()
    user=st.session_state
    with st.sidebar:
        st.markdown("## 🔮 PredictAI"); st.caption(f"@{user.get('username','user')}"); st.caption(user.get("email",""))
        page=st.radio("Workspace",["Overview","Owner · Users","Owner · Audit log"])
        st.button("Sign out",on_click=sign_out,use_container_width=True)
    if page=="Overview":
        render_hero(f"Welcome, {user.get('full_name','there')}.","Your workspace for document intelligence and data-driven insights.")
        render_feature_cards()
        st.info("Integrate your existing document analysis, dataset analysis, AI, and report pages into this layout.")
    elif user.get("role")!="Owner":
        st.error("Owner permissions are required.")
    elif page=="Owner · Users":
        render_hero("User management","Search accounts and manage access.","OWNER COMMAND CENTER")
        search=st.text_input("Search by name, email, or username")
        status=st.selectbox("Status",["All","active","pending_verification","blocked"])
        role=st.selectbox("Role",["All","Regular User","Special User","Owner"])
        for account in list_users(search,status,role):
            with st.container(border=True):
                c1,c2,c3=st.columns([3,2,1])
                with c1: st.markdown(f"**{account['full_name']}** · @{account['username']}"); st.caption(account["email"])
                with c2: st.write(f"Role: {account['role']}"); st.write(f"Status: {account['status']}")
                with c3:
                    if account["role"]=="Owner": st.caption("Protected owner")
                    elif account["status"]=="blocked":
                        if st.button("Unblock",key=f"u{account['id']}"):
                            ok,msg=unblock_user(account["id"],user["username"]); (st.success if ok else st.error)(msg); st.rerun()
                    else:
                        if st.button("Block",key=f"b{account['id']}"):
                            st.session_state[f"confirm_{account['id']}"]=True
                        if st.session_state.get(f"confirm_{account['id']}"):
                            if st.button("Confirm block",key=f"c{account['id']}"):
                                ok,msg=block_user(account["id"],user["username"],"Owner Command Center"); st.session_state.pop(f"confirm_{account['id']}",None); (st.success if ok else st.error)(msg); st.rerun()
                            if st.button("Cancel",key=f"x{account['id']}"):
                                st.session_state.pop(f"confirm_{account['id']}",None); st.rerun()
    else:
        render_hero("Security audit log","Review recent account-management events.","OWNER COMMAND CENTER")
        st.dataframe(audit_log(),use_container_width=True,hide_index=True)

if st.session_state.get("user_id"): protected_page()
else: login_page()
