"""Cloudflare Workers AI chat client used by PredictAI Phase 6."""
from __future__ import annotations
import os
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Any
import requests

DEFAULT_MODEL = "@cf/meta/llama-3.3-70b-instruct-fp8-fast"


def chat_with_cloudflare(messages: list[dict[str, str]], temperature: float = 0.2, max_tokens: int = 900, timeout: int = 90) -> str:
    """Call Workers AI, enforcing the shared daily quota for regular accounts."""
    task_user = None
    task_date = datetime.now(ZoneInfo(os.getenv("PREDICTAI_QUOTA_TIMEZONE", "Asia/Kolkata"))).date().isoformat()
    task_key = uuid.uuid4().hex
    is_followup = any(m.get("role") == "assistant" for m in (messages or []) if isinstance(m, dict))
    try:
        import streamlit as st
        current_user = st.session_state.get("predictai_user") or {}
    except Exception:
        current_user = {}
    regular_account = bool(current_user.get("username")) and current_user.get("role", "regular") != "owner" and not current_user.get("special_access")
    if regular_account and not is_followup:
        from predictai_core.phase8.accounts import reserve_daily_task, finish_daily_task, daily_task_usage
        task_user = current_user["username"]
        if not reserve_daily_task(task_user, task_date, task_key, int(os.getenv("PREDICTAI_REGULAR_DAILY_TASK_LIMIT", "3"))):
            used = daily_task_usage(task_user, task_date)
            raise RuntimeError(f"Daily PredictAI limit reached: you have used {used} of {os.getenv('PREDICTAI_REGULAR_DAILY_TASK_LIMIT', '3')} new AI tasks today. Follow-up questions in an existing AI conversation do not consume another task. Your allowance resets at midnight ({os.getenv('PREDICTAI_QUOTA_TIMEZONE', 'Asia/Kolkata')}).")
    account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID", "").strip()
    token = os.getenv("CLOUDFLARE_API_TOKEN", "").strip()
    model = os.getenv("CLOUDFLARE_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
    if not account_id or not token:
        if task_user:
            finish_daily_task(task_user, task_date, task_key, False)
        raise RuntimeError("Cloudflare credentials are missing. Add CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN to your .env file.")
    if not messages or any(not isinstance(m, dict) or m.get("role") not in {"system", "user", "assistant"} or not isinstance(m.get("content"), str) for m in messages):
        if task_user:
            finish_daily_task(task_user, task_date, task_key, False)
        raise ValueError("Messages must be a non-empty list of role/content strings.")
    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model}"
    try:
        response = requests.post(url, headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}, json={"messages": messages, "max_tokens": int(max_tokens), "temperature": float(temperature)}, timeout=timeout)
    except requests.Timeout as exc:
        if task_user:
            finish_daily_task(task_user, task_date, task_key, False)
        raise RuntimeError("Cloudflare AI timed out. Try a shorter question or retry later.") from exc
    except requests.RequestException as exc:
        if task_user:
            finish_daily_task(task_user, task_date, task_key, False)
        raise RuntimeError(f"Could not connect to Cloudflare Workers AI: {exc.__class__.__name__}") from exc
    if not response.ok:
        if task_user:
            finish_daily_task(task_user, task_date, task_key, False)
        if response.status_code in (401, 403):
            raise RuntimeError("Cloudflare rejected the API credentials or permissions. Check the account ID and Workers AI token.")
        if response.status_code == 429:
            raise RuntimeError("Cloudflare rate limit or AI quota reached. Check Workers AI usage and retry after the limit resets.")
        raise RuntimeError(f"Cloudflare Workers AI returned HTTP {response.status_code}: {response.text[:500]}")
    try:
        data: dict[str, Any] = response.json()
    except ValueError as exc:
        if task_user:
            finish_daily_task(task_user, task_date, task_key, False)
        raise RuntimeError("Cloudflare returned invalid JSON.") from exc
    result = data.get("result") or {}
    content = None
    if isinstance(result, dict):
        choices = result.get("choices") or []
        if choices:
            content = (choices[0].get("message") or {}).get("content")
        content = content or result.get("response") or result.get("text")
    if not content and isinstance(data.get("response"), str):
        content = data["response"]
    if not isinstance(content, str) or not content.strip():
        if task_user:
            finish_daily_task(task_user, task_date, task_key, False)
        raise RuntimeError("Cloudflare returned an empty or unrecognised model response.")
    if task_user:
        finish_daily_task(task_user, task_date, task_key, True)
    return content.strip()
