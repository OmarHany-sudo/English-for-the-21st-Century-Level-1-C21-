from pathlib import Path
from bs4 import BeautifulSoup
import json,re,html,shutil,collections
P=Path(__file__).resolve().parents[1]; R=P; E=html.escape
soup=BeautifulSoup((P/'tools/legacy-template.html').read_text(),'html5lib')
oldnav=json.loads(soup.select_one('#book-navigation').string)
legacy=[soup.select_one('#'+n['id']).extract() for n in oldnav[2:]]
oldcover=soup.select_one('#cover').extract();oldcover['id']='legacy-cover';oldcover['class']=['cover-page','legacy-cover']
original_toc=soup.select_one('#contents .original-toc').extract();soup.select_one('#contents').decompose()
D={k:json.loads((P/f'content/{k}.json').read_text()) for k in ['revision','units45']}
N={n['id']:n for d in D.values() for n in d['nodes']}; rendered=[];manifest=[]; nav=[]; articles=[]
names=['People & Places','Introductions & Conversations','Friends & Family','Networks','Work']
desc='A comprehensive and condensed revision guide covering all five units of English for the 21st Century – Level 1, including essential vocabulary, grammar rules, conversations, writing skills, practice questions, and answer keys.'
ar_desc='مذكرة مراجعة نهائية مختصرة وشاملة للوحدات الخمس، تشمل أهم المفردات والقواعد والمحادثات وقواعد الكتابة، بالإضافة إلى تدريبات متنوعة ونموذج الإجابة، استعدادًا لامتحانات Quiz وMidterm.'
def frag(t):return BeautifulSoup(t,'html.parser')
def direction(t):return 'rtl' if re.search('[\u0621-\u064a]',t) else 'ltr'
def bidi(t):
 if direction(t)=='ltr':return f'<bdi dir="ltr" lang="en">{E(t)}</bdi>'
 # Keep Latin expressions together, including numerals, apostrophes and punctuation.
 pat=r"[A-Za-z0-9][A-Za-z0-9\s’'.,!?;:()\[\]/_+&=–—−→%-]*"
 out=[];at=0
 for m in re.finditer(pat,t):
  part=m.group();core=part.rstrip();trail=part[len(core):]
  out.append(E(t[at:m.start()]));out.append('<bdi dir="ltr" lang="en">'+E(core)+'</bdi>'+E(trail));at=m.end()
 out.append(E(t[at:]));return ''.join(out)
def source(t,id,tag='p',cls='source-paragraph',page=None):
 manifest.append({'id':id,'text':t,'page':page})
 markup=bidi(t)
 if tag in ['h1','h2']:
  match=re.match(r'^(\d+\. )(.+)',t)
  if match:markup='<span class="source-number" title="ترقيم المصدر">'+E(match[1])+'</span>'+bidi(match[2])
 return f'<{tag} id="{id}" data-source="{id}" class="{cls}" dir="{direction(t)}">{markup}</{tag}>'
def range_nodes(key,start,end=None):
 a=D[key]['nodes'];i=next(i for i,n in enumerate(a) if n['id']==start);j=next((i for i,n in enumerate(a) if n['id']==end),len(a)) if end else len(a)
 return a[i:j]
def callout(t):return '<aside class="revision-note" dir="rtl">'+t+'</aside>'
def link(h,t,cls='revision-link'):return f'<a class="{cls}" href="#{h}">{E(t)}</a>'
def source_link(n):
 key=n['id'].split('-')[0];filename=D[key]['source'];return f'<a class="source-cite" href="sources/{filename}#page={n["page"]}" target="_blank" rel="noopener">المصدر · ص {n["page"]} ↗</a>'
def number(n):
 m=re.match(r'^(\d+)[.\[]',n.get('text',''));return int(m[1]) if m else None
