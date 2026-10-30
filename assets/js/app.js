'use strict';
(() => {
  const $ = (s, root = document) => root.querySelector(s);
  const $$ = (s, root = document) => [...root.querySelectorAll(s)];
  const nav = JSON.parse($('#book-navigation').textContent);
  const sections = $$('.book-section');
  const sidebar = $('#sidebar');
  const modal = $('#search-dialog');
  let activeIndex = 0;
  let lastMenuFocus = null;
  let searchMatches = [], shown = 0;
  let scrollScheduled = false;
  let expandedForPrint = [];
  const storage = {
    get(key) { try { return localStorage.getItem('c21.' + key); } catch { return null; } },
    set(key, val) { try { localStorage.setItem('c21.' + key, val); } catch { /* file:// can restrict storage */ } }
  };
  // Each source paragraph has its own address. Existing heading anchors remain untouched.
  $$('[data-source]').forEach(el => { if (!el.id) el.id = el.dataset.source; });
  function resolve(id) {
    let el = document.getElementById(id) || document.querySelector('[data-source="' + CSS.escape(id) + '"]');
    if (!el) return null;
    const section = el.closest('.book-section');
    if (!section) return null;
    return { el, section, index: nav.findIndex(n => n.id === section.id) };
  }
  function menu(open) {
    sidebar.inert = matchMedia('(max-width: 1000px)').matches && !open;
    sidebar.classList.toggle('open', open);
    $('#scrim').classList.toggle('visible', open);
    $('#open-menu').setAttribute('aria-expanded', String(open));
    if (open) { lastMenuFocus = document.activeElement; $('#close-menu').focus(); }
    else if (lastMenuFocus) { lastMenuFocus.focus({ preventScroll: true }); lastMenuFocus = null; }
  }
  function updateProgress() {
    const current = sections[activeIndex];
    if (!current) return;
    const rect = current.getBoundingClientRect();
    const absoluteTop = rect.top + window.scrollY;
    const available = Math.max(1, current.offsetHeight - window.innerHeight + 140);
    const fraction = Math.max(0, Math.min(1, (window.scrollY - absoluteTop + 100) / available));
    const pct = activeIndex === 0 ? 0 : Math.min(100, Math.round(((activeIndex - 1 + fraction) / (nav.length - 2)) * 100));
    $('#reading-progress').style.width = pct + '%';
    $('#reading-status').textContent = activeIndex === 0 ? 'المراجعة النهائية · خمس وحدات' : 'تقدّم القراءة · ' + pct + '%';
    $('#back-to-top').classList.toggle('visible', window.scrollY > 380);
    scrollScheduled = false;
  }
  function route(shouldScroll = true) {
    let id;
    try { id = decodeURIComponent(location.hash.slice(1)) || 'cover'; } catch { id = 'cover'; }
    const result = resolve(id) || resolve('cover');
    if (!result) return;
    activeIndex = Math.max(0, result.index);
    sections.forEach(s => s.classList.toggle('active', s === result.section));
    $('#cover-companion').style.display = result.section.id === 'cover' ? '' : 'none';
    $('#current-location').textContent = nav[activeIndex].title;
    document.title = nav[activeIndex].title + ' · C21';
    $$('#book-nav [data-route]').forEach(a => {
      const active = a.dataset.route === result.section.id;
      a.classList.toggle('active', active);
      if (active) {
        a.setAttribute('aria-current', 'page');
        let parent = a.parentElement;
        while (parent && parent !== sidebar) { if (parent.tagName === 'DETAILS') parent.open = true; parent = parent.parentElement; }
      } else a.removeAttribute('aria-current');
    });
    $$('.nav-topics').forEach(n => n.classList.toggle('active', n.dataset.for === result.section.id));
    const group = $('#book-nav .nav-group[data-unit="' + nav[activeIndex].unit + '"]');
    if (group) group.open = true;
    const prev = $('#previous-lesson'), next = $('#next-lesson');
    prev.setAttribute('aria-disabled', String(activeIndex === 0));
    next.setAttribute('aria-disabled', String(activeIndex === nav.length - 1));
    if (activeIndex > 0) { prev.href = '#' + nav[activeIndex - 1].id; $('b', prev).textContent = nav[activeIndex - 1].title; }
    if (activeIndex < nav.length - 1) { next.href = '#' + nav[activeIndex + 1].id; $('b', next).textContent = nav[activeIndex + 1].title; }
    $('#section-counter').textContent = String(activeIndex + 1).padStart(2, '0') + ' / ' + nav.length;
    storage.set('last-section', result.section.id);
    if (sidebar.classList.contains('open')) menu(false);
    if (shouldScroll) requestAnimationFrame(() => {
      if (result.el !== result.section) {
        let parent = result.el.parentElement;
        while (parent && parent !== result.section) { if (parent.tagName === 'DETAILS') parent.open = true; parent = parent.parentElement; }
        result.el.scrollIntoView({ behavior: 'instant', block: 'start' });
        window.scrollBy({ top: -105, behavior: 'instant' });
        result.el.classList.remove('search-flash');
        void result.el.offsetWidth;
        result.el.classList.add('search-flash');
        setTimeout(() => result.el.classList.remove('search-flash'), 2200);
      } else window.scrollTo({ top: 0, behavior: 'instant' });
      updateProgress();
    });
    updateProgress();
  }
  function applyTheme(theme) {
    document.documentElement.dataset.theme = theme;
    const dark = theme === 'dark';
    $('#theme-toggle').setAttribute('aria-pressed', String(dark));
    $('#theme-toggle').setAttribute('aria-label', dark ? 'تفعيل الوضع النهاري' : 'تفعيل الوضع الليلي');
    $('#theme-toggle').innerHTML = dark ? '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 1v2m0 18v2M1 12h2m18 0h2M4 4l2 2m12 12 2 2M4 20l2-2M18 6l2-2"/></svg>' : '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path d="M20 14A9 9 0 0 1 10 3a9 9 0 1 0 10 11Z"/></svg>';
  }
  // Arabic diacritics, hamza forms and case are normalized only in the search index.
  // The displayed source text is never rewritten.
  function normalize(s) {
    return s.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f\u064b-\u065f\u0670\u0640]/g, '').replace(/[أإآٱ]/g, 'ا').replace(/ى/g, 'ي').replace(/[\u200e\u200f\u202a-\u202e]/g, '');
  }
  const index = $$('[data-source]').map(el => ({ el, text: el.textContent, normalized: normalize(el.textContent), section: el.closest('.book-section') })).filter(x => x.section);
  function textWithHighlight(container, text, query) {
    // Preserve original characters. Build a position map from normalized to original text.
    let normalized = '', map = [];
    for (let i = 0; i < text.length; i++) {
      const ch = normalize(text[i]);
      for (const c of ch) { normalized += c; map.push(i); }
    }
    const at = normalized.indexOf(query);
    const start = at >= 0 ? map[at] : 0;
    const end = at >= 0 ? map[at + query.length - 1] + 1 : 0;
    const lo = Math.max(0, start - 65), hi = Math.min(text.length, Math.max(end + 115, lo + 180));
    if (lo > 0) container.append(document.createTextNode('… '));
    container.append(document.createTextNode(text.slice(lo, start)));
    if (at >= 0) { const mark = document.createElement('mark'); mark.textContent = text.slice(start, end); container.append(mark); }
    container.append(document.createTextNode(text.slice(at >= 0 ? end : lo, hi)));
    if (hi < text.length) container.append(document.createTextNode(' …'));
  }
  function renderSearch(reset = true) {
    const results = $('#search-results');
    if (reset) { results.replaceChildren(); shown = 0; }
    const oldMore = $('.search-more', results); if (oldMore) oldMore.remove();
    const query = normalize($('#search-input').value.trim());
    const batch = searchMatches.slice(shown, shown + 50);
    batch.forEach(item => {
      const link = document.createElement('a'); link.className = 'search-result'; link.href = '#' + item.el.id;
      const label = document.createElement('small'); label.dir = 'auto';
      label.textContent = nav.find(n => n.id === item.section.id)?.title || '';
      const snippet = document.createElement('p'); snippet.dir = 'auto'; textWithHighlight(snippet, item.text, query);
      link.append(label, snippet);
      link.addEventListener('click', () => { modal.close(); if (location.hash === link.hash) route(true); });
      results.append(link);
    });
    shown += batch.length;
    if (shown < searchMatches.length) {
      const more = document.createElement('button'); more.className = 'search-more print-button'; more.textContent = 'عرض المزيد (' + (searchMatches.length - shown) + ')'; more.addEventListener('click', () => renderSearch(false)); results.append(more);
    }
  }
  function search() {
    const query = normalize($('#search-input').value.trim());
    if (!query) { $('#search-count').textContent = 'ابحث بالعربية أو الإنجليزية في جميع الوحدات.'; $('#search-results').replaceChildren(); return; }
    searchMatches = index.filter(item => item.normalized.includes(query));
    $('#search-count').textContent = searchMatches.length + ' نتيجة في الكتاب';
    renderSearch();
    if (!searchMatches.length) { const p = document.createElement('p'); p.className = 'search-empty'; p.textContent = 'لم نعثر على نتائج. جرّب كلمة أخرى أو جزءاً من العبارة.'; $('#search-results').append(p); }
  }
  function openSearch() { if (!modal.open) modal.showModal(); setTimeout(() => $('#search-input').focus(), 20); }
  function preparePrint() {
    if (expandedForPrint.length) return; // Idempotent if a PDF renderer repeats beforeprint.
    expandedForPrint = $$('details.original-toc:not([open])'); expandedForPrint.forEach(el => el.open = true);
  }
  function restorePrint() { expandedForPrint.forEach(el => el.open = false); expandedForPrint = []; }
  document.body.classList.add('js-ready');
  applyTheme(storage.get('theme') || 'light');
  $('#theme-toggle').addEventListener('click', () => { const next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark'; applyTheme(next); storage.set('theme', next); });
  $('#open-menu').addEventListener('click', () => menu(true));
  $('#close-menu').addEventListener('click', () => menu(false));
  $('#scrim').addEventListener('click', () => menu(false));
  $('#open-search').addEventListener('click', openSearch);
  $('#close-search').addEventListener('click', () => modal.close());
  modal.addEventListener('click', e => { if (e.target === modal) { const r = modal.getBoundingClientRect(); if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) modal.close(); } });
  let searchTimer;
  $('#search-input').addEventListener('input', () => { clearTimeout(searchTimer); searchTimer = setTimeout(search, 110); });
  $('#print-book').addEventListener('click', async () => { await document.fonts.ready; window.print(); });
  window.addEventListener('beforeprint', preparePrint);
  window.addEventListener('afterprint', restorePrint);
  $('#back-to-top').addEventListener('click', () => window.scrollTo({ top: 0, behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth' }));
  window.addEventListener('hashchange', () => route(true));
  window.addEventListener('scroll', () => { if (!scrollScheduled) { scrollScheduled = true; requestAnimationFrame(updateProgress); } }, { passive: true });
  window.addEventListener('resize', () => { updateProgress(); sidebar.inert = matchMedia('(max-width: 1000px)').matches && !sidebar.classList.contains('open'); });
  document.addEventListener('keydown', e => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); openSearch(); }
    if (e.key === 'Escape' && sidebar.classList.contains('open')) menu(false);
    if (e.key === 'Tab' && sidebar.classList.contains('open') && !modal.open) {
      const focusables = $$('a,button,summary', sidebar).filter(el => el.offsetParent !== null);
      const first = focusables[0], last = focusables[focusables.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
  });
  // Re-clicking a current chapter still returns to the beginning of that chapter.
  document.addEventListener('click', e => {
    const a = e.target.closest('a[href^="#"]');
    if (a && a.hash === location.hash && !a.hasAttribute('aria-disabled')) { e.preventDefault(); route(true); }
    if (a && a.getAttribute('aria-disabled') === 'true') e.preventDefault();
  });
  sidebar.inert = matchMedia('(max-width: 1000px)').matches;
  route(true);
  document.fonts.ready.then(updateProgress);
})();
