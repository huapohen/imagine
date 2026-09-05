#!/usr/bin/env python3
"""Build a 16-page Chinese BP from reviewed narrative and live financial CSVs.
Uses only local runtime dependencies. No credentials, network, or font copying.
"""
from pathlib import Path
import csv, hashlib, json, re
from xml.sax.saxutils import escape
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor, Color, white
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle
from pypdf import PdfReader

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
BUS=ROOT/'docs/business'
OUT=HERE/'lingban-business-plan.pdf'
FONT=Path('/System/Library/Fonts/Supplemental/Arial Unicode.ttf')
pdfmetrics.registerFont(TTFont('CN',str(FONT)))
W,H=595.276,841.89
M=44;CW=W-2*M
INK='#102D3C';TEAL='#168E80';MUTED='#547078';PALE='#E9F4F0';LINE='#CFDFDC';GOLD='#D8B679';NAVY='#0B2333';RED='#B86853'
C=canvas.Canvas(str(OUT),pagesize=(W,H),pageCompression=1)
C.setTitle('灵伴 LINGBAN｜晶鼠商业计划书｜2026年9月')
C.setAuthor('Imagine / 灵伴项目')
C.setSubject('创始前验证阶段商业计划，含估算财务、建议融资、交付门槛与官方来源')
LAYOUT=[];PAGE=0

def norm(t):return t.replace('—','-').replace('–','-').replace('‑','-').replace('≥','>=')
def rect(x,top,w,h,fill,stroke=None,r=0):
 C.setFillColor(HexColor(fill));C.setStrokeColor(HexColor(stroke or fill))
 if r:C.roundRect(x,H-top-h,w,h,r,stroke=bool(stroke),fill=1)
 else:C.rect(x,H-top-h,w,h,stroke=bool(stroke),fill=1)
def text(t,x,top,size=11,color=INK):
 C.setFillColor(HexColor(color));C.setFont('CN',size);C.drawString(x,H-top-size,norm(t))
 LAYOUT.append({'page':PAGE,'type':'text','top':top,'bottom':top+size,'text':t})
def p(t,x,top,w,h=200,size=10.5,leading=17,color=INK):
 style=ParagraphStyle('body',fontName='CN',fontSize=size,leading=leading,textColor=HexColor(color),wordWrap='CJK',spaceAfter=0)
 # Explicit <br/> only; escape all other content.
 t=escape(norm(t)).replace('&lt;br/&gt;','<br/>')
 q=Paragraph(t,style);aw,ah=q.wrap(w,h)
 if ah>h+0.1:raise ValueError(f'Page {PAGE}: paragraph overflow {ah}>{h}: {t[:80]}')
 if top+ah>788:raise ValueError(f'Page {PAGE}: paragraph crosses footer {top+ah}')
 q.drawOn(C,x,H-top-ah);LAYOUT.append({'page':PAGE,'type':'paragraph','top':top,'bottom':top+ah,'text':t})
 return ah

def table(headers,rows,widths,top,size=9.3,pad=8,maxh=520):
 sty=ParagraphStyle('cell',fontName='CN',fontSize=size,leading=size*1.55,textColor=HexColor(INK),wordWrap='CJK')
 hs=ParagraphStyle('head',parent=sty,textColor=white,fontSize=size)
 data=[[Paragraph(escape(norm(str(v))),hs) for v in headers]]+[[Paragraph(escape(norm(str(v))),sty) for v in row] for row in rows]
 t=Table(data,colWidths=widths,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),HexColor(TEAL)),('ROWBACKGROUNDS',(0,1),(-1,-1),[HexColor('#FFFFFF'),HexColor('#F0F6F3')]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),pad),('RIGHTPADDING',(0,0),(-1,-1),pad),('TOPPADDING',(0,0),(-1,-1),pad),('BOTTOMPADDING',(0,0),(-1,-1),pad),('LINEBELOW',(0,0),(-1,0),0.5,HexColor(LINE))]))
 _,th=t.wrap(CW,maxh)
 if th>maxh or top+th>786:raise ValueError(f'Page {PAGE}: table overflow {th} top {top}')
 t.drawOn(C,M,H-top-th);LAYOUT.append({'page':PAGE,'type':'table','top':top,'bottom':top+th})
 return top+th

def line(top):
 C.setStrokeColor(HexColor(LINE));C.setLineWidth(.6);C.line(M,H-top,W-M,H-top)
def label(t,top):text(t,M,top,12,TEAL)
def callout(t,top,h=70):
 rect(M,top,CW,h,PALE,r=6);p(t,M+15,top+12,CW-30,h-22,11,18)
def start(chapter,title,sub=''):
 global PAGE
 PAGE+=1
 rect(0,0,W,H,'#FAFCFB');text('灵伴  LINGBAN',M,25,9,TEAL);text('BUSINESS PLAN  /  2026.09',W-230,25,8.5,MUTED)
 text(chapter,M,61,9,TEAL);p(title,M,80,CW,65,25,33)
 if sub:p(sub,M,123,CW,40,10,16,MUTED)
 line(786);text('创始前验证阶段 · 数字均须按标示区分事实、假设与建议',M,801,7.7,MUTED);text(f'{PAGE:02d} / 16',W-80,801,8,MUTED)
def end():C.showPage()
def read(name):
 with (BUS/name).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
eco=read('financial-sku-economics.csv');summ=read('financial-summary.csv');monthly=read('financial-monthly.csv')
s299=next(x for x in eco if x['sku']=='S299');base=next(x for x in summ if x['scenario']=='base')
assert s299['contribution_per_unit']=='66.51'
assert round(float(base['cumulative_profit_after_nre']))==-290211

# 01: cover
PAGE=1
rect(0,0,W,H,'#FAFCFB');text('创始前验证阶段  /  2026年9月6日',M,35,9,TEAL)
text('灵伴',M,74,43,INK);text('LINGBAN',M+110,93,22,TEAL)
text('手边的主动式办公伙伴',M,141,24,INK)
text('晶鼠 Crystal Mouse · 商业计划书',M,183,12,MUTED)
C.drawImage(str(ROOT/'hardware/renders/hero_raw.png'),0,H-693,width=W,height=W*1500/1800,mask='auto')
rect(M,658,CW,108,'#FFFFFF',r=8)
p('先帮助员工接住任务，\n再把本人批准的业务结果交给团队。'.replace('\n','<br/>'),M+16,673,CW-32,50,16,24)
p('原创三维概念渲染，非实物或量产证明。品牌与商标待检索。',M+16,734,CW-32,25,8.5,13,MUTED)
text('融资、销量、成本和时间表均按事实层级标注；无已确认投资或客户实绩。',M,793,8,MUTED)
end()

# 02
start('01  /  执行摘要','先证明持续有用，再承担库存','员工先受益；企业价值来自被批准的交付结果，而非个人监控。')
p('Imagine / 灵伴用成熟有线鼠标底座与独立灯、触摸、小屏模块，把电脑本地agent的主动提醒带到手边。首发只制造目标售价299元的核心版，以真实任务留存检验硬件是否值得存在。',M,174,CW,85,12,20)
for i,(a,b) in enumerate([('299元','首发目标价'),('66.51元','单台贡献估算'),('20人','自愿研究目标')]):
 x=M+i*(CW/3);rect(x,278,CW/3-10,93,PALE,r=5);text(a,x+13,290,24,TEAL);p(b,x+13,331,CW/3-28,28,9.5,15)
label('当前状态',402)
p('有可审阅的产品方案、原型实现方向、商业模型和公开研究；没有可披露的已融资、订单、收入、用户留存或完成硬件测试结果。所有指标均为待检验门槛。',M,430,CW,80)
label('三个最重要的决策',523)
table(['判断','证据与动作'],[['用户是否持续需要','D7仍启用目标>=60%，每周至少一次有帮助提醒者>=50%。'],['硬件是否有额外价值','与相同软件通知交叉比较；确认率增量目标>=15个百分点，打扰不增加。'],['交付是否值得扩大','真实报价、质量/合规和单位贡献通过；现金覆盖90天必要义务。']],[135,CW-135],551,size=9.7,pad=9,maxh=200)
p('阅读路径：产品与信任 03-05｜验证与市场 06-07｜经济与融资 08-11｜交付与组织 12-15｜来源 16',M,742,CW,38,8.5,14,MUTED)
end()

