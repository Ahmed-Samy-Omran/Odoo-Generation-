import os
import json
from app.models.schemas import ModuleConfig
from app.generators.OdooModuleGenerator import OdooModuleGenerator

# 1. بيانات تجريبية لمحاكاة ملف الـ JSON الذي سيرسله المستخدم
sample_json_data = {
    "module_name": "hospital_management",
    "module_description": "Module for managing hospital patients, doctors, and appointments",
    "models": [
        {
            "name": "hospital.patient",
            "description": "Patient Records",
            "rec_name": "name",
            "fields": [
                {"name": "name", "type": "char", "label": "Patient Name", "required": True},
                {"name": "age", "type": "integer", "label": "Age"},
                {"name": "gender", "type": "selection", "label": "Gender",
                 "selection_options": [["male", "Male"], ["female", "Female"], ["other", "Other"]]},
                {"name": "doctor_id", "type": "many2one", "label": "Primary Doctor", "relation": "hospital.doctor"},
                {"name": "appointment_ids", "type": "one2many", "label": "Appointments",
                 "relation": "hospital.appointment", "inverse_name": "patient_id"}
            ],
            "tree_view_fields": ["name", "age", "gender", "doctor_id"],
            "form_view_fields": ["name", "age", "gender", "doctor_id", "appointment_ids"],
            "search_view": {
                "name": "hospital_patient_search",
                "fields": ["name", "doctor_id"],
                "filters": [
                    {"name": "male_patients", "string": "Male Patients", "domain": "[('gender', '=', 'male')]"}
                ],
                "group_by": [
                    {"name": "gender", "string": "Gender"}
                ]
            }
        },
        {
            "name": "hospital.doctor",
            "description": "Doctor Records",
            "rec_name": "name",
            "fields": [
                {"name": "name", "type": "char", "label": "Doctor Name", "required": True},
                {"name": "specialty", "type": "char", "label": "Specialty"},
                {"name": "patient_ids", "type": "one2many", "label": "Patients", "relation": "hospital.patient",
                 "inverse_name": "doctor_id"}
            ],
            "tree_view_fields": ["name", "specialty"],
            "form_view_fields": ["name", "specialty", "patient_ids"],
            "search_view": {
                "name": "hospital_doctor_search",
                "fields": ["name", "specialty"],
                "filters": [
                    {"name": "doctors_with_patients", "string": "Doctors with Patients",
                     "domain": "[('patient_ids', '!=', False)]"}
                ],
                "group_by": [
                    {"name": "specialty", "string": "Specialty"}
                ]
            }
        },
        {
            "name": "hospital.appointment",
            "description": "Patient Appointments",
            "rec_name": "name",
            "fields": [
                {"name": "name", "type": "char", "label": "Appointment Ref", "required": True},
                {"name": "patient_id", "type": "many2one", "label": "Patient", "relation": "hospital.patient",
                 "required": True},
                {"name": "doctor_id", "type": "many2one", "label": "Doctor", "relation": "hospital.doctor",
                 "required": True},
                {"name": "appointment_date", "type": "datetime", "label": "Appointment Date"}
            ],
            "tree_view_fields": ["name", "patient_id", "doctor_id", "appointment_date"],
            "form_view_fields": ["name", "patient_id", "doctor_id", "appointment_date"],
            "search_view": {
                "name": "hospital_appointment_search",
                "fields": ["name", "patient_id", "doctor_id"],
                "filters": [
                    {"name": "today_appointments", "string": "Today's Appointments",
                     "domain": "[('appointment_date', '>=', context_today().strftime('%Y-%m-%d 00:00:00')), ('appointment_date', '<=', context_today().strftime('%Y-%m-%d 23:59:59'))]"}
                ],
                "group_by": [
                    {"name": "doctor_id", "string": "Doctor"},
                    {"name": "appointment_date", "string": "Appointment Date"}
                ]
            }
        }
    ],
    "actions": [
        {
            "name": "Patients",
            "res_model": "hospital.patient",
            "view_mode": "tree,form",
            "help_text": "Manage your hospital patients"
        },
        {
            "name": "Doctors",
            "res_model": "hospital.doctor",
            "view_mode": "tree,form",
            "help_text": "Manage your hospital doctors"
        },
        {
            "name": "Appointments",
            "res_model": "hospital.appointment",
            "view_mode": "tree,form",
            "help_text": "Manage patient appointments"
        }
    ],
    "menus": [
        {
            "name": "Hospital Management",
            "sequence": 10
        },
        {
            "name": "Patients",
            "parent_xml_id": "hospital_management.menu_hospital_management_menu",
            "action_xml_id": "hospital_management.patients_action",
            "sequence": 10
        },
        {
            "name": "Doctors",
            "parent_xml_id": "hospital_management.menu_hospital_management_menu",
            "action_xml_id": "hospital_management.doctors_action",
            "sequence": 20
        },
        {
            "name": "Appointments",
            "parent_xml_id": "hospital_management.menu_hospital_management_menu",
            "action_xml_id": "hospital_management.appointments_action",
            "sequence": 30
        }
    ]
}


def run_test():
    # الحصول على المسار الحالي للملف لضمان العثور على القوالب
    base_dir = os.path.dirname(os.path.abspath(__file__))
    templates_path = os.path.join(base_dir, "templates")
    output_path_base = os.path.join(base_dir, "generated_modules")

    print(f"📂 مسار القوالب: {templates_path}")
    print("⏳ جاري التحقق من البيانات باستخدام Pydantic Schemas...")

    # التحقق من البيانات عبر الـ Schema
    validated_data = ModuleConfig(**sample_json_data)

    print("⚙️ جاري تشغيل محرك التوليد OdooModuleGenerator...")

    # استدعاء المولد وتمرير البيانات الموثقة كـ Dict
    generator = OdooModuleGenerator(templates_dir=templates_path)
    final_output_path = generator.generate_module(validated_data.model_dump(), output_dir=output_path_base)

    print(f"🎉 مبروك! تم توليد موديول أودو بالكامل بنجاح في: {final_output_path}")


if __name__ == "__main__":
    run_test()
