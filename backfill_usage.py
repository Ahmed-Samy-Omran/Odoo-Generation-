"""Backfill estimated API usage for historical generation jobs.

Usage tracking was added on 2026-08-09; jobs created before that have no
rows in `api_usage_logs`, so the dashboard shows no historical usage.
This script inserts one estimated row per generation job (the
analyze-requirements call that produced the module config), attributed to
the primary provider (NaraRouter/mistral-large). Backfilled rows are
marked with `error_message = "estimated_backfill:true"` so they can be
filtered out later if needed.

Run:  python backfill_usage.py
"""

import os
import sys

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()

# Primary provider that handled historical jobs (provider order: nara first)
PROVIDER_NAME = "NaraRouter/mistral-large"
MODEL_NAME = "mistral-large"

# Baselines calibrated against real NaraRouter/mistral-large analyze calls
# (observed totals ~828 and ~971 tokens).
PROMPT_BASE = 600
COMPLETION_BASE = 250
TOKENS_PER_MODEL = 120
TOKENS_PER_FIELD = 25
TOKENS_PER_DESC_CHAR = 1 / 4


def estimate_tokens(module_config):
    if not isinstance(module_config, dict):
        return PROMPT_BASE, COMPLETION_BASE

    models = module_config.get("models") or []
    model_count = 0
    field_count = 0
    for model in models:
        if not isinstance(model, dict):
            continue
        model_count += 1
        field_count += len(model.get("fields") or [])

    description = str(module_config.get("module_description") or "")
    prompt = int(PROMPT_BASE + min(len(description) * TOKENS_PER_DESC_CHAR, 800))
    completion = int(
        COMPLETION_BASE
        + model_count * TOKENS_PER_MODEL
        + field_count * TOKENS_PER_FIELD
    )
    return prompt, completion


def main() -> int:
    if not (SUPABASE_URL and SUPABASE_KEY):
        print("ERROR: SUPABASE_URL / SUPABASE_KEY missing from .env")
        return 1

    client = create_client(SUPABASE_URL, SUPABASE_KEY)

    jobs_result = client.table("generation_jobs").select("job_id,module_config,created_at").execute()
    jobs = getattr(jobs_result, "data", []) or []

    logs_result = client.table("api_usage_logs").select("job_id").execute()
    logs = getattr(logs_result, "data", []) or []
    existing_job_ids = {row.get("job_id") for row in logs if row.get("job_id")}

    inserted = 0
    skipped = 0
    for job in jobs:
        job_id = job.get("job_id")
        if not job_id or job_id in existing_job_ids:
            skipped += 1
            continue

        config = job.get("module_config")
        if isinstance(config, list):
            config = config[0] if config else {}
        prompt_tokens, completion_tokens = estimate_tokens(
            config if isinstance(config, dict) else None
        )
        total_tokens = prompt_tokens + completion_tokens

        client.table("api_usage_logs").insert({
            "job_id": job_id,
            "provider_name": PROVIDER_NAME,
            "model_name": MODEL_NAME,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "status": "success",
            "error_message": "estimated_backfill:true",
            "created_at": job.get("created_at"),
        }).execute()

        inserted += 1
        print(
            f"  + {job_id}  created_at={job.get('created_at')}  "
            f"prompt={prompt_tokens} completion={completion_tokens} total={total_tokens}"
        )

    print(f"\nInserted {inserted} row(s); skipped {skipped} (already logged / no job_id).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