# 03
start('02  /  用户与任务','主动性来自新证据，而非刷存在感','假设：工作遗漏源于跨应用上下文断裂和提醒过载，需要真实任务验证。')
p('首批面向有自主软件安装权、经常处理多文档和多任务的知识工作者：产品经理、项目协调者、独立开发者和小型服务团队。暂不进入医疗、涉密办公、金融交易或严禁外围设备的组织。',M,174,CW,85)
table(['真实场景','最小授权范围','介入与成功证据'],[['下班前交接','本人任务、截止时间、本人更新','临近截止且有未交接新状态；给草稿，由本人确认完成。'],['等待反馈','用户选定任务及相关消息增量','新回复解除阻塞，安静窗口后提醒；本人标有帮助。'],['恢复长期任务','用户自建目标和选择的资料','新证据改变下一步；中断后能够恢复，建议有理由。'],['专注陪伴','本人手动设置时段','允许的结束/休息节点轻提示；愿意保留且不感到评判。']],[88,150,CW-238],286,size=9.6,pad=10,maxh=330)
label('“陪伴”的具体边界',630)
p('陪伴是可关闭的语气、可见状态和轻量反馈。无情感索取、内疚式催促、老板正在看等操控设计；休息依据用户选择的时间，不推断疲劳、抑郁或健康状况。',M,658,CW,76)
end()

# 04
start('03  /  产品与架构','成熟鼠标链路，与AI模块分离','采用电脑已有算力，换取更低的首期硬件复杂度。')
for top,title,body in [(178,'01  标准USB有线鼠标OEM底座','移动、按键与滚轮走成熟HID。AI模块断开或本地agent退出时，鼠标仍应工作；必须实测验证。'),(309,'02  ESP32-S3独立交互模块','离散共阳RGB灯、GPIO4/5/6 PWM；触摸与小屏仅显示简化状态。最终引脚按硬件规格冻结，不缓存任务原文。'),(440,'03  电脑本地agent','任务、证据、安静窗口、去重与审批；可选云模型只接收明确授权的必要内容。无模型时保留本地规则降级。')]:
 rect(M,top,CW,110,PALE,r=6);text(title,M+14,top+12,13,TEAL);p(body,M+14,top+43,CW-28,60,10.5,17)
label('首期取舍与实现边界',582)
p('原型接受双USB线或经评估的hub；单线化需验证供电、兼容与EMC。USB-OTG与Serial-JTAG共享PHY，不能假设同时独立工作。[S6]\n不做电池、无线产品宣传、常驻录屏、锁屏远程操作、独立大模型算力、机器人运动。触摸只是交互入口，不宣传不可绕过的安全芯片隔离。'.replace('\n','<br/>'),M,613,CW,120)
p('复用Active Agent的事件/任务/审批架构概念；实际连接器、协议兼容与安装体验另行验收。[S8]',M,747,CW,30,8.5,14,MUTED)
end()

# 05
start('04  /  信任与公司授权','采购设备，不等于获得个人数据','自愿、按来源、按结果授权；员工可拒绝、暂停和撤回。')
table(['个人可见','企业可见'],[['任务原文、选择的资料、私人回顾和个人偏好；默认本地保存。','本人逐项批准分享的业务结果；满足人数和防推断条件的固定周期汇总。'],['基本鼠标能力不因拒绝共享或停止订阅而失效。','不能通过采购合同或一次雇佣同意默认获得全部信息。']],[CW/2,CW/2],178,size=10,pad=12,maxh=235)
label('最低五人，只是第一道门',440)
p('至少5名不同授权参与者才显示聚合；还须限制小切片、极端值、相邻窗口差分推断、自由文本识别与个人钻取。人数阈值不是匿名化证明或法律免责。',M,469,CW,75)
callout('禁止隐蔽录音/摄像、键盘记录、私聊采集、键鼠活跃度排名，以及情绪、生理、健康或个人绩效评分。无自动雇佣决策。',568,84)
p('外部发送/写入前展示对象、内容与范围，再批准。撤回与删除入口必须可用；已分享结果的处理需按合同和合法留存义务明确。个人信息保护法要求最小必要、透明与相应处理依据；跨境、角色和处理合同按实际部署审查。[S5]',M,682,CW,86,10,16)
end()

