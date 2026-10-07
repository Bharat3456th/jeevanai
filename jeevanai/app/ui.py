# Built-in web interface (served at / by app/main.py)
HTML_PAGE = r'''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>JeevanAI</title>
<style>
:root{--bg:#f6f7fb;--card:#fff;--tx:#1d2433;--mu:#667085;--bd:#e3e6ee;--ac:#4f46e5;--ok:#16a34a;--wa:#d97706;--er:#dc2626}
@media(prefers-color-scheme:dark){:root{--bg:#10131a;--card:#181c26;--tx:#e8ebf2;--mu:#98a2b3;--bd:#2a3040;--ac:#818cf8}}
*{box-sizing:border-box}body{margin:0;font-family:system-ui,Segoe UI,sans-serif;background:var(--bg);color:var(--tx)}
header{display:flex;gap:12px;align-items:center;justify-content:space-between;padding:12px 20px;border-bottom:1px solid var(--bd);background:var(--card);flex-wrap:wrap}
h1{font-size:20px;margin:0}h1 span{color:var(--ac)}
nav{display:flex;gap:4px;flex-wrap:wrap}nav button{background:none;border:0;padding:8px 12px;border-radius:8px;color:var(--mu);cursor:pointer;font-size:14px}
nav button.on{background:var(--ac);color:#fff}
main{max-width:900px;margin:20px auto;padding:0 16px}
.card{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:16px;margin-bottom:14px}
label{display:block;font-size:13px;color:var(--mu);margin:10px 0 0}
input,select,textarea{width:100%;margin-top:4px;padding:9px 10px;border:1px solid var(--bd);border-radius:8px;background:var(--bg);color:var(--tx);font:inherit}
.row{display:flex;gap:12px}.row>*{flex:1}
button.pr{margin-top:14px;padding:10px 18px;border:0;border-radius:8px;background:var(--ac);color:#fff;font-size:15px;cursor:pointer}
button.pr:disabled{opacity:.6}
button.sm{padding:5px 10px;border-radius:6px;border:1px solid var(--bd);background:var(--card);color:var(--tx);cursor:pointer}
.badge{display:inline-block;padding:2px 9px;border-radius:99px;font-size:12px;background:var(--bd);color:var(--tx)}
.badge.allowed,.badge.approved,.badge.completed{background:var(--ok);color:#fff}
.badge.approval_required,.badge.pending{background:var(--wa);color:#fff}
.badge.blocked,.badge.failed,.badge.error,.badge.rejected{background:var(--er);color:#fff}
.resp{white-space:pre-wrap;line-height:1.55}pre{background:var(--bg);padding:10px;border-radius:8px;overflow:auto;font-size:13px}
table{width:100%;border-collapse:collapse;font-size:14px}td,th{text-align:left;padding:8px 6px;border-bottom:1px solid var(--bd);vertical-align:top}
.err{color:var(--er)}.mu{color:var(--mu);font-size:13px}.pane{display:none}.pane.on{display:block}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:10px;margin-bottom:14px}
.stat{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:14px}.stat b{display:block;font-size:26px}
.auth{max-width:380px;margin:60px auto}.dot{background:var(--er);color:#fff;border-radius:99px;padding:0 6px;font-size:11px;margin-left:4px}
#toast{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);background:var(--tx);color:var(--bg);padding:10px 16px;border-radius:8px;display:none;max-width:90%}
a{color:var(--ac)}
</style></head><body>
<div id="auth"><main><div class="card auth">
 <h1>Jeevan<span>AI</span></h1><h3 id="atitle">Login</h3>
 <label id="nameRow" hidden>Name<input id="aname" autocomplete="name"></label>
 <label>Email<input id="aemail" type="email" autocomplete="email"></label>
 <label>Password (min 8 characters)<input id="apass" type="password" autocomplete="current-password"></label>
 <button class="pr" id="abtn">Login</button><p class="err" id="aerr"></p>
 <p class="mu"><a href="#" id="aswap">Create new account</a></p></div></main></div>
<div id="shell" hidden>
<header><h1>Jeevan<span>AI</span></h1><nav id="nav"></nav><span class="mu"><span id="who"></span> <button class="sm" id="out">Logout</button></span></header>
<main>
<div id="dash" class="pane on"><div class="stats" id="stats"></div><div class="card"><b>Recent activity</b><div id="recent"></div></div></div>
<div id="run" class="pane"><div class="card">
 <div class="row"><label>Agent<select id="agent"></select></label><label>Action<select id="action"></select></label></div>
 <p class="mu" id="adesc"></p><div id="fields"></div><button class="pr" id="go">Run</button></div>
 <div class="card" id="result" hidden></div></div>
<div id="approvals" class="pane"><div id="apList"></div><div class="card" id="apOut" hidden></div></div>
<div id="perms" class="pane"><div class="card" id="pList"></div><button class="sm" id="reset">Reset to defaults</button></div>
<div id="activity" class="pane"><div class="card" id="acList"></div></div>
<div id="docs" class="pane"><div class="card"><input type="file" id="file" accept=".pdf,.txt,.md"><button class="pr" id="up">Upload</button><p class="err" id="upErr"></p></div><div class="card" id="dList"></div></div>
<div id="products" class="pane"><div class="card" id="prList"></div></div>
<div id="alerts" class="pane"><div class="card" id="alList"></div></div>
</main></div><div id="toast"></div>
<script>
const $=s=>document.querySelector(s);
const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const fmt=s=>{if(!s)return'-';const d=new Date(/[zZ]$|[+-]\d\d:?\d\d$/.test(s)?s:s+'Z');return d.toLocaleString()};
let token=localStorage.getItem('jt')||'',agents={},docs=[],prods=[],ROLES=[],mode='login';
const A={
 create_study_plan:[["topic","Topic","text","p"],["days","Days","number","p",7],["hours_per_day","Hours per day","number","p",2]],
 summarize_notes:[["notes","Paste your notes","textarea","m"]],
 generate_quiz:[["notes","Paste notes","textarea","m"],["count","Questions","number","p",5]],
 analyze_resume:[["resume","Paste resume text","textarea","m"]],
 skill_gap:[["target_role","Target role","role","p"],["resume","Paste resume text","textarea","p"]],
 career_roadmap:[["target_role","Target role","role","p"],["months","Months","number","p",6]],
 summarize_document:[["document_id","Document","doc","p"]],
 extract_dates:[["document_id","Document","doc","p"]],
 ask_document:[["document_id","Document","doc","p"],["question","Your question","textarea","m"]],
 track_product:[["url","Product URL","text","p"],["name","Name (optional)","text","p"],["target_price","Target price (optional)","number","p"]],
 check_price:[["product_id","Product","prod","p"]],
 set_price_alert:[["product_id","Product","prod","p"],["target_price","Target price","number","p"]],
 purchase:[]};
function toast(m){const t=$('#toast');t.textContent=m;t.style.display='block';setTimeout(()=>t.style.display='none',3500)}
async function api(path,o={}){
 const h={};if(token)h.Authorization='Bearer '+token;
 let body;if(o.json){h['Content-Type']='application/json';body=JSON.stringify(o.json)}if(o.form)body=o.form;
 const r=await fetch(path,{method:o.method||'GET',headers:h,body});let d=null;try{d=await r.json()}catch{}
 if(r.status===401&&!o.noauth){logout();throw new Error('Session expired. Please login again.')}
 if(!r.ok){let m=d&&d.detail;if(Array.isArray(m))m=m.map(x=>x.msg).join('; ');throw new Error(m||r.statusText)}
 return d}
function logout(){token='';localStorage.removeItem('jt');$('#shell').hidden=true;$('#auth').hidden=false}
function setMode(m){mode=m;$('#atitle').textContent=m==='login'?'Login':'Create account';$('#abtn').textContent=m==='login'?'Login':'Register';
 $('#nameRow').hidden=m==='login';$('#aswap').textContent=m==='login'?'Create new account':'I already have an account';$('#aerr').textContent=''}
$('#aswap').onclick=e=>{e.preventDefault();setMode(mode==='login'?'register':'login')};
$('#abtn').onclick=async()=>{
 $('#aerr').textContent='';$('#abtn').disabled=true;
 try{const j={email:$('#aemail').value,password:$('#apass').value};if(mode==='register')j.name=$('#aname').value;
  const r=await api('/api/auth/'+mode,{method:'POST',json:j,noauth:true});token=r.access_token;localStorage.setItem('jt',token);$('#apass').value='';await boot(r.user)}
 catch(e){$('#aerr').textContent=e.message}$('#abtn').disabled=false};
['aemail','apass','aname'].forEach(i=>$('#'+i).addEventListener('keydown',e=>{if(e.key==='Enter')$('#abtn').click()}));
$('#out').onclick=logout;
function show(r,el){
 const d=r.data||{};let h=`<span class="badge ${esc(r.status||'')}">${esc(r.status||'ok')}</span> `;
 if(r.mode)h+=`<span class="badge">${esc(r.mode)}</span>`;
 if(r.message)h+=`<p>${esc(r.message)}</p>`;if(r.response)h+=`<p class="resp">${esc(r.response)}</p>`;
 if(d.plan)h+=d.plan.map(p=>`<div class="card"><b>Day ${p.day}</b> - ${esc(p.goal)}<ul>${p.tasks.map(t=>`<li>${esc(t)}</li>`).join('')}</ul></div>`).join('');
 else if(d.quiz)h+=d.quiz.map((q,i)=>`<div class="card"><b>${i+1}. ${esc(q.question)}</b>${q.options?'<ul>'+q.options.map(o=>`<li>${esc(o)}</li>`).join('')+'</ul>':''}<details><summary>Answer</summary>${esc(q.answer)}${q.explanation?'<br>'+esc(q.explanation):''}</details></div>`).join('');
 else if(d.dates)h+='<table><tr><th>Date</th><th>ISO</th><th>Context</th></tr>'+d.dates.map(x=>`<tr><td>${esc(x.date)}${x.upcoming?' <span class="badge pending">upcoming</span>':''}</td><td>${esc(x.iso||'-')}</td><td class="mu">${esc(x.context)}</td></tr>`).join('')+'</table>';
 else if(d.roadmap)h+=d.roadmap.map(m=>`<div class="card"><b>Month ${m.month}</b>: ${esc(m.focus.join(', '))}<br><span class="mu">Project: ${esc(m.project)}</span></div>`).join('');
 else if(d.sources)h+=`<details><summary>Sources</summary>${d.sources.map(s=>`<p class="mu">${esc(s)}</p>`).join('')}</details>`;
 else if(Object.keys(d).length)h+=`<pre>${esc(JSON.stringify(d,null,2))}</pre>`;
 if(r.approval_id)h+=`<p>Approval #${r.approval_id} created. Open the Approvals tab to approve it.</p>`;
 el.hidden=false;el.innerHTML=h}
function fail(el,e){el.hidden=false;el.innerHTML=`<p class="err">${esc(e.message)}</p>`}
function fields(){
 const a=$('#action').value,box=$('#fields');box.innerHTML='';
 $('#adesc').textContent=agents[$('#agent').value]?.description||'';
 (A[a]||[]).forEach(([k,l,t,w,d])=>{let i;
  if(t==='textarea')i=`<textarea id="f_${k}" rows="6"></textarea>`;
  else if(t==='role')i=`<select id="f_${k}">${ROLES.map(r=>`<option>${esc(r)}</option>`).join('')}</select>`;
  else if(t==='doc')i=`<select id="f_${k}">${docs.map(x=>`<option value="${x.id}">#${x.id} ${esc(x.filename)}</option>`).join('')||'<option value="">Upload a document first (Documents tab)</option>'}</select>`;
  else if(t==='prod')i=`<select id="f_${k}">${prods.map(x=>`<option value="${x.id}">#${x.id} ${esc(x.name||x.url.slice(0,40))}</option>`).join('')||'<option value="">Track a product first</option>'}</select>`;
  else i=`<input id="f_${k}" type="${t}" value="${d??''}">`;
  box.insertAdjacentHTML('beforeend',`<label>${l}${i}</label>`)});
 if(!(A[a]||[]).length)box.innerHTML='<p class="mu">No input needed.</p>'}
function actions(){$('#action').innerHTML=agents[$('#agent').value].actions.map(x=>`<option value="${x}">${x.replace(/_/g,' ')}</option>`).join('');fields()}
$('#go').onclick=async()=>{
 const payload={};let message='';
 for(const [k,,t,w] of A[$('#action').value]||[]){let v=$('#f_'+k).value;if(v==='')continue;if(t==='number'||t==='doc'||t==='prod')v=Number(v);if(w==='m')message=v;else payload[k]=v}
 $('#go').disabled=true;$('#go').textContent='Running...';
 try{show(await api('/api/agent/run',{method:'POST',json:{agent:$('#agent').value,action:$('#action').value,message,payload}}),$('#result'));prods=await api('/api/products');fields()}catch(e){fail($('#result'),e)}
 $('#go').disabled=false;$('#go').textContent='Run'};
async function loadDash(){
 const s=await api('/api/stats');
 const c=[['Completed',s.completed],['Blocked',s.blocked],['Pending approvals',s.pending_approvals],['Documents',s.documents],['Products',s.products],['Unread alerts',s.unread_alerts]];
 $('#stats').innerHTML=c.map(([n,v])=>`<div class="stat"><b>${v}</b><span class="mu">${n}</span></div>`).join('');
 $('#recent').innerHTML=s.recent.length?'<table>'+s.recent.map(r=>`<tr><td>${esc(r.agent)} / ${esc(r.action)}</td><td><span class="badge ${esc(r.status)}">${esc(r.status)}</span></td><td class="mu">${fmt(r.created_at)}</td></tr>`).join('')+'</table>':'<p class="mu">Nothing yet. Try the Run agent tab.</p>';
 setBadge('alerts',s.unread_alerts);setBadge('approvals',s.pending_approvals)}
function setBadge(t,n){const b=$('#tab_'+t);if(!b)return;b.querySelector('.dot')?.remove();if(n>0)b.insertAdjacentHTML('beforeend',`<span class="dot">${n}</span>`)}
async function loadRun(){[docs,prods]=await Promise.all([api('/api/documents'),api('/api/products')]);fields()}
async function loadApprovals(){
 const l=await api('/api/approvals');
 $('#apList').innerHTML=l.length?l.map(a=>`<div class="card"><b>${esc(a.agent)} / ${esc(a.action)}</b> <span class="badge pending">pending</span><p class="mu">${esc(a.message)||esc(JSON.stringify(a.payload))}</p><button class="sm" onclick="decide(${a.id},'approve')">Approve</button> <button class="sm" onclick="decide(${a.id},'reject')">Reject</button></div>`).join(''):'<div class="card mu">No pending approvals.</div>'}
async function decide(id,w){try{show(await api(`/api/approvals/${id}/${w}`,{method:'POST'}),$('#apOut'))}catch(e){fail($('#apOut'),e)}loadApprovals()}
async function loadPerms(){
 const l=await api('/api/permissions');
 $('#pList').innerHTML='<p class="mu">ALLOW = runs now, ASK = needs your approval, BLOCK = never runs.</p><table><tr><th>Agent</th><th>Action</th><th>Permission</th></tr>'+l.map(p=>`<tr><td>${esc(p.agent)}</td><td>${esc(p.action)}</td><td><select onchange="setPerm('${esc(p.agent)}','${esc(p.action)}',this.value)">${['ALLOW','ASK','BLOCK'].map(v=>`<option${v===p.permission?' selected':''}>${v}</option>`).join('')}</select></td></tr>`).join('')+'</table>'}
async function setPerm(agent,action,permission){try{await api('/api/permissions',{method:'POST',json:{agent,action,permission}});toast('Saved')}catch(e){toast(e.message)}}
$('#reset').onclick=async()=>{await api('/api/permissions/reset',{method:'POST'});loadPerms();toast('Permissions reset')};
async function loadActivity(){
 const l=await api('/api/activity');
 $('#acList').innerHTML=l.length?'<table><tr><th>Time</th><th>Agent</th><th>Action</th><th>Status</th></tr>'+l.map(r=>`<tr><td>${fmt(r.created_at)}</td><td>${esc(r.agent)}</td><td>${esc(r.action)}</td><td><span class="badge ${esc(r.status)}">${esc(r.status)}</span></td></tr>`).join('')+'</table>':'<p class="mu">No activity yet.</p>'}
async function loadDocs(){
 docs=await api('/api/documents');
 $('#dList').innerHTML=docs.length?'<table>'+docs.map(d=>`<tr><td>#${d.id}</td><td>${esc(d.filename)}</td><td class="mu">${d.characters} chars</td><td><button class="sm" onclick="delDoc(${d.id})">Delete</button></td></tr>`).join('')+'</table>':'<p class="mu">No documents yet. Upload a PDF, TXT or MD file.</p>'}
async function delDoc(id){await api('/api/documents/'+id,{method:'DELETE'});loadDocs()}
$('#up').onclick=async()=>{const f=$('#file').files[0];$('#upErr').textContent='';if(!f)return;
 const fd=new FormData();fd.append('file',f);try{await api('/api/documents',{method:'POST',form:fd});$('#file').value='';toast('Uploaded');loadDocs()}catch(e){$('#upErr').textContent=e.message}};
async function loadProducts(){
 prods=await api('/api/products');
 $('#prList').innerHTML=prods.length?'<table><tr><th>Product</th><th>Price</th><th>Target</th><th></th></tr>'+prods.map(p=>`<tr><td>#${p.id} ${esc(p.name||'')}<br><a class="mu" href="${esc(p.url)}" target="_blank" rel="noopener noreferrer">${esc(p.url.slice(0,50))}</a></td><td>${p.last_price??'-'} ${esc(p.currency)}<br><span class="mu">${fmt(p.last_checked)}</span></td><td>${p.target_price??'-'} ${p.alert_enabled?'<span class="badge pending">alert on</span>':''}</td><td><button class="sm" onclick="chk(${p.id})">Check</button> <button class="sm" onclick="delProd(${p.id})">Delete</button></td></tr>`).join('')+'</table>':'<p class="mu">No products. Use Run agent, then Shopping Agent, then track product.</p>'}
async function chk(id){try{const r=await api('/api/agent/run',{method:'POST',json:{agent:'shopping',action:'check_price',payload:{product_id:id}}});toast(r.response||r.message);loadProducts()}catch(e){toast(e.message)}}
async function delProd(id){await api('/api/products/'+id,{method:'DELETE'});loadProducts()}
async function loadAlerts(){
 const l=await api('/api/notifications');
 $('#alList').innerHTML=l.length?l.map(n=>`<p><b>${esc(n.title)}</b> ${n.is_read?'':'<span class="badge pending">new</span>'}<br><span class="mu">${esc(n.body)} - ${fmt(n.created_at)}</span></p>`).join(''):'<p class="mu">No alerts yet. Set a price alert on a product.</p>';
 if(l.some(n=>!n.is_read)){await api('/api/notifications/read',{method:'POST'});setBadge('alerts',0)}}
const TABS={dash:['Dashboard',loadDash],run:['Run agent',loadRun],approvals:['Approvals',loadApprovals],perms:['Permissions',loadPerms],activity:['Activity',loadActivity],docs:['Documents',loadDocs],products:['Products',loadProducts],alerts:['Alerts',loadAlerts]};
$('#nav').innerHTML=Object.entries(TABS).map(([k,[n]])=>`<button id="tab_${k}" data-t="${k}">${n}</button>`).join('');
function go(t){document.querySelectorAll('.pane').forEach(p=>p.classList.toggle('on',p.id===t));
 document.querySelectorAll('nav button').forEach(b=>b.classList.toggle('on',b.dataset.t===t));TABS[t][1]().catch(e=>toast(e.message))}
$('#nav').onclick=e=>{const b=e.target.closest('button');if(b)go(b.dataset.t)};
async function boot(user){
 try{if(!user)user=await api('/api/auth/me');
  [agents,ROLES]=[await api('/api/agents'),(await api('/api/meta')).roles];
  $('#agent').innerHTML=Object.entries(agents).map(([k,v])=>`<option value="${k}">${esc(v.name)}</option>`).join('');
  $('#agent').onchange=actions;$('#action').onchange=fields;actions();
  $('#who').textContent=user.name||user.email;$('#auth').hidden=true;$('#shell').hidden=false;go('dash')}
 catch(e){logout()}}
setMode('login');if(token)boot();
setInterval(()=>{if(token&&!$('#shell').hidden)api('/api/stats').then(s=>{setBadge('alerts',s.unread_alerts);setBadge('approvals',s.pending_approvals)}).catch(()=>{})},60000);
</script></body></html>
'''