special_heads={5:'vocabulary',7:'grammar',9:'expressions',11:'writing',16:'tips',24:'vocabulary',26:'grammar',28:'expressions',30:'writing',35:'tips',43:'vocabulary',45:'grammar',48:'expressions',50:'writing',56:'tips',64:'vocabulary',66:'grammar',68:'expressions',70:'writing',76:'tips',84:'vocabulary',86:'grammar',88:'expressions',90:'writing',96:'tips'}
head_nums=set(special_heads)|{104,107,108,109,110,111,114,125,136,138,149,160,171,182,194,205,216,218,229,240,251,262}
cats=['choose','complete','match','correct','rearrange','conversations','grammar','vocabulary']
cat_titles=['Choose the correct answer','Complete the sentences','Match the words','Correct the mistakes','Rearrange the words','Complete the conversations','Grammar questions','Vocabulary questions']
qheads=[114,125,136,138,149,160,171,182]; aheads=[194,205,216,218,229,240,251,262]
qnums=[list(range(115,125)),list(range(126,136)),[],list(range(139,149)),list(range(150,160)),list(range(161,171)),list(range(172,182)),list(range(183,193))]
anums=[list(range(195,205)),list(range(206,216)),[217],list(range(219,229)),list(range(230,240)),list(range(241,251)),list(range(252,262)),list(range(263,273))]
paired={};qalinks={}
for cat,qs,ans in zip(cats,qnums,anums):
 for ix,(q,a) in enumerate(zip(qs,ans),1):paired[q]=(f'question-{cat}-{ix}',f'answer-{cat}-{ix}','راجع الإجابة');paired[a]=(f'answer-{cat}-{ix}',f'question-{cat}-{ix}','ارجع للسؤال')
paired[217]=('answer-match','practice-match','ارجع للمطابقة')
flags={119:'السياق الذي يحدد صاحب الأخت غير موجود في السؤال المطبوع؛ حُفظ السؤال كما ورد، دون إضافة اسم.',126:'النص المطبوع يحتوي خانة واحدة، بينما النموذج يعرض بلدًا وجنسية. لم نُضف خانة مفقودة.',131:'المصدر يورد (have/has) فقط دون جملة. لم نؤلف نص السؤال.',132:'المصدر يورد (possessive) فقط دون جملة. لم نؤلف نص السؤال.',134:'المصدر يورد (negative) فقط دون جملة. لم نؤلف نص السؤال.',143:'جملة التصحيح غير موجودة في هذا الموضع من المصدر؛ حُفظت التعليمة فقط.',155:'مجموعة الكلمات مطبوعة بهذه الصورة، ونموذجها يكتفي بطلب الإكمال باسم. لم تُستكمل من عندنا.',199:'هذه هي الإجابة المطبوعة؛ اسم Ali غير موجود في السؤال المقابل.',206:'الإجابة مطبوعة ببلد وجنسية، رغم وجود خانة واحدة في السؤال.',235:'نموذج المصدر يذكر طلب الإكمال باسم فقط؛ لا توجد جملة كاملة هنا.',246:'الشرطة المائلة واردة في النموذج، دون بديل بعدها.',255:'الشرطة المائلة واردة في النموذج، دون بديل بعدها.'}

