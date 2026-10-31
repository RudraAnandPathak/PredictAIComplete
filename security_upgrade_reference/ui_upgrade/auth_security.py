"""Security helpers for PredictAI integration. Adapt to your existing account store."""
from __future__ import annotations
import hashlib, hmac, os, re, secrets, sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Optional

EMAIL_RE = re.compile(r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$")
def utc_now(): return datetime.now(timezone.utc).isoformat(timespec="seconds")
def normalize_email(email): return (email or "").strip().lower()
def is_valid_email(email):
    email = normalize_email(email)
    return len(email) <= 254 and bool(EMAIL_RE.fullmatch(email))
def _db_path(): return os.environ.get("PREDICTAI_AUTH_DB", str(Path.cwd() / "predictai_auth.db"))

@contextmanager
def connect_db() -> Iterator[sqlite3.Connection]:
    db = sqlite3.connect(_db_path(), timeout=15)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("PRAGMA journal_mode=WAL")
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally: db.close()

def init_auth_db():
    with connect_db() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
          id INTEGER PRIMARY KEY AUTOINCREMENT, full_name TEXT NOT NULL,
          email TEXT NOT NULL UNIQUE, username TEXT NOT NULL UNIQUE,
          password_hash TEXT NOT NULL,
          role TEXT NOT NULL DEFAULT 'Regular User' CHECK(role IN ('Owner','Special User','Regular User')),
          status TEXT NOT NULL DEFAULT 'pending_verification' CHECK(status IN ('pending_verification','active','blocked')),
          email_verified INTEGER NOT NULL DEFAULT 0 CHECK(email_verified IN (0,1)),
          created_at TEXT NOT NULL, updated_at TEXT NOT NULL, blocked_at TEXT, blocked_by TEXT
        );
        CREATE TABLE IF NOT EXISTS auth_audit_log (
          id INTEGER PRIMARY KEY AUTOINCREMENT, actor_username TEXT, target_user_id INTEGER,
          action TEXT NOT NULL, details TEXT, created_at TEXT NOT NULL,
          FOREIGN KEY(target_user_id) REFERENCES users(id)
        );
        CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
        """)
        db.commit()

def hash_password(password: str) -> str:
    if not isinstance(password, str) or len(password) < 12:
        raise ValueError("Use a password with at least 12 characters.")
    salt = secrets.token_bytes(16); iterations = 600_000
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
    return f"pbkdf2_sha256${iterations}${salt.hex()}${digest.hex()}"

def verify_password(password: str, stored_hash: str) -> bool:
    try:
        scheme, rounds, salt, digest = stored_hash.split("$", 3)
        if scheme != "pbkdf2_sha256": return False
        candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), int(rounds)).hex()
        return hmac.compare_digest(candidate, digest)
    except (ValueError, TypeError, AttributeError): return False

def create_pending_user(full_name: str, email: str, username: str, password: str):
    """Creates a pending account only. Does not send verification email."""
    full_name, email, username = (full_name or "").strip(), normalize_email(email), (username or "").strip()
    if not full_name: return False, "Enter your full name."
    if not is_valid_email(email): return False, "Enter a valid email address."
    if not re.fullmatch(r"[A-Za-z0-9_.-]{3,32}", username):
        return False, "Username must be 3–32 characters (letters, numbers, _, ., -)."
    try: password_hash = hash_password(password)
    except ValueError as exc: return False, str(exc)
    now = utc_now()
    try:
        with connect_db() as db:
            cur = db.execute("""INSERT INTO users(full_name,email,username,password_hash,role,status,email_verified,created_at,updated_at)
                VALUES(?,?,?,?, 'Regular User','pending_verification',0,?,?)""",
                (full_name,email,username,password_hash,now,now))
            db.execute("INSERT INTO auth_audit_log(actor_username,target_user_id,action,details,created_at) VALUES(NULL,?,'registration_pending','Email verification not configured',?)",(cur.lastrowid,now))
        return True, "Account created but not active. Configure and complete email verification before access is granted."
    except sqlite3.IntegrityError: return False, "That email address or username is already registered."

def authenticate_user(username_or_email: str, password: str):
    key = (username_or_email or "").strip()
    with connect_db() as db:
        row = db.execute("""SELECT id,full_name,email,username,password_hash,role,status,email_verified
            FROM users WHERE lower(username)=lower(?) OR lower(email)=lower(?)""",(key,key)).fetchone()
    if not row or not verify_password(password,row["password_hash"]):
        return False,"Incorrect username/email or password.",None
    if row["status"] == "blocked": return False,"This account has been blocked. Contact the administrator.",None
    if row["status"] != "active" or not row["email_verified"]:
        return False,"Account not active. Complete email verification first.",None
    return True,"Signed in successfully.",{k:row[k] for k in ("id","full_name","email","username","role","status")}

def get_user_by_id(user_id: int) -> Optional[dict]:
    with connect_db() as db:
        row=db.execute("SELECT id,full_name,email,username,role,status,email_verified,created_at,updated_at,blocked_at,blocked_by FROM users WHERE id=?",(int(user_id),)).fetchone()
    return dict(row) if row else None

def require_active_session():
    """Re-check DB status on each protected rerun to catch blocked active sessions."""
    try:
        import streamlit as st
        user_id=st.session_state.get("user_id")
        if user_id is None: return False,"Please sign in."
        user=get_user_by_id(int(user_id))
        if not user or user["status"] != "active" or not user["email_verified"]:
            for key in ("user_id","username","email","full_name","role","authenticated"):
                st.session_state.pop(key,None)
            return False,"Session is no longer active. Please sign in again."
        return True,"OK"
    except Exception: return False,"Could not validate the current session."
