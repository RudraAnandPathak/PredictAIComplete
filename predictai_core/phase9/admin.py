from __future__ import annotations

import os
import pandas as pd
import streamlit as st

REGULAR_DOCUMENT_LIMIT = 3
REGULAR_PAGES_PER_DOCUMENT = 100

def _setting(name: str, default: str = "") -> str:
    value = os.getenv(name)
    if value is not None and str(value).strip():
        return str(value).strip()
    try:
        value = st.secrets.get(name, default)
        return str(value).strip() if value is not None else default
    except Exception:
        return default

def require_owner(user: dict | None) -> None:
    if not user or user.get("role") != "owner":
        raise PermissionError("The Owner Command Center is available only to the authenticated owner.")

def get_analytics(actor: dict | None = None):
    from predictai_core.phase8.accounts import get_analytics as account_analytics
    return account_analytics(actor)

def render_owner_dashboard(user: dict):
    from predictai_core.phase8.accounts import list_users, set_special_access, set_blocked, record_event
    require_owner(user)
    st.title("👑 PredictAI Owner Command Center")
    st.caption("Private administrative analytics. Counts reflect events recorded by this application.")
    try:
        data = get_analytics(user)
        users = list_users(user)
    except Exception as exc:
        st.error("The account service could not be reached. No account data was changed.")
        st.caption(str(exc))
        return
    cols = st.columns(4)
    for col, label, key in [
        (cols[0], "Registered users", "registered_users"),
        (cols[1], "Special users", "special_users"),
        (cols[2], "Documents uploaded", "documents_uploaded"),
        (cols[3], "Questions asked", "questions_asked"),
    ]:
        col.metric(label, data.get(key, 0))
    cols2 = st.columns(3)
    cols2[0].metric("Reports generated", data.get("reports_generated", 0))
    cols2[1].metric("AI requests completed", data.get("ai_requests_succeeded", 0))
    cols2[2].metric("AI requests failed", data.get("ai_requests_failed", 0))
    st.info("Usage metrics are based on instrumented events. Older or uninstrumented actions are not included.")
    st.subheader("👥 User Management & Special Access")
    if users:
        st.dataframe(pd.DataFrame(users), use_container_width=True, hide_index=True)
        eligible = [u["username"] for u in users if u.get("role") != "owner"]
        if eligible:
            selected = st.selectbox("Select user", eligible)
            selected_user = next(u for u in users if u["username"] == selected)
            action = st.radio("Special access", ["Grant", "Revoke"], horizontal=True,
                              index=0 if selected_user.get("special_access") else 1)
            if st.button("Apply access change", type="primary"):
                try:
                    set_special_access(user, selected, action == "Grant")
                    record_event(user["username"], "admin_action", f"{action.lower()} special access for {selected}")
                    st.success(f"Special access {action.lower()}ed for {selected}.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
            if "is_blocked" in selected_user:
                block_label = "Unblock account" if selected_user.get("is_blocked") else "Block account"
                if st.button(block_label, key="p9_block_user"):
                    try:
                        set_blocked(user, selected, not bool(selected_user.get("is_blocked")))
                        st.success(f"Account {selected} updated.")
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))
    else:
        st.info("No registered users yet.")
    st.subheader("📈 Daily usage history")
    if data.get("daily_usage"):
        st.dataframe(pd.DataFrame(data["daily_usage"]), use_container_width=True, hide_index=True)
    else:
        st.info("No usage events have been recorded yet.")
    st.subheader("⚙️ Platform configuration status")
    st.write({
        "Cloudflare AI configured": bool(_setting("CLOUDFLARE_ACCOUNT_ID") and _setting("CLOUDFLARE_API_TOKEN")),
        "Special access management": "Owner-granted and revocable",
        "Owner bootstrap secret configured": bool(_setting("PREDICTAI_OWNER_SETUP_SECRET")),
        "Cloudflare D1 account storage configured": bool(_setting("PREDICTAI_API_URL") and _setting("PREDICTAI_API_TOKEN")),
        "Regular-user document limit": REGULAR_DOCUMENT_LIMIT,
        "Pages per regular-user document": REGULAR_PAGES_PER_DOCUMENT,
    })
