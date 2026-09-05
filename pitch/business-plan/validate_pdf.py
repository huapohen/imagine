#!/usr/bin/env python3
"""Render every PDF page and perform conservative structural/text QA."""
from pathlib import Path
import hashlib,json,subprocess
from PIL import Image,ImageDraw
from pypdf import PdfReader
import pdfplumber
from reportlab.pdfbase.ttfonts import TTFont
HERE=Path(__file__).resolve().parent
PDF=HERE/'lingban-business-plan.pdf'
QA=HERE/'qa';QA.mkdir(exist_ok=True)
POPPLER=Path('/Users/lwblx/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/override/pdftoppm')
subprocess.run([str(POPPLER),'-r','110','-png',str(PDF),str(QA/'page')],check=True)
reader=PdfReader(str(PDF));assert len(reader.pages)==16
font=TTFont('CNcheck','/System/Library/Fonts/Supplemental/Arial Unicode.ttf')
text='\n'.join(p.extract_text() or '' for p in reader.pages)
missing=sorted({ch for ch in text if not ch.isspace() and ord(ch) not in font.face.charToGlyph})
assert not missing,missing
bad=[]
with pdfplumber.open(str(PDF)) as doc:
 for i,page in enumerate(doc.pages,1):
  for ch in page.chars:
   if ch['x0'] < -1 or ch['x1']>page.width+1 or ch['top'] < -1 or ch['bottom']>page.height+1:bad.append((i,ch['text'],ch['x0'],ch['top']))
assert not bad,bad
embedded=set()
for page in reader.pages:
 for _,reference in page['/Resources']['/Font'].items():
  f=reference.get_object();desc=f.get('/FontDescriptor')
  if desc:
   d=desc.get_object()
   if any(k in d for k in ('/FontFile','/FontFile2','/FontFile3')):embedded.add(str(f['/BaseFont']))
assert embedded
assert '500万元' in text and '60万元' in text and '66.51' in text
assert sum([200,100,60,80,60])==500
images=sorted(QA.glob('page-*.png'));assert len(images)==16
sheet=Image.new('RGB',(1240,1832),'#dce5e2');draw=ImageDraw.Draw(sheet)
for i,f in enumerate(images):
 im=Image.open(f).convert('RGB');im.thumbnail((292,419));x=i%4*310+9;y=i//4*458+8;sheet.paste(im,(x,y));draw.text((x,y+423),f'PAGE {i+1:02}',fill='#102d3c')
sheet.save(QA/'contact-sheet.jpg',quality=94)
report={'pdf_sha256':hashlib.sha256(PDF.read_bytes()).hexdigest(),'pages':len(reader.pages),'rendered_pages':len(images),'render_dpi':110,'embedded_fonts':sorted(embedded),'missing_font_glyphs':missing,'out_of_page_glyphs':bad,'financing_allocation_total_wan':500,'visual_review_required':True,'note':'Automated checks do not replace visual review; see QA.md for inspection performed.'}
(QA/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))
