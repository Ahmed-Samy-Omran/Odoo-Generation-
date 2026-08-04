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

            metadata_path = component_dir / "metadata.json"
            if not metadata_path.exists():
                continue

            try:
                raw = metadata_path.read_text(encoding="utf-8")
                payload = json.loads(raw)
                metadata = ComponentMetadata(**payload)
                components.append(
                    ComponentRegistryEntry(component_id=component_dir.name, metadata=metadata)
                )
            except (json.JSONDecodeError, ValidationError) as exc:
                raise ValueError(f"Invalid metadata for component '{component_dir.name}': {exc}") from exc

        return components