# 06
start('05  /  可证伪验证','20人研究，先剥离硬件增量','所有数值为预先设定目标，无完成或统计显著性声明。')
label('随机交叉体验',178)
p('同一位参与者各体验一周软件通知与一周鼠标灯/触摸通知，随机安排顺序；保持任务和内容相同。记录确认率、处理延迟、关闭频次、主观打扰和每周“有帮助”的主动提醒。',M,206,CW,85)
table(['待验证问题','拟定门槛','失败后的动作'],[['持续使用','D7仍启用>=60%；每周有帮助者>=50%','两轮改进后D7<40%，停止备货。'],['硬件增量','确认率绝对增量>=15个百分点；打扰不增加','改为软件或可选桌面配件。'],['真实价格选择','至少8人愿在299元选择购买或明确可退订金','区分熟人支持与办公需求，调整定位。'],['交付质量','小批一次良率>=95%；目标退款<=5%','连续两批退款>10%或一次良率<90%，冻结采购。']],[112,191,CW-303],315,size=9.4,pad=10,maxh=325)
label('观测纪律',669)
p('北极星是“每周至少一次确认有帮助的用户数”，而非灯光互动数。上传研究数据需自愿授权、最少化；保留失败和负反馈。小样本仅用于方向判断，不宣称普适效率提升。',M,699,CW,74,10,16)
end()

# 07
start('06  /  市场与竞争','从可触达名单开始，不套万亿市场','没有可靠的中国AI鼠标细分销量，本项目不报告未经支撑的TAM。')
rect(M,176,CW,97,PALE,r=6);text('200名个人 × 20% = 40人',M+15,189,18,TEAL);text('30个小团队 × 10% = 3个团队',M+15,224,17,INK)
p('上方是名单目标与试用转化假设，尚无客户。先20人研究，再争取3个10-30人设计伙伴团队；后续市场按适配工位、安装权限与预算接受度逐项调查。',M,292,CW,77)
table(['参考对象','可证实的官方信息','本项目取舍'],[['Microduck','约25cm/800g、15舵机；官方预售399美元，税运另计。[S1-S3]','借鉴可见人格与可维护架构；不引入运动复杂度。'],['Violoop','预发布预约；399美元起、优惠后369美元起；HDMI/USB-HID路线。[S4]','用电脑算力降低硬件复杂度，承认安装和权限依赖。'],['大厂鼠标/软件助手','单个灯/屏与提醒功能容易复制；尚无独占壁垒。','累积任务体验、授权信任、可靠交付与用户推荐。']],[85,224,CW-309],399,size=9.4,pad=10,maxh=255)
p('Microduck stars不等于销量；Violoop性能与token节约仅为厂商主张。本次未证实两者订单、交付或众筹“爆卖”。不使用其商标素材、网页设计或未明确许可的硬件文件。',M,698,CW,76,9.5,16,MUTED)
end()

