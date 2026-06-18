import json
from app.models.schemas import ModuleConfig
from app.generators.OdooModuleGenerator import OdooModuleGenerator

# 1. بيانات تجريبية لمحاكاة ملف الـ JSON الذي سيرسله المستخدم
sample_json_data = {
    "module_name": "custom_hospital",
    "module_description": "Module for managing hospital patients and doctors",
    "models": [
        {
            "name": "hospital.patient",
            "description": "Patient Records",
            "rec_name": "name",
            "fields": [
                {"name": "name", "type": "char", "required": True},
                {"name": "age", "type": "integer"},
                {"name": "gender", "type": "selection"},
                {"name": "doctor_id", "type": "many2one", "relation": "hospital.doctor"}
            ]
        },
        {
            "name": "hospital.doctor",
            "description": "Doctor Records",
            "rec_name": "name",
            "fields": [
                {"name": "name", "type": "char", "required": True},
                {"name": "specialty", "type": "char"}
            ]
        }
    ]
}


def run_test():
    print("⏳ جاري التحقق من البيانات باستخدام Pydantic Schemas...")
    # التحقق من البيانات عبر الـ Schema
    validated_data = ModuleConfig(**sample_json_data)

    print("⚙️ جاري تشغيل محرك التوليد OdooModuleGenerator...")
    # استدعاء المولد وتمرير البيانات الموثقة كـ Dict
    generator = OdooModuleGenerator(templates_dir="templates")
    output_path = generator.generate_module(validated_data.model_dump(), output_dir="generated_modules")

    print(f"🎉 مبروك! تم توليد موديول أودو بالكامل بنجاح في: {output_path}")


if __name__ == "__main__":
    run_test()
