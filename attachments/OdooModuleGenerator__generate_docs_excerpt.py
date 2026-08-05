    def _generate_docs(self, config: Dict[str, Any], module_path: str) -> None:
        """Copy ADRs and business rules from matched components into module docs/ folder."""
        matched = config.get("matched_components") or []
        if not matched:
            return

        docs_dir = os.path.join(module_path, "docs")
        Path(docs_dir).mkdir(parents=True, exist_ok=True)

        registry = ComponentRegistryService()
        for comp_id in matched:
            comp_dir = registry.get_component_dir(comp_id)
            if not comp_dir:
                continue

            # Copy business_rules.md if present
            br = Path(comp_dir) / "business_rules.md"
            if br.exists() and br.is_file():
                shutil.copy(str(br), os.path.join(docs_dir, br.name))

            # Copy adrs/ folder markdown files
            adrs_dir = Path(comp_dir) / "adrs"
            if adrs_dir.exists() and adrs_dir.is_dir():
                for f in sorted(adrs_dir.iterdir()):
                    if f.is_file() and f.suffix.lower() == ".md":
                        shutil.copy(str(f), os.path.join(docs_dir, f.name))

            # Also copy any ADR-like md files at component root (e.g., 001-*.md or *adr*.md)
            for f in sorted(Path(comp_dir).iterdir()):
                if f.is_file() and f.suffix.lower() == ".md":
                    name = f.name.lower()
                    if name.startswith("00") or "adr" in name:
                        shutil.copy(str(f), os.path.join(docs_dir, f.name))
