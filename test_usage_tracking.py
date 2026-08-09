"""Verify API usage tracking.

Tests:
1. A mock AI request through _call_provider must read response.usage
   (prompt_tokens / completion_tokens) and hand them to log_api_usage.
2. The same for the chat flow via _call_provider_chat.
3. When Supabase is configured, a row inserted by log_api_usage must be
   readable back from the api_usage_logs table.

Run:  python test_usage_tracking.py
"""

import sys
import uuid
from types import SimpleNamespace
from unittest import mock

from app.services.ai_service import AIService
from app.services.supabase_service import supabase_service


def _fake_response(content='{"modules": []}', prompt_tokens=120, completion_tokens=340):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))],
        usage=SimpleNamespace(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
        ),
    )


def _fake_client(response):
    completions = SimpleNamespace(create=mock.MagicMock(return_value=response))
    chat = SimpleNamespace(completions=completions)
    return SimpleNamespace(chat=chat)


def _mock_provider(name="MockProvider", model="mock-model"):
    return {"name": name, "model": model, "key": "sk-mock", "url": "https://mock.example/v1"}


def test_generation_call_logs_usage():
    service = AIService(redis_url="")
    provider = _mock_provider()
    captured = {}

    with mock.patch.object(service, "_get_client", return_value=_fake_client(_fake_response(prompt_tokens=12, completion_tokens=34))):
        with mock.patch("app.services.supabase_service.supabase_service.log_api_usage") as fake_log:
            content = service._call_provider(provider, "Build a library module", job_id="job-usage-gen")
            fake_log.assert_called_once()
            captured = fake_log.call_args.kwargs

    assert content == '{"modules": []}'
    assert captured["provider_name"] == "MockProvider"
    assert captured["model_name"] == "mock-model"
    assert captured["prompt_tokens"] == 12
    assert captured["completion_tokens"] == 34
    assert captured["total_tokens"] == 46
    assert captured["status"] == "success"
    assert captured["job_id"] == "job-usage-gen"
    print("PASS: _call_provider logged response.usage metrics to log_api_usage")


def test_chat_call_logs_usage():
    service = AIService(redis_url="")
    provider = _mock_provider(name="ChatProvider", model="chat-model")
    captured = {}

    with mock.patch.object(service, "_get_client", return_value=_fake_client(_fake_response(prompt_tokens=5, completion_tokens=7))):
        with mock.patch("app.services.supabase_service.supabase_service.log_api_usage") as fake_log:
            content = service._call_provider_chat(provider, [{"role": "user", "content": "hi"}], job_id="job-usage-chat")
            fake_log.assert_called_once()
            captured = fake_log.call_args.kwargs

    assert captured["provider_name"] == "ChatProvider"
    assert captured["prompt_tokens"] == 5
    assert captured["completion_tokens"] == 7
    assert captured["total_tokens"] == 12
    assert captured["status"] == "success"
    assert captured["job_id"] == "job-usage-chat"
    print("PASS: _call_provider_chat logged response.usage metrics to log_api_usage")


def test_logging_failure_does_not_break_generation():
    service = AIService(redis_url="")
    provider = _mock_provider()

    with mock.patch.object(service, "_get_client", return_value=_fake_client(_fake_response())):
        with mock.patch("app.services.supabase_service.supabase_service.log_api_usage", side_effect=Exception("boom")):
            content = service._call_provider(provider, "Build a module", job_id="job-usage-fail")

    assert content == '{"modules": []}'
    print("PASS: generation still succeeds when usage logging raises")


def test_usage_row_appears_in_database():
    if not supabase_service.is_enabled():
        print("SKIP: Supabase not configured; cannot verify api_usage_logs table")
        return

    job_id = str(uuid.uuid4())
    supabase_service.log_api_usage(
        provider_name="test_usage_tracking",
        model_name="mock-model",
        prompt_tokens=10,
        completion_tokens=5,
        total_tokens=15,
        status="success",
        job_id=job_id,
    )

    rows = supabase_service.get_usage_logs(days=7)
    matches = [row for row in rows if row.get("job_id") == job_id]
    assert matches, f"No api_usage_logs row found for job_id={job_id}"
    row = matches[0]
    assert row["provider_name"] == "test_usage_tracking"
    assert row["model_name"] == "mock-model"
    assert int(row["prompt_tokens"]) == 10
    assert int(row["completion_tokens"]) == 5
    assert int(row["total_tokens"]) == 15
    assert row["status"] == "success"
    print(f"PASS: row appears in api_usage_logs for job_id={job_id}")


def run_all():
    tests = [
        test_generation_call_logs_usage,
        test_chat_call_logs_usage,
        test_logging_failure_does_not_break_generation,
        test_usage_row_appears_in_database,
    ]
    failures = 0
    for test in tests:
        try:
            test()
        except AssertionError as exc:
            failures += 1
            print(f"FAIL: {test.__name__}: {exc}")
        except Exception as exc:
            failures += 1
            print(f"ERROR: {test.__name__}: {type(exc).__name__}: {exc}")
    if failures:
        print(f"\n{len(tests) - failures}/{len(tests)} passed, {failures} failed")
        return 1
    print(f"\nAll {len(tests)} tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(run_all())
