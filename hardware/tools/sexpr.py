import re,json
def parse(s):
 ts=re.findall(r'"(?:\\.|[^"\\])*"|\(|\)|[^\s()]+',s);i=0
 def rec():
  nonlocal i
  t=ts[i];i+=1
  if t!='(':return t
  a=[]
  while ts[i]!=')':a.append(rec())
  i+=1;return a
 return rec()
def dump(x):return '('+' '.join(map(dump,x))+')' if isinstance(x,list) else x
