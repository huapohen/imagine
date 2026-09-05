'use strict';
const $=s=>document.querySelector(s);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let token='', person=null, state=null, loading=false, renderSignature='';
const statuses={open:'进行中',blocked:'已阻塞',done:'已完成',pending:'待审批',approved:'已批准 · 本地保存',rejected:'已拒绝'};
const auditNames={'event.accepted':'事件已接收','agent.reminded':'新证据触发提醒','action.proposed':'提出待审批动作','action.approved':'批准并写入本地','action.rejected':'拒绝动作','alert.feedback':'提醒反馈','consent.granted':'授权业务结果分享','consent.revoked':'撤销并删除共享数据','business.shared':'明确分享业务结果','demo.seeded':'初始化合成演示','hardware.simulated':'设备状态模拟','plugin.registered':'插件权限已登记','a2a.submitted':'A2A 已提交','a2a.working':'A2A 正在处理','a2a.completed':'A2A 处理完成'};
function toast(msg){$('#toast').textContent=msg;$('#toast').hidden=false;clearTimeout(toast.timer);toast.timer=setTimeout(()=>$('#toast').hidden=true,4500)}
async function api(path,data){const r=await fetch(path,{method:data===undefined?'GET':'POST',headers:{Authorization:'Bearer '+token,...(data===undefined?{}:{'Content-Type':'application/json'})},body:data===undefined?undefined:JSON.stringify(data)});const value=await r.json();if(!r.ok)throw Error(value.error||'请求失败');return value}
function clock(t){return new Date(t*1000).toLocaleTimeString('zh-CN',{hour:'2-digit',minute:'2-digit',second:'2-digit'})}
function empty(icon,body){return `<div class="empty"><span>${icon}</span>${body}</div>`}
function metric(label,value,note){return `<article class="metric"><label>${esc(label)}</label><strong>${esc(value)}</strong><small>${esc(note)}</small></article>`}
function render(){
 const openEvidence=new Set([...document.querySelectorAll('details[data-evidence][open]')].map(x=>x.dataset.evidence));
 $('#metrics').innerHTML=metric('待推进的任务',state.tasks.filter(t=>t.state==='open').length,'留意进展，记住上下文')+metric('值得留意的变化',state.alerts.filter(a=>!a.feedback).length,'新证据才触发，不重复打扰')+metric('等待你决定',state.actions.filter(a=>a.status==='pending').length,'批准前，不执行动作')+metric('本地已保存',state.outbox.length,'外发次数始终为 0');
 const focus=state.preferences.focus_until>Date.now()/1000;
 $('#agentStatus').textContent=focus?'◌ 专注中 · 暂缓全部主动提醒':'● 灵伴正在留意';
 $('#alertCount').textContent=state.alerts.length+' 条提醒';
 $('#alerts').innerHTML=state.alerts.length?state.alerts.slice(0,8).map(a=>{const e=JSON.parse(a.explanation);return `<article class="alert ${esc(a.rule)}"><div class="alert-icon">${a.rule==='meeting'?'◷':a.rule==='rest'?'◌':'⚑'}</div><div class="alert-content"><h3>${esc(a.title)}</h3><p>${esc(e.reason)}</p><small>${clock(a.created)} · ${a.feedback?esc({useful:'已标记有帮助',dismissed:'已忽略',snooze:'已安静 10 分钟'}[a.feedback]):'新的变化'}</small><details data-evidence="${esc(a.id)}"><summary>为什么提醒我？</summary><p>${esc(e.decision)}<br>规则：${esc(e.rule)} · 证据：${esc(e.evidence_id||'用户休息计时器')}<br>${e.task_version?'任务版本：'+esc(e.task_version):''}</p></details>${a.feedback?'':`<div class="alert-buttons"><button data-feedback="useful" data-id="${esc(a.id)}">有帮助</button><button data-feedback="snooze" data-id="${esc(a.id)}">安静 10 分钟</button><button data-feedback="dismissed" data-id="${esc(a.id)}">忽略</button></div>`}</div></article>`}).join(''):empty('◎',focus?'专注时间，不打扰你。新提醒会等你回来。':'一切平静。试试上方场景，让灵伴留意新的变化。');
 document.querySelectorAll('details[data-evidence]').forEach(x=>x.open=openEvidence.has(x.dataset.evidence));
 $('#tasks').innerHTML=state.tasks.length?state.tasks.map(t=>`<div class="task ${esc(t.state)}"><span class="task-state">${t.state==='done'?'✓':t.state==='blocked'?'!':'·'}</span><div>${esc(t.title)}<small>${esc(t.project)} · v${t.version}${t.due?' · '+clock(t.due):''}</small></div><select aria-label="${esc(t.title)}的状态" data-task="${esc(t.id)}">${Object.entries(statuses).filter(([k])=>['open','blocked','done'].includes(k)).map(([k,v])=>`<option value="${k}" ${k===t.state?'selected':''}>${v}</option>`).join('')}</select></div>`).join(''):empty('◫','暂时没有任务，添加第一步吧。');
 $('#actions').innerHTML=state.actions.length?state.actions.slice(0,8).map(a=>`<article class="action"><h3>${esc(a.title)}</h3><p>${esc(a.body)}</p><div class="buttons">${a.status==='pending'?`<button class="small primary" data-decision="approve" data-id="${a.id}">批准 · 保存本地</button><button class="small" data-decision="reject" data-id="${a.id}">拒绝</button>`:''}<span>${esc(statuses[a.status])}</span></div></article>`).join(''):empty('◇','暂无待审批动作。会议场景会准备一份会议要点。');
 $('#outboxSummary').textContent='查看本地 outbox · '+state.outbox.length+' 条';
 $('#outbox').innerHTML=state.outbox.map(o=>{const x=JSON.parse(o.payload);return `<article class="action"><h3>${esc(x.title)}</h3><p>${esc(x.body)}</p><small>local-only · ${clock(o.created)}</small></article>`}).join('')||'<p class="section-note">没有已批准的本地记录。</p>';
 $('#consentToggle').textContent=state.consent?'撤销分享':'授权业务分享';
 $('#shareForm').querySelector('button').disabled=!state.consent;
 const hw=state.hardware;$('#orb').className='orb '+hw.led;$('#hardwareTitle').textContent=hw.screen;$('#hardwareText').textContent=hw.privacy?'隐私优先：真实板 SW3V3 断电、LED 关闭 / 引脚高阻；此处仅电脑 UI':focus?'专注时间已开启，主动提醒暂缓':'灯光与小屏状态由本地模拟器驱动';$('#ledLabel').textContent=hw.led.toUpperCase();$('#privacyToggle').textContent=hw.privacy?'关闭模拟隐私':'启用模拟隐私';$('#touchButton').disabled=hw.privacy;
 $('#audit').innerHTML=state.audit.slice(0,8).map(a=>`<div class="audit-row"><span>${clock(a.created)}</span><b>${esc(auditNames[a.kind]||a.kind)}</b><span title="${esc(a.detail)}">${esc(a.detail)}</span></div>`).join('');
}
function renderEnterprise(s){$('#enterpriseSummary').innerHTML=s.available?`<div class="metrics">${metric('授权分享群组',s.cohort,'至少 5 人方可展示')}${metric('明确分享的完成数',s.completed,'业务结果合计')}${metric('明确分享的阻塞数',s.blocked,'业务结果合计')}${metric('个人数据可见性','不可见','无个人明细与评分')}</div>`:`<div class="enterprise-suppressed"><div class="eyebrow">PRIVACY THRESHOLD ACTIVE</div><h2>分享人数不足，结果已隐藏。</h2><p>${esc(s.reason)}</p><span class="pill">撤销即时生效 · 不展示小样本结果</span></div>`}
async function refresh(){if(!person||loading)return;loading=true;try{if(person.role==='employee'){state=await api('/api/state');const signature=JSON.stringify(state)+(state.preferences.focus_until>Date.now()/1000);if(signature!==renderSignature){render();renderSignature=signature}}else renderEnterprise(await api('/api/enterprise/summary'))}catch(e){toast(e.message)}finally{loading=false}}
async function login(value){token=value.trim();renderSignature='';try{person=(await api('/api/me')).person;$('#login').hidden=true;$('#workspace').hidden=false;const enterprise=person.role==='enterprise';$('#employeeView').hidden=enterprise;$('#enterpriseView').hidden=!enterprise;$('.sidebar nav').hidden=enterprise;$('#roleLabel').textContent=enterprise?'企业成果工作台':'个人工作台';$('#personName').textContent=person.name;$('#greeting').textContent=enterprise?'团队的成果，在尊重中看见。':'把专注，留给重要的事。';$('#subtitle').textContent=enterprise?'仅展示明确授权的业务聚合。个人生活与状态，属于个人。':'我会留意新的变化，只在需要时轻轻提醒。';$('#agentStatus').hidden=enterprise;$('#token').value='';await refresh();await modelStatus()}catch(e){token='';person=null;$('#loginError').textContent=e.message}}
$('#loginForm').addEventListener('submit',e=>{e.preventDefault();login($('#token').value)});
$('#logout').addEventListener('click',()=>{token='';person=null;state=null;$('#workspace').hidden=true;$('#login').hidden=false;$('#loginError').textContent='已退出。访问令牌不保存在浏览器存储中。'});
async function run(fn,success){try{await fn();if(success)toast(success);await refresh()}catch(e){toast(e.message)}}
document.addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;
 if(b.dataset.scenario)run(()=>api('/api/scenarios',{name:b.dataset.scenario}),{meeting:'会议事件已摄入，灵伴已判断并准备审批要点。',blocked:'阻塞状态已记住。同一状态不会反复提醒。',focus:'25 分钟专注已开启，休息提醒将暂缓至专注结束。',resume:'专注已结束，已检查待触发的休息建议。',revoke:'分享已撤销，相关共享数据已清除。'}[b.dataset.scenario]);
 if(b.dataset.feedback)run(()=>api('/api/alerts/feedback',{id:b.dataset.id,feedback:b.dataset.feedback}),'反馈已记录');
 if(b.dataset.decision)run(()=>api('/api/actions/decide',{id:b.dataset.id,decision:b.dataset.decision}),b.dataset.decision==='approve'?'已批准，仅保存至本地 outbox。':'已拒绝，没有生成 outbox。');
 if(b.dataset.section){document.querySelectorAll('.nav-item').forEach(x=>x.classList.toggle('active',x===b));document.getElementById(b.dataset.section).scrollIntoView({behavior:'smooth'})}
});
$('#taskForm').addEventListener('submit',e=>{e.preventDefault();run(async()=>{await api('/api/events',{idempotency_key:crypto.randomUUID(),type:'task.upsert',payload:{id:crypto.randomUUID(),title:$('#taskTitle').value}});$('#taskTitle').value=''},'任务已记住')});
$('#tasks').addEventListener('change',e=>{const t=state.tasks.find(t=>t.id===e.target.dataset.task);if(t)run(()=>api('/api/events',{idempotency_key:crypto.randomUUID(),type:t.kind==='meeting'?'meeting.upsert':'task.upsert',payload:{id:t.id,title:t.title,state:e.target.value,due_at:t.due,project:t.project}}),'任务状态已更新')});
$('#actionForm').addEventListener('submit',e=>{e.preventDefault();run(async()=>{await api('/api/actions',{title:$('#actionTitle').value,body:$('#actionBody').value});e.target.reset()},'动作已提交，等待审批')});
$('#shareForm').addEventListener('submit',e=>{e.preventDefault();run(()=>api('/api/share',{completed:Number($('#completed').value),blocked:Number($('#blocked').value)}),'你确认的业务结果已分享')});
$('#consentToggle').addEventListener('click',()=>run(()=>api('/api/consent',{enabled:!state.consent}),state.consent?'已撤销并删除共享数据':'仅已授权，请继续明确分享结果'));
$('#privacyToggle').addEventListener('click',()=>run(()=>api('/api/hardware',{privacy:!state.hardware.privacy}),'模拟隐私状态已更新'));
$('#touchButton').addEventListener('click',()=>run(()=>api('/api/hardware',{touch:true,led:'teal',screen:'收到你的轻触 · 仅模拟'}),'触摸事件已模拟'));
$('#refresh').addEventListener('click',refresh);
$('#dateLabel').textContent=new Date().toLocaleDateString('zh-CN',{month:'long',day:'numeric',weekday:'long'})+' / A LITTLE MORE CLARITY';
const initial=new URLSearchParams(location.hash.slice(1)).get('token');
if(initial){history.replaceState(null,'',location.pathname);login(initial)}
setInterval(()=>{if(!document.hidden&&!document.querySelector('input:focus,textarea:focus,select:focus'))refresh()},2500);

$('#modelForm').addEventListener('submit',async e=>{e.preventDefault();const b=e.target.querySelector('button');b.disabled=true;try{const r=await api('/api/model/propose',{scenario:$('#modelScenario').value,synthetic_consent:$('#modelConsent').checked,idempotency_key:crypto.randomUUID()});toast(r.source==='model'?'模型草稿已生成，请核对后审批。':'已生成离线草稿（模型未启用、不可用或预算已用尽）。');await refresh()}catch(err){toast(err.message)}finally{b.disabled=false;$('#modelConsent').checked=false;await modelStatus()}});
async function modelStatus(){if(!person||person.role!=='employee')return;try{const s=await api('/api/model/status');$('#modelStatus').textContent=s.enabled?'临时模型测试 · '+s.model+' / '+s.reasoning_effort+' · 已调用 '+s.calls_used+'/'+s.max_calls+' 次 · 仅处理固定合成场景':'离线草稿 · 无模型调用';}catch(e){$('#modelStatus').textContent='模型状态暂不可用'}}
