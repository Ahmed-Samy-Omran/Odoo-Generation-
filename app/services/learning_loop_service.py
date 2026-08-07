"""Learning loop service.

This module provides a small utility to append learning entries to
`knowledge_registry/learning_log.json` after successful module
generation. Entries include the original prompt, matched components,
and the generated files for each module.

Standards:
- Uses type hints on public functions.
- Includes Google-style docstrings.
- Minimal external dependencies.
"""

import json
import os
import datetime
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.services.component_registry_service import ComponentRegistryService

logger = logging.getLogger(__name__)

TEXT_EXTENSIONS = {".py", ".xml", ".csv", ".js", ".css", ".html", ".md", ".txt", ".json"}


def _get_registry_dir(registry_dir: Optional[str] = None) -> str:
    return ComponentRegistryService(registry_dir=registry_dir).registry_dir


def _get_learning_log_path(registry_dir: Optional[str] = None) -> Path:
    registry_path = Path(_get_registry_dir(registry_dir))
    registry_path.mkdir(parents=True, exist_ok=True)
    return registry_path / "learning_log.json"


def _load_learning_log(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
        if isinstance(data, list):
            return data
    except Exception:
        pass
    return []


def _write_learning_log(path: Path, entries: List[Dict[str, Any]]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)


def _collect_files_from_paths(module_paths: List[str]) -> List[Dict[str, str]]:
    files = []
    for module_path in module_paths:
        module_name = os.path.basename(module_path)
        for root, _, filenames in os.walk(module_path):
            for filename in filenames:
                ext = os.path.splitext(filename)[1].lower()
                if ext not in TEXT_EXTENSIONS:
                    continue
                full_path = os.path.join(root, filename)
                rel_path = os.path.relpath(full_path, module_path).replace("\\", "/")
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.read()
                except OSError:
                    continue
                files.append({
                    "name": filename,
                    "path": f"{module_name}/{rel_path}",
                    "content": content,
                })
    return sorted(files, key=lambda x: x["path"])


def append_learning_entry(
    job_id: str,
    prompt: Optional[str],
    modules: List[Dict[str, Any]],
    module_paths: List[str],
    matched_components: Optional[List[str]] = None,
    notes: Optional[List[str]] = None,
    registry_dir: Optional[str] = None,
) -> None:
    """Append a learning entry to the global learning log.

    Args:
        job_id: Unique identifier for the generation job.
        prompt: The original user prompt used to generate the module(s).
        modules: The module configuration(s) that were generated.
        module_paths: File system paths to the generated module directories.
        matched_components: Optional list of matched component IDs used during generation.
        notes: Optional list of textual notes about the generation (e.g., "pushed to github").
        registry_dir: Optional override for the knowledge registry directory.
    """
    path = _get_learning_log_path(registry_dir)
    entries = _load_learning_log(path)

    try:
        collected_files = _collect_files_from_paths(module_paths)
    except Exception as exc:
        logger.exception("Failed collecting files for learning entry: %s", exc)
        collected_files = []

    modules_data: List[Dict[str, Any]] = []
    for index, module in enumerate(modules):
        module_path = module_paths[index] if index < len(module_paths) else None
        module_name = (
            os.path.basename(module_path)
            if module_path
            else (module.get("module_name") if isinstance(module, dict) else None)
        )
        module_files = [file for file in collected_files if file["path"].startswith(f"{module_name}/")] if module_name else []
        modules_data.append(
            {
                "module_name": module_name,
                "module_config": module if isinstance(module, dict) else {},
                "generated_files": module_files,
            }
        )

    entry: Dict[str, Any] = {
        "timestamp": datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat(),
        "job_id": job_id,
        "prompt": prompt,
        "matched_components": matched_components or [],
        "modules": modules_data,
        "notes": notes or [],
    }

    entries.append(entry)
    try:
        _write_learning_log(path, entries)
    except Exception as exc:
        logger.exception("Failed to write learning log to %s: %s", path, exc)
