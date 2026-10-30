import pymupdf as fitz, json, re, html
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'tools/extraction-work'; OUT.mkdir(parents=True,exist_ok=True)
SOURCES={'revision':'C21_Level1_Final_Revision_Units1-5_AR.pdf','units45':'C21_Level1_Units4-5_Study_Guide_AR.pdf'}
def cluster(vals,tol=.9):
 out=[]
 for v in sorted(vals):
  if not out or v-out[-1]>tol:out.append(v)
 return out

def logical(ss):
 # PDF glyph runs use DejaVu for RTL text/punctuation, Noto for LTR runs.
 # Empty fallback-space overlays are not content and must not duplicate spacing.
 ss=[s for s in ss if s['text'].strip()]
 if not ss:return ''
 lines=[]
 for s in sorted(ss,key=lambda s:s['origin'][1]):
  if not lines or abs(s['origin'][1]-lines[-1][0]['origin'][1])>5.5:lines.append([s])
  else:lines[-1].append(s)
 texts=[]
 for line in lines:
  runs=[]
  for s in sorted(line,key=lambda s:s['bbox'][0]):
   typ='r' if 'DejaVu' in s['font'] or 'OpenSymbol' in s['font'] else 'l'
   t=s['text'].strip().replace('\uf0b7','•')
   if runs and runs[-1]['typ']==typ:
    run=runs[-1]
    gap=s['bbox'][0]-run['right']
    join=' ' if gap>1.1 or s['text'].startswith(' ') or run['tailspace'] else ''
    run['text']=(t+join+run['text']) if typ=='r' else (run['text']+join+t)
    run['right']=s['bbox'][2];run['tailspace']=s['text'].endswith(' ')
   else:runs.append({'typ':typ,'text':t,'right':s['bbox'][2],'tailspace':s['text'].endswith(' ')})
  if any(r['typ']=='r' for r in runs):runs.reverse()
  texts.append(' '.join(r['text'] for r in runs))
 text=' '.join(texts)
 # Correct Arabic lam-alef extraction order, not source wording.
 text=re.sub(r' +([\u064b-\u065f])',r'\1',text)
 text=re.sub(r'\s+([.,!?;:،؛؟\]\)])',r'\1',text)
 text=re.sub(r'([\[(])\s+',r'\1',text)
 text=re.sub(r'\s+', ' ',text).strip()
 return text

def extract(key,name):
 doc=fitz.open(ROOT/'sources'/name); nodes=[]; audit=[]; previous_xs=None
 for pi,p in enumerate(doc):
  spans=[];blocks=[]; footer=[]
  for bi,b in enumerate(p.get_text('rawdict')['blocks']):
   ss=[]
   for li,l in enumerate(b.get('lines',[])):
    for si,raw in enumerate(l['spans']):
     parts=[]
     chars0=list(raw['chars'])
     for j in range(len(chars0)-1):
      ch=chars0[j]
      if ch['c'] in 'اأإآ' and ch['bbox'][2]-ch['bbox'][0]<.1 and chars0[j+1]['c']=='ل':
       chars0[j],chars0[j+1]=chars0[j+1],chars0[j]
     for ch in chars0:
      if not parts or abs(ch['origin'][0]-parts[-1][-1]['origin'][0])>25 or abs(ch['origin'][1]-parts[-1][-1]['origin'][1])>3:parts.append([ch])
      else:parts[-1].append(ch)
     for qi,chars in enumerate(parts):
      s={k:v for k,v in raw.items() if k!='chars'}
      s['text']=''.join(c['c'] for c in chars)
      s['bbox']=[min(c['bbox'][0] for c in chars),min(c['bbox'][1] for c in chars),max(c['bbox'][2] for c in chars),max(c['bbox'][3] for c in chars)]
      s['origin']=chars[0]['origin']
      s['sid']=f'{key}-p{pi+1}-b{bi}-l{li}-s{si}-q{qi}';s['block']=bi
      if s['origin'][1]>745:footer.append(s)
      else:spans.append(s);ss.append(s)
   if ss:blocks.append(ss)
  lines=[];rects=[]
  for d in p.get_drawings():
   for it in d['items']:
    if it[0]=='l' and abs(it[1].y-it[2].y)<.1 and abs(it[1].x-it[2].x)>400:lines.append(it[1].y)
    if it[0]=='re':rects.append(it[1])
  ys=cluster(lines);regions=[]
  if len(ys)%3==2:regions.append((ys[0],None,ys[1]));ys=ys[2:]
  assert len(ys)%3==0,(key,pi,ys)
  regions += [(ys[i],ys[i+1],ys[i+2]) for i in range(0,len(ys),3)]
  used=set();pnodes=[]
  for ti,(top,head,bottom) in enumerate(regions):
   rs=[r for r in rects if r.y0>=top-1 and r.y1<=bottom+1 and r.width>20]
   xs=cluster([x for r in rs for x in [r.x0,r.x1]])
   if len(xs)<3:xs=previous_xs
   assert xs and len(xs)>2,(key,pi,ti,'no cols')
   previous_xs=xs
   edges=cluster([top,bottom]+([head] if head else [])+[y for r in rs for y in [r.y0,r.y1]])
   rows=[]
   for ri,(y1,y2) in enumerate(zip(edges,edges[1:])):
    if y2-y1<2:continue
    cells=[]
    for ci,(x1,x2) in enumerate(zip(xs,xs[1:])):
     cell=[s for s in spans if y1-.7<s['origin'][1]<y2+.3 and x1-1<=s['bbox'][0]<x2-1 and s['sid'] not in used]
     used.update(s['sid'] for s in cell)
     cells.append({'text':logical(cell),'span_ids':[s['sid'] for s in cell if s['text'].strip()]})
    rows.append(cells)
   pnodes.append({'kind':'table','page':pi+1,'y':top,'header':bool(head),'rows':rows,'columns':len(xs)-1})
  for ss in blocks:
   available=[s for s in ss if s['sid'] not in used]
   if not available:continue
   text=logical(available)
   if not text:continue
   pnodes.append({'kind':'paragraph','page':pi+1,'y':min(s['bbox'][1] for s in available),'text':text,'bold':all('Bold' in s['font'] for s in available if s['text'].strip()),'span_ids':[s['sid'] for s in available if s['text'].strip()]})
   used.update(s['sid'] for s in available)
  pnodes.sort(key=lambda n:n['y'])
  for ni,n in enumerate(pnodes):n['id']=f'{key}-p{pi+1}-{ni}';nodes.append(n)
  expected={s['sid'] for s in spans if s['text'].strip()}
  audit.append({'page':pi+1,'body_spans':len(expected),'covered':len(expected&used),'missing':list(expected-used),'footer':logical(footer)})
 data={'source':name,'nodes':nodes,'audit':audit}
 (OUT/f'{key}-structured.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
 with (OUT/f'{key}-structured.txt').open('w') as out:
  for n in nodes:
   out.write(f"\n[{n['id']}] "+('BOLD ' if n.get('bold') else '')+(n.get('text','TABLE') if n['kind']=='paragraph' else '\n'+'\n'.join(' | '.join(c['text'] for c in row) for row in n['rows']))+'\n')
 print(key,len(nodes),'nodes',sum(n['kind']=='table' for n in nodes),'tables',sum(a['body_spans'] for a in audit),'spans',sum(len(a['missing']) for a in audit),'missing')
if __name__=='__main__':
 for key,name in SOURCES.items():extract(key,name)
