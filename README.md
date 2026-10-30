# C21 — Final Revision · Units 1–5

تحديث داخل مشروع `c21-ebook` نفسه، باستخدام HTML/CSS/JavaScript دون إطار عمل أو اعتماد شبكي أثناء التشغيل.

- **Course:** English for the 21st Century – Level 1
- **Code:** C21
- **Content:** Final Revision – Units 1 to 5
- **العنوان:** المراجعة النهائية الشاملة للوحدات الخمس

## التشغيل

افتح `index.html` مباشرة بعد فك ضغط المشروع، مع إبقاء مجلد `assets` بجانبه. يعمل البحث والتنقل والخطوط محليًا. حفظ الوضع الليلي وقائمة التحقق يعتمد على سماح المتصفح بالتخزين المحلي.

للمعاينة عبر خادم:

```bash
cd c21-ebook
python -m http.server 8080 --bind 0.0.0.0
```

لا توجد خطوة npm أو build مطلوبة. لا يستدعي الموقع APIs أو CDN. روابط PDF تحتاج الملفات المحلية داخل `sources/`.

## المحتوى والتنقل

- `#cover` — غلاف المراجعة لخمس وحدات.
- `#overview` — وصف المقرر وأهداف المراجعة وروابط الوحدات.
- `#contents` — الفهرس الموحد للمراجعة والمكتبة التفصيلية.
- `#unit-1` … `#unit-5` — المراجعة، بالترتيب المطلوب.
- لكل وحدة: `-vocabulary`، `-grammar`، `-expressions`، `-writing`، `-tips`.
- `#grammar-reference` و`#vocabulary-reference` — المراجع السريعة.
- `#vocabulary-unit-1` … `#vocabulary-unit-5` — مفردات كل وحدة.
- `#practice` — ثمانية أقسام للتدريب؛ و`#answers` — الإجابات في صفحة منفصلة.
- `#exam-checklist` — 50 خانة تحقق محفوظة محليًا، مع النقطة الإضافية المطبوعة في المصدر.
- `#study-u4-*` و`#study-u5-*` — شرح الوحدتين 4 و5، متضمنًا المهارات والنماذج والتكملات الموسومة في المصدر.
- `#practice-u4`، `#practice-u5`، `#practice-u45` — اختبارات الدليل التفصيلي، مع صفحات `#answers-u4` و`#answers-u5` و`#answers-u45` منفصلة.
- `#grammar45` و`#vocabulary45` — جداول وقاموس دليل 4–5.
- `#sources` — الملفات الأصلية وحدود الإجابات والمقدمات والأغلفة الأصلية.
- روابط `#lesson-00` … `#lesson-28` القديمة لا تزال صالحة؛ محتواها محفوظ، بما فيه الإهداء والفهرس الورقي.

شريط تقدم القراءة يصف موضع القراءة، وليس درجة امتحان أو اكتمال تعلم. عداد قائمة التحقق مستقل عنه. تفاصيل الإضافات ونتائج الاختبار في `REVISION_REPORT.md`.

## المصدر والدقة

المرفقان المستخدمان **PDF** وليسا DOCX:

1. `sources/C21_Level1_Final_Revision_Units1-5_AR.pdf` — 30 صفحة.
2. `sources/C21_Level1_Units4-5_Study_Guide_AR.pdf` — 27 صفحة.

المحتوى نصوص وجداول HTML قابلة للبحث، وليس صور صفحات فقط. سجل المحتوى في `revision-manifest.json`، وسجل إصلاح ترتيب النص واللام–ألف والترقيم والحروف المتباعدة في `content/extraction-repairs.json`.

بعض الأسئلة ناقصة أو غير متسقة في المصدر نفسه؛ تم إبقاؤها والتنبيه إليها، لا تأليف بدائل لها. عنوان قائمة الخمسين يتبعه 51 بندًا في PDF؛ أُبقيت النقطة الأخيرة كملاحظة إضافية. لا توجد ملفات الصوت أو عرض الشرائح، ولم تُخترع إجاباتها.

## تعديل المحتوى وإعادة توليد HTML

البيانات المنسقة في:

- `content/revision.json`
- `content/units45.json`

لتحديث HTML بعد تحريرها:

```bash
pip install beautifulsoup4 html5lib
python tools/integrate_revision.py
```

يعتمد المولد على القالب السابق المحفوظ في `tools/legacy-template.html`؛ لا يعيد بناء التصميم ولا يمحو الدروس القديمة. يحتفظ بملفات CSS/JS الحالية. إذا عدلت هيكل الصفحة يدويًا فادمج تعديلك في المولد أيضًا قبل إعادة تشغيله.

**إعادة الاستخراج اختيارية، وليست مطلوبة لتشغيل الموقع:**

```bash
pip install PyMuPDF
python tools/extract_sources.py
python tools/prepare_content.py
python tools/integrate_revision.py
```

الأمر `prepare_content.py` يعيد إنشاء ملفات JSON من المصادر ويطبق إصلاحات الاستخراج المسجلة في السكربت؛ احفظ أي تعديلات تحريرية إضافية قبل تشغيله. ملفات العمل تنشأ داخل `tools/extraction-work/`.

## الاختبار

```bash
pip install -r tools/requirements-dev.txt
playwright install chromium
# شغّل خادم 8080 في نافذة أخرى أولًا
python tools/verify_revision.py
```

نتائج النسخة الحالية: `revision-verification.json`. ينشئ الاختبار لقطات شاشة وPDF فحص داخل `tools/qa-output/`؛ ليست اعتمادًا لتشغيل الموقع.

## الطباعة والملفات التاريخية

زر الطباعة يستخدم تخطيط A4 ويطبع جميع الأقسام، ويفتح التفاصيل المصدرية مؤقتًا. عولجت فواصل الفصول والأغلفة المحفوظة لتجنب صفحات فواصل فارغة غير لازمة.

`print/C21_Level1_Ebook_Print.pdf` و`verification.json` و`content-manifest.json` تخص **الإصدار السابق للوحدات 1–3**، وتُركت كأرشيف، لا كمخرجات المراجعة الجديدة. كذلك `docs/LEGACY_README.md` و`docs/LEGACY_QUALITY_CHECK.md` توثيق تاريخي. مرجع جودة النسخة الحالية هو `QUALITY_CHECK.md` و`revision-verification.json`.

الخطوط المحلية Cairo وInter وتراخيص OFL محفوظة كما كانت.
