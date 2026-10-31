from auth_security import connect_db, utc_now

def _owner(actor):
    with connect_db() as db:
        row=db.execute("SELECT role,status FROM users WHERE lower(username)=lower(?)",(actor,)).fetchone()
    if not row or row['role']!='Owner' or row['status']!='active': raise PermissionError('Owner privileges required.')
def list_users(actor_username,search='',status='All',role='All'):
    _owner(actor_username)
    sql='SELECT id,full_name,email,username,role,status,email_verified,created_at,updated_at,blocked_at,blocked_by FROM users WHERE 1=1'; p=[]
    if search.strip():
        q=f'%{search.strip()}%'; sql+=' AND (full_name LIKE ? OR email LIKE ? OR username LIKE ?)'; p += [q,q,q]
    if status!='All': sql+=' AND status=?'; p.append(status)
    if role!='All': sql+=' AND role=?'; p.append(role)
    sql+=' ORDER BY created_at DESC'
    with connect_db() as db: return [dict(r) for r in db.execute(sql,p).fetchall()]
def _audit(db,actor,uid,action,details=''):
    db.execute('INSERT INTO auth_audit_log(actor_username,target_user_id,action,details,created_at) VALUES(?,?,?,?,?)',(actor,uid,action,(details or '')[:500],utc_now()))
def block_user(target_user_id,actor_username,reason=''):
    _owner(actor_username)
    with connect_db() as db:
        target=db.execute('SELECT id,username,role,status FROM users WHERE id=?',(int(target_user_id),)).fetchone()
        if not target: return False,'User not found.'
        if target['role']=='Owner': return False,'Owner accounts cannot be blocked.'
        if target['username'].lower()==actor_username.lower(): return False,'You cannot block your own account.'
        if target['status']=='blocked': return True,'User is already blocked.'
        now=utc_now(); db.execute("UPDATE users SET status='blocked',blocked_at=?,blocked_by=?,updated_at=? WHERE id=?",(now,actor_username,now,int(target_user_id)))
        _audit(db,actor_username,int(target_user_id),'user_blocked',reason)
    return True,'User blocked.'
def unblock_user(target_user_id,actor_username):
    _owner(actor_username)
    with connect_db() as db:
        t=db.execute('SELECT id,role,status,email_verified FROM users WHERE id=?',(int(target_user_id),)).fetchone()
        if not t: return False,'User not found.'
        if t['role']=='Owner': return False,'Owner accounts cannot be changed here.'
        if not t['email_verified']: return False,'User must verify their email first.'
        if t['status']!='blocked': return True,'User is not blocked.'
        db.execute("UPDATE users SET status='active',blocked_at=NULL,blocked_by=NULL,updated_at=? WHERE id=?",(utc_now(),int(target_user_id)))
        _audit(db,actor_username,int(target_user_id),'user_unblocked')
    return True,'User unblocked.'
def audit_log(actor_username,limit=100):
    _owner(actor_username); limit=max(1,min(int(limit),500))
    with connect_db() as db: return [dict(r) for r in db.execute('SELECT id,actor_username,target_user_id,action,details,created_at FROM auth_audit_log ORDER BY id DESC LIMIT ?',(limit,)).fetchall()]

def set_special_access(target_user_id, actor_username, enabled=True):
    _owner(actor_username)
    with connect_db() as db:
        target=db.execute('SELECT id,username,role,status,email_verified FROM users WHERE id=?',(int(target_user_id),)).fetchone()
        if not target: return False,'User not found.'
        if target['role']=='Owner': return False,'Owner role cannot be changed here.'
        if not target['email_verified'] or target['status']!='active': return False,'Account must be active and email-verified first.'
        role='Special User' if enabled else 'Regular User'
        db.execute('UPDATE users SET role=?,updated_at=? WHERE id=?',(role,utc_now(),int(target_user_id)))
        _audit(db,actor_username,int(target_user_id),'special_access_granted' if enabled else 'special_access_revoked',f'Role changed to {role}')
    return True,('Special access granted.' if enabled else 'Special access revoked.')
