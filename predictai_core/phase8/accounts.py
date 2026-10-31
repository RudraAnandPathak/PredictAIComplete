from __future__ import annotations
import hashlib, hmac, os, secrets, sqlite3
from pathlib import Path
from typing import Any
ITERATIONS=310_000
DB_PATH=Path(os.getenv('PREDICTAI_ACCOUNTS_DB',str(Path.home()/'.predictai'/'accounts.db'))).expanduser()
_ALLOWED_EVENTS={'registration','document_upload','question_asked','report_generated','ai_success','ai_error','login','admin_action'}
def _setting(name:str,default:str='')->str:
 v=os.getenv(name)
 if v is not None and str(v).strip(): return str(v).strip()
 try:
  import streamlit as st
  v=st.secrets.get(name,default); return str(v).strip() if v is not None else default
 except Exception:return default
def _remote_enabled()->bool:return bool(_setting('PREDICTAI_API_URL') and _setting('PREDICTAI_API_TOKEN'))
def _api(path:str,payload:dict[str,Any]|None=None)->dict[str,Any]:
 import requests
 token=_setting('PREDICTAI_API_TOKEN')
 if not token: raise RuntimeError('PREDICTAI_API_TOKEN is not configured.')
 try:r=requests.post(_setting('PREDICTAI_API_URL').rstrip('/')+'/'+path.lstrip('/'),json=payload or {},headers={'Authorization':f'Bearer {token}','Content-Type':'application/json'},timeout=(5,20))
 except requests.RequestException as e:raise RuntimeError('PredictAI account service is temporarily unavailable.') from e
 try:d=r.json()
 except ValueError:d={}
 if not r.ok:
  m=d.get('error') or f'Account service returned HTTP {r.status_code}.'
  if r.status_code in (400,401,403,404,409,429):raise ValueError(str(m))
  raise RuntimeError(str(m))
 return d
def _connect():
 if _remote_enabled():raise RuntimeError('Direct SQLite access is disabled in Cloudflare mode.')
 DB_PATH.parent.mkdir(parents=True,exist_ok=True);c=sqlite3.connect(DB_PATH);c.row_factory=sqlite3.Row
 c.execute("CREATE TABLE IF NOT EXISTS users(username TEXT PRIMARY KEY COLLATE NOCASE,salt TEXT NOT NULL,password_hash TEXT NOT NULL,special_access INTEGER NOT NULL DEFAULT 0,role TEXT NOT NULL DEFAULT 'regular',created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,email TEXT,full_legal_name TEXT,is_blocked INTEGER NOT NULL DEFAULT 0)")
 cols={r['name'] for r in c.execute('PRAGMA table_info(users)')}
 for col,ddl in [('role',"ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'regular'"),('email','ALTER TABLE users ADD COLUMN email TEXT'),('full_legal_name','ALTER TABLE users ADD COLUMN full_legal_name TEXT'),('is_blocked','ALTER TABLE users ADD COLUMN is_blocked INTEGER NOT NULL DEFAULT 0')]:
  if col not in cols:c.execute(ddl)
 c.execute("CREATE TABLE IF NOT EXISTS daily_ai_tasks(id INTEGER PRIMARY KEY AUTOINCREMENT,username TEXT NOT NULL COLLATE NOCASE,task_date TEXT NOT NULL,task_key TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'reserved',created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,UNIQUE(username,task_date,task_key))")
 c.execute("CREATE TABLE IF NOT EXISTS usage_events(id INTEGER PRIMARY KEY AUTOINCREMENT,username TEXT,event_type TEXT NOT NULL,detail TEXT,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)");c.commit();return c
def _hash_password(p:str,s:bytes)->bytes:return hashlib.pbkdf2_hmac('sha256',p.encode(),s,ITERATIONS)
def register(username:str,password:str,special_code:str='',owner_setup_secret:str='',email:str='',full_legal_name:str='')->dict:
 n,p=str(username or '').strip(),str(password or '');em=str(email or '').strip().lower();name=' '.join(str(full_legal_name or '').split())
 if len(n)<3 or len(n)>64 or any(x.isspace() for x in n):raise ValueError('Username must contain 3–64 characters and no spaces.')
 if len(p)<12:raise ValueError('Password must be at least 12 characters long.')
 if em:
  import re
  if len(em)>254 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',em):raise ValueError('Enter a valid email address.')
 if name and (len(name)<3 or len(name)>120):raise ValueError('Enter a valid full legal name.')
 if special_code:raise ValueError('Special access is granted by the owner after account creation.')
 if _remote_enabled() and owner_setup_secret:raise RuntimeError('Owner bootstrap is not available through the configured remote account service. Configure its server-side owner bootstrap before using owner setup.')
 if _remote_enabled():return _api('register',{'username':n,'password':p,'email':em or None,'full_legal_name':name or None}).get('user',{})
 sp=False;secret=_setting('PREDICTAI_OWNER_SETUP_SECRET');role='regular'
 if owner_setup_secret:
  configured_owner=_setting('PREDICTAI_OWNER_USERNAME')
  if not configured_owner or n.casefold()!=configured_owner.casefold():raise ValueError('Owner setup is available only for the configured owner username.')
  if len(secret)<32 or not hmac.compare_digest(owner_setup_secret,secret):raise ValueError('Owner setup secret is invalid or not configured securely.')
  role,sp='owner',False
 salt=secrets.token_bytes(16);hashed=_hash_password(p,salt).hex()
 try:
  with _connect() as c:
   if em and c.execute('SELECT 1 FROM users WHERE lower(email)=lower(?)',(em,)).fetchone():raise ValueError('That email address is already registered.')
   c.execute("CREATE TABLE IF NOT EXISTS app_settings(key TEXT PRIMARY KEY,value TEXT NOT NULL)")
   c.execute('BEGIN IMMEDIATE')
   if role=='owner' and (c.execute("SELECT 1 FROM users WHERE role='owner'").fetchone() or c.execute("SELECT 1 FROM app_settings WHERE key='owner_bootstrap_consumed'").fetchone()):raise ValueError('Owner setup has already been completed.')
   if role!='owner' and not c.execute("SELECT 1 FROM users WHERE role='owner'").fetchone() and len(secret)>=32:
    # Until initialized, regular accounts are allowed, but the owner secret remains available.
    pass
   c.execute('INSERT INTO users(username,salt,password_hash,special_access,role,email,full_legal_name) VALUES(?,?,?,?,?,?,?)',(n,salt.hex(),hashed,int(sp),role,em or None,name or None));c.execute('INSERT INTO usage_events(username,event_type,detail) VALUES(?,?,?)',(n,'registration','account created'))
   if role=='owner':c.execute("INSERT INTO app_settings(key,value) VALUES('owner_bootstrap_consumed','1')")
 except sqlite3.IntegrityError as e:raise ValueError('That username or email is already registered.') from e
 return {'username':n,'special_access':sp,'role':role,'email':em,'full_legal_name':name,'is_blocked':False}
def authenticate(username:str,password:str)->dict|None:
 n,p=str(username or '').strip(),str(password or '')
 if _remote_enabled():
  try:return _api('login',{'username':n,'password':p}).get('user')
  except ValueError:return None
 with _connect() as c:r=c.execute('SELECT username,salt,password_hash,special_access,role,email,full_legal_name,is_blocked FROM users WHERE username=? COLLATE NOCASE',(n,)).fetchone()
 if not r or bool(r['is_blocked']):return None
 if not hmac.compare_digest(_hash_password(p,bytes.fromhex(r['salt'])).hex(),r['password_hash']):return None
 with _connect() as c:c.execute('INSERT INTO usage_events(username,event_type,detail) VALUES(?,?,?)',(r['username'],'login','successful login'))
 return {'username':r['username'],'special_access':bool(r['special_access']),'role':r['role'],'email':r['email'],'full_legal_name':r['full_legal_name'],'is_blocked':bool(r['is_blocked'])}
def record_event(username:str,event_type:str,detail:str='')->None:
 if event_type not in _ALLOWED_EVENTS:raise ValueError('Unsupported usage event.')
 n,d=str(username or '')[:64],str(detail or '')[:200]
 if _remote_enabled():_api('event',{'username':n,'event_type':event_type,'detail':d});return
 with _connect() as c:c.execute('INSERT INTO usage_events(username,event_type,detail) VALUES(?,?,?)',(n,event_type,d))
def _require_owner(actor:dict|None)->str:
 if not actor or not actor.get('username'):raise PermissionError('Owner privileges are required.')
 username=str(actor['username']).strip()
 if _remote_enabled():
  if actor.get('role')!='owner':raise PermissionError('Owner privileges are required.')
  return username
 with _connect() as c:
  row=c.execute('SELECT role,is_blocked FROM users WHERE username=? COLLATE NOCASE',(username,)).fetchone()
 if not row or row['role']!='owner' or row['is_blocked']:
  raise PermissionError('Owner privileges are required.')
 return username
def list_users(actor:dict|None=None)->list[dict]:
 _require_owner(actor)
 if _remote_enabled():
  return _api('users',{'actor_username':actor.get('username')}).get('users',[])
 with _connect() as c:r=c.execute('SELECT username,full_legal_name,email,special_access,role,is_blocked,created_at FROM users ORDER BY created_at DESC').fetchall()
 return [dict(x) for x in r]
def set_special_access(actor:dict,username:str,enabled:bool)->None:
 actor_username=_require_owner(actor)
 if _remote_enabled():_api('special-access',{'actor_username':actor.get('username'),'username':username,'enabled':bool(enabled)});return
 with _connect() as c:
  r=c.execute('SELECT role FROM users WHERE username=? COLLATE NOCASE',(username,)).fetchone()
  if not r:raise ValueError('User not found.')
  if r['role']=='owner':raise ValueError('Owner privileges cannot be changed here.')
  c.execute('UPDATE users SET special_access=? WHERE username=? COLLATE NOCASE',(int(bool(enabled)),username));c.execute('INSERT INTO usage_events(username,event_type,detail) VALUES(?,?,?)',(actor_username,'admin_action',f"special access {'granted' if enabled else 'revoked'} for {username}"))
def set_blocked(actor:dict,username:str,blocked:bool)->None:
 actor_username=_require_owner(actor)
 if _remote_enabled():_api('block',{'actor_username':actor.get('username'),'username':username,'blocked':bool(blocked)});return
 with _connect() as c:
  r=c.execute('SELECT role FROM users WHERE username=? COLLATE NOCASE',(username,)).fetchone()
  if not r:raise ValueError('User not found.')
  if r['role']=='owner':raise ValueError('The owner account cannot be blocked.')
  c.execute('UPDATE users SET is_blocked=? WHERE username=? COLLATE NOCASE',(int(bool(blocked)),username));c.execute('INSERT INTO usage_events(username,event_type,detail) VALUES(?,?,?)',(actor_username,'admin_action',f"{'blocked' if blocked else 'unblocked'} account {username}"))
def get_account_status(username:str)->dict|None:
 if _remote_enabled():return _api('status',{'username':str(username or '').strip()}).get('user')
 with _connect() as c:r=c.execute('SELECT username,role,special_access,is_blocked,email,full_legal_name FROM users WHERE username=? COLLATE NOCASE',(str(username or '').strip(),)).fetchone()
 return dict(r) if r else None
def daily_task_usage(username:str,task_date:str)->int:
 if _remote_enabled():return int(_api('daily-usage',{'username':username,'task_date':task_date}).get('count',0))
 with _connect() as c:return int(c.execute("SELECT COUNT(*) FROM daily_ai_tasks WHERE username=? AND task_date=? AND status IN ('reserved','completed')",(username,task_date)).fetchone()[0])
def reserve_daily_task(username:str,task_date:str,task_key:str,limit:int=3)->bool:
 if _remote_enabled():
  try:return bool(_api('reserve-task',{'username':username,'task_date':task_date,'task_key':task_key,'limit':int(limit)}).get('reserved'))
  except ValueError as e:
   if 'Daily AI task limit' in str(e):return False
   raise
 with _connect() as c:
  c.execute('BEGIN IMMEDIATE');used=int(c.execute("SELECT COUNT(*) FROM daily_ai_tasks WHERE username=? AND task_date=? AND status IN ('reserved','completed')",(username,task_date)).fetchone()[0])
  if used>=limit:c.rollback();return False
  try:c.execute("INSERT INTO daily_ai_tasks(username,task_date,task_key,status) VALUES(?,?,?,'reserved')",(username,task_date,task_key))
  except sqlite3.IntegrityError:c.rollback();return True
  c.commit();return True
def finish_daily_task(username:str,task_date:str,task_key:str,success:bool)->None:
 if _remote_enabled():_api('finish-task',{'username':username,'task_date':task_date,'task_key':task_key,'success':bool(success)});return
 with _connect() as c:
  if success:c.execute("UPDATE daily_ai_tasks SET status='completed' WHERE username=? AND task_date=? AND task_key=?",(username,task_date,task_key))
  else:c.execute("DELETE FROM daily_ai_tasks WHERE username=? AND task_date=? AND task_key=? AND status='reserved'",(username,task_date,task_key))
def count_events(username:str,event_type:str)->int:
 if _remote_enabled():return int(_api('event-count',{'username':username,'event_type':event_type}).get('count',0))
 with _connect() as c:return int(c.execute('SELECT COUNT(*) FROM usage_events WHERE username=? AND event_type=?',(username,event_type)).fetchone()[0])
def get_analytics(actor:dict|None=None)->dict:
 _require_owner(actor)
 if _remote_enabled():
  return _api('analytics',{'actor_username':actor.get('username')})
 with _connect() as c:
  users=c.execute('SELECT COUNT(*) FROM users').fetchone()[0];special=c.execute("SELECT COUNT(*) FROM users WHERE special_access=1 AND role!='owner'").fetchone()[0];events={r['event_type']:r['n'] for r in c.execute('SELECT event_type,COUNT(*) AS n FROM usage_events GROUP BY event_type')};daily=[dict(r) for r in c.execute('SELECT date(created_at) AS day,event_type,COUNT(*) AS count FROM usage_events GROUP BY date(created_at),event_type ORDER BY day DESC LIMIT 100')]
 return {'registered_users':users,'special_users':special,'documents_uploaded':events.get('document_upload',0),'questions_asked':events.get('question_asked',0),'reports_generated':events.get('report_generated',0),'ai_requests_succeeded':events.get('ai_success',0),'ai_requests_failed':events.get('ai_error',0),'daily_usage':daily,'tracked_events':events}
