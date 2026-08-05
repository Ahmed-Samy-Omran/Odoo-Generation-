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
