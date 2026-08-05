# Architecture Knowledge Platform

## 1. الرؤية

منصة المعرفة الهندسية تهدف إلى جعل بناء موديولات Odoo أسرع وأكثر قابلية للتكرار. المنصة تجمع بين:
- سجلات المعرفة المركبة التي تصف مكونات أعمال قابلة لإعادة الاستخدام.
- منظومة AI تعمل على تحليل متطلبات المستخدم وتحويلها إلى هيكل موديول موجَّه.
- حلقة تعلم تحفظ تجارب التوليد السابقة لتطوير المكونات والبرومبتات بمرور الوقت.

هذه المنصة تساعد فرق التطوير على توليد موديولات مخصصة بسرعة، وتوثيق القرارات الهندسية، وتحسين أداء النظام عبر البيانات التاريخية.


### Vision

The Architecture Knowledge Platform is designed to make Odoo module creation faster and more repeatable. It combines:
- a component registry that describes reusable business building blocks.
- an AI orchestrator that translates user requirements into module structure.
- a learning loop that records generation outcomes for future improvements.

This platform helps development teams generate custom modules quickly, document architectural decisions, and improve the system over time based on historical data.

## 2. المكونات الرئيسية

### ComponentRegistry

`ComponentRegistryService` هو المكون المسؤول عن:
- إيجاد المكونات المعرفة في `knowledge_registry/`.
- قراءة التعريفات الوصفية لـ components عبر `metadata.json`.
- توفير المسار الصحيح للمكونات أثناء التوليد.

وظيفة هذا المكون هي ربط المتطلبات الواردة من المستخدم بالمكونات المهيأة مسبقًا، وتمكين إعادة استخدام القواعد الأمنية، الوثائق، وملفات البنية المعرفة داخل المكون.

### AIOrchestrator

المسار الرئيسي هنا هو `app/services/ai_service.py`.

يعمل AI Orchestrator على:
- استدعاء واجهات الشبكات العصبية لتحليل برومبت المستخدم.
- بناء برومبت إدخالي قياسي مع قواعد وصيغة استجابة محددة.
- تحويل النص الناتج من الـ AI إلى شكل `GeneratorPayload` صالح.
- البحث عن مكونات متطابقة في سجلات المعرفة باستخدام `component_registry_service`.

المنصة تعتمد على طبقة ذكية قادرة على:
- تحليل متطلبات المستخدم بلغة طبيعية.
- ربط المتطلبات بمكونات موجودة.
- تشغيل مسار التوليد الكامل إلى تكوين موديول.

### LearningLoop

المكون الجديد هو `app/services/learning_loop_service.py`.

يقوم هذا المكون بتسجيل كل تجربة توليد ناجحة في ملف:
- `knowledge_registry/learning_log.json`

المعلومات المسجلة تشمل:
- `job_id` الخاص بعملية التوليد
- الـ Prompt الأصلي من المستخدم
- المكونات المستخدمة (`matched_components`)
- الوحدات المولدة والملفات الناتجة
- أي ملاحظات أو مخرجات إضافية

هذه البيانات تهدف إلى دعم التحسين المستقبلي للبرومبتات والمكونات، وتحليل جودة التوليد عبر الزمن.


### Key Components

#### ComponentRegistry

`ComponentRegistryService` is responsible for:
- discovering components under `knowledge_registry/`
- reading component metadata from `metadata.json`
- resolving component directories during generation.

This service maps user requirements to reusable knowledge components, enabling reuse of security rules, docs, and architecture artifacts.

#### AIOrchestrator

The main entry point is `app/services/ai_service.py`.

The AI Orchestrator:
- calls AI providers to analyze the user prompt
- constructs a standardized prompt with schema rules
- converts the AI output into a valid `GeneratorPayload`
- searches for matching registry components via `component_registry_service`

It allows the platform to understand natural language requirements, reuse existing components, and generate a complete module configuration.

#### LearningLoop

Implemented in `app/services/learning_loop_service.py`.

This service logs each successful generation to:
- `knowledge_registry/learning_log.json`

Logged data includes:
- the prompt from the user
- matched components used
- generated modules and their files
- notes or additional metadata

This log supports future prompt improvement, component refinement, and generation quality analysis.

## 3. كيفية الاستخدام

### تشغيل النظام

1. تنشيط البيئات الافتراضية:
   - `cd Odoo-Generation-`
   - `.\.venv\Scripts\Activate.ps1`
2. تشغيل الخادم:
   - `python -m uvicorn main:app --host 127.0.0.1 --port 8002`
3. التأكد من صحة الخدمة:
   - `GET http://127.0.0.1:8002/health`

### توليد موديول من تكوين JSON

1. أرسل طلب `POST` إلى `/generate-module/` مع جسم JSON مطابق لـ `GeneratorPayload`.
2. ستتلقى `job_id` فورًا.
3. راقب الحالة باستخدام `/job/{job_id}`.
4. بعد اكتمال التوليد، استخدم `download_url` لتنزيل ZIP.

### تحليل المتطلبات وإنشاء الموديول تلقائيًا

1. أرسل برومبت المستخدم إلى endpoint:
   - `POST /analyze-requirements/`
2. يتم تحليل البرومبت بواسطة AI.
3. يقوم النظام بتوليد الموديول تلقائيًا ويحفظ تقدم العمل في job.
4. تتوفر النتيجة النهائية عبر `/download/{job_id}` أو `github_url` إذا كان `git_deploy_target` هو `github`.


### How to Use

#### Start the system

1. Activate the virtual environment:
   - `cd Odoo-Generation-`
   - `.\.venv\Scripts\Activate.ps1`
2. Run the server:
   - `python -m uvicorn main:app --host 127.0.0.1 --port 8002`
3. Verify health:
   - `GET http://127.0.0.1:8002/health`

#### Generate a module from JSON

1. Send a `POST` to `/generate-module/` with a JSON body matching `GeneratorPayload`.
2. Receive a `job_id` immediately.
3. Poll `/job/{job_id}` for progress.
4. Download the ZIP using the returned `download_url` once done.

#### Analyze requirements and auto-generate a module

1. Send the user prompt to:
   - `POST /analyze-requirements/`
2. The AI analyzes the prompt.
3. The system generates the module automatically and updates job progress.
4. Final output is available at `/download/{job_id}` or via `github_url` if `git_deploy_target` is `github`.

## 4. أمثلة

### إضافة مكون جديد إلى `knowledge_registry`

1. أضف مجلدًا جديدًا تحت `knowledge_registry/`:
   - `knowledge_registry/new_component/v1.0/`
2. أضف ملف `metadata.json` في المجلد:
   ```json
   {
     "name": "New Component",
     "version": "v1.0",
     "description": "Component for a specific feature",
     "capabilities": ["hospital", "security", "docs"],
     "tags": ["hospital_management", "workflow"]
   }
   ```
3. أضف الملفات الداعمة:
   - `business_rules.md`
   - `docs/001-initial-design.md`
   - `security/ir.model.access.csv`
4. تأكد أن `ComponentRegistryService` يمكنه إيجاد المجلد عبر `KNOWLEDGE_REGISTRY_PATH` أو المسار الافتراضي.

### استخدام النظام عبر نقطة النهاية

```bash
curl -X POST http://127.0.0.1:8002/analyze-requirements/ \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Create a hospital management module with patient, doctor, and appointment models"}'
```

ثم:
```bash
curl http://127.0.0.1:8002/job/<job_id>
```

### مثال عملي لإنشاء تعلم جديد

عند اكتمال عملية توليد ناجحة، يسجل النظام تلقائيًا إدخالًا جديدًا في:
- `knowledge_registry/learning_log.json`

إدخال الحلقة يتضمن:
- البرومبت الأصلي
- المكونات المستخدمة
- ملفّات الموديول الناتج


### Examples

#### Add a new registry component

1. Create a new folder under `knowledge_registry/`:
   - `knowledge_registry/new_component/v1.0/`
2. Add `metadata.json` in the folder:
   ```json
   {
     "name": "New Component",
     "version": "v1.0",
     "description": "Component for a specific feature",
     "capabilities": ["hospital", "security", "docs"],
     "tags": ["hospital_management", "workflow"]
   }
   ```
3. Add supporting files:
   - `business_rules.md`
   - `docs/001-initial-design.md`
   - `security/ir.model.access.csv`
4. Ensure `ComponentRegistryService` can discover the folder using `KNOWLEDGE_REGISTRY_PATH` or the default path.

#### Use the system via endpoint

```bash
curl -X POST http://127.0.0.1:8002/analyze-requirements/ \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Create a hospital management module with patient, doctor, and appointment models"}'
```

Then:
```bash
curl http://127.0.0.1:8002/job/<job_id>
```

#### Practical learning example

When a generation succeeds, the system automatically writes a new entry to:
- `knowledge_registry/learning_log.json`

The log entry includes:
- the original prompt
- the matched components used
- the generated module files

## 5. الخطوات المستقبلية

1. **واجهة قراءة سجل التعلم**
   - إضافة endpoint لعرض `learning_log.json` بطريقة منظمة.
2. **تحليل بيانات التعلم**
   - استخراج مقاييس مثل: تكرار المكونات، جودة التوليد، وتعليقات المستخدم.
3. **تحسين البرومبتات تلقائيًا**
   - إنشاء وحدة تتعلم من السجل وتولد برومبتات محسنة بناءً على النتائج السابقة.
4. **دمج تقييمات المستخدم**
   - إضافة حقل `feedback` أو `rating` داخل سجل التعلم.
5. **توسيع سجل المكونات**
   - دعم مكونات أكثر تعقيدًا مع وظائف إعادة استخدام أعمق للوثائق والأمان.

---

ملف الوثيقة هذا يصف المنصة الحالية ويضع أساسًا لفهم بنية النظام وكيفية استخدامه وتطويره مستقبلاً.


### Future Steps

1. **Learning log viewer endpoint**
   - Add an API endpoint to present `learning_log.json` in a structured format.
2. **Learning data analysis**
   - Extract metrics like component usage frequency, generation quality, and user feedback.
3. **Automatic prompt improvement**
   - Build a module that learns from the log and generates better prompts over time.
4. **User feedback integration**
   - Add a `feedback` or `rating` field to learning entries.
5. **Component registry expansion**
   - Support richer components with deeper reuse of docs and security patterns.

---

This document describes the current platform and provides a foundation for understanding the architecture, usage, and future development.
