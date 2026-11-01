const ITERATIONS = 310000;
const EVENTS = new Set(['registration','document_upload','question_asked','report_generated','ai_success','ai_error','login','admin_action']);
const json = (data, status=200) => new Response(JSON.stringify(data), {status, headers:{'content-type':'application/json; charset=utf-8','cache-control':'no-store'}});
const fail = (message, status=400) => json({error:message}, status);
const bytesToHex = bytes => [...new Uint8Array(bytes)].map(x=>x.toString(16).padStart(2,'0')).join('');
const hexToBytes = hex => Uint8Array.from(hex.match(/.{2}/g)||[], x=>parseInt(x,16));
async function derive(password, salt, iterations=ITERATIONS) {
  const key = await crypto.subtle.importKey('raw', new TextEncoder().encode(password), 'PBKDF2', false, ['deriveBits']);
  return bytesToHex(await crypto.subtle.deriveBits({name:'PBKDF2',hash:'SHA-256',salt,iterations}, key, 256));
}
async function matchesSecret(candidate, expected) {
  if (!candidate || !expected) return false;
  const [a,b] = await Promise.all([crypto.subtle.digest('SHA-256',new TextEncoder().encode(candidate)),crypto.subtle.digest('SHA-256',new TextEncoder().encode(expected))]);
  const x=new Uint8Array(a), y=new Uint8Array(b); let diff=0; for(let i=0;i<x.length;i++)diff|=x[i]^y[i]; return diff===0;
}
const userView = r => ({username:r.username,email:r.email||'',full_legal_name:r.full_legal_name||'',role:r.role,special_access:!!r.special_access,is_blocked:!!r.is_blocked,created_at:r.created_at});
async function body(request) { try { return await request.json(); } catch { throw new Error('Request body must be valid JSON.'); } }
async function owner(db, username) {
  if (!username) return false;
  const row=await db.prepare('SELECT role,is_blocked FROM users WHERE username=? COLLATE NOCASE').bind(username).first();
  return !!row && row.role==='owner' && !row.is_blocked;
}
async function event(db, username, type, detail='') {
  if(!EVENTS.has(type)) throw new Error('Unsupported usage event.');
  await db.prepare('INSERT INTO usage_events(username,event_type,detail) VALUES(?,?,?)').bind(String(username).slice(0,64),type,String(detail||'').slice(0,200)).run();
}
async function route(request, env, path) {
  if (!env.D1) return fail('Account database is not configured.',500);
  const auth=request.headers.get('authorization')||'';
  if (!env.API_TOKEN || !(await matchesSecret(auth.replace(/^Bearer\s+/i,''),env.API_TOKEN))) return fail('Unauthorized.',401);
  const b=await body(request), db=env.D1;
  try {
    if(path==='/register') {
      const username=String(b.username||'').trim(), password=String(b.password||''), email=String(b.email||'').trim().toLowerCase(), name=String(b.full_legal_name||'').trim().replace(/\s+/g,' ');
      if(username.length<3||username.length>64||/\s/.test(username)) return fail('Username must contain 3–64 characters and no spaces.');
      if(password.length<12) return fail('Password must be at least 12 characters long.');
      if(!email||email.length>254||! /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return fail('Enter a valid email address.');
      if(name.length<3||name.length>120) return fail('Enter a valid full legal name.');
      const ownerName=String(env.OWNER_USERNAME||'').trim();
      const wantsOwner=!!ownerName && username.toLowerCase()===ownerName.toLowerCase();
      let role='regular', special=0;
      if(wantsOwner) {
        if(!(await matchesSecret(String(b.owner_setup_secret||''),env.OWNER_SETUP_SECRET))) return fail('This username is reserved for the configured owner.',403);
        role='owner';
      } else if(await matchesSecret(String(b.special_code||''),env.SPECIAL_ACCESS_CODE)) special=1;
      const salt=crypto.getRandomValues(new Uint8Array(16)), saltHex=bytesToHex(salt), hash=await derive(password,salt);
      if(wantsOwner) {
        let results;
        try { results=await db.batch([
          db.prepare(`INSERT INTO users(username,email,full_legal_name,password_salt,password_hash,password_iterations,role,special_access)
            SELECT ?,?,?,?,?,?,'owner',0 WHERE (SELECT initialized FROM owner_state WHERE id=1)=0
            AND NOT EXISTS(SELECT 1 FROM users WHERE role='owner')`).bind(username,email,name,saltHex,hash,ITERATIONS),
          db.prepare(`UPDATE owner_state SET initialized=1,owner_username=?,initialized_at=CURRENT_TIMESTAMP
            WHERE id=1 AND initialized=0 AND EXISTS(SELECT 1 FROM users WHERE username=? COLLATE NOCASE AND role='owner')`).bind(username,username),
        ]); } catch { return fail('That username or email is already registered.',409); }
        if(!results?.[0]?.meta?.changes) return fail('Owner initialization has already been completed.',409);
      } else {
        try { await db.prepare('INSERT INTO users(username,email,full_legal_name,password_salt,password_hash,password_iterations,role,special_access) VALUES(?,?,?,?,?,?,?,?)').bind(username,email,name,saltHex,hash,ITERATIONS,role,special).run(); }
        catch { return fail('That username or email is already registered.',409); }
      }
      await event(db,username,'registration','account created');
      return json({user:{username,email,full_legal_name:name,role,special_access:!!special,is_blocked:false}});
    }
    if(path==='/login') {
      const username=String(b.username||'').trim();
      const row=await db.prepare('SELECT * FROM users WHERE username=? COLLATE NOCASE').bind(username).first();
      if(!row||row.is_blocked||!(await matchesPassword(String(b.password||''),row))) return fail('Username or password is incorrect.',401);
      await event(db,row.username,'login','successful login'); return json({user:userView(row)});
    }
    if(path==='/users') {
      if(!(await owner(db,b.actor_username))) return fail('Owner privileges are required.',403);
      const {results=[]}=await db.prepare('SELECT username,email,full_legal_name,role,special_access,is_blocked,created_at FROM users ORDER BY created_at DESC').all(); return json({users:results.map(userView)});
    }
    if(path==='/special-access'||path==='/block') {
      if(!(await owner(db,b.actor_username))) return fail('Owner privileges are required.',403);
      const target=await db.prepare('SELECT role FROM users WHERE username=? COLLATE NOCASE').bind(String(b.username||'')).first();
      if(!target) return fail('User not found.',404); if(target.role==='owner') return fail('Owner privileges cannot be changed here.',403);
      const enabled=path==='/special-access'?!!b.enabled:!!b.blocked, column=path==='/special-access'?'special_access':'is_blocked';
      await db.prepare(`UPDATE users SET ${column}=?,updated_at=CURRENT_TIMESTAMP WHERE username=? COLLATE NOCASE`).bind(enabled?1:0,b.username).run();
      await event(db,b.actor_username,'admin_action',`${path==='/block'?'block':'special access'} updated for ${b.username}`); return json({ok:true});
    }
    if(path==='/status') { const row=await db.prepare('SELECT username,email,full_legal_name,role,special_access,is_blocked FROM users WHERE username=? COLLATE NOCASE').bind(String(b.username||'')).first(); return json({user:row?userView(row):null}); }
    if(path==='/event') { await event(db,b.username,b.event_type,b.detail); return json({ok:true}); }
    if(path==='/event-count') { const row=await db.prepare('SELECT COUNT(*) AS n FROM usage_events WHERE username=? AND event_type=?').bind(b.username,b.event_type).first(); return json({count:Number(row?.n||0)}); }
    if(path==='/daily-usage') { const row=await db.prepare("SELECT COUNT(*) AS n FROM daily_ai_tasks WHERE username=? AND task_date=? AND status IN ('reserved','completed')").bind(b.username,b.task_date).first(); return json({count:Number(row?.n||0)}); }
    if(path==='/reserve-task') {
      const limit=Math.max(0,Number(b.limit)||3);
      try {
        const result=await db.prepare(`INSERT INTO daily_ai_tasks(username,task_date,task_key,status)
          SELECT ?,?,?, 'reserved' WHERE (SELECT COUNT(*) FROM daily_ai_tasks WHERE username=? AND task_date=? AND status IN ('reserved','completed')) < ?`)
          .bind(b.username,b.task_date,b.task_key,b.username,b.task_date,limit).run();
        if(result?.meta?.changes) return json({reserved:true});
        const duplicate=await db.prepare('SELECT 1 AS found FROM daily_ai_tasks WHERE username=? AND task_date=? AND task_key=?').bind(b.username,b.task_date,b.task_key).first();
        return duplicate?json({reserved:true}):fail('Daily AI task limit reached.',429);
      } catch { const duplicate=await db.prepare('SELECT 1 AS found FROM daily_ai_tasks WHERE username=? AND task_date=? AND task_key=?').bind(b.username,b.task_date,b.task_key).first(); return duplicate?json({reserved:true}):fail('Daily AI task limit reached.',429); }
    }
    if(path==='/finish-task') { if(b.success) await db.prepare("UPDATE daily_ai_tasks SET status='completed' WHERE username=? AND task_date=? AND task_key=?").bind(b.username,b.task_date,b.task_key).run(); else await db.prepare("DELETE FROM daily_ai_tasks WHERE username=? AND task_date=? AND task_key=? AND status='reserved'").bind(b.username,b.task_date,b.task_key).run(); return json({ok:true}); }
    if(path==='/analytics') {
      if(!(await owner(db,b.actor_username))) return fail('Owner privileges are required.',403);
      const {results:users=[]}=await db.prepare('SELECT COUNT(*) AS n FROM users').all(), {results:special=[]}=await db.prepare("SELECT COUNT(*) AS n FROM users WHERE special_access=1 AND role!='owner'").all(), {results:ev=[]}=await db.prepare('SELECT event_type,COUNT(*) AS n FROM usage_events GROUP BY event_type').all(), {results:daily=[]}=await db.prepare('SELECT date(created_at) AS day,event_type,COUNT(*) AS count FROM usage_events GROUP BY date(created_at),event_type ORDER BY day DESC LIMIT 100').all();
      const counts=Object.fromEntries(ev.map(x=>[x.event_type,Number(x.n)])); return json({registered_users:Number(users[0]?.n||0),special_users:Number(special[0]?.n||0),documents_uploaded:counts.document_upload||0,questions_asked:counts.question_asked||0,reports_generated:counts.report_generated||0,ai_requests_succeeded:counts.ai_success||0,ai_requests_failed:counts.ai_error||0,daily_usage:daily,tracked_events:counts});
    }
    return fail('Not found.',404);
  } catch { return fail('Account service error. Please try again later.',500); }
}
async function matchesPassword(password,row) { const hash=await derive(password,hexToBytes(row.password_salt),Number(row.password_iterations)||ITERATIONS); return await matchesSecret(hash,row.password_hash); }
export default { async fetch(request,env) {
  if(request.method!=='POST') return fail('Method not allowed.',405);
  const url=new URL(request.url); const path=url.pathname.replace(/^\/+/,'');
  return route(request,env,'/'+path.replace(/^api\//,''));
}};