def render_nodes(nodes,route,title_from_first=False,check=False):
 out=[];heads=[];in_topic=False;i=0;lastpage=None
 while i<len(nodes):
  n=nodes[i];i+=1;rendered.append(n['id']);page=n['page'];text=n.get('text','');num=number(n)
  if page!=lastpage:
   out.append('<div class="source-page">'+source_link(n)+'</div>');lastpage=page
  if n['kind']=='table':
   combined=[n]
   while i<len(nodes) and nodes[i]['kind']=='table' and not nodes[i]['header'] and nodes[i]['columns']==n['columns']:
    combined.append(nodes[i]);rendered.append(nodes[i]['id']);i+=1
   out.append(f'<div class="table-scroll revision-table" role="region" aria-label="جدول تعليمي — {route}" tabindex="0"><table dir="ltr"><caption>جدول من المصدر · ص {page}'+('–'+str(combined[-1]['page']) if len(combined)>1 else '')+'</caption>')
   body=False
   for ni,table in enumerate(combined):
    for ri,row in enumerate(table['rows']):
     ishead=ni==0 and ri==0 and table['header']
     if ishead:out.append('<thead>')
     elif not body:out.append('<tbody>');body=True
     out.append('<tr>')
     for ci,c in enumerate(row):
      tag='th' if ishead else 'td';out.append('<'+tag+(' scope="col"' if ishead else '')+'>')
      out.append(source(c['text'],f"{table['id']}-r{ri}-c{ci}",cls='cell-text',page=table['page']));out.append('</'+tag+'>')
     out.append('</tr>')
     if ishead:out.append('</thead>')
   if body:out.append('</tbody>')
   out.append('</table></div>');continue
  ismain=title_from_first and n is nodes[0]
  ish=(num in head_nums and n['id'].startswith('revision')) or n.get('bold',False)
  if ismain:
   out.append(source(text,n['id'],'h1','lesson-title',page));continue
  if check and num and num>=274:
   if num<324:
    out.append(f'<label class="exam-check"><input type="checkbox" data-check="exam-{num-273}"/><span class="check-number">{num-273:02}</span><span>'+source(text,n['id'],'span','check-copy',page)+'</span></label>')
   else:out.append(callout('نقطة إضافية واردة بعد الخمسين في المصدر، محفوظة دون حذف:')+source(text,n['id'],page=page))
   continue
  if ish:
   if in_topic:out.append('</section>')
   anchor=n['id']+'-topic';label=re.sub(r'^\d+\.\s*','',text)
   if route.startswith('unit-') and num in special_heads:anchor=route+'-'+special_heads[num]
   if route=='practice' and num in qheads:anchor='practice-'+cats[qheads.index(num)]
   if route=='answers' and num in aheads:anchor='answers-'+cats[aheads.index(num)]
   if route=='vocabulary-reference' and num in range(107,112):anchor='vocabulary-unit-'+str(num-106)
   typ='grammar' if 'Grammar' in text or 'قواعد' in text else ('vocabulary' if 'Vocabulary' in text else 'content')
   out.append(f'<section class="topic-block type-{typ}" id="{anchor}">');in_topic=True
   out.append(source(text,n['id'],'h2','topic-heading',page));heads.append({'id':anchor,'title':label,'level':2})
   if route=='practice' and num in qheads:out.append(link('answers-'+cats[qheads.index(num)],'نموذج إجابة هذا القسم ←'))
   if route=='answers' and num in aheads:out.append(link('practice-'+cats[aheads.index(num)],'← العودة لتدريبات هذا القسم'))
   continue
  pair=paired.get(num) if n['id'].startswith('revision') and route in ['practice','answers'] else None
  if pair:out.append(f'<div class="question-card" id="{pair[0]}">')
  # Join source paragraph fragments visually while retaining individually addressable spans.
  out.append(source(text,n['id'],page=page))
  if num in flags and n['id'].startswith('revision') and route in ['practice','answers']:out.append(callout('<strong>تنبيه من فحص المصدر:</strong> '+E(flags[num])))
  if n['id']=='units45-p11-1':out.append(callout('النص المطبوع به فصل غير واضح لحروف المثال وعلامة الخطأ؛ حُفظ كما يظهر بالمصدر ولم تُخمن العلامة المفقودة.'))
  if pair:out.append(link(pair[1],pair[2],'answer-jump')+'</div>')
 if in_topic:out.append('</section>')
 return ''.join(out),heads

def add(route,title,unit,nodes=None,extra='',first=True,check=False,library=False):
 h,heads=render_nodes(nodes or [],route,first,check)
 opening=f'<div class="lesson-breadcrumb" dir="ltr">C21 / LEVEL 1 <span>{"DETAILED STUDY" if library else "FINAL REVISION"}</span></div>'
 if not nodes or not first:opening+=f'<h1 class="lesson-title" dir="{direction(title)}">{bidi(title)}</h1>'
 if nodes and first:
  cut=h.find('</h1>')+5
  if cut>4:opening+=h[:cut];h=h[cut:]
 body=f'<article class="book-section lesson-page revision-section" id="{route}" data-unit="{unit}">{opening}{extra}{h}</article>'
 articles.append((route,body));nav.append({'id':route,'title':title,'unit':unit,'heads':heads,'library':library})

