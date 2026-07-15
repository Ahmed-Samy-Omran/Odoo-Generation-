import json
import logging
import sys

from app.services.ai_service import AIService

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("app.services.ai_service").setLevel(logging.WARNING)

TEST_PROMPT = (
    "Create a simple odoo module for 'Library' with one model 'Book' "
    "and fields: name (char), isbn (char)."
)


def print_provider_result(index: int, result) -> None:
    print("=" * 60)
    print(f"[{index}] {result.name}")
    print(f"    Model : {result.model}")
    print(f"    URL   : {result.url}")
    print(f"    Key   : {result.key_status}")

    if result.success:
        print("    Status: SUCCESS")
        print(f"    Module: {result.module_name}")
        return

    print("    Status: FAILED")
    if result.error_type:
        print(f"    Type  : {result.error_type}")
    if result.http_status:
        print(f"    HTTP  : {result.http_status}")
    if result.error_message:
        print("    Error :")
        message = str(result.error_message)
        try:
            if isinstance(result.error_message, dict):
                print(json.dumps(result.error_message, indent=6, ensure_ascii=False))
            else:
                parsed = json.loads(message)
                print(json.dumps(parsed, indent=6, ensure_ascii=False))
        except (json.JSONDecodeError, TypeError):
            for line in message.splitlines():
                print(f"           {line}")
    if result.response_preview:
        print(f"    Preview: {result.response_preview[:200]}...")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("Testing all AI providers independently...\n")
    service = AIService()
    results = service.test_all_providers(TEST_PROMPT)

    for index, result in enumerate(results, start=1):
        print_provider_result(index, result)
        print()

    success_count = sum(1 for r in results if r.success)
    print("=" * 60)
    print(f"Summary: {success_count}/{len(results)} providers succeeded")
    return 0 if success_count else 1


if __name__ == "__main__":
    raise SystemExit(main())
