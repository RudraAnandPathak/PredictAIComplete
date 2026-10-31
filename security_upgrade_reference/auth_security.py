"""PredictAI authentication, email verification, quotas, and audit helpers.
Local/staging security baseline; review deployment-specific controls before public launch.
"""
from __future__ import annotations
import hashlib, hmac, os, re, secrets, smtplib, sqlite3, ssl
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from pathlib import Path

EMAIL_RE = re.compile(r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$")
REGULAR_DOC_LIMIT = 3
REGULAR_PAGE_LIMIT = 100

def utc_now(): return datetime.now(timezone.utc).isoformat(timespec="seconds")
def normalize_email(email): return (email or "").strip().lower()
def is_valid_email(email):
    email=normalize_email(email); return len(email)<=254 and bool(EMAIL_RE.fullmatch(email))
def _db_path(): return os.environ.get("PREDICTAI_AUTH_DB", str(Path(__file__).resolve().parent / "predictai_auth.db"))
@contextmanager
def connect_db():
    db=sqlite3.connect(_db_path(),timeout=20); db.row_factory=sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON"); db.execute("PRAGMA journal_mode=WAL")
    try:
        yield db; db.commit()
    except Exception:
        db.rollback(); raise
    finally: db.close()
def init_auth_db():
    with connect_db() as db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,full_name TEXT NOT NULL,email TEXT NOT NULL UNIQUE,username TEXT NOT NULL UNIQUE,password_hash TEXT NOT NULL,role TEXT NOT NULL DEFAULT 'Regular User' CHECK(role IN ('Owner','Special User','Regular User')),status TEXT NOT NULL DEFAULT 'pending_verification' CHECK(status IN ('pending_verification','active','blocked')),email_verified INTEGER NOT NULL DEFAULT 0 CHECK(email_verified IN (0,1)),created_at TEXT NOT NULL,updated_at TEXT NOT NULL,blocked_at TEXT,blocked_by TEXT);
        CREATE TABLE IF NOT EXISTS auth_audit_log(id INTEGER PRIMARY KEY AUTOINCREMENT,actor_username TEXT,target_user_id INTEGER,action TEXT NOT NULL,details TEXT,created_at TEXT NOT NULL,FOREIGN KEY(target_user_id) REFERENCES users(id));
        CREATE TABLE IF NOT EXISTS email_verification_tokens(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,token_hash TEXT NOT NULL UNIQUE,expires_at TEXT NOT NULL,used_at TEXT,created_at TEXT NOT NULL,FOREIGN KEY(user_id) REFERENCES users(id));
        CREATE TABLE IF NOT EXISTS usage_events(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,event_type TEXT NOT NULL,resource_hash TEXT,details TEXT,created_at TEXT NOT NULL,FOREIGN KEY(user_id) REFERENCES users(id));
        CREATE UNIQUE INDEX IF NOT EXISTS idx_usage_unique_upload ON usage_events(user_id,resource_hash) WHERE event_type='document_uploaded' AND resource_hash IS NOT NULL;
        CREATE INDEX IF NOT EXISTS idx_users_status ON users(status); CREATE INDEX IF NOT EXISTS idx_usage_created ON usage_events(created_at);
        ''')
def _audit(db, actor, uid, action, details=''):
    db.execute('INSERT INTO auth_audit_log(actor_username,target_user_id,action,details,created_at) VALUES(?,?,?,?,?)',(actor,uid,action,(details or '')[:500],utc_now()))
def hash_password(password):
    if not isinstance(password,str) or len(password)<12: raise ValueError('Use a password with at least 12 characters.')
    if len(password)>1024: raise ValueError('Password is too long.')
    salt=secrets.token_bytes(16); rounds=600_000
    digest=hashlib.pbkdf2_hmac('sha256',password.encode(),salt,rounds)
    return f'pbkdf2_sha256${rounds}${salt.hex()}${digest.hex()}'
def verify_password(password, stored_hash):
    try:
        scheme,rounds,salt,digest=stored_hash.split('$',3)
        if scheme!='pbkdf2_sha256': return False
        test=hashlib.pbkdf2_hmac('sha256',password.encode(),bytes.fromhex(salt),int(rounds)).hex()
        return hmac.compare_digest(test,digest)
    except (ValueError,TypeError,AttributeError): return False
def create_pending_user(full_name,email,username,password):
    full_name=(full_name or '').strip(); email=normalize_email(email); username=(username or '').strip()
    if not full_name or len(full_name)>120: return False,'Enter a name (maximum 120 characters).'
    if not is_valid_email(email): return False,'Enter a valid email address.'
    if not re.fullmatch(r'[A-Za-z0-9_.-]{3,32}',username): return False,'Username must be 3–32 characters: letters, numbers, _, . or -.'
    try: ph=hash_password(password)
    except ValueError as e: return False,str(e)
    now=utc_now()
    try:
        with connect_db() as db:
            cur=db.execute("INSERT INTO users(full_name,email,username,password_hash,role,status,email_verified,created_at,updated_at) VALUES(?,?,?,?, 'Regular User','pending_verification',0,?,?)",(full_name,email,username,ph,now,now))
            _audit(db,None,cur.lastrowid,'registration_created','Pending email verification')
        return True,'Account created. Check your email for a verification link.'
    except sqlite3.IntegrityError: return False,'That email address or username is already registered.'
def _smtp_configured(): return bool(os.getenv('PREDICTAI_SMTP_HOST') and os.getenv('PREDICTAI_SMTP_FROM'))
def send_verification_email(user_id,email,username):
    if not _smtp_configured(): return False,'Email delivery is not configured. Set the SMTP variables in .env first.'
    token=secrets.token_urlsafe(32); token_hash=hashlib.sha256(token.encode()).hexdigest(); now=datetime.now(timezone.utc); exp=(now+timedelta(minutes=30)).isoformat(timespec='seconds')
    with connect_db() as db:
        recent=db.execute("SELECT created_at FROM email_verification_tokens WHERE user_id=? ORDER BY id DESC LIMIT 1",(user_id,)).fetchone()
        if recent:
            try:
                if now-datetime.fromisoformat(recent['created_at'])<timedelta(minutes=1): return False,'Please wait one minute before requesting another verification email.'
            except ValueError: pass
        db.execute('INSERT INTO email_verification_tokens(user_id,token_hash,expires_at,created_at) VALUES(?,?,?,?)',(user_id,token_hash,exp,now.isoformat(timespec='seconds')))
    base=os.getenv('PREDICTAI_PUBLIC_URL','http://localhost:8501').rstrip('/')
    link=f'{base}/?verify={token}'
    msg=EmailMessage(); msg['Subject']='Verify your PredictAI account'; msg['From']=os.getenv('PREDICTAI_SMTP_FROM'); msg['To']=email
    msg.set_content(f'Hello {username},\n\nVerify your PredictAI account within 30 minutes using this link:\n{link}\n\nIf you did not create this account, ignore this message.')
    host=os.getenv('PREDICTAI_SMTP_HOST'); port=int(os.getenv('PREDICTAI_SMTP_PORT','587')); user=os.getenv('PREDICTAI_SMTP_USER'); password=os.getenv('PREDICTAI_SMTP_PASSWORD')
    try:
        if os.getenv('PREDICTAI_SMTP_SSL','false').lower()=='true':
            with smtplib.SMTP_SSL(host,port,context=ssl.create_default_context(),timeout=20) as s:
                if user: s.login(user,password or '')
                s.send_message(msg)
        else:
            with smtplib.SMTP(host,port,timeout=20) as s:
                s.ehlo()
                if os.getenv('PREDICTAI_SMTP_STARTTLS','true').lower()=='true': s.starttls(context=ssl.create_default_context()); s.ehlo()
                if user: s.login(user,password or '')
                s.send_message(msg)
        return True,'Verification email sent.'
    except Exception as e: return False,f'Could not send email ({type(e).__name__}). Check SMTP configuration.'
def verify_email_token(token):
    if not token: return False,'Missing verification token.'
    th=hashlib.sha256(token.encode()).hexdigest(); now=datetime.now(timezone.utc)
    with connect_db() as db:
        row=db.execute('SELECT id,user_id,expires_at,used_at FROM email_verification_tokens WHERE token_hash=?',(th,)).fetchone()
        if not row or row['used_at']: return False,'This verification link is invalid or already used.'
        try: expired=datetime.fromisoformat(row['expires_at'])<now
        except ValueError: expired=True
        if expired: return False,'This verification link has expired. Request a new one.'
        db.execute("UPDATE email_verification_tokens SET used_at=? WHERE id=?",(now.isoformat(timespec='seconds'),row['id']))
        db.execute("UPDATE users SET email_verified=1,status='active',updated_at=? WHERE id=? AND status='pending_verification'",(now.isoformat(timespec='seconds'),row['user_id']))
        _audit(db,None,row['user_id'],'email_verified','Email verification completed')
    return True,'Email verified. You can now sign in.'
def get_user_by_email_or_username(key):
    with connect_db() as db:
        r=db.execute('SELECT * FROM users WHERE lower(username)=lower(?) OR lower(email)=lower(?)',(key,key)).fetchone()
    return dict(r) if r else None
def authenticate_user(key,password):
    row=get_user_by_email_or_username((key or '').strip())
    if not row or not verify_password(password,row['password_hash']): return False,'Incorrect username/email or password.',None
    if row['status']=='blocked': return False,'This account is blocked. Contact the administrator.',None
    if row['status']!='active' or not row['email_verified']: return False,'Verify your email before signing in.',None
    with connect_db() as db: _audit(db,row['username'],row['id'],'login_success','')
    return True,'Signed in successfully.',{k:row[k] for k in ('id','full_name','email','username','role','status')}
def get_user_by_id(uid):
    with connect_db() as db: r=db.execute('SELECT id,full_name,email,username,role,status,email_verified,created_at,updated_at,blocked_at,blocked_by FROM users WHERE id=?',(int(uid),)).fetchone()
    return dict(r) if r else None
def require_active_session():
    import streamlit as st
    uid=st.session_state.get('user_id')
    if uid is None: return False,'Please sign in.'
    u=get_user_by_id(uid)
    if not u or u['status']!='active' or not u['email_verified']:
        for k in ('user_id','username','email','full_name','role','authenticated'): st.session_state.pop(k,None)
        return False,'Your session is no longer active. Please sign in again.'
    st.session_state['role']=u['role']; return True,'OK'
def create_owner_account(full_name,email,username,password):
    try: ph=hash_password(password)
    except ValueError as e: return False,str(e)
    now=utc_now()
    try:
        with connect_db() as db:
            cur=db.execute("INSERT INTO users(full_name,email,username,password_hash,role,status,email_verified,created_at,updated_at) VALUES(?,?,?,?, 'Owner','active',1,?,?)",((full_name or '').strip(),normalize_email(email),(username or '').strip(),ph,now,now))
            _audit(db,username,cur.lastrowid,'owner_provisioned','Created via local provisioning CLI')
        return True,'Owner account created.'
    except sqlite3.IntegrityError: return False,'Email or username already exists.'
def record_event(uid,event_type,resource_hash=None,details=''):
    with connect_db() as db:
        if event_type=='document_uploaded' and resource_hash:
            db.execute('INSERT OR IGNORE INTO usage_events(user_id,event_type,resource_hash,details,created_at) VALUES(?,?,?,?,?)',(uid,event_type,resource_hash,details[:500],utc_now()))
        else: db.execute('INSERT INTO usage_events(user_id,event_type,resource_hash,details,created_at) VALUES(?,?,?,?,?)',(uid,event_type,resource_hash,details[:500],utc_now()))
def get_usage(uid):
    with connect_db() as db:
        docs=db.execute("SELECT COUNT(*) n FROM usage_events WHERE user_id=? AND event_type='document_uploaded'",(uid,)).fetchone()['n']
        questions=db.execute("SELECT COUNT(*) n FROM usage_events WHERE user_id=? AND event_type='question_asked'",(uid,)).fetchone()['n']
        ai=db.execute("SELECT COUNT(*) n FROM usage_events WHERE user_id=? AND event_type='ai_request_completed'",(uid,)).fetchone()['n']
        failed=db.execute("SELECT COUNT(*) n FROM usage_events WHERE user_id=? AND event_type='ai_request_failed'",(uid,)).fetchone()['n']
    return {'documents':docs,'questions':questions,'ai_completed':ai,'ai_failed':failed}
def owner_metrics():
    with connect_db() as db:
        users=db.execute("SELECT role,status,COUNT(*) n FROM users GROUP BY role,status").fetchall()
        totals=db.execute("SELECT event_type,COUNT(*) n FROM usage_events GROUP BY event_type").fetchall()
        daily=db.execute("SELECT substr(created_at,1,10) day,event_type,COUNT(*) n FROM usage_events WHERE created_at>=datetime('now','-30 days') GROUP BY day,event_type ORDER BY day").fetchall()
        recent=db.execute("SELECT u.username,e.event_type,e.details,e.created_at FROM usage_events e JOIN users u ON u.id=e.user_id ORDER BY e.id DESC LIMIT 100").fetchall()
    return [dict(x) for x in users],[dict(x) for x in totals],[dict(x) for x in daily],[dict(x) for x in recent]