# Cover: reuse the existing illustration, type hierarchy, palette and dedication.
art=str(oldcover.select_one('.cover-visual'))
labels=['5 Units','Final Exam Revision','Quiz & Midterm Preparation','Vocabulary & Grammar','Practice Questions','Answer Key']
cover=f'''<article class="book-section cover-page revision-cover" data-unit="0" id="cover"><div class="cover-topline"><span>THE FINAL REVISION EDITION</span><span>01 / 02 / 03 / 04 / 05</span></div><div class="cover-layout"><div class="cover-content"><p class="cover-meta">ENGLISH FOR THE 21st CENTURY – LEVEL 1</p><p class="cover-english">ENGLISH</p><p class="cover-title">for the 21st Century</p><p class="cover-level">Level 1 · C21</p><h1 class="revision-cover-title">Final Revision<br/>– Units 1 to 5</h1><p class="revision-cover-ar" dir="rtl">المراجعة النهائية الشاملة للوحدات الخمس</p><div class="revision-badges">{''.join('<span>'+x+'</span>' for x in labels)}</div><p class="revision-dedication" dir="rtl">إهداء إلى فيرو وليد <span>♥</span></p></div>{art}</div><div class="revision-cover-descriptions"><p dir="ltr">{E(desc)}</p><p dir="rtl">{E(ar_desc)}</p></div><div class="cover-bottom"><span>FIVE UNITS. ONE COMPLETE REVISION.</span><a class="start-reading" href="#overview">ابدأ المراجعة ←</a></div></article>'''
articles.append(('cover',cover));nav.append({'id':'cover','title':'C21 · Final Revision – Units 1 to 5','unit':0,'heads':[]})
unitcards='<div class="revision-unit-grid">'+''.join(f'<a href="#unit-{i}"><span>0{i}</span><div><small>UNIT {i}</small><strong dir="ltr">{E(name)}</strong></div><b>↗</b></a>' for i,name in enumerate(names,1))+'</div>'
quick='<div class="revision-actions">'+''.join(link(a,b) for a,b in [('grammar-reference','Grammar Quick Reference'),('vocabulary-reference','Vocabulary Quick Reference'),('practice','Practice Questions'),('answers','Answer Key'),('exam-checklist','50 Things to Remember')])+'</div>'
overview=f'<p class="ui-description" dir="ltr">{E(desc)}</p><p class="ui-description">{E(ar_desc)}</p><h2 class="topic-heading">أهداف المراجعة</h2><ul class="revision-objectives"><li>مراجعة مفردات وقواعد الوحدات الخمس بالترتيب.</li><li>مراجعة المحادثات وقواعد الكتابة والأمثلة الواردة في المذكرات.</li><li>حل التدريبات ثم مراجعة نموذج الإجابة المنفصل.</li></ul>{unitcards}{quick}'+callout('المحتوى من الملفين المرفقين، مع الإبقاء على دروس الوحدات 1–3 السابقة. الإضافات التعليمية التوضيحية تُعرض بوسمها الأصلي. هذه تدريبات مراجعة، وليست أسئلة امتحان فعلية. '+link('sources','حدود المصدر والأسئلة الناقصة'))
add('overview','Course Overview · نظرة عامة',0,range_nodes('revision','revision-p2-11','revision-p3-0'),extra=overview,first=False)
add('contents','فهرس المراجعة والمكتبة التفصيلية',0,extra='__CONTENTS__',first=False)
unit_ranges=[('revision-p3-0','revision-p6-0'),('revision-p6-0','revision-p9-0'),('revision-p9-0','revision-p12-0'),('revision-p12-0','revision-p14-0'),('revision-p14-0','revision-p16-0')]
subtitles=[('vocabulary','Important Vocabulary'),('grammar','Grammar – Key Rules'),('expressions','Expressions & Conversations'),('writing','Important Writing Rules'),('tips','Exam Tips')]
for i,(start,end) in enumerate(unit_ranges,1):
 quickunit='<nav class="unit-topic-links" aria-label="أقسام الوحدة">'+''.join(link(f'unit-{i}-{a}',b) for a,b in subtitles)+'</nav>'
 quickunit+='<div class="revision-actions">'+link(f'vocabulary-unit-{i}','قاموس الوحدة')+link('practice','تدريبات المراجعة')+link(['lesson-00','lesson-08','lesson-17','study-u4-careers','study-u5-jobs'][i-1],'الشرح التفصيلي للوحدة')+'</div>'
 add(f'unit-{i}',f'Unit {i} – {names[i-1]}',i,range_nodes('revision',start,end),extra=quickunit)
add('grammar-reference','Grammar Quick Reference',6,range_nodes('revision','revision-p16-0','revision-p18-0'),extra=link('grammar45','جداول إضافية من شرح الوحدتين 4–5'))
add('vocabulary-reference','Vocabulary Quick Reference',6,range_nodes('revision','revision-p18-0','revision-p22-0'),extra='<nav class="unit-topic-links">'+''.join(link(f'vocabulary-unit-{i}',f'Unit {i}') for i in range(1,6))+link('vocabulary45','قاموس الشرح التفصيلي 4–5')+'</nav>')
practiceextra=callout('حل أولًا ثم انتقل إلى نموذج الإجابة. بعض الأسئلة ناقصة في الملف الأصلي وقد تم التنبيه بجوارها؛ لا توجد إجابات مُخمنة.')+ '<nav class="unit-topic-links">'+''.join(link('practice-'+a,b) for a,b in zip(cats,cat_titles))+'</nav><div class="revision-actions">'+''.join(link('practice-'+a,b) for a,b in [('u4','اختبار Unit 4 التفصيلي'),('u5','اختبار Unit 5 التفصيلي'),('u45','امتحان Units 4–5')])+'</div>'
add('practice','Practice Questions',7,range_nodes('revision','revision-p22-0','revision-p26-0'),extra=practiceextra)
add('answers','Answer Key',8,range_nodes('revision','revision-p26-0','revision-p29-0'),extra=callout('هذا نموذج المصدر، دون استبدال الإجابات. ملاحظات عدم الاتساق لا تغيّر النص المطبوع.')+'<nav class="unit-topic-links">'+''.join(link('answers-'+a,b) for a,b in zip(cats,cat_titles))+'</nav><div class="revision-actions">'+''.join(link('answers-'+a,b) for a,b in [('u4','إجابات Unit 4'),('u5','إجابات Unit 5'),('u45','إجابات الامتحان 4–5')])+'</div>')
checkextra=callout('عنوان المصدر «50 Things»، لكن تحته 51 نقطة (274–324). أُدرجت أول 50 نقطة كقائمة تحقق، وحُفظت النقطة الأخيرة كملاحظة إضافية. علامات التحقق تقيس مراجعتك الذاتية، لا درجة اختبار.')+'<div class="checklist-toolbar"><output id="checklist-progress" aria-live="polite">0 / 50</output><button type="button" id="reset-checklist">إلغاء كل العلامات</button></div>'
add('exam-checklist','50 Things to Remember Before the Exam',9,range_nodes('revision','revision-p29-0'),extra=checkextra,check=True)
# Detailed library: old sections and stable anchors retained in full.
for item,el in zip(oldnav[2:],legacy):
 item=dict(item);item['library']=True
 if item['id']=='lesson-28':item['unit']=9;el['data-unit']='9';item['title']='مراجعة المصدر السابق – Units 1–3'
 nav.append(item);articles.append((item['id'],str(el)))
