"""Plot exact generated KiCad pad/track coordinates, not a cosmetic board illustration."""
from pathlib import Path
import sys,math
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R));from sexpr import parse
D=R/'NOT-FOR-FAB';a=parse((D/'lingban_carrier.kicad_pcb').read_text())
im=Image.new('RGB',(1320,1280),'#0c1727');d=ImageDraw.Draw(im);fontpath='/System/Library/Fonts/Supplemental/Arial.ttf'
def font(s):return ImageFont.truetype(fontpath,s)
d.text((60,35),'LINGBAN  /  EVT-A INTERACTION CARRIER',font=font(35),fill='white');d.text((60,88),'ACTUAL KICAD ROUTING  |  36 x 76 mm  |  2 layers  |  NOT-FOR-FAB',font=font(22),fill='#96bad1')
S=12
for which,X in [('F.Cu',120),('B.Cu',780)]:
 Y=220
 def pt(x,y):return X+float(x)*S,Y+float(y)*S
 d.rectangle((*pt(0,0),*pt(36,76)),fill='#12473b',outline='#9addd2',width=2)
 d.rectangle((*pt(7,0),*pt(29,8)),fill='#21402e');d.text(pt(8,2.2),'ANTENNA',font=font(17),fill='#dbdfa2')
 d.text((X,153),which+' / top coordinates',font=font(26),fill='#cae8ef')
 for e in a:
  if not isinstance(e,list):continue
  def get(n):return next((x[1:] for x in e if isinstance(x,list) and x[0]==n),None)
  if e[0]=='segment' and get('layer')[0].strip('"')==which:
   d.line([pt(*get('start')),pt(*get('end'))],fill='#ff9981' if which=='F.Cu' else '#85c2ff',width=max(1,round(float(get('width')[0])*S)))
  if e[0]=='via':
   x,y=map(float,get('at'));rr=float(get('size')[0])/2;dr=float(get('drill')[0])/2
   d.ellipse((*pt(x-rr,y-rr),*pt(x+rr,y+rr)),fill='#e8c469');d.ellipse((*pt(x-dr,y-dr),*pt(x+dr,y+dr)),fill='#08171c')
 for fp in a:
  if not isinstance(fp,list) or fp[0]!='footprint':continue
  def get(n):return next((x[1:] for x in fp if isinstance(x,list) and x[0]==n),None)
  ox,oy=map(float,get('at')[:2]);ref=next(x[2].strip('"') for x in fp if isinstance(x,list) and x[0]=='property' and x[1]=='"Reference"')
  for p in fp:
   if not isinstance(p,list) or p[0]!='pad':continue
   def pp(n):return next((x[1:] for x in p if isinstance(x,list) and x[0]==n),None)
   layers=[v.strip('"') for v in pp('layers')]
   if which not in layers and '*.Cu' not in layers:continue
   dx,dy=map(float,pp('at')[:2]);x,y=ox+dx,oy+dy;w,h=map(float,pp('size'));color='#e6c777' if p[2]!='np_thru_hole' else '#08171c'
   bounds=(*pt(x-w/2,y-h/2),*pt(x+w/2,y+h/2))
   if p[3]=='circle':d.ellipse(bounds,fill=color)
   else:d.rectangle(bounds,fill=color)
   if pp('drill'):
    rr=float(pp('drill')[0])/2;d.ellipse((*pt(x-rr,y-rr),*pt(x+rr,y+rr)),fill='#071320')
  if not ref.startswith('H'):d.text(pt(ox+.9,oy-2.2),ref+(' DNI' if ref=='D1' else ''),font=font(13),fill='#eef6eb')
d.text((60,1165),'Trace 0.25 mm  |  Via 0.65 / 0.30 mm  |  Bottom passives, top development-board sockets',font=font(22),fill='#bad1df')
d.text((60,1202),'Digital ERC / DRC passed. Electrical, ESD, connector and assembly validation remain open.',font=font(21),fill='#ddbea3')
im.save(D/'plots/pcb-routed.png')