# 08
start('07  /  产品组合与收入','首发只制造299元核心版','其余档位用于价格与包装验证，不同时采购五套模具。')
table(['目标含税价','交付边界','推出条件'],[['99元','普通透明有线鼠标；无伴随AI模块承诺','OEM稳定且有独立需求'],['199元','灯与触摸，无屏','299留存成立、共板降本成立'],['299元','灯、触摸、小屏；本地规则基础任务','首批唯一制造SKU'],['499元','核心版、桌面底座/外观套件、3个月限定服务','套装需求成立，明确服务额度'],['899元','核心设备、企业配置/培训、3个月限定支持','授权与安全验收，实施成本可控'],['1499 / 3999元','桌面计算底座 / 团队终端概念','未定规格和BOM；不预售、不计收入']],[85,253,CW-338],176,size=9.4,pad=10,maxh=390)
label('硬件先成立，服务不做无限承诺',609)
p('个人19元/月、团队39元/席/月仅为服务访谈价，未计入模型。实测调用成本、额度、退款和留存后再上线。1000台×299元=29.9万元含税商品流水，不是ARR；100名持续支付19元的用户才对应2.28万元年化订阅毛额。',M,641,CW,99)
p('渠道：创始人真实案例 > 自愿试用 > 小批直销 > 企业设计伙伴；前100台不铺经销、不做大额投流。',M,751,CW,28,8.5,14,MUTED)
end()

# 09
start('08  /  单台经济','299元售价，66.51元贡献估算','1000台规模设计目标；无工厂书面报价，不是净利润。[S7]')
# Stacked cost composition
parts=[('制造',108,TEAL),('税预留',34.4,'#70B6A6'),('获客',45,'#A7CDC2'),('其余费用',45.09,GOLD),('贡献',66.51,NAVY)]
x=M
for name,v,col in parts:
 ww=CW*v/299;rect(x,188,ww,42,col);x+=ww