G=[
 ('study-u4-careers','4A · Careers & Events',4,'units45-p3-0','units45-p4-17'),
 ('study-u4-pronouns','4A · Pronouns & Email',4,'units45-p4-17','units45-p6-9'),
 ('study-u4-conversations','4B · Conversations about Friends',4,'units45-p6-9','units45-p8-1'),
 ('study-u4-look','4C · Look at me!',4,'units45-p8-1','units45-p8-14'),
 ('study-u4-writing','Writing Skills · Unit 4',4,'units45-p8-14','units45-p10-3'),
 ('study-u4-skills','C21 Skills · Unit 4',4,'units45-p10-3','units45-p10-15'),
 ('study-u4-review','Unit 4 · مراجعة وأخطاء شائعة',4,'units45-p10-15','units45-p11-6'),
 ('practice-u4','Unit 4 · اختبار الشرح التفصيلي',7,'units45-p11-6','units45-p11-17'),
 ('answers-u4','Unit 4 · نموذج الإجابة التفصيلي',8,'units45-p11-17','units45-p13-0'),
 ('study-u5-jobs','5A · Jobs, Places & Adjectives',5,'units45-p13-0','units45-p15-15'),
 ('study-u5-simple','5B · My Life — Present Simple',5,'units45-p15-15','units45-p17-6'),
 ('study-u5-careers','5C · Career Choices & Profiles',5,'units45-p17-6','units45-p19-0'),
 ('study-u5-writing','Writing Skills · Unit 5',5,'units45-p19-0','units45-p19-19'),
 ('study-u5-skills','C21 Skills · Unit 5',5,'units45-p19-19','units45-p21-0'),
 ('study-u5-extension','Present Simple · تكملة توضيحية من المصدر',5,'units45-p21-0','units45-p21-17'),
 ('study-u5-review','Unit 5 · مراجعة وأخطاء شائعة',5,'units45-p21-17','units45-p22-10'),
 ('practice-u5','Unit 5 · اختبار الشرح التفصيلي',7,'units45-p22-10','units45-p23-0'),
 ('answers-u5','Unit 5 · نموذج الإجابة التفصيلي',8,'units45-p23-0','units45-p24-0'),
 ('vocabulary45','Units 4–5 · قاموس الشرح التفصيلي',6,'units45-p24-0','units45-p25-1'),
 ('grammar45','Units 4–5 · جداول القواعد التفصيلية',6,'units45-p25-1','units45-p26-1'),
 ('practice-u45','Units 4–5 · الامتحان النهائي الشامل',7,'units45-p26-1','units45-p26-17'),
 ('answers-u45','Units 4–5 · إجابات الامتحان النهائي',8,'units45-p26-17','units45-p27-12')]
for route,title,unit,start,end in G:
 extra=''
 if route.startswith('practice-'):extra=link(route.replace('practice-','answers-'),'انتقل إلى نموذج الإجابة')
 elif route.startswith('answers-'):extra=link(route.replace('answers-','practice-'),'← العودة إلى الاختبار')
 elif unit in [4,5]:extra=link(f'unit-{unit}','← المراجعة المختصرة للوحدة')
 if route=='study-u5-extension':extra+=callout('تكملة توضيحية واردة في المذكرة المرفقة؛ ليست إضافة من الموقع أو نقلًا حرفيًا لكل نشاط من الكتاب.')
 add(route,title,unit,range_nodes('units45',start,end),extra=extra,library=True)
