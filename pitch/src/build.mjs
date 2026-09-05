import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import {pathToFileURL,fileURLToPath} from 'node:url';
import {Presentation,PresentationFile} from '@oai/artifact-tool';
import sharp from 'sharp';
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const REPO=path.dirname(ROOT);
const RUNTIME='/Users/lwblx/.cache/codex-runtimes/codex-primary-runtime';
process.env.RUNTIME_NODE_MODULES=path.join(RUNTIME,'dependencies/node/node_modules');
const SKILL='/Users/lwblx/.codex/plugins/cache/openai-primary-runtime/presentations/26.904.11930/skills/presentations';
const FONT='Hiragino Sans GB';
const C={ink:'#102D3C',navy:'#0B2333',teal:'#168E80',mint:'#8CE5D0',white:'#FAFCFB',muted:'#547078',line:'#CFDFDC',pale:'#E9F4F0',gold:'#D8B679'};
const run=process.argv[2] || new Date().toISOString().replace(/[:.]/g,'-');
const DIR=path.join(ROOT,'.build',run), OUT=path.join(ROOT,'deliverables',run); await fs.mkdir(DIR,{recursive:true});await fs.mkdir(OUT,{recursive:true});
const csv=async f=>{const a=(await fs.readFile(path.join(REPO,f),'utf8')).replace(/^\uFEFF/,'').trim().split(/\r?\n/).map(x=>x.split(','));return a.slice(1).map(row=>Object.fromEntries(a[0].map((h,i)=>[h,row[i]])));};
const skus=await csv('docs/business/financial-sku-economics.csv');const eco=skus.find(x=>x.sku==='S299');
if(Number(eco.price_incl_tax)!==299 || Number(eco.manufacturing_cost)!==108 || Number(eco.cac)!==45 || Number(eco.contribution_per_unit)!==66.51) throw new Error('商业模型已变化，请同步第12页讲稿与固定假设后重建。');
const scenarios=await csv('docs/business/financial-summary.csv');const base=scenarios.find(x=>x.scenario==='base');if(Math.round(Number(base.cumulative_profit_after_nre))!==-290211)throw new Error('基准情景已变化，请更新融资页讲稿。');
await sharp(path.join(ROOT,'assets/crystal-mouse.svg')).resize(1600,1440).png().toFile(path.join(ROOT,'assets/crystal-mouse.png'));
await sharp(path.join(ROOT,'assets/hardware-hero-source.png')).extract({left:220,top:280,width:1260,height:1140}).png().toFile(path.join(ROOT,'assets/hardware-product.png'));
const protocolSource=await fs.readFile(path.join(REPO,'software/lingban/protocols.py'),'utf8');
if(!protocolSource.includes("MCP_VERSION='2025-06-18'")||!protocolSource.includes("A2A_VERSION='0.3.0'"))throw new Error('协议版本变化，请同步第6页及讲稿。');
const hardwareProduct=await fs.readFile(path.join(ROOT,'assets/hardware-product.png'));
const product=await fs.readFile(path.join(ROOT,'assets/crystal-mouse.png'));
const p=Presentation.create({slideSize:{width:1280,height:720}});const meta=[];let s;
function rect(x,y,w,h,fill,line='none',lw=0){return s.shapes.add({geometry:'rect',position:{left:x,top:y,width:w,height:h},fill,line:{fill:line,width:lw}});}
function text(str,x,y,w,h,size=26,color=C.ink,bold=false){const z=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});z.text=str;z.text.style={typeface:FONT,fontSize:size,color,bold,verticalAlignment:'top',autoFit:'none',wrap:'square',insets:{left:0,right:0,top:0,bottom:0}};return z;}
function line(x,y,w,color=C.line){rect(x,y,w,1,color);}
function slide(title,note,source,dark=false,foot=''){s=p.slides.add();s.background.fill=dark?C.navy:C.white;meta.push({number:meta.length+1,title,note,source,foot});if(title){text(title,64,48,1140,74,42,dark?C.white:C.ink,true);line(64,140,1152,dark?'#284651':C.line);}text(String(meta.length).padStart(2,'0'),1164,672,50,28,17,dark?'#A5C4C6':C.muted);if(foot)text(foot,64,652,1070,52,16,dark?'#B6D2CE':C.muted);s.speakerNotes.textFrame.setText(note+'\n\n来源：'+source);return s;}
function imageProduct(x,y,w,h){s.images.add({blob:new Uint8Array(product),contentType:'image/png',alt:'原创透明晶鼠与微型天空城堡概念示意，非实物照片',position:{left:x,top:y,width:w,height:h},fit:'contain'});}
function labelBody(label,body,x,y,w=510,dark=false){text(label,x,y,w,46,28,dark?C.mint:C.teal,true);text(body,x,y+55,w,106,25,dark?C.white:C.ink);}
function table(values,widths,x=64,y=184,h=390,font=24,highlight=-1){const rows=values.length;const tb=s.tables.add({rows,columns:values[0].length,left:x,top:y,width:widths.reduce((a,b)=>a+b,0),height:h,columnWidths:widths,values});tb.borders.assign({fill:C.line,width:.5});tb.cells.block({row:0,column:0,rowCount:rows,columnCount:values[0].length}).assign({textStyle:{typeface:FONT,fontSize:font,color:C.ink},margins:{left:16,right:12,top:12,bottom:8},anchor:'center'});for(let r=0;r<rows;r++){tb.rows[r].height=h/rows;for(let c=0;c<values[0].length;c++){const cell=tb.getCell(r,c);cell.fill=r===0?C.ink:r===highlight?C.pale:C.white;cell.text.style={typeface:FONT,fontSize:font,color:r===0?C.white:C.ink,bold:r===0||r===highlight};}}return tb;}
const BP='docs/business/business-plan.md（2026-09-06）';const F='docs/research/findings.md（官方来源快照，2026-09-06）';
// 01
slide('', '灵伴LINGBAN暂定为项目品牌，晶鼠Crystal Mouse是首个系列，名称和商标仍待检索。我们希望用透明鼠标中的原创天空城堡，让主动式办公伙伴成为手边可见的存在。先帮助员工接住任务，再把本人批准的业务结果交给团队。本项目处于创始前验证阶段，没有可披露的客户、订单、收入或已完成硬件验证。今天希望讨论的是一套可证伪的产品路径和建议融资方案。',BP,false,'创始前验证阶段   2026.09   品牌与商标待检索');
text('灵伴',64,121,540,100,80,C.ink,true);text('LINGBAN',68,225,520,65,40,C.teal,true);text('手边的主动式办公伙伴',68,348,560,70,39,C.ink,true);text('晶鼠 Crystal Mouse',70,442,500,43,27,C.muted);imageProduct(560,63,700,580);text('原创产品概念示意',829,594,330,35,17,C.muted);
// 02
slide('工作中的下一步，常常等不到人来追问','设想一名项目协调者：下午还在等确认，傍晚回复到了，却没有回到交接清单。传统通知告诉他“有一条消息”，聊天式AI又要求他重新解释上下文。我们的需求假设是：当有新证据足以改变下一步时，用户愿意收到一次有理由、可以延后的轻提示。效率价值用真实任务的采纳和完成来验证，当前没有效率提升实绩。',BP,false,'需求假设，尚无访谈或效率实绩');
text('17:40',64,198,400,95,72,C.teal,true);text('回复已经到了\n交接仍然停在原地',64,308,570,150,44,C.ink,true);
labelBody('任务跨应用','截止时间、文档和等待状态\n缺少同一个任务上下文。',727,204,465);labelBody('提醒缺少理由','用户需要知道发生了什么变化，\n以及现在是否值得处理。',727,398,465);
//03
slide('一次主动协作的完整故事','这是合成场景。用户只授权一个交接任务及必要资料。系统等待新证据，安静窗口结束后通过灯光轻提示。触摸只打开电脑上的解释和草稿，不直接替用户执行。用户选择确认、稍后或者忽略。只有确认后才复制或导出结果，企业只收到本人另行批准分享的交接内容。我们跟踪本人是否认为有帮助，避免以提醒次数作为成功。',BP,false,'合成场景与拟实现交互，现场演示需清楚标识');
const flow=[['01','授权任务','仅选择这次交接的资料与截止时间'],['02','等待新证据','相关回复解除阻塞，安静窗口结束'],['03','轻提示与解释','灯光提示，触摸后展示依据及交接草稿'],['04','本人决定','确认、稍后或忽略，审批后复制或导出'],['05','明确分享结果','本人逐项批准业务交付物，个人回顾私有']];flow.forEach((r,i)=>{let y=183+i*85;text(r[0],64,y,75,50,33,C.teal,true);text(r[1],164,y,288,48,29,C.ink,true);text(r[2],489,y+3,700,48,26);if(i<4)line(164,y+66,1025);});
//04
slide('鼠标的价值需要独立证明','鼠标高频接触、自然可触达，有机会在屏幕通知之外提供低强度提示。透明城堡让状态可见，也可能带来传播辨识度。但高端鼠标用户可能不愿更换，有线、手型和灯光打扰也会降低接受度。因此用20人随机交叉试验，每人分别体验一周相同软件通知和一周灯光触摸，保持内容一致。门槛是确认率绝对提升至少15个百分点、打扰评分不变差，且至少8人在299元真实价格愿意购买或付明确可退订金。没有硬件增量就转向软件加可选配件。',BP,false,'20人小样本仅作方向性验证，不宣称统计显著或普适效率提升');
labelBody('手边可见、触手可及','低亮度灯表达状态，触摸后再展开信息。\n外观吸引首次尝试，任务价值决定留存。',64,194,1110);
line(64,359,1152);text('20人',64,399,340,78,60,C.teal,true);text('随机交叉体验',66,490,345,45,27);text('≥15个百分点',480,399,440,80,49,C.teal,true);text('硬件确认率绝对提升目标',482,490,500,45,26);text('≥8人',970,399,240,78,54,C.teal,true);text('299元购买意愿',972,490,235,48,25);text('若增量不成立，停止为硬件差异压库存。',64,580,1120,46,29,C.ink,true);
//05
slide('透明晶鼠，保留日常鼠标的可靠性','首款核心版沿用成熟USB HID有线鼠标底座，加独立ESP32-S3交互模块，负责灯、触摸和小屏。电脑承担AI，ESP32不运行大模型。原创微型城堡是静态摆件，无复杂运动机构。首期无摄像头、麦克风、生理传感，舒适度提示只基于用户设定时间。设备应有可见状态与物理静音控制，任何未来采集器都须另行评估并有遮挡。双线或合规hub可作为原型取舍，单线化要做供电、兼容和EMC检查。此图为硬件会话原创三维建模概念渲染，不是实物样机。图源hardware/renders/hero_raw.png，导入时裁去空白背景并保留产品主体。',BP+'；AGENTS.md；hardware/renders/hero_raw.png',false,'原创概念示意，尚无实物打样、板级验证、量产或认证完成证据');
s.images.add({blob:new Uint8Array(hardwareProduct),contentType:'image/png',alt:'硬件会话原创三维建模概念渲染，非实物',position:{left:64,top:179,width:586,height:447},fit:'contain'});labelBody('299元首发核心版','透明外壳与原创静态城堡\nRGB灯、触摸与小屏状态显示',717,185,485);labelBody('成熟HID底座＋独立交互模块','AI运行于电脑，HID保持独立。\n小屏仅显示简化状态，不存任务原文。',717,374,485);text('物理静音与状态指示为设计要求',717,580,490,40,22,C.teal,true);
//06
slide('Agent架构与协议实现子集','本稿以电脑端本地规则Agent和合成数据演示为验收范围，已实现任务证据、专注静默、审批与持久化。批准只写本地outbox，没有外部发送器。软件完成记录说明可选模型适配由主控独立验收，本稿不覆盖或验证其实现与模型调用。设备状态可模拟，软件完成记录已报告LB1集成代码与模拟测试修复完成，仍待实物验收。本次融资稿任务未复跑软件或固件测试，未接实机、未烧录或验证端到端硬件连通。MCP按2025-06-18实现每行UTF-8 stdio JSON-RPC 2.0，覆盖initialize、notifications/initialized、ping、tools/list、tools/call和错误响应。四个工具为tasks_list、events_ingest、action_propose、enterprise_summary，转发本地HTTP服务复用角色鉴权，不提供自动批准执行。A2A按0.3.0实现Agent Card、message/send、tasks/get，只支持blocking=true的新建文本摘要任务。submitted、working、completed在同步事务内写审计，终态与文本artifact持久化，查询按身份隔离，messageId按身份幂等。软件验收记录覆盖真实stdio/HTTP鉴权、握手与错误、任务生命周期/归属/重试和持久化；本融资稿同步只核对记录与源码，不将此称为官方认证。MCP未覆盖resources、prompts、sampling、elicitation、roots、subscriptions、cancellation、进度、分页、listChanged、HTTP transport、OAuth与官方SDK端到端互通。A2A未覆盖流式/SSE、取消、重订阅、推送、异步、多轮上下文、文件/数据part、扩展metadata、gRPC、HTTP+JSON binding、签名或扩展Agent Card及OAuth。普通REST接口不冒充MCP/A2A，软件子集测试不代表实机连通。','software/COMPLETION.md；docs/software/README.md；docs/software/protocols.md；software/lingban/protocols.py；software/lingban/mcp.py；software/test-output/latest-tests.txt',true,'本地合成演示子集，非官方互通或认证。LB1待实机验证、未验证硬件连通');
const arch=[{x:64,w:276,h:'设备交互',b:'HID底座独立设计\n灯／触摸／小屏可模拟\nLB1待实机验证'},{x:390,w:486,h:'电脑本地规则 Agent',b:'任务与证据、专注静默\n人工审批只写本地outbox\n无外部发送，模型适配另验收'},{x:926,w:290,h:'本地授权服务',b:'员工／企业角色鉴权\n明确提交的业务聚合\n企业连接器待接入'}];
arch.forEach(a=>{rect(a.x,179,a.w,169,'#143B47');text(a.h,a.x+19,196,a.w-38,44,26,C.mint,true);text(a.b,a.x+19,251,a.w-38,93,21,C.white);});rect(340,260,50,3,C.mint);rect(876,260,50,3,C.mint);
text('MCP 2025-06-18',64,371,555,48,30,C.mint,true);text('stdio JSON-RPC：握手、ping\ntools/list、tools/call（4个工具）',64,427,555,77,23,C.white);
text('A2A 0.3.0',708,371,508,48,30,C.mint,true);text('Agent Card、message/send、tasks/get\n同步文本摘要与持久化任务',708,427,508,77,22,C.white);
text('测试记录：真实stdio／HTTP鉴权、握手与错误、任务生命周期／归属／持久化。',64,521,1152,38,22,C.white);
text('MCP未覆盖：resources、prompts、HTTP、OAuth等，完整清单见讲稿。',64,568,1152,35,21,'#B6D2CE');
text('A2A未覆盖：流式、取消、推送、异步、多轮上下文等，未做官方SDK互通。',64,607,1152,35,21,'#B6D2CE');
//07
slide('员工掌握分享范围，企业获得业务结果','个人任务原文、私聊、浏览轨迹不进入企业看板，雇佣关系中的一次同意不等于一切数据共享。企业看到员工逐项批准的业务结果，以及至少5名不同授权参与者在固定周期内的汇总。不足人数不显示，禁止个人钻取，还须防止小切片和相邻时间窗口差分推断。人数阈值不是匿名化证明。用户需要能撤回授权和删除。我们明确禁止秘密录音摄像、键盘记录、绕过同意、情绪和生理信息评定员工，以及自动雇佣决策。',BP+'；'+F+'；个人信息保护法第5-7、13、15、24、28-29条',false,'≥5人是产品阈值，不能替代合法处理依据、访问控制与匿名化评估');
labelBody('个人可见','任务原文、资料与私人回顾\n本人选择范围，可撤回和删除。',64,194,524);labelBody('企业可见','逐项批准分享的业务结果\n≥5名授权参与者的固定周期聚合',708,194,508);line(64,387,1152);text('禁止个人钻取与敏感切片',64,425,1100,52,34,C.ink,true);text('无秘密录音摄像、键盘记录或情绪／生理员工评分。\n无自动雇佣决策，单次雇佣同意不等于全部共享。',64,506,1150,93,27);
//08
slide('首发只制造299元核心版','全部价格是人民币含税目标价。99元是普通透明鼠标，无AI伴随模块承诺。199元是灯触摸无屏版。299元是首发唯一制造版本，保留灯、触摸和小屏。499元套装和899元企业试点包在需求与验收成立后再推出，服务和支持均有明确期限与额度。1499和3999元仅为半年后生态探索，不接预售、不计收入。现阶段不同时采购五套模具。',BP,false,'99/199/499/899为定价验证及后续方案。1499/3999仅生态探索，不收预售');
table([['目标含税价','交付边界','推出条件'],['99元','普通透明有线鼠标，无伴随AI模块','有独立需求、OEM稳定'],['199元','灯＋触摸，无屏','共板降本与299元留存成立'],['299元','灯＋触摸＋小屏，离线规则可用','首发唯一制造SKU'],['499元','核心版＋底座／套件＋3个月限定服务','复购与推荐成立'],['899元','核心设备＋单席试点配置与限定支持','企业授权和安全验收通过']],[172,623,357],64,183,410,23,3);
//09
slide('Microduck与Violoop提供不同路线的启发','研究截至2026年9月6日。Microduck是Pollen Robotics官方公开的小型双足机器人项目，官方称约25厘米、800克和15个舵机。我们能借鉴可见人格与可维护架构，官方产品页标注入门预售价399美元，税运另计，2026年8月27日开启预售，但实际成交、订单或众筹成绩未证实。Violoop官网为预发布预约，展示HDMI输入、USB-HID和实体确认键，显示399美元起、预约优惠后369美元起。本次未证实交付或销量，算力和性能属于厂商主张。灵伴复用电脑算力降低硬件复杂度，代价是依赖本地安装、系统权限和电脑在线。未使用其视觉素材或未经许可的设计。',F+'；https://github.com/pollen-robotics/microduck ；https://pollen-robotics.com/microduck ；https://violoop.ai',false,'研究快照日期2026-09-06。官网主张不等于独立测试，GitHub stars不等于销量');
table([['对象','可确认的公开事实','对灵伴的启发与边界'],['Microduck','25cm双足机器人，15个舵机\n预售价399美元，税运另计','可见人格、可维护架构\n成交／订单／众筹成绩未证实'],['Violoop','官网预发布预约\n399美元起，优惠后369美元起','独立算力与实体确认路线\n交付／销量／性能未独立验证'],['灵伴方案','电脑Agent＋成熟HID底座\nESP32-S3仅负责交互','降低首期硬件复杂度\n依赖本地安装与电脑在线']],[211,448,493],64,187,409,24);
//10
slide('市场测算从可触达名单开始','目前没有足够可靠的官方中国AI鼠标细分销量，不使用泛AI万亿市场作为依据。第一阶段目标名单为200名个人和30个小团队，预计试用转化率20%与10%都只是销售假设，分别对应40人和3个团队的潜在试用。先安排20名自愿研究参与者，再争取3个10到30人的设计伙伴团队。下一层市场规模需要城市或行业公司数、适配工位数、允许安装Agent比例和预算接受度，每一项都有调查出处。目前没有已签客户。',BP,false,'名单规模与转化率均为计划假设，尚无客户、订单或收入实绩');
text('200名个人',64,192,560,80,54,C.teal,true);text('×20%试用转化假设＝40人',67,289,558,48,28);text('30个小团队',708,192,510,80,54,C.teal,true);text('×10%试用转化假设＝3个团队',711,289,505,48,26);line(64,393,1152);text('先完成20名自愿用户研究',64,432,1130,57,38,C.ink,true);text('再争取3个10–30人的设计伙伴团队。\n下一层规模按适配工位、安装权限与预算接受度逐项调查。',64,516,1130,102,28);
//11
slide('收入先来自硬件，服务先验证付费意愿','首阶段采用小批直销，不依赖尚未存在的订阅补贴硬件。1000台299元产品对应29.9万元含税商品流水，不是ARR。服务访谈价格为个人19元每月、团队39元每席每月，模型调用量、单位价格与退款未实测前不卖无限额度。只有100名持续支付19元的用户才对应2.28万元年化订阅毛额，当前留存尚未验证。个人可以只用离线规则或自己的模型凭据。企业支持按范围和额度交付，优先防止长账期与实施人力侵蚀收益。',BP,false,'全部为假设。财务模型暂不计订阅收入，融资不计营业收入');
text('29.9万元',64,196,620,91,64,C.teal,true);text('1000台 × 299元\n含税商品流水示例',67,304,560,100,30);labelBody('个人19元／月','服务访谈价，先实测调用成本与留存。\n100名付费者对应2.28万元年化订阅毛额。',707,202,505);labelBody('团队39元／席／月','服务访谈价，另行约定授权、\n模型额度、实施与支持边界。',707,404,500);text('直销试用案例积累后，再扩大渠道。',64,554,590,86,29,C.ink,true);
//12
slide('299元版的单位现金贡献估算','制造成本与现金贡献直接取商业模型S299行。当前1000台计划批量口径，完整制造成本108元，按含税价预留13%销项税且不抵扣进项，退款按售价4%、渠道3%、质保按制造成本2%，另含履约、支持、获客和退货物流。每台现金贡献66.51元，贡献率22.24%。制造目标良率和损耗口径须以商业成本定义为准，未取得供应商书面报价。月固定支出5.5万元时，约需827台该版本的贡献覆盖固定费用，尚不覆盖12万元前期NRE。不能将此处现金贡献当成净利润。',BP+'；docs/business/financial-sku-economics.csv；financial-assumptions.csv；outline.md',false,'1000台规模估算，108元含10元损耗预留，良率未验证。税款按13%销项预留、不抵进项。');
text(eco.contribution_per_unit+'元',64,194,505,92,64,C.teal,true);text('每台现金贡献估计',67,305,480,50,31);text((Number(eco.contribution_rate_on_gross_sales)*100).toFixed(2)+'%  贡献率',67,385,510,56,36,C.ink,true);text('约'+eco.units_to_cover_monthly_fixed_opex+'台／月\n覆盖5.5万元月固定支出',67,486,527,106,28);
text('小批成本170元时，贡献仅约3.27元。',67,599,535,33,22,C.muted);
const other=(Number(eco.channel_fee)+Number(eco.fulfillment)+Number(eco.warranty_reserve)+Number(eco.support_cost)+Number(eco.return_logistics_reserve)).toFixed(2);
table([['售价与扣项','元／台'],['含税目标售价','299.00'],['制造完整成本','108.00'],['税款及退款预留',(Number(eco.vat_reserve_no_input_credit)+Number(eco.refund_reserve)).toFixed(2)],['渠道、履约、质保、支持等',other],['获客成本',Number(eco.cac).toFixed(2)],['剩余现金贡献',eco.contribution_per_unit]],[428,172],616,185,426,23,6);
//13
slide('7天样机与30天试销的交付门槛','7天目标为5台可重复演示原型，预算上限估算1.5万元，不代表已批准支出。8到30天在累计12万元NRE内分批完成20人试用、10台EVT以及合规适用性和采购确认。30天只是争取试销的窗口：必须完成硬件、用户、安全合规和小批验收，才考虑50到100台受控交付，若不满足门槛就延后至M2至M3。目标D7仍启用比例至少60%，每周有帮助提醒用户至少50%，小批一次合格率至少95%。不能承诺7天量产或30天必出货。',BP+'；'+F,false,'计划目标，尚无完成证据。30天试销受硬件、安全合规、用户与采购验收门槛约束');
const gates=[['D1–D7','5台演示原型','HID独立可靠，授权链完整\n预算上限估算1.5万元'],['D8–D30','20人试用＋10台EVT','安全合规评估与采购确认\n累计12万元NRE内分批释放'],['达标后','50–100台受控交付','一次合格率目标≥95%\n未达门槛顺延至M2–M3']];gates.forEach((r,i)=>{const x=64+i*393;text(r[0],x,198,367,62,43,C.teal,true);text(r[1],x,293,367,80,32,C.ink,true);text(r[2],x,406,367,120,25);});text('试用门槛：D7仍启用≥60%，每周“有帮助”提醒用户≥50%。',64,575,1150,49,26);
//14
slide('半年生态，按留存与交付证据推进','M1证明任务闭环，M2受控交付，M3依据真实使用决定是否继续鼠标。M4再开放灯、触摸和状态协议及一个参考配件。M5邀请少量开发者做经过人工审核的只读插件。M6才决定199元无屏版或桌面灯是否立项。分批累计1000台是验证目标，财务基准情景截至M6为910台，不能把目标当预测。每个新硬件必须具备独立需求、BOM、售后责任和现金门槛。1499与3999元生态概念不接预售，不计收入。',BP+'；docs/business/financial-scenarios.csv',false,'半年路线为目标，财务基准M1–M6累计910台。1499/3999元生态概念不计收入');
const roadmap=[['M1','任务闭环','授权、证据、审批'],['M2','受控交付','质量与售后记录'],['M3','留存决策','继续鼠标或转软件'],['M4','开放交互协议','一个参考配件'],['M5','少量开发者','审核后的只读插件'],['M6','下一款立项','无屏版或桌面灯']];roadmap.forEach((r,i)=>{const x=64+(i%3)*393,y=i<3?193:415;text(r[0],x,y,350,52,36,C.teal,true);text(r[1],x,y+62,365,52,30,C.ink,true);text(r[2],x,y+121,365,48,25);});
//15
slide('待招团队与外部专业能力','这里是责任岗位设计，不是已有团队履历。当前没有可核验的创始团队背景可以披露。核心计划按三人团队加按次外包推进：产品与商业负责人、本地Agent工程师、硬件与供应链负责人。外部按需要采购工业设计、测试、隐私法律和认证能力。本轮精简验证模型月固定成本5.5万元，其中人员4.2万元，属于预算假设。关键岗位到位和职责落实是融资后释放扩张预算的前置条件。',BP+'；docs/business/financial-assumptions.csv',false,'岗位与预算均为计划，未提供可核验的成员姓名、履历或招聘完成证据');
table([['计划岗位','优先交付责任'],['产品／商业负责人','用户研究、定价验证、设计伙伴与现金纪律'],['本地Agent工程师','任务证据、权限审批、可恢复执行与发布'],['硬件／供应链负责人','HID独立链路、结构装配、质量与交付'],['按次外部专业能力','工业设计、测试、隐私法律与合规认证']],[380,772],64,190,345,26);
text('精简验证模型：月固定支出5.5万元，其中人员4.2万元。',64,576,1152,52,28,C.teal,true);
//16
slide('建议融资500万元，按证据分段投入','融资500万元是建议目标，没有融资承诺或已到账资金。本轮融资用途建议为：产品和Agent研发200万元，硬件工程、试制和合规100万元，用户验证与设计伙伴60万元，量产准备及周转80万元，预备金60万元，合计500万元。不是一次性批准支出。先按BP的1.5万元原型和累计12万元NRE门槛释放，再凭需求、合规、留存和现金证据扩展。商业计划第11节已列明这套融资建议，并明确500万元并非用户指定金额。财务CSV是独立的60万元假设起始现金模型，NRE12万元、月固定支出5.5万元。基准10个月含税流水158.09万元，累计亏损29.02万元，期末现金60494.30元（约6.05万元），最低现金4.59万元。500万元扩张预算尚无同口径分月现金模型，不报告其跑道或回报。',BP+'第11节；docs/business/financial-model.md；docs/business/financial-summary.csv；docs/business/financial-assumptions.csv',false,'500万元及用途为融资建议，未获承诺。60万元精简验证模型为独立情景，不能推算500万元跑道');
text('500万元',64,197,528,92,66,C.teal,true);text('建议融资目标',67,306,540,51,32);text('按原型、需求、合规和\n交付证据释放预算',67,394,520,118,34,C.ink,true);text('60万元精简模型（10个月）\n期末现金6.05万元，累计亏损29.02万元',67,543,520,89,23,C.muted);
table([['建议用途','万元','占比'],['产品与Agent研发','200','40%'],['硬件试制与合规','100','20%'],['用户验证与设计伙伴','60','12%'],['量产准备与周转','80','16%'],['预备金','60','12%'],['合计','500','100%']],[365,119,116],616,184,438,23,6);
//17
slide('风险对应明确的停止条件','核心风险首先是任务价值和硬件增量不成立，其次是人体工学、材料耐久和批次质量，以及权限误用和现金压力。如果20人中D7仍启用低于40%，两轮改进无改善就停止备货。连续两批退款大于10%或者制造一次良率低于90%，冻结新采购。任何未经授权外传或者外部动作都要求立即停用相关功能并修复、通知受影响者。未来90天现金预测转负时，停止非必要NRE和营销，优先完成交付、退款与保修。竞争方容易复制单个提醒功能，壁垒要通过可靠授权、低打扰策略和可重复任务价值积累。',BP,false,'阈值是管理规则，尚无达到或触发的实际测试记录');
table([['风险','停止或纠偏条件'],['用户不持续启用','D7仍启用<40%，两轮改进无效，停止备货'],['质量与售后失控','连续两批退款>10%或制造一次良率<90%，冻结新批'],['授权与信任受损','发现未经授权外传／动作，立即停用并修复通知'],['现金与库存压力','未来90天现金预测转负，暂停非必要NRE和营销']],[360,792],64,194,369,25);
text('可累积资产：可信授权、任务证据质量、低打扰策略与可靠交付。',64,588,1140,46,26,C.teal,true);
//18
slide('', '我们希望投资人共同验证的核心判断是：员工是否因为少一次遗漏、顺利完成一次交接而继续启用。先把299元晶鼠和本地Agent闭环做实，再以明确授权的结果支持团队。当前讨论的500万元是融资建议，后续预算应按里程碑释放。第10个月设为战略检查点，选择可以是继续经营、融资、合作或者有序停止。“10个月1亿美元退出”只能作为极端目标情景，没有估值依据、投资承诺或收购方保证，也不用于现金流模型。下一步的证据是可重复的5台原型、20人试用及获验收的小批交付。',BP+'；用户融资叙事要求',true,'10个月1亿美元退出仅为目标情景，无估值依据或收购承诺，不进入财务预测');
text('让下一步，更容易发生',64,135,1138,96,66,C.white,true);text('员工先受益\n团队获得本人批准的业务结果',68,297,1130,151,43,C.mint,true);text('建议融资500万元，验证299元晶鼠的持续任务价值。',68,508,1120,70,31,C.white);text('第10个月战略检查点：持续经营、合作或有序停止。',68,581,1120,45,24,'#B6D2CE');
// Export and finalize.
const {finalizePresentation}=await import(pathToFileURL(path.join(SKILL,'container_tools/artifact_tool_utils.mjs')).href);
const candidate=path.join(DIR,'candidate.pptx');await(await PresentationFile.exportPptx(p)).save(candidate);
await fs.writeFile(path.join(DIR,'slides.json'),JSON.stringify(meta,null,2));
const finalPath=path.join(OUT,'lingban-vc-deck.pptx');
const result=await finalizePresentation({workspaceDir:ROOT,candidatePath:candidate,finalPath,pythonExecutable:path.join(RUNTIME,'dependencies/python/bin/python3'),integrityValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit',...[8,9,12,15,16,17].flatMap(n=>['--require-native-table-slide',String(n)])],explicitTotalSlideCount:18,tableArithmeticContracts:[{slide:16,table:1,label_column:0,total_row:6,value_columns:[1],component_rows:[1,2,3,4,5]}],requiredNativeTableOwnerSlides:[8,9,12,15,16,17],requiredNativeChartOwnerSlides:[],fontPolicy:{basis:'design',families:[FONT]},verifyArtifactToolImport:true,receiptPath:path.join(DIR,'validation.json')});
await fs.writeFile(path.join(OUT,'speaker-notes.md'),'# 灵伴 LINGBAN VC演示稿逐页讲稿\n\n18页，建议12–15分钟。所有计划、预算和目标均无实绩。\n\n'+meta.map(m=>`## ${String(m.number).padStart(2,'0')} ${m.title|| (m.number===1?'灵伴 LINGBAN':'让下一步，更容易发生')}\n\n${m.note}\n\n来源：${m.source}\n`).join('\n'));
const sourceFiles=['docs/business/business-plan.md','docs/business/outline.md','docs/business/financial-sku-economics.csv','docs/business/financial-summary.csv','docs/business/financial-assumptions.csv','docs/business/financial-model.md','docs/business/financial-scenarios.csv','docs/research/findings.md','docs/research/sources.json','software/COMPLETION.md','docs/software/README.md','docs/software/protocols.md','software/lingban/protocols.py','software/lingban/mcp.py','software/test-output/latest-tests.txt','hardware/renders/hero_raw.png','hardware/renders/README.md'];
const hashes=[];for(const f of sourceFiles){hashes.push({path:f,sha256:crypto.createHash('sha256').update(await fs.readFile(path.join(REPO,f))).digest('hex')});}
await fs.writeFile(path.join(DIR,'source-manifest.json'),JSON.stringify({capturedAt:new Date().toISOString(),sources:hashes},null,2));
await fs.writeFile(path.join(ROOT,'.build','latest.json'),JSON.stringify({run,dir:DIR,out:OUT,pptx:finalPath},null,2));
console.log(JSON.stringify({run,out:OUT,sha256:result.finalSha256,slides:18},null,2));
