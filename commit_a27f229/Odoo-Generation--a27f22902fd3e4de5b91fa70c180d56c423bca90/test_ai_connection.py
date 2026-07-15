import json
import logging
import sys

from app.services.ai_service import AIService

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)

TEST_PROMPT = (
    "Create a simple odoo module for 'Library' with one model 'Book' "
    "and fields: name (char), isbn (char)."
)


def test_ai_connection():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    service = AIService()
    print("--- Testing all providers (detailed) ---\n")

    results = service.test_all_providers(TEST_PROMPT)
    for index, result in enumerate(results, start=1):
        print(f"[{index}] {result.name} | model={result.model}")
        if result.success:
            print(f"    OK -> module: {result.module_name}")
        else:
            print(f"    FAIL -> {result.error_type}: {result.error_message}")
        print()

    print("--- Fallback chain test (first working provider wins) ---")
    try:
        result = service.analyze_requirements(TEST_PROMPT)
        print(f"OK -> module: {result.modules[0].module_name}")
    except Exception as e:
        print(f"FAIL -> {e}")


if __name__ == "__main__":
    test_ai_connection()