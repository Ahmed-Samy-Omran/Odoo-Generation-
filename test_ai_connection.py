# test_ai.py
from app.services.ai_service import AIService


def test_ai_connection():
    try:
        # إحنا بنعمل Instance للـ Service اللي كتبناها
        service = AIService()

        # بنبعت طلب صغير وبسيط عشان نجرب
        prompt = "Create a simple odoo module for 'Library' with one model 'Book' and fields: name (char), isbn (char)."

        print("--- جاري اختبار الاتصال بالـ AI ---")
        result = service.analyze_requirements(prompt)

        print("\n--- نجح الاتصال! ---")
        print(f"تم إنشاء الموديول بنجاح: {result.modules[0].module_name}")

    except Exception as e:
        print(f"\n--- فشل الاختبار ---")
        print(f"الخطأ: {e}")


if __name__ == "__main__":
    test_ai_connection()