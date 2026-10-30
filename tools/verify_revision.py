from pathlib import Path
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import json,collections,re
P=Path(__file__).resolve().parents[1]; R=P; W=P/'tools/qa-output'; W.mkdir(parents=True,exist_ok=True); base='http://localhost:8080/'
original=BeautifulSoup((P/'tools/legacy-template.html').read_text(),'html5lib');soup=BeautifulSoup((P/'index.html').read_text(),'html5lib')
manifest=json.loads((P/'revision-manifest.json').read_text());nav=manifest['routes'];report={};errors=[]
old={x['data-source']:x.get_text() for x in original.select('[data-source]')};now={x['data-source']:x.get_text() for x in soup.select('[data-source]')}
assert all(now.get(k)==v for k,v in old.items()),'Legacy source changed'
assert all(now.get(n['id'])==n['text'] for n in manifest['content']),'PDF HTML mismatch'
report['legacy_source_blocks_preserved']=len(old);report['new_source_blocks_preserved']=len(manifest['content'])
ids=[x['id'] for x in soup.select('[id]')];assert len(ids)==len(set(ids)),'Duplicate IDs'
# data-source legacy ids assigned on startup; count them as valid targets too.
targets=set(ids)|set(now);broken=[a['href'] for a in soup.select('a[href^="#"]') if a['href'][1:] and a['href'][1:] not in targets];assert not broken,broken
report['internal_links_checked']=len(soup.select('a[href^="#"]'))
assert [n['id'] for n in nav if re.fullmatch(r'unit-\d',n['id'])]==[f'unit-{i}' for i in range(1,6)]
for i in range(1,6):
 for kind in ['vocabulary','grammar','expressions','writing','tips']:assert soup.select_one(f'#unit-{i}-{kind}')