sourceextra='<p class="ui-description">أرقام النص الأصلي محفوظة كما هي. روابط «المصدر» تفتح الصفحة المقابلة من PDF. أرقام صفحات الكتاب الدراسي المذكورة داخل الشرح ليست أرقام صفحات الموقع.</p>'
sourceextra+=callout('ملاحظات على الأصل: الأسئلة 131 و132 و134 بلا جمل، والسؤال 143 بلا جملة تصحيح. السؤال 119 لا يحدد صاحب الأخت، بينما الإجابة 199 تذكر Ali. السؤال 126 وإجابته غير متطابقين في عدد الخانات؛ السؤال 155 وإجابته 235 غير مكتملين. توجد شرطات مائلة دون بديل في الإجابات 246 و255. وحوار الدليل ص 7 يكرر اسم Maria كما في المصدر. لم تُصحح هذه المضامين أو تُستكمل بالتخمين.')
sourceextra+=callout('تم ضبط اتجاه النص، وترتيب لام–ألف، والمسافات والحروف المنفصلة الناتجة عن استخراج PDF، مع سجل إصلاحات طباعية. لم تُضف إجابات استماع/فيديو. ملفات PDF الأصلية محفوظة للرجوع إلى أي موضع ملتبس.')
for k,d in D.items():sourceextra+=f'<p><a class="revision-link" href="sources/{d["source"]}" target="_blank" rel="noopener">تنزيل {"المراجعة النهائية (30 صفحة)" if k=="revision" else "شرح الوحدتين 4–5 (27 صفحة)"} ↗</a></p>'
notes,heads=render_nodes(range_nodes('units45','units45-p27-12'),'sources',False)
sourceextra+=notes
for title,nodes in [('الغلاف والفهرس الأصليان — Final Revision',range_nodes('revision','revision-p1-0','revision-p2-11')),('الغلاف والمقدمة والفهرس — Units 4–5',range_nodes('units45','units45-p1-0','units45-p3-0'))]:
 h,_=render_nodes(nodes,'sources',False);sourceextra+=f'<details class="original-toc source-archive"><summary>{title}</summary>{h}</details>'
sourceextra+='<details class="original-toc source-archive"><summary>غلاف النسخة السابقة وإهداؤها — محفوظان</summary>'+str(oldcover).replace('id="paper"','id="legacy-paper"').replace('url(#paper)','url(#legacy-paper)')+'</details>'
add('sources','المصادر وحدود الإجابات',9,extra=sourceextra,first=False)
# Electronic contents and navigation from one common route registry.
def navlink(n):
 t=E(n['title']);h=f'<a data-route="{n["id"]}" href="#{n["id"]}" dir="auto">{t}</a>'
 if n.get('heads'):h+=f'<div class="nav-topics" data-for="{n["id"]}">'+''.join(f'<a href="#{x["id"]}" dir="auto">{E(x["title"])}</a>' for x in n['heads'])+'</div>'
 return h
navhtml=''.join('<a class="nav-home" data-route="'+n['id']+'" href="#'+n['id']+'">'+E(n['title'])+'</a>' for n in nav[:3])
for unit,title in [(i,n) for i,n in enumerate(names,1)]+[(6,'Quick References'),(7,'Practice Questions'),(8,'Answer Key'),(9,'Exam Checklist & Sources')]:
 members=[n for n in nav if n['unit']==unit];primary=[n for n in members if not n.get('library')];support=[n for n in members if n.get('library')]
 navhtml+=f'<details class="nav-group" data-unit="{unit}"><summary><span class="unit-badge">{unit:02}</span><span><small>{"UNIT "+str(unit) if unit<6 else "REVISION"}</small><b dir="ltr">{E(title)}</b></span><span class="chevron">⌄</span></summary><div class="nav-lessons">'+''.join(navlink(n) for n in primary)
 if support:navhtml+='<details class="library-nav"><summary>الشرح التفصيلي والمحتوى المحفوظ</summary>'+''.join(navlink(n) for n in support)+'</details>'
 navhtml+='</div></details>'
soup.select_one('#book-nav').clear();soup.select_one('#book-nav').append(frag(navhtml))
contents=unitcards+quick+'<h2 class="topic-heading">مكتبة الشرح والتدريب التفصيلي</h2><div class="toc-grid">'
for unit,title in [(i,n) for i,n in enumerate(names,1)]+[(6,'References'),(7,'Practice'),(8,'Answers'),(9,'Sources & Checklist')]:
 contents+=f'<div class="toc-unit"><div class="toc-unit-top"><span>{unit:02}</span><p>C21 LEVEL 1</p></div><h3 dir="ltr">{E(title)}</h3><ol>'+''.join(f'<li><a href="#{n["id"]}" dir="auto">{E(n["title"])}<span>↗</span></a></li>' for n in nav if n['unit']==unit)+'</ol></div>'
contents+='</div>'+str(original_toc)
# Rebuild only section placement; the original shell, controls, fonts and legacy lesson HTML are retained.
companion=soup.select_one('#cover-companion');companion.select_one('p').string='خمس وحدات، ومراجع سريعة، وتدريبات بإجابات منفصلة — مع مكتبة الشرح التفصيلي.'
companion.select_one('.tiny-label').string='YOUR FIVE-UNIT REVISION'
for route,body in articles:
 if route=='contents':body=body.replace('__CONTENTS__',contents)
 companion.insert_before(frag(body))
companion.extract();soup.select_one('#cover').insert_after(companion)
soup.select_one('#book-navigation').string=json.dumps(nav,ensure_ascii=False)
soup.title.string='C21 · Final Revision – Units 1 to 5'
soup.select_one('.sidebar-bottom small').string='UNITS 01 — 05'
soup.select_one('meta[name="description"]')['content']=desc
for name,value in [('course-title','English for the 21st Century – Level 1'),('course-code','C21'),('content-title','Final Revision – Units 1 to 5'),('description-ar',ar_desc)]:
 soup.head.append(soup.new_tag('meta',attrs={'name':name,'content':value}))
brand=soup.select_one('.brand-copy');brand.clear();brand.append('FINAL REVISION');brand.append(frag('<small>C21 · Level 1 · Units 1–5</small>'))
for st in soup.find_all(string=True):
 if 'THREE UNITS' in st:st.replace_with(st.replace('THREE UNITS','FIVE UNITS'))
 if 'COMPLETE STUDY GUIDE' in st and st.parent and st.parent.get('class')==['tiny-label']:st.replace_with('FINAL REVISION · UNITS 1–5')
newcss=soup.new_tag('link',href='assets/css/revision.css',rel='stylesheet');soup.head.append(newcss)
newjs=soup.new_tag('script',src='assets/js/revision.js');soup.body.append(newjs)
# Preserve source prose exactly after the documented PDF typography corrections.
assert len(rendered)==len(set(rendered)),[x for x,c in collections.Counter(rendered).items() if c>1]
assert set(rendered)==set(N),(set(N)-set(rendered))
for section in soup.select('.revision-section'):
 for p in list(section.select('p.source-paragraph')):
  if not p.parent or p.get('data-source','').startswith('src-'):continue
  while True:
   nxt=p.find_next_sibling()
   if not nxt or nxt.name!='p' or 'source-paragraph' not in nxt.get('class',[]):break
   pt=p.get_text().strip();nt=nxt.get_text().strip()
   if re.search(r'[.!?؟؛:]$',pt) or re.match(r'^(?:[0-9]+[.)(]|•|[ABC]:|الترجمة:|Omar$|Hi Mum|See you soon)',nt):break
   if pt in ['Hi Mum,','See you soon,','Omar']:break
   if p.has_attr('data-source'):
    inner=soup.new_tag('span')
    for attr in ['id','data-source','dir']:inner[attr]=p[attr];del p[attr]
    for child in list(p.contents):inner.append(child.extract())
    p.append(inner);p['dir']=direction(pt+' '+nt)
   nxt.name='span';nxt['class']=['source-fragment'];p.append(' ');p.append(nxt.extract());p['dir']=direction(p.get_text())

(P/'index.html').write_text(str(soup))
(P/'revision-manifest.json').write_text(json.dumps({'sources':[{'filename':d['source'],'pages':len(d['audit']),'audit':d['audit']} for d in D.values()],'nodes':len(N),'content':manifest,'routes':nav},ensure_ascii=False,indent=2))
(P/'sources').mkdir(exist_ok=True)
# Source PDFs are already in sources/; no network or runtime generation is used.
print('routes',len(nav),'source nodes',len(rendered),'searchable content blocks',len(manifest))
