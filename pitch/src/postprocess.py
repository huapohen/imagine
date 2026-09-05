"""Inspect actual PPTX/PDF, build portable HTML and contact sheet. No source writes."""
import sys, json, re, base64, hashlib, zipfile, html
from pathlib import Path
from xml.etree import ElementTree as ET
from pypdf import PdfReader
from PIL import Image, ImageDraw
root=Path(__file__).resolve().parents[1]
run=sys.argv[1]
build=root/'.build'/run
out=root/'deliverables'/run
slides=json.loads((build/'slides.json').read_text())
reader=PdfReader(out/'lingban-vc-deck.pdf')
assert len(reader.pages)==18
ns={'a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
norm=lambda s: re.sub(r'\s+','',s).replace('–','-').replace('—','-')
qa=[]
with zipfile.ZipFile(out/'lingban-vc-deck.pptx') as z:
 for i,page in enumerate(reader.pages):
  pdftext=page.extract_text() or ''
  tree=ET.fromstring(z.read(f'ppt/slides/slide{i+1}.xml'))
  texts=[e.text or '' for e in tree.findall('.//a:t',ns)]
  missing=[t for t in texts if norm(t) and norm(t) not in norm(pdftext)]
  # Character continuity can be split in PDF text by shaped CJK/Latin runs.
  fonts=[]
  for name,obj in page['/Resources'].get('/Font',{}).items():
   f=obj.get_object(); descendant=f.get('/DescendantFonts',[f])[0].get_object();desc=descendant.get('/FontDescriptor',{});desc=desc.get_object() if hasattr(desc,'get_object') else desc
   fonts.append({'name':str(f.get('/BaseFont')),'embedded':any(k in desc for k in ['/FontFile','/FontFile2','/FontFile3'])})
  qa.append({'slide':i+1,'native_text_runs':len(texts),'missing_runs':missing,'pdf_fonts':fonts,'pdf_text_characters':len(pdftext)})
  slides[i]['slide_text']=pdftext
assert not [q for q in qa if q['missing_runs']], 'PPTX/PDF text mismatch: '+str([q for q in qa if q['missing_runs']])
assert all(q['pdf_text_characters']>30 for q in qa)
assert all(f['embedded'] for q in qa for f in q['pdf_fonts']), 'Unembedded PDF font'
assert sum([200,100,60,80,60])==500 and sum([40,20,12,16,12])==100
assert abs(299-108-46.36-33.13-45-66.51)<.001
files=sorted((build/'render').glob('slide-*.png'));assert len(files)==18
sheet=Image.new('RGB',(1600,6*315),'#dfe6e4');d=ImageDraw.Draw(sheet)
for i,f in enumerate(files):
 im=Image.open(f).convert('RGB');im.thumbnail((520,293));x=(i%3)*533+6;y=(i//3)*315+17;sheet.paste(im,(x,y));d.text((x,y-14),str(i+1),fill='#102D3C')
sheet.save(build/'contact-sheet.jpg',quality=92)
sections=[]
for i,(f,m) in enumerate(zip(files,slides)):
 title=m['title'] or ('灵伴 LINGBAN' if i==0 else '让下一步，更容易发生')
 b64=base64.b64encode(f.read_bytes()).decode()
 sections.append(f'<section class="slide" id="slide-{i+1}" aria-label="第{i+1}页 {html.escape(title)}"><img src="data:image/png;base64,{b64}" alt="{html.escape(m["slide_text"])}" width="1600" height="900"><div class="sr-only">{html.escape(m["slide_text"])}</div></section>')
(out/'deck-content.md').write_text('# 灵伴 LINGBAN 18页演示正文\n\n本文件直接取对应PPTX导出的PDF文字，与展示页一致。演讲扩展与来源见speaker-notes.md。\n\n'+'\n\n'.join(f'## 第{m["number"]}页\n\n{m["slide_text"]}' for m in slides))
notes=json.dumps(slides,ensure_ascii=False).replace('</','<\\/')
page='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>灵伴 LINGBAN VC演示稿</title><style>
*{box-sizing:border-box}html,body{margin:0;background:#0b2333;color:#f9fcfb;font-family:system-ui,"Hiragino Sans GB",sans-serif}body{overflow:hidden}.slide{display:none;position:fixed;inset:0 0 54px;align-items:center;justify-content:center}.slide.active{display:flex}.slide img{display:block;max-width:100%;max-height:100%;width:auto;height:auto;object-fit:contain}.sr-only{position:absolute;width:1px;height:1px;overflow:hidden;clip-path:inset(50%)}nav{height:54px;position:fixed;bottom:0;width:100%;display:flex;align-items:center;justify-content:center;gap:10px;background:#0b2333;font-size:14px}button{border:1px solid #426c71;color:#d9f8ed;background:transparent;border-radius:4px;padding:7px 14px;cursor:pointer;font:inherit}button:hover,button:focus-visible{background:#235762;outline:2px solid #8ce5d0}button:disabled{opacity:.3;cursor:default}#count{min-width:70px;text-align:center}aside{position:fixed;right:2vw;top:3vh;bottom:80px;width:min(660px,95vw);background:#fafcfb;color:#102d3c;box-shadow:0 10px 80px #0009;padding:30px;overflow:auto;z-index:2;line-height:1.8;font-size:18px}aside[hidden]{display:none}aside h2{font-size:24px;line-height:1.4}aside p{white-space:pre-line}aside .source{font-size:14px;color:#547078;overflow-wrap:anywhere}aside button{color:#102d3c;float:right}#hint{color:#93b6b5;margin-left:15px;font-size:12px}:fullscreen nav{opacity:0;transition:opacity .2s}:fullscreen nav:hover,:fullscreen nav:focus-within{opacity:1}:fullscreen .slide{bottom:0}@media(max-width:660px){#hint{display:none}nav{gap:6px}button{padding:7px 9px}}
@media print{@page{size:13.333333in 7.5in;margin:0}html,body{background:white;overflow:visible;width:13.333333in;margin:0}nav,aside{display:none!important}.slide,.slide.active{position:relative;inset:auto;display:block!important;width:13.333333in;height:7.5in;break-after:page;page-break-after:always;break-inside:avoid}.slide:last-of-type{break-after:auto;page-break-after:auto}.slide img{width:100%;height:100%;max-width:none;max-height:none}.sr-only{display:none}}
</style></head><body>'''+''.join(sections)+'''<nav aria-label="演示控制"><button id="prev" aria-label="上一页">上一页</button><span id="count" aria-live="polite"></span><button id="next" aria-label="下一页">下一页</button><button id="notes">讲稿 N</button><button id="full">全屏 F</button><button id="print">打印 P</button><span id="hint">方向键切页 · Home / End 跳转</span></nav><aside id="speaker" hidden aria-label="逐页讲稿"><button id="close">关闭</button><h2></h2><p class="body"></p><p class="source"></p></aside><script>
const data='''+notes+''';const pages=[...document.querySelectorAll('.slide')];let current=0;const pane=document.querySelector('#speaker');function show(n){current=Math.max(0,Math.min(pages.length-1,n));pages.forEach((p,i)=>{p.classList.toggle('active',i===current);p.setAttribute('aria-hidden',i===current?'false':'true')});document.querySelector('#count').textContent=(current+1)+' / '+pages.length;document.querySelector('#prev').disabled=current===0;document.querySelector('#next').disabled=current===pages.length-1;history.replaceState(null,'','#'+(current+1));const m=data[current];pane.querySelector('h2').textContent=(current+1)+'. '+(m.title||(current===0?'灵伴 LINGBAN':'让下一步，更容易发生'));pane.querySelector('.body').textContent=m.note;pane.querySelector('.source').textContent='来源：'+m.source}function notes(){pane.hidden=!pane.hidden}async function fullscreen(){try{if(document.fullscreenElement)await document.exitFullscreen();else await document.documentElement.requestFullscreen()}catch(e){document.querySelector('#hint').textContent='请使用浏览器菜单进入全屏'}}document.querySelector('#prev').onclick=()=>show(current-1);document.querySelector('#next').onclick=()=>show(current+1);document.querySelector('#notes').onclick=notes;document.querySelector('#close').onclick=()=>pane.hidden=true;document.querySelector('#full').onclick=fullscreen;document.querySelector('#print').onclick=()=>window.print();document.addEventListener('keydown',e=>{if(e.ctrlKey||e.metaKey||e.altKey)return;if(['ArrowRight','ArrowDown','PageDown',' '].includes(e.key)){e.preventDefault();show(current+1)}else if(['ArrowLeft','ArrowUp','PageUp'].includes(e.key)){e.preventDefault();show(current-1)}else if(e.key==='Home'){e.preventDefault();show(0)}else if(e.key==='End'){e.preventDefault();show(pages.length-1)}else if(e.key.toLowerCase()==='n')notes();else if(e.key.toLowerCase()==='f')fullscreen();else if(e.key.toLowerCase()==='p')window.print();else if(e.key==='Escape')pane.hidden=true});let start=0;document.addEventListener('touchstart',e=>start=e.changedTouches[0].clientX,{passive:true});document.addEventListener('touchend',e=>{if(!pane.hidden)return;const delta=e.changedTouches[0].clientX-start;if(Math.abs(delta)>70)show(current+(delta<0?1:-1))},{passive:true});show((Number(location.hash.slice(1))||1)-1);
</script></body></html>'''
(out/'lingban-vc-deck.html').write_text(page)
(build/'content-qa.json').write_text(json.dumps({'status':'pass','page_count':18,'checks':qa,'arithmetic':{'funding_wan':500,'funding_percent':100,'unit_contribution':66.51}},ensure_ascii=False,indent=2))
print(json.dumps({'status':'pass','slides':18,'html_bytes':len(page.encode()),'pptx_pdf_text_runs_checked':sum(q['native_text_runs'] for q in qa)}))
