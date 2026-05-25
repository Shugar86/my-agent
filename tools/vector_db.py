import os
import uuid
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class VectorDB:
    """ChromaDB-based vector store for RAG knowledge base.

    Embedded mode — zero config, persists to data/chroma/.
    Uses all-MiniLM-L6-v2 (384-dim) via Chroma's default embedding function.
    """

    def __init__(self, persist_dir: str = "data/chroma"):
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self._client = None
        self._collection = None
        self._init_db()

    def _init_db(self):
        try:
            import chromadb
            self._client = chromadb.PersistentClient(
                path=str(self.persist_dir),
                settings=chromadb.Settings(
                    anonymized_telemetry=False,
                    allow_reset=False,
                ),
            )
            self._collection = self._client.get_or_create_collection(
                name="knowledge_base",
                metadata={"hnsw:space": "cosine"},
            )
            logger.info("ChromaDB ready at %s (count=%d)", self.persist_dir, self._collection.count())
        except Exception as e:
            logger.error("Failed to init ChromaDB: %s", e)
            raise

    def add_text(self, content: str, source: str = "", metadata: dict = None) -> str:
        doc_id = str(uuid.uuid4())
        meta = {"source": source, ** (metadata or {})}
        self._collection.add(
            documents=[content],
            metadatas=[meta],
            ids=[doc_id],
        )
        logger.debug("Added doc %s (source=%s, len=%d)", doc_id, source, len(content))
        return doc_id

    def search(self, query: str, n_results: int = 5) -> list:
        if self._collection.count() == 0:
            return []
        results = self._collection.query(
            query_texts=[query],
            n_results=min(n_results, self._collection.count()),
        )
        output = []
        if not results["ids"] or not results["ids"][0]:
            return []
        for i, doc_id in enumerate(results["ids"][0]):
            meta = (results["metadatas"][0][i] or {}) if results["metadatas"] else {}
            output.append({
                "id": doc_id,
                "content": results["documents"][0][i] if results["documents"] else "",
                "source": meta.get("source", ""),
                "score": float(results["distances"][0][i]) if results["distances"] else 0.0,
            })
        return output

    def list_documents(self) -> list:
        if self._collection.count() == 0:
            return []
        data = self._collection.get()
        docs = []
        for i in range(len(data["ids"])):
            meta = (data["metadatas"][i] or {}) if data["metadatas"] else {}
            doc_content = data["documents"][i] if data["documents"] else ""
            docs.append({
                "id": data["ids"][i],
                "source": meta.get("source", ""),
                "content_preview": doc_content[:200] + "..." if len(doc_content) > 200 else doc_content,
                "content_length": len(doc_content),
            })
        return docs

    def delete(self, doc_id: str):
        self._collection.delete(ids=[doc_id])

    def count(self) -> int:
        return self._collection.count()

    def close(self):
        if self._client:
            self._client = None
            self._collection = None

    def reset(self):
        if self._client:
            self._client.delete_collection("knowledge_base")
            self._collection = self._client.get_or_create_collection(name="knowledge_base")