x=M
for i,(name,v,col) in enumerate(parts):
 xx=M+(i%3)*174;yy=247+(i//3)*29;rect(xx,yy+2,8,8,col);text(f'{name} {v:.2f}',xx+14,yy,9.5)
p('其余45.09元：渠道8.97、退款11.96、履约12、质保2.16、支持8、逆向物流2。税按13%销项预留且不抵进项，偏保守；实际税务口径待会计确认。',M,319,CW,66,9.5,16)
table(['制造BOM项目','元/台','制造BOM项目','元/台'],[['OEM底座','19','透明壳/结构','11'],['ESP32-S3模块','16','小屏及排线','15'],['灯/导光/触摸','5','PCB/电源/连接等','14'],['装配/100%测试','12','包装/标签','6'],['损耗/返工预留','10','完整制造合计','108']],[176,61,209,CW-446],409,size=9.4,pad=8,maxh=255)
callout('仅299版约需827台/月覆盖5.5万元固定支出，尚未收回12万元NRE。小批制造成本若升至170元，单台贡献仅约3.27元。',688,78)
end()

# 10
start('09  /  现金与情景','增长会占用现金，不会自动盈利','60万元假设起始现金；12万元NRE；月固定支出5.5万元。[S7]')
# vector cash chart
cx,ct,cw,ch=M+36,199,CW-47,218
colors={'downside':RED,'base':TEAL,'upside':NAVY};names={'downside':'下行','base':'基准','upside':'上行'}
lo,hi=-5,55
for v in [-5,0,15,30,45]:
 yy=H-(ct+ch-(v-lo)/(hi-lo)*ch);C.setStrokeColor(HexColor(LINE));C.setLineWidth(.5);C.line(cx,yy,cx+cw,yy);text(str(v),M, H-yy-6,8,MUTED)
for sc in colors:
 data=sorted([r for r in monthly if r['scenario']==sc],key=lambda z:int(z['month']))
 path=C.beginPath()
 for i,r in enumerate(data):
  xx=cx+int(r['month'])/10*cw;yy=H-(ct+ch-(float(r['ending_cash'])/10000-lo)/(hi-lo)*ch)
  if i==0:path.moveTo(xx,yy)
  else:path.lineTo(xx,yy)
 C.setStrokeColor(HexColor(colors[sc]));C.setLineWidth(2);C.drawPath(path)
for i in range(11):text(str(i),cx+i/10*cw-3,ct+ch+9,8,MUTED)
text('万元',M,180,8,MUTED);text('月份（0为一次投入后）',M+280,450,8,MUTED)
for i,sc in enumerate(colors):rect(M+i*93,451,13,4,colors[sc]);text(names[sc],M+19+i*93,443,9)
rows=[]
for s in summ:rows.append([names[s['scenario']],str(s['total_units']),f"{float(s['total_gross_sales'])/10000:.2f}",f"{float(s['cumulative_profit_after_nre'])/10000:.2f}",f"{float(s['ending_cash'])/10000:.2f}"])
table(['情景','累计台数','流水/万元','损益/万元','期末现金/万元'],rows,[65,85,116,117,CW-383],484,size=8.9,pad=8,maxh=170)
p('提前一个月全额采购并留10%缓冲；899企业包晚一个月回款。M10仍为M11按15%增长备货，避免期末停止采购虚增现金。所有情景都缺少舒适的90天固定费用缓冲；下行M10现金转负。',M,647,CW,75,9.5,16)
p('模型未含订阅、融资收入、利息、所得税或新模具费；初期小批制造成本高于规模假设，需按真实报价补入。CSV可改可重算，不能直接作为采购批准。',M,730,CW,46,8.8,14,MUTED)
end()

# 11
start('10  /  建议融资','建议讨论500万元天使融资','建议金额与用途；非用户指定金额、非已获承诺、非到账资金。')
text('500万元',M,174,38,TEAL);p('按原型、需求、合规与交付证据分段释放预算。',M,234,CW,35,12,20)
alloc=[('产品与Agent研发',200,'40%'),('硬件试制与合规',100,'20%'),('用户验证与设计伙伴',60,'12%'),('量产准备与周转',80,'16%'),('预备金',60,'12%')]
table(['建议用途','万元','占比'],alloc+[('合计',500,'100%')],[CW-160,80,80],298,size=10,pad=11,maxh=290)
callout('500万元融资方案，与60万元精简验证模型是两个独立口径。尚未建立500万元同口径分月跑道，不能沿用原团队费用推算长期现金安全。',644,86)
p('预算不构成支出授权。岗位、报价、试点范围与融资条款明确后，另建扩张模型；到账前不以预期融资承担采购或人员承诺。[S7]',M,744,CW,36,8.5,14,MUTED)
end()

# 12
start('11  /  7天与30天交付','7天做5台演示样机，不承诺量产','D1为物料可用且团队实际开工的首日；1.5万元原型预算为估算。')
table(['时间','当天动作','证据/退路'],[['D1','冻结299版；清点OEM底座/开发板/屏/触摸件','规格v0.1和短缺清单；必要时外置模块'],['D2','台架接线、鼠标独立HID枚举、模块通信','USB/功耗记录；不强行单线化'],['D3','灯/触摸/屏状态机与本地任务闭环','输入-提示-理由-确认可重复演示'],['D4','展示壳/固定架；手感、热和线缆评估','尺寸与装配记录；非量产壳明确标示'],['D5','装5台并编号；离线/断连恢复','每台测试与固件版本，不良隔离'],['D6','10个场景复测；少量自愿试用','缺陷与授权记录；只展示已通过路径'],['D7','设计评审；决定是否进入EVT','5台记录完整或明确失败原因，不宣布出货']],[49,219,CW-268],177,size=9,pad=8,maxh=365)
label('D8-D30：有条件的小批窗口',602)
p('D8-D14：10台EVT、DFM、20人自愿试用、合规适用性与报价确认。D15通过G1才下50-100台受控试产单；D16-D25来料、首件、组装、全检和缺陷闭环；D26通过G2，D27-D30才分批交付。',M,631,CW,83,10,16)
p('新开模、返板、供料或实验室排期未解决即延期。三十天是争取窗口，不是发货保证；不以“试产”免除法定消费者权利。[S9]',M,733,CW,42,9,14,MUTED)
end()

# 13
start('12  /  工厂与质量','先锁定可验收的规格，再比较报价','至少3份同口径书面RFQ；尚未联系或承诺任何工厂。[S9]')
table(['放行门','必须具备的证据'],[['G0 原型 > EVT','鼠标链路独立；授权闭环；5台记录；无安全关键缺陷。'],['G1 EVT > 试产采购','10台EVT功能通过；DFM/BOM/合法USB身份明确；合规路径和资金覆盖。'],['G2 试产 > 交付','规定测试/适用合规完成；100%出货功能合格；首次良率>=95%；追溯/售后/需求门槛通过。']],[129,CW-129],178,size=9.7,pad=11,maxh=235)
label('RFQ必须拆开的项目',446)
p('OEM型号及关键料号、税率/发票、MOQ/MPQ、交期、损耗/返工、NRE/治具/模具所有权、运输、售后和ECN。合法VID/PID与型号对应报告是先决条件；未经书面确认不得替料。',M,476,CW,82)
label('验收覆盖完整使用链',589)
p('每台鼠标与模块功能；USB插拔、休眠恢复与模块复位；功耗/温升；触摸/显示；壳体锐边、裂纹、手汗与磨损；线材与包装；老化与序列号；未经授权输入/撤回/删除/团队少于5人等隐私用例。',M,617,CW,83)
p('合规由有资质方按最终结构、供电、无线能力和销售地区判断。首批不套用不相关证书或随意AQL表。采购谈判可争取30%/70%，现金模型仍保守按提前全额支付。',M,717,CW,59,9.2,15,MUTED)
end()

# 14
start('13  /  半年生态','每个新硬件，都要独立证明值得做','前六个月最多一个新增硬件试验，不同时铺八条供应链。')
table(['月份','核心交付与门槛'],[['M1-M2','任务闭环、20人试用、受控小批；质量、安装、授权和有用性通过。'],['M3-M4','验证鼠标相对软件的增量；达标后分批扩大，开放状态协议与一个参考配件。'],['M5-M6','少量人工审核的只读插件；根据留存、BOM、售后和现金决定下一款立项。']],[81,CW-81],176,size=9.7,pad=10,maxh=215)
label('八种其他硬件的建议优先级',419)
table(['优先','方向与概念价','判断'],[['1 / 2','USB桌面灯149-299；触摸旋钮199-399','低复杂度、无需换鼠标，优先验证。'],['3 / 4','任务宏键199-499；电子纸任务牌299-699','共用任务协议；验证快捷性和可读性。'],['5 / 6','脚踏开关149-299；无摄像头表情伙伴499-899','岗位或陪伴偏好更窄；关注误触与吃灰。'],['7 / 8','计算底座1499；团队终端3999','高复杂度远期概念；未定BOM，不预售。']],[55,258,CW-313],449,size=9.2,pad=9,maxh=242)
p('插件默认只读、权限声明、可撤回、签名版本与回滚先于收费。设备不掌握企业凭据；团队终端拒绝个人排行。财务基准M6累计910台，分批1000台目标不等于预测。[S7]',M,722,CW,54,9,15,MUTED)
end()

# 15
start('14  /  团队、风险与战略选择','第10个月是检查点，不是退出承诺','没有既定收购方、估值依据或融资到账日期。')
p('计划三人核心角色：产品/商业、本地agent工程、硬件/供应链；工业设计、测试、法律和认证按次采购。不是已有团队履历。精简模型人员月支出4.2万元、固定支出合计5.5万元，均为预算假设。',M,176,CW,89)
table(['风险','停止或纠偏规则'],[['有用性不足','两轮改进后D7仍启用<40%，停止硬件备货。'],['质量/售后','连续两批退款>10%或首次良率<90%，冻结采购并根因分析。'],['信任受损','未经授权外传/动作立即停用、修复并按流程通知。'],['现金紧张','未来90天预测转负，停止非必要NRE/营销；先完成既有义务。']],[91,CW-91],297,size=9.5,pad=9,maxh=231)
label('四种合法、可执行的选择',558)
p('继续经营：留存、贡献和现金成立后缩到主SKU、控制采购。\n讨论融资：带真实试用、退款、账目和交付证据，不保证成交。\n合作或交易：只在实际书面意向出现后比较授权、分销、股权或资产方案。\n有序停止：优先交付/退款、保修、员工/供应商/税费与数据义务。'.replace('\n','<br/>'),M,586,CW,112,10,18)
p('可尽调资产是合法代码、设计、品牌、工装、库存和合同；不出售个人任务、私聊或员工画像。残值依据真实报价，不能按理想销售价或假设并购倍数保证投资回报。',M,719,CW,57,9.2,15,MUTED)
end()

# 16
start('15  /  来源与证据','公开研究与可重算底稿','抓取日：2026-09-06（Asia/Shanghai）。厂商主张不等于独立测试。')
sources=[
 ('S1','Microduck官方README','https://raw.githubusercontent.com/pollen-robotics/microduck/main/README.md','约25cm/800g、RK3566、15舵机、50Hz、可维护软件架构。'),
 ('S2','Microduck GitHub API','https://api.github.com/repos/pollen-robotics/microduck','快照7374 stars/858 forks、Apache-2.0元数据；不代表销量。'),
 ('S3','Microduck官方产品页','https://pollen-robotics.com/microduck','标注2026-08-27开启预售、399美元税运另计；未核实订单/交付。'),
 ('S4','Violoop官网','https://violoop.ai','预发布预约399美元起、优惠后369美元起；性能为厂商主张。'),
 ('S5','中国人大网：个人信息保护法','http://www.npc.gov.cn/npc/c2/c30834/202108/t20210820_313088.html','最小必要、透明、撤回、自动化决策与敏感信息等条款。'),
 ('S6','Espressif ESP32-S3 USB设备文档','https://docs.espressif.com/projects/esp-usb/en/latest/esp32s3/usb_device.html','USB Full-Speed、CDC/HID和PHY限制；不证明本项目已实测。'),
 ('S7','项目商业底稿与财务CSV','docs/business/README.md','business-plan / financial-model / calculate_financials.py及输入输出CSV。'),
 ('S8','Active Agent参考README','../active_agent/README.md','只复用架构概念；未读取环境凭据，集成完成度另验收。'),
 ('S9','项目工厂与交付底稿','docs/manufacturing-commercial/','RFQ、验收排期、BOM与采购排期CSV；均未外发或下单。')]
y=175
for k,title,url,note in sources:
 text(k,M,y,9,TEAL);text(title,M+27,y,9.5,INK)
 h=p(url,M+27,y+16,CW-27,29,7.8,12,MUTED)
 h2=p(note,M+27,y+17+h,CW-27,30,8.2,13)
 if url.startswith('http'):C.linkURL(url,(M+27,H-y-18-h,W-M,H-y-16),relative=0,thickness=0)
 y+=18+h+h2+12
p('完整抓取时间、成功/失败状态及SHA-256见docs/research/sources.json；仅完整成功快照作为事实来源。保留Markdown与构建脚本；产品图为项目原创概念渲染，非实物。',M,734,CW,44,8.5,14,MUTED)
end()
assert PAGE==16
C.save()
reader=PdfReader(str(OUT));assert len(reader.pages)==16
extracted=[page.extract_text() or '' for page in reader.pages]
assert all(len(t)>100 for t in extracted)
assert '500万元' in extracted[10] and '60万元' in extracted[10]
assert '66.51' in extracted[8] and '399' in extracted[15]
assert not any('\ufffd' in t for t in extracted)
(HERE/'qa/layout.json').write_text(json.dumps(LAYOUT,ensure_ascii=False,indent=2))
(HERE/'qa/extracted-text.txt').write_text('\n\n'.join(f'PAGE {i+1}\n{t}' for i,t in enumerate(extracted)))
inputs=[BUS/'business-plan.md',BUS/'financial-summary.csv',BUS/'financial-monthly.csv',BUS/'financial-sku-economics.csv',ROOT/'docs/research/findings.md',ROOT/'docs/research/sources.json',ROOT/'hardware/renders/hero_raw.png']
(HERE/'qa/source-manifest.json').write_text(json.dumps([{'path':str(f.relative_to(ROOT)),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in inputs],ensure_ascii=False,indent=2))
print(f'Created {OUT}; {len(reader.pages)} pages; {OUT.stat().st_size} bytes')
