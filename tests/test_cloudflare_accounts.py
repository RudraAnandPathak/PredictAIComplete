import json
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[1]


def test_remote_register_login_and_privileged_changes_use_worker_api(monkeypatch):
    from predictai_core.phase8 import accounts

    monkeypatch.setenv("PREDICTAI_ACCOUNT_MODE", "remote")
    monkeypatch.setenv("PREDICTAI_API_URL", "https://accounts.example.workers.dev")
    monkeypatch.setenv("PREDICTAI_API_TOKEN", "test-server-token")
    calls = []

    def post(url, json, headers, timeout):
        calls.append((url, json, headers, timeout))
        if url.endswith("/register"):
            return SimpleNamespace(ok=True, status_code=200, json=lambda: {"user": {"username": json["username"], "role": "regular"}})
        if url.endswith("/login"):
            return SimpleNamespace(ok=True, status_code=200, json=lambda: {"user": {"username": json["username"], "role": "owner", "special_access": False}})
        return SimpleNamespace(ok=True, status_code=200, json=lambda: {"ok": True})

    monkeypatch.setattr("requests.post", post)
    created = accounts.register("member1", "long-password-123", "special", "owner-secret", "m@example.com", "Member Example")
    signed_in = accounts.authenticate("member1", "long-password-123")
    accounts.set_special_access({"username": "owner", "role": "owner"}, "member1", True)
    assert created["username"] == "member1"
    assert signed_in["role"] == "owner"
    assert [c[0].rsplit("/", 1)[1] for c in calls] == ["register", "login", "special-access"]
    assert all(c[2]["Authorization"] == "Bearer test-server-token" for c in calls)
    assert calls[0][1]["password"] == "long-password-123"
    assert "test-server-token" not in json.dumps(calls[0][1])


def test_remote_mode_fails_closed_without_api_instead_of_opening_sqlite(monkeypatch, tmp_path):
    from predictai_core.phase8 import accounts

    monkeypatch.setenv("PREDICTAI_ACCOUNT_MODE", "remote")
    monkeypatch.delenv("PREDICTAI_API_URL", raising=False)
    monkeypatch.delenv("PREDICTAI_API_TOKEN", raising=False)
    monkeypatch.setattr(accounts, "DB_PATH", tmp_path / "should-not-exist.db")
    with pytest.raises(RuntimeError, match="Cloudflare D1 account API is not configured"):
        accounts.register("member", "long-password-123", email="member@example.com", full_legal_name="Member Example")
    with pytest.raises(RuntimeError, match="Cloudflare D1 account API is not configured"):
        accounts.authenticate("member", "long-password-123")
    assert not (tmp_path / "should-not-exist.db").exists()


def test_d1_schema_and_worker_enforce_persistent_account_contract():
    schema = (ROOT / "cloudflare/worker/migrations/0001_accounts.sql").read_text()
    worker = (ROOT / "cloudflare/worker/src/index.js").read_text()
    assert "password_salt TEXT NOT NULL" in schema and "password_hash TEXT NOT NULL" in schema
    assert "owner_state" in schema and "initialized INTEGER NOT NULL DEFAULT 0" in schema
    assert "special_access INTEGER NOT NULL DEFAULT 0" in schema
    assert "PBKDF2" in worker and "310000" in worker
    assert "WHERE (SELECT initialized FROM owner_state WHERE id=1)=0" in worker
    assert "NOT EXISTS(SELECT 1 FROM users WHERE role='owner')" in worker
    assert "db.prepare(" in worker and ".bind(" in worker
    assert "authorization" in worker and "API_TOKEN" in worker
    assert "localStorage" not in worker and "document.cookie" not in worker


def test_worker_does_not_persist_access_codes_or_plaintext_password_columns():
    schema = (ROOT / "cloudflare/worker/migrations/0001_accounts.sql").read_text().lower()
    assert "password TEXT" not in schema
    assert "owner_setup_secret" not in schema
    assert "special_access_code" not in schema
