# Engineering Standards

This document defines mandatory engineering standards for the Odoo-Generation project.

## 1. Code Style
- Use Python 3.11+ type hints for all public functions and methods.
- Write docstrings for every public function, method, class using *Google* style.
- Follow PEP8 for indentation and line lengths (max 100 characters).
- Avoid wildcard imports. Use explicit imports.

## 2. Project Structure
- `app/services/` — long-running services, external integrations, and orchestration logic.
- `app/models/` — Pydantic models and schemas.
- `app/generators/` — code generators and templating logic.
- `app/utils/` — utility helpers, small pure functions.
- `app/tests/` — unit and integration tests (already under `tests/`).
- `knowledge_registry/` — component data and metadata.

## 3. Error Handling
- Use structured logging via Python's `logging` module. Include `job_id` or request identifiers when available.
- Catch and re-raise exceptions with context when appropriate. Do not swallow exceptions silently.
- Return user-facing messages at API boundaries; keep internal stack traces in logs only.

## 4. Testing
- "No new feature without a test" rule. Every change must be covered by unit tests.
- Use `pytest` with clear naming conventions: `test_<module>_<behavior>.py`.
- Keep CI-friendly and deterministic tests; avoid network calls unless mocked.

## 5. Component Standards (for `knowledge_registry`)
Each component should follow the structure:
```
knowledge_registry/<component_name>/<version>/
  metadata.json         # must follow ComponentMetadata schema
  business_rules.md     # optional, human-readable rules
  adrs/                 # optional, architecture decision records
  docs/                 # optional, additional docs
  security/             # optional, security CSVs (ir.model.access.csv)
```
- `metadata.json` must include `name`, `version`, `description`, `capabilities` (list), and optional `tags`.
- All markdown files must be UTF-8 encoded.

## Compliance and Maintenance
- Run `pytest tests/` after changes. Aim for green CI locally.
- Use code reviews to enforce standards.

---

These standards are mandatory; follow them for all future contributions.