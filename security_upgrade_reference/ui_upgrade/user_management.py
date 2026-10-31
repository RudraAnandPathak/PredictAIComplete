"""Owner user-management helpers. Enforce Owner role server-side at each call site."""
from auth_security import connect_db, utc_now

def list_users(search="", status="All", role="All"):
    sql="""SELECT id,full_name,email,username,role,status,email_verified,created_at,updated_at,blocked_at,blocked_by FROM users WHERE 1=1"""
    params=[]
    if search.strip():
        needle=f"%{search.strip()}%"
        sql+=" AND (full_name LIKE ? OR email LIKE ? OR username LIKE ?)"
        params.extend([needle,needle,needle])
    if status!="All": sql+=" AND status=?"; params.append(status)
    if role!="All": sql+=" AND role=?"; params.append(role)
    sql+=" ORDER BY created_at DESC"
    with connect_db() as db: return [dict(r) for r in db.execute(sql,params).fetchall()]

def _audit(db, actor, target_id, action, details=""):
    db.execute("INSERT INTO auth_audit_log(actor_username,target_user_id,action,details,created_at) VALUES(?,?,?,?,?)",
               (actor,target_id,action,details[:500],utc_now()))

def block_user(target_user_id, actor_username, reason=""):
    with connect_db() as db:
        target=db.execute("SELECT id,username,role,status FROM users WHERE id=?",(int(target_user_id),)).fetchone()
        if not target: return False,"User not found."
        if target["role"]=="Owner": return False,"Owner accounts cannot be blocked with this helper."
        if target["username"].lower()==actor_username.lower(): return False,"You cannot block your own account."
        if target["status"]=="blocked": return True,"User is already blocked."
        now=utc_now()
        db.execute("UPDATE users SET status='blocked',blocked_at=?,blocked_by=?,updated_at=? WHERE id=?",(now,actor_username,now,int(target_user_id)))
        _audit(db,actor_username,int(target_user_id),"user_blocked",reason)
    return True,"User blocked. Ensure account status is rechecked before every protected action."

def unblock_user(target_user_id, actor_username):
    with connect_db() as db:
        target=db.execute("SELECT id,username,role,status,email_verified FROM users WHERE id=?",(int(target_user_id),)).fetchone()
        if not target: return False,"User not found."
        if target["role"]=="Owner": return False,"Owner accounts cannot be changed with this helper."
        if not target["email_verified"]: return False,"Verify the user's email before unblocking."
        if target["status"]!="blocked": return True,"User is not blocked."
        now=utc_now()
        db.execute("UPDATE users SET status='active',blocked_at=NULL,blocked_by=NULL,updated_at=? WHERE id=?",(now,int(target_user_id)))
        _audit(db,actor_username,int(target_user_id),"user_unblocked")
    return True,"User unblocked."

def audit_log(limit=100):
    limit=max(1,min(int(limit),500))
    with connect_db() as db:
        rows=db.execute("SELECT id,actor_username,target_user_id,action,details,created_at FROM auth_audit_log ORDER BY id DESC LIMIT ?",(limit,)).fetchall()
    return [dict(r) for r in rows]
