import os
import re
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class RAGService:
    """Local RAG service for indexing Odoo addons and retrieving relevant chunks.

    This service is optional — if sentence-transformers or chromadb cannot be
    imported (e.g. due to a PyTorch version conflict), RAG will be silently
    disabled and the AI service will proceed without local reference context.
    """

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: str = "odoo_reference",
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        odoo_addons_path: Optional[str] = None,
    ) -> None:
        self.repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.persist_directory = self._resolve_path(
            persist_directory or os.getenv("RAG_PERSIST_DIRECTORY", os.path.join(self.repo_root, "chroma_db"))
        )
        self.collection_name = collection_name or os.getenv("RAG_COLLECTION_NAME", "odoo_reference")
        self.model_name = model_name or os.getenv("RAG_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")
        self.odoo_addons_path = self._resolve_path(
            odoo_addons_path or os.getenv("RAG_ODDO_ADDONS_PATH", os.path.join(self.repo_root, "odoo", "addons"))
        )

        self._client = None
        self._collection = None
        self._embedder = None
        self._rag_available: Optional[bool] = None  # None = not yet checked

    def _resolve_path(self, path: Optional[str]) -> str:
        if not path:
            return os.path.join(self.repo_root, "chroma_db")
        if os.path.isabs(path):
            return path
        return os.path.join(self.repo_root, path)

    def _is_available(self) -> bool:
        """Check once whether RAG dependencies can be loaded."""
        if self._rag_available is not None:
            return self._rag_available
        try:
            self._get_dependencies()
            self._rag_available = True
        except RuntimeError as exc:
            logger.warning("RAG service disabled: %s", exc)
            self._rag_available = False
        return self._rag_available

    def _get_dependencies(self):
        try:
            import chromadb  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("chromadb is required. Install it with: pip install chromadb") from exc

        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
        except (ImportError, Exception) as exc:  # pragma: no cover
            raise RuntimeError(
                f"sentence-transformers could not be loaded ({exc}). "
                "RAG search will be disabled."
            ) from exc

        return chromadb, SentenceTransformer

    def _ensure_ready(self):
        if self._collection is not None:
            return self._collection

        chromadb, SentenceTransformer = self._get_dependencies()
        os.makedirs(self.persist_directory, exist_ok=True)
        self._client = chromadb.PersistentClient(path=self.persist_directory)
        self._collection = self._client.get_or_create_collection(name=self.collection_name)
        self._embedder = SentenceTransformer(self.model_name)
        return self._collection

    def _chunk_text(self, text: str, chunk_size: int = 180, overlap: int = 40) -> List[str]:
        cleaned = re.sub(r"\r\n?", "\n", text).strip()
        if not cleaned:
            return []

        words = re.split(r"\s+", cleaned)
        if len(words) <= chunk_size:
            return [cleaned]

        chunks: List[str] = []
        start = 0
        while start < len(words):
            end = start + chunk_size
            chunk_words = words[start:end]
            if not chunk_words:
                break
            chunks.append(" ".join(chunk_words))
            if end >= len(words):
                break
            start += max(1, chunk_size - overlap)

        return [chunk for chunk in chunks if chunk.strip()]

    def _iter_source_files(self, source_path: Optional[str] = None) -> List[Path]:
        base_path = Path(source_path or self.odoo_addons_path)
        if not base_path.exists():
            return []

        files: List[Path] = []
        for file_path in base_path.rglob("*"):
            if not file_path.is_file():
                continue
            if file_path.suffix.lower() not in {".py", ".xml"}:
                continue
            files.append(file_path)
        return sorted(files)

    def _collect_documents(self, source_path: Optional[str] = None) -> List[Dict[str, Any]]:
        documents: List[Dict[str, Any]] = []
        for file_path in self._iter_source_files(source_path):
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue

            rel_path = file_path.relative_to(Path(source_path or self.odoo_addons_path)).as_posix()
            chunks = self._chunk_text(content)
            for i, chunk in enumerate(chunks):
                documents.append(
                    {
                        "id": f"{rel_path}:{i}",
                        "document": chunk,
                        "metadata": {
                            "source": rel_path,
                            "file_type": file_path.suffix.lower().lstrip("."),
                        },
                    }
                )
        return documents

    def _embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        if self._embedder is None:
            self._ensure_ready()
        embeddings = self._embedder.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        return embeddings.tolist()

    def index_directory(self, source_path: Optional[str] = None, reset: bool = False) -> Dict[str, Any]:
        if not self._is_available():
            return {
                "success": False,
                "error": "RAG dependencies unavailable (sentence-transformers/chromadb could not be loaded).",
                "indexed_files": 0,
                "indexed_chunks": 0,
            }
        self._ensure_ready()
        if reset:
            try:
                self._client.delete_collection(self.collection_name)
            except Exception:
                pass
            self._collection = self._client.get_or_create_collection(name=self.collection_name)

        documents = self._collect_documents(source_path)
        if not documents:
            return {
                "success": True,
                "indexed_files": 0,
                "indexed_chunks": 0,
                "collection": self.collection_name,
                "persist_directory": self.persist_directory,
            }

        ids = [item["id"] for item in documents]
        content = [item["document"] for item in documents]
        metadatas = [item["metadata"] for item in documents]
        embeddings = self._embed_texts(content)

        self._collection.add(
            ids=ids,
            documents=content,
            metadatas=metadatas,
            embeddings=embeddings,
        )

        return {
            "success": True,
            "indexed_files": len({item["metadata"]["source"].split("/")[0] for item in documents}),
            "indexed_chunks": len(documents),
            "collection": self.collection_name,
            "persist_directory": self.persist_directory,
        }

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        if not query or not query.strip():
            return []

        if not self._is_available():
            return []

        self._ensure_ready()
        query_embedding = self._embed_texts([query])[0]
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        return [
            {
                "content": doc,
                "metadata": meta,
                "distance": dist,
            }
            for doc, meta, dist in zip(documents, metadatas, distances)
        ]

    def _format_search_results(self, results: List[Dict[str, Any]]) -> str:
        if not results:
            return "No local reference context available."

        sections = []
        for idx, result in enumerate(results, start=1):
            source = result.get("metadata", {}).get("source", "unknown")
            # Avoid feeding previously generated modules back into the AI prompt
            if "generated_modules" in source or source.startswith("generated_modules/"):
                continue
            content = (result.get("content") or "").strip()
            # Return a short, single-line snippet to reduce noise and prevent accidental code copying
            snippet = content.replace("\n", " ")[:400]
            sections.append(f"[{idx}] Source: {source} — {snippet}")

        if not sections:
            return "No local reference context available."

        return "Reference Context:\n" + "\n\n".join(sections)
