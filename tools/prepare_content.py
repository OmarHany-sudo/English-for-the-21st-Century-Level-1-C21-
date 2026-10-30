import json,re
from pathlib import Path
root=Path(__file__).resolve().parents[1]; dest=root/'content';dest.mkdir(exist_ok=True)
# Repairs below concern PDF text order, ligatures, punctuation and split glyphs only.
# Exercise omissions are deliberately NOT completed. Original PDFs remain available.
REPLACE={
 'قري با':'قريبًا','فع ل ااً':'فعلًا','ًر قصي ا':' قصيرًا','واض.اح':'واضحًا.','أبحا اث':'أبحاثًا','ٍهطا':'طاهٍ','ق،ّيم':'قيّم،','/ y./':'/y/.','/ y /':'/y/','a m.':'a.m.','p m.':'p.m.','محا م':'محام', 'T -shirt':'T-shirt','ًب غالا':'غالبًا','غالًاب':'غالبًا','غال با':'غالبًا','غالًبا':'غالبًا',
 'ن صًا':'نصًا','حرفًا مني':'حرفيًا من','مقط عا':'مقطعًا','أو ل ااً':'أولًا','تعري اف':'تعريفًا','اهتما ما':'اهتمامًا','ختاً.ام':'ختامًا.',
 'أه ل ااً':'أهلًا','قري.اب':'قريبًا.','ج ا؟ ولاد':'جدًا؟ ولا','أشخا ا':'أشخاصًا','جم ل ااً':'جملًا','أجًرر حوا ا':'أجرِ حوارًا',
 'سعي دا':'سعيدًا','ح.ّسنها':'حسّنها.','ح ل ااًًي حرفا':'حلًا حرفيًا','مستخدًام':'مستخدمًا','مستخد ما':'مستخدمًا',
 'اسً:ام':'اسمًا:','طبيعً(اي':'طبيعيًا (','استبيا نا':'استبيانًا','ضع خ ا':'ضع خطًا','وص فا':'وصفًا','سؤا ل ااً':'سؤالًا','سؤا ااًل':'سؤالًا',
 'خصو صًا':'خصوصًا','شر حا':'شرحًا','مبي ًعا':'مبيعًا','ح ًقا':'حقًا','مناسًبا':'مناسبًا','واضًحا':'واضحًا',
 '4ًع ما':'4 معًا','4&ًع ما':'& 4 معًا',':صحح':'صحح:',':اختر':'اختر:',':رتب':'رتب:',':مثال':'مثال:',
}
OVERRIDES={
 'revision-p5-1':'17. فرّق بين Egypt (country) و Egyptian (nationality).',
 'revision-p8-4':'40. فرّق بين profession: writer وبين nationality: Portuguese.',
 'revision-p12-4':'65. I want to tell you about... / Best wishes / See you soon /.',
 'revision-p14-5':'85. Collocations: high salary، long hours، flexible hours، helpful colleagues، friendly boss، interesting job.',
 'revision-p22-17':'129. Nice to meet you. – ______, ______.',
 'revision-p22-18':'130. [U3] I → ______; they → ______; she → ______.',
 'revision-p22-21':'133. ______ study together.',
 'revision-p24-0':"162. [U1] A: How old are you? B: I'm 19 years ______.",
 'revision-p24-3':"165. [U3] A: Who's the woman with glasses? B: She's my ______.",
 'revision-p24-4':'166. [U3] A: Can you repeat that, please? B: ______.',
 'revision-p24-7':'169. [U5] A: Do you work in an office? B: Yes, I ______.',
 'revision-p24-11':'173. [U1] كوّن سؤالًا من: She is Japanese.',
 'revision-p24-12':'174. [U2] اختر short answer: Is he a writer? – Yes, ______.',
 'revision-p24-13':'175. [U2] حوّل إلى اختصار: They are not Italian.',
 'revision-p24-14':'176. [U3] أكمل: I have; he ______; they ______.',
 'revision-p24-18':'180. [U5] حوّل للنفي: We live in Cairo.',
 'revision-p24-19':'181. [U5] كوّن سؤالًا: they / study / English?',
 'revision-p26-19':"212. parents'.",
 'revision-p26-24':'217. 1-B، 2-A، 3-D، 4-C، 5-E.',
 'revision-p27-25':'246. Of course /.',
 'revision-p28-6':"255. They're not Italian /.",
 'units45-p5-18':'good / at / science → He is good at science.',
 'units45-p8-17':'he/she/it + s أو es. وإذا انتهى الفعل بحرف ساكن + y غالبًا تتحول y إلى ies: study → studies.',
 'units45-p10-8':'مثال دمج توضيحي: Carmen Rodriguez is from Morocco. She is a student. → Carmen Rodriguez is a',
 'units45-p11-1':'• He study engineering. H → e studies engineering. ✓',
 'units45-p18-15':'economics. (Femi فاعل، studies فعل، economics مفعول/تكملة).',
 'units45-p21-4':'1) أغلب الأفعال: نضيف s: work → works، read → reads، live → lives.',
 'units45-p21-5':'2) الأفعال المنتهية بـ -ch, -sh, -ss, -x, -o غالبًا نضيف es: watch → watches، wash → washes، go → goes.',
 'units45-p21-6':'3) consonant + y: نحذف y ونضيف ies: study → studies، try → tries. أما vowel + y فنضيف s فقط: play →',
 'units45-p22-11':'15. A nurse works in a ______.',
}
OVERRIDES['revision-p22-17']='129. – Nice to meet you, ______.'
OVERRIDES.update({
 'units45-p2-7':'• Unit 4 – Networks: Careers & Events، Pronouns، Conversations about friends، Look at me!،',
 'units45-p2-8':'Writing Skills، C21 Skills، مراجعة واختبار.',
 'units45-p2-9':'• Unit 5 – Work: Jobs، Places of work، Adjectives، Present Simple، University subjects، Profiles،',
 'units45-p2-10':'Writing Skills، C21 Skills، مراجعة واختبار.',
 'units45-p9-8':'• نشاط 4: أكمل Profile نادية بصيغ الأفعال في الأقواس. حدد الفاعل قبل الفعل: Naya = she، her friends =',
 'units45-p19-12':'أسباب اختيارك في حوالي 100 كلمة.',
 'units45-p14-2':'وهكذا.',
})
CELL_OVERRIDES={
 ('units45-p3-2',2,1):'Pronouns: he, she, it, we, they',
 ('units45-p4-20',1,2):'Ahmed is my friend. He is kind. – أحمد صديقي، هو طيب.',
 ('units45-p10-16',1,1):'he مذكر مفرد؛ she مؤنث مفرد؛ it شيء مفرد؛ we أنا وآخرون؛ they جمع.',
 ('revision-p9-7',0,2):'مثال + ملاحظة',
 ('revision-p9-7',1,1):'I → my; you → your; he → his; she → her; it → its; we → our; they → their',
 ('revision-p12-6',0,2):'مثال + ملاحظة',('revision-p14-7',0,2):'مثال + ملاحظة',
}
changes=[]
def clean(t):
 t=re.sub(r'(\d+)\[\.\s*',r'\1. [',t)
 t=re.sub(r'^(\d+)\(\.\s*',r'\1. (',t)
 t=re.sub(r'^أهم القواعد (\d+)\. Grammar –',r'\1. Grammar – أهم القواعد',t)
 for a,b in REPLACE.items():t=t.replace(a,b)
 t=re.sub(r'([\u0621-\u064a])(\d)',r'\1 \2',t)
 t=re.sub(r'(\d)([\u0621-\u064a])',r'\1 \2',t)
 t=re.sub(r'([\u0621-\u064a])ً([\u0621-\u064a])ا',r'\1\2ًا',t)
 t=re.sub(r'([a-zA-Z])([\u0621-\u064a])',r'\1 \2',t)
 t=re.sub(r'^ص (\d+)\s*–(\d+) (.+) \|$',r'\3 | ص \1–\2',t)
 t=re.sub(r'^ص (\d+) (.+) \|$',r'\2 | ص \1',t)
 t=re.sub(r'([.?]) /$',r'/ \1',t)
 return t
for key in ['revision','units45']:
 d=json.loads((root/f'tools/extraction-work/{key}-structured.json').read_text())
 for n in d['nodes']:
  if n['kind']=='paragraph':
   before=n['text'];n['text']=OVERRIDES.get(n['id'],clean(before))
   if n['text']!=before:changes.append({'id':n['id'],'before':before,'after':n['text']})
  else:
   for ri,row in enumerate(n['rows']):
    for ci,c in enumerate(row):
     before=c['text'];c['text']=CELL_OVERRIDES.get((n['id'],ri,ci),clean(before))
     if c['text']!=before:changes.append({'id':f"{n['id']}-r{ri}-c{ci}",'before':before,'after':c['text']})
 (dest/f'{key}.json').write_text(json.dumps(d,ensure_ascii=False,indent=2))
(dest/'extraction-repairs.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2))
print('documented typography repairs',len(changes))
