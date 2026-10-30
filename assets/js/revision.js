'use strict';
(() => {
  const boxes = [...document.querySelectorAll('[data-check]')];
  const key = 'c21.final-revision.checklist.v1';
  let saved = [];
  try { saved = JSON.parse(localStorage.getItem(key) || '[]'); } catch { /* offline storage may be restricted */ }
  if (!Array.isArray(saved)) saved = [];
  boxes.forEach(box => { box.checked = saved.includes(box.dataset.check); });
  function update() {
    const selected = boxes.filter(box => box.checked).map(box => box.dataset.check);
    document.getElementById('checklist-progress').textContent = `${selected.length} / ${boxes.length}`;
    try { localStorage.setItem(key, JSON.stringify(selected)); } catch { /* still usable without persistence */ }
  }
  boxes.forEach(box => box.addEventListener('change', update));
  document.getElementById('reset-checklist').addEventListener('click', () => { boxes.forEach(box => { box.checked = false; }); update(); });
  update();
})();
