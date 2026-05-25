"""RAG Skill — register vector search tools and inject knowledge context."""

import logging
from tools import vector_tools
from tools.vector_db import VectorDB

logger = logging.getLogger(__name__)

_db = None


def _get_db():
    global _db
    if _db is None:
        _db = VectorDB()
    return _db


def get_relevant_context(query: str, n_results: int = 3) -> str:
    """Search knowledge base and return formatted context string."""
    try:
        db = _get_db()
        results = db.search(query, n_results=n_results)
        if not results:
            return ""
        parts = []
        for r in results:
            src = f" [{r['source']}]" if r.get("source") else ""
            parts.append(f"{r['content']}{src}")
        return "\n\n---\n\n".join(parts)
    except Exception as e:
        logger.warning("RAG context lookup failed: %s", e)
        return ""


def get_knowledge_summary() -> str:
    """Return a summary of what's in the knowledge base."""
    try:
        db = _get_db()
        docs = db.list_documents()
        if not docs:
            return "Knowledge base is empty."
        count = len(docs)
        sources = set(d["source"] for d in docs if d.get("source"))
        source_str = ", ".join(sources) if sources else "various sources"
        return f"Knowledge base contains {count} document(s) from: {source_str}"
    except Exception as e:
        return f"Knowledge base unavailable: {e}"


def register_tools():
    vector_tools.register_tools()


def unregister_tools():
    vector_tools.unregister_tools()
