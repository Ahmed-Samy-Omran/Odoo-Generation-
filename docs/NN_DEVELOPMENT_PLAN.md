# خطة تطوير OdooGen باستخدام النيورال نتورك

> وثيقة الدراسة والخطة الكاملة لتطوير المشروع عبر الشبكات العصبية
> القرارات المبنية عليها: تحسين **جودة التوليد** • بدون GPU • البداية بمقياس **جودة الموديول**

---

## جدول المحتويات

1. [دراسة المشروع الحالي](#1-دراسة-المشروع-الحالي)
2. [أين تظهر النيورال نتورك الآن](#2-أين-تظهر-النيورال-نتورك-الآن)
3. [الفجوات الرئيسية](#3-الفجوات-الرئيسية)
4. [فرص إدخال النيورال نتورك](#4-فرص-إدخال-النيورال-نتورك)
5. [البلان الكاملة](#5-البلان-الكاملة)
6. [التطبيق على الكود (ملف-بملف)](#6-التطبيق-على-الكود-ملف-بملف)
7. [التبعيات الجديدة](#7-التبعيات-الجديدة)
8. [مقاييس النجاح](#8-مقاييس-النجاح)

---

## 1) دراسة المشروع الحالي

### البنية العامة

**OdooGen** — منصة تولد موديولات Odoo كاملة من نص طبيعي أو مخطط JSON.

### Backend (`Odoo-Generation-`) — FastAPI

| المكوّن | الدور |
|---|---|
| `app/services/ai_service.py` | الوسيط الذكي: برومبت → استدعاء مزوّدات LLM (NaraRouter/Gemini/OpenRouter مع fallback) → JSON صالح `GeneratorPayload` |
| `app/services/rag_service.py` | RAG محلي: `sentence-transformers/all-MiniLM-L6-v2` + ChromaDB (مفهرسة من مصدر Odoo) |
| `app/generators/OdooModuleGenerator.py` | توليد الملفات (models/views/security/reports) عبر قوالب Jinja2 |
| `app/services/component_registry_service.py` | سجل مكوّنات قابلة لإعادة الاستخدام (`knowledge_registry/`) |
| `app/services/learning_loop_service.py` | تسجيل كل تجربة توليد في `learning_log.json` |
| `app/services/supabase_service.py` | تخزين الجوبات + سجلات الاستخدام `api_usage_logs` + الـ History |
| `main.py` | الـ Endpoints: `/analyze-requirements/` • `/generate-module/` • `/chat/` • `/job/{id}` • `/rag/*` • `/api/stats/usage` |

### Frontend (`odoo-Gen-Front`) — React 18 + TypeScript + Vite

- شات عربي/إنجليزي مع مساعد "Senior Odoo Architect"
- محرر ERD بـ React Flow (`@xyflow/react`)
- عارض الملفات المولّدة (`CanvasView`) مع syntax highlighting
- داشبورد استخدام النماذج (`MonitorView`) بـ Recharts
- History/Restore من Supabase

### المسار الرئيسي لتوليد الموديول

```
نص المستخدم → ai_service.analyze_requirements()
              ├── RAG search (أحياناً مش مفهرس)
              ├── _find_matching_components (مطابقة بالكلمات)
              ├── بناء البرومبت → LLM (مزوّد واحد مع fallback)
              └── _parse_response → GeneratorPayload
→ OdooModuleGenerator (قوالب Jinja2) → ملفات + ZIP/GitHub
→ learning_loop_service.append_learning_entry
```

---

## 2) أين تظهر النيورال نتورك الآن

1. **مكالمات LLM عن بُعد** — توليد الـ schema والرد على الشات (شبكات عصبية مستضافة، بدون أي تدريب محلي).
2. **Embedding model** `all-MiniLM-L6-v2` في الـ RAG — بسيط وغير مستخدم بفعالية (الكوليكشن مش مفهرس بالكامل).
3. **مطابقة المكوّنات بالكلمات المفتاحية** في `_find_matching_components` (ai_service.py:498) — **ليست ML أصلاً**، مجرد `keyword in prompt`.

---

## 3) الفجوات الرئيسية

- ❌ **لا يوجد مقياس جودة**: الموديول يخرج للمستخدم بدون أي تحقق أنه صالح/قابل للتثبيت.
- ❌ **لا يوجد feedback loop للأخطاء**: لو الـ AI غلط في الـ schema، الجيل يشتغل والمستخدم ياخد ملف مكسور.
- ❌ المطابقة بالكلمات المفتاحية فاتت السياق (مش بتفهم الـ synonyms أو الدلالة).
- ❌ الـ RAG ما لهش reranker، والنتائج بتدخل البرومبت بنسبة ضوضاء عالية.
- ❌ الـ `learning_log.json` بيتراكم من غير أي تحليل أو استخدام.

---

## 4) فرص إدخال النيورال نتورك

| # | الفرصة | النوع | الجهد | العائد |
|---|---|---|---|---|
| 1 | **مقياس جودة الموديول** (Quality Scorer) | MLP/تصنيف على embeddings | متوسط | عالي — يمنع تسليم موديولات فاسدة |
| 2 | **مطابقة دلالية للمكوّنات** | Similarity neural embeddings | منخفض | عالي — اختيار مكوّن أصح |
| 3 | **Reranker للـ RAG** | Cross-encoder (BERT) | متوسط | متوسط — سياق أدق في البرومبت |
| 4 | **التنبؤ بنوع الحقل/العلاقة** | تصنيف متعدد الفئات | متوسط | متوسط — schema أدق من البداية |
| 5 | **معماري توليد محلي** (Fine-tune LLM) | LoRA على Qwen/LLaMA | عالي (محتاج GPU/كلاود) | عالي — بدون تكلفة API |

---

## 5) البلان الكاملة

### المرحلة 0 — طبقة البيانات (أساس كل حاجة)

**الهدف:** بناء dataset مقفول بـ (module_config + الملفات المولّدة + label جودة 0/1).

1. **مستخرج بيانات** — سكربت جديد `ml/dataset_builder.py` يدمج:
   - `knowledge_registry/learning_log.json` (prompt + config + ملفات)
   - جوبات Supabase (`generation_jobs`) — configs + chat_history
   - `history.json` + `generated_modules/`

2. **مولّد أمثلة سلبية** — `ml/negative_generator.py` يفسد configs سليمة عمداً:
   - حقل بدون `name`
   - relation لـ model غير موجود
   - selection بدون `selection_options`
   - `inherit_model` خاطئ
   - XML مكسور / ملفات فاضية

3. **التصنيف التلقائي** — نقاط تحقق Rule-based (`ml/validators.py`):
   - الـ schema يتسلايم مع Pydantic بدون أخطاء
   - كل `relation` تشير لـ model موجود
   - كل `selection` ليه `selection_options`
   - الـ XML سليم والمراجع (menus/actions) محلولة
   - الملفات المولّدة غير فاضية

4. **مخرج**: `ml/data/train.jsonl` — كل سطر: `{config_hash, config_json, features, label}`.

---

### المرحلة 1 — نموذج مقياس الجودة (الـ MVP، يعمل على CPU)

**الهدف:** موديل بياخد `module_config` ويرجّع score جودة `0.0–1.0`.

1. **الموديل** (صغير حقيقي على CPU):
   - Embed الـ config: `sentence-transformers` تحوّل الـ config لـ JSON string → vector (384 بعد)
   - **feature vector يدوي**: عدد الموديلات، الحقول، الأغلاقات، وجود relations بلا هدف، نسب أنواع الحقول... (تلتقط أخطاء لا يراها الـ embedding)
   - **MLP classifier** (طبقتان) فوق الـ vector — يُدرَّب بـ `scikit-learn` أو PyTorch CPU (بيانات صغيرة = ثواني)

2. **الملفات الجديدة**:
   - `ml/quality_model.py` — تعريف الموديل + train/predict
   - `ml/train_quality.py` — تدريب + حفظ بـ `joblib`/ONNX
   - `app/services/quality_service.py` — واجهة الـ score مدمجة في الباك

3. **الدمج في المسار** — في `ai_service._parse_response` (ai_service.py:549):
   - لو score < عتبة → **Retry بالـ error feedback**: البرومبت يتعاد مرّة بملاحظات "الموديل كشف أن X غير صالح" بدل تسليم ناتج فاسد
   - أو لو لسه فاشل → تحذير للمستخدم + تخطي الجيل

4. **Eval**: `tests/test_quality_model.py` + تقرير `ml/eval_report.md` (precision/recall/F1 + threshold tuning).

---

### المرحلة 2 — مطابقة دلالية + Reranker (تحسين السياق بدون GPU)

1. **استبدال المطابقة بالكلمات** في `_find_matching_components`:
   - Embed كل component metadata مرّة (cached) → cosine similarity مع الـ prompt
   - عتبة top-k بدل `score > 0`

2. **Reranker للـ RAG** — `cross-encoder/ms-marco-MiniLM-L-6-v2` (حجم صغير، سريع على CPU):
   - يعيد ترتيب نتائج ChromaDB الأولية → يُرسل أفضل 2 فقط في البرومبت

3. **النتيجة**: برومبت أنضف + اختيار مكوّن أدق = schema أقوى قبل ما يدخل الموديل الأصلي.

---

### المرحلة 3 — Quality-Gated Generation Loop (تكملة الفائدة)

1. **Best-of-N**: توليد 3 configs بدل 1 (بنفس البرومبت + temperature متنوعة) → الـ Quality Scorer يختار الأعلى.
2. **التنبؤ بنوع الحقل** (`ml/field_predictor.py`): تصنيف label الحقل النصي → `char/int/float/many2one/selection` (نفس تقنية المرحلة 1).
3. **رصد النتائج في learning_log**: إضافة حقول `quality_score` و `feedback` — دورة تحسين ذاتي ببيانات تدريب أكثر تلقائياً.

---

### المرحلة 4 (اختياري — عند توفّر GPU/كلاود) — توليد محلي

- Fine-tune `Qwen2.5-3B-Coder` أو `Llama-3.2-3B` بـ **LoRA** على البيانات (prompt → module_config JSON).
- تحويله كمزوّد جديد في `provider_groups` بـ `ai_service.py:73` (محلي عبر Ollama/vLLM) — يقلل تكلفة API للأبد.

---

## 6) التطبيق على الكود (ملف-بملف)

| الخطوة | الملف | التغيير |
|---|---|---|
| 1 | `ml/validators.py` (جديد) | نقاط فحص rule-based + مولّد أمثلة سلبية |
| 2 | `ml/dataset_builder.py` (جديد) | جمع `learning_log.json` + Supabase → `train.jsonl` |
| 3 | `ml/quality_model.py` (جديد) | MLP على embeddings + features |
| 4 | `ml/train_quality.py` (جديد) | تدريب على CPU + حفظ ONNX/joblib |
| 5 | `app/services/quality_service.py` (جديد) | واجهة score/تصنيف تعمل من الـ Backend |
| 6 | `app/services/ai_service.py` | `_parse_response` يضيف فحص الجودة + retry loop |
| 7 | `app/services/ai_service.py` | `_find_matching_components` يتحول للـ similarity |
| 8 | `app/services/rag_service.py` | Cross-encoder reranker |
| 9 | `main.py` | Endpoint `GET /api/quality/stats` (نسبة الموديولات المجتازة) |
| 10 | `tests/` | اختبارات لكل وحدة جديدة (قاعدة "no feature without test") |

---

## 7) التبعيات الجديدة

`requirements.txt`:
- `scikit-learn`
- `onnxruntime`
- `joblib`

خفيفة وتعمل على CPU بالكامل. لا توجد حاجة لـ torch إلا في المرحلة 4.

---

## 8) مقاييس النجاح

- **F1 لمقياس الجودة** ≥ 0.90 على مجموعة اختبار محجوزة.
- **نسبة retry الناجحة**: أول محاولة ثانية تنتج config مجتاز العتبة ≥ 70%.
- **زمن إضافي لكل جيل** ≤ 1–2 ثانية (الموديلات سريعة على CPU).

---

### ملاحظات أخيرة

- الـ data pipeline (المرحلة 0) هي الأساس — بدونها لا يوجد تدريب مفيد.
- المرحلتان 1 و 2 تعطيان أثراً فورياً على جودة التوليد بأقل جهد، وكلاهما يعمل بدون GPU.
- كل إضافة تلتزم بـ `ENGINEERING_STANDARDS.md`: اختبارات مع كل ميزة، نوع بيانات، Google-style docstrings.