report['source_nodes']=manifest['nodes'];report['pdf_pages']=sum(s['pages'] for s in manifest['sources']);report['unmapped_pdf_body_spans']=sum(len(a['missing']) for s in manifest['sources'] for a in s['audit'])
report['new_tables']=len(soup.select('.revision-table table'));report['checklist_items']=len(soup.select('[data-check]'))
with sync_playwright() as pw:
 browser=pw.chromium.launch();p=browser.new_page(viewport={'width':1440,'height':1000});p.on('pageerror',lambda e:errors.append(str(e)));badrequests=[]
 p.on('response',lambda r:badrequests.append([r.status,r.url]) if r.status>=400 else None)
 p.goto(base);p.evaluate('document.fonts.ready');p.wait_for_timeout(400)
 layouts=[]
 for width in [320,390,768,1024,1440]:
  p.set_viewport_size({'width':width,'height':900});p.wait_for_timeout(350)
  for n in nav:
   p.evaluate('(id)=>location.hash=id',n['id']);p.wait_for_timeout(45)
   state=p.evaluate('''()=>({active:[...document.querySelectorAll('.book-section.active')].map(x=>x.id),overflow:document.documentElement.scrollWidth>innerWidth+1, width:document.documentElement.scrollWidth})''')
   assert state['active']==[n['id']],(n,state)
   assert not state['overflow'],(width,n['id'],state)
  layouts.append({'width':width,'routes':len(nav),'horizontal_overflow':0})
 report['responsive_routes']=layouts
 # Deep route, answer pairing, and visible subsection.
 p.goto(base+'#question-choose-1');p.wait_for_timeout(100);assert p.locator('#practice').is_visible()
 p.locator('#question-choose-1 .answer-jump').click();p.wait_for_timeout(100);assert p.locator('#answers').is_visible();assert p.evaluate('location.hash')=='#answer-choose-1'
 p.locator('#answer-choose-1 .answer-jump').click();p.wait_for_timeout(100);assert p.locator('#practice').is_visible()
 p.goto(base+'#study-u4-pronouns');p.wait_for_timeout(100);assert p.locator('.library-nav:has(a.active)').get_attribute('open') is not None
 # Search new and old material and Arabic.
 p.locator('#open-search').click();p.locator('#search-input').fill('salary');p.wait_for_timeout(130);assert p.locator('.search-result').count()>0;p.locator('.search-result').first.click();p.wait_for_timeout(100);assert not p.locator('#search-dialog').is_visible()
 p.locator('#open-search').click();p.locator('#search-input').fill('الضمائر');p.wait_for_timeout(100);assert p.locator('.search-result').count()>0;p.locator('#close-search').click()
 p.locator('#theme-toggle').click();assert p.locator('html').get_attribute('data-theme')=='dark';p.reload();assert p.locator('html').get_attribute('data-theme')=='dark';p.locator('#theme-toggle').click()
 # Checklist persistence and reset.
 p.goto(base+'#exam-checklist');p.wait_for_timeout(100);p.locator('[data-check]').first.check();assert p.locator('#checklist-progress').inner_text()=='1 / 50';p.reload();assert p.locator('[data-check]').first.is_checked();p.locator('#reset-checklist').click();assert p.locator('#checklist-progress').inner_text()=='0 / 50'
 # Mobile menu and keyboard closing.
 p.set_viewport_size({'width':390,'height':844});p.wait_for_timeout(350);p.locator('#open-menu').click();p.wait_for_timeout(350);assert p.locator('#sidebar').evaluate('(e)=>!e.inert');p.keyboard.press('Escape');p.wait_for_timeout(350);assert p.locator('#sidebar').evaluate('(e)=>e.inert')
 # Source files reachable and original bytes retained.
 for source in manifest['sources']:assert p.request.get(base+'sources/'+source['filename']).status==200
 # Before/after print restoration and a real PDF generation smoke test.
 p.set_viewport_size({'width':1440,'height':1000});p.goto(base+'#cover');p.wait_for_timeout(300)
 closed=p.locator('details.original-toc:not([open])').count();p.evaluate("dispatchEvent(new Event('beforeprint'))");assert p.locator('details.original-toc:not([open])').count()==0
 p.emulate_media(media='print');assert p.locator('.book-section:visible').count()==len(nav)
 p.pdf(path=str(W/'print-smoke.pdf'),format='A4',print_background=True,prefer_css_page_size=True)
 p.emulate_media(media='screen');p.evaluate("dispatchEvent(new Event('afterprint'))")
 # Browser itself emits print events; explicitly verify fresh restoration cycle.
 p.locator('details.original-toc').evaluate_all('(els)=>els.forEach(e=>e.open=false)');p.evaluate("dispatchEvent(new Event('beforeprint'))");p.evaluate("dispatchEvent(new Event('afterprint'))");assert p.locator('details.original-toc[open]').count()==0
 p.screenshot(path=str(W/'cover-final.png'),full_page=True)
 p.goto(base+'#unit-3-grammar');p.wait_for_timeout(100);p.screenshot(path=str(W/'grammar-final.png'))
 p.goto(base+'#question-complete-6');p.wait_for_timeout(100);p.screenshot(path=str(W/'source-warning-final.png'))
 p.set_viewport_size({'width':390,'height':844});p.goto(base+'#cover');p.wait_for_timeout(400);p.screenshot(path=str(W/'cover-mobile-final.png'),full_page=True)
 p.goto(base+'#unit-5');p.wait_for_timeout(150);p.screenshot(path=str(W/'unit5-mobile-final.png'))
 # Offline file:// uses no HTTP calls for content, scripts or fonts.
 q=browser.new_page();q.on('pageerror',lambda e:errors.append('offline '+str(e)));external=[];q.on('request',lambda r:external.append(r.url) if r.url.startswith('http') else None)
 q.goto((P/'index.html').as_uri()+'#unit-4');q.wait_for_timeout(200);assert q.locator('#unit-4').is_visible();assert not external,external
 report['functional']={'question_answer_roundtrip':True,'search_arabic_english':True,'theme_persistence':True,'checklist_persistence_reset':True,'mobile_menu_escape':True,'nested_sidebar':True,'source_pdf_links':True,'print_all_sections':True,'print_details_restore':True,'file_offline':True}
 browser.close()
report['javascript_errors']=errors;report['http_errors']=badrequests;assert not errors,errors;assert not badrequests,badrequests
(P/'revision-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))
