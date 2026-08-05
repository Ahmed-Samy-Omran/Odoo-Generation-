import json
import os
from pathlib import Path
from typing import List, Optional

from pydantic import ValidationError

from app.models.schemas import ComponentMetadata, ComponentRegistryEntry


class ComponentRegistryService:
    def __init__(self, registry_dir: Optional[str] = None):
        self.repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.registry_dir = self._resolve_path(
            registry_dir or os.getenv("KNOWLEDGE_REGISTRY_PATH", os.path.join(self.repo_root, "knowledge_registry"))
        )

    def _resolve_path(self, path: Optional[str]) -> str:
        if not path:
            return os.path.join(self.repo_root, "knowledge_registry")
        if os.path.isabs(path):
            return path
        return os.path.join(self.repo_root, path)

    def list_components(self) -> List[ComponentRegistryEntry]:
        if not os.path.isdir(self.registry_dir):
            return []

        components: List[ComponentRegistryEntry] = []
        for component_dir in sorted(Path(self.registry_dir).iterdir()):
            if not component_dir.is_dir():
                continue

            direct_metadata_path = component_dir / "metadata.json"
            if direct_metadata_path.exists():
                self._append_component_entry(components, component_dir.name, direct_metadata_path)
                continue

            for version_dir in sorted(component_dir.iterdir()):
                if not version_dir.is_dir():
                    continue

                metadata_path = version_dir / "metadata.json"
                if not metadata_path.exists():
                    continue

                component_id = f"{component_dir.name}/{version_dir.name}"
                self._append_component_entry(components, component_id, metadata_path)

        return components

    def _append_component_entry(
        self,
        components: List[ComponentRegistryEntry],
        component_id: str,
        metadata_path: Path,
    ) -> None:
        try:
            raw = metadata_path.read_text(encoding="utf-8")
            payload = json.loads(raw)
            metadata = ComponentMetadata(**payload)
            components.append(
                ComponentRegistryEntry(component_id=component_id, metadata=metadata)
            )
        except (json.JSONDecodeError, ValidationError) as exc:
            raise ValueError(f"Invalid metadata for component '{component_id}': {exc}") from exc

    def get_component_dir(self, component_id: str) -> Optional[Path]:
        """Return the Path to a component directory given its component_id (e.g. 'name' or 'name/version').

        If the directory does not exist, returns None.
        """
        if not component_id:
            return None

        parts = component_id.split("/")
        # knowledge_registry/<name> or knowledge_registry/<name>/<version>
        base = Path(self.registry_dir)
        if len(parts) == 1:
            candidate = base / parts[0]
            if candidate.exists() and candidate.is_dir():
                return candidate
        else:
            candidate = base / parts[0] / parts[1]
            if candidate.exists() and candidate.is_dir():
                return candidate

        # fallback: try top-level name folder
        candidate = base / parts[0]
        if candidate.exists() and candidate.is_dir():
            return candidate

        return None
