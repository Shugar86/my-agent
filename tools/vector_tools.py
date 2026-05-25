import os
import logging
from typing import Optional
from core.tool_registry import registry
from tools.vector_db import VectorDB

logger = logging.getLogger(__name__)
_db = None


def _get_db():
    global _db
    if _db is None:
        _db = VectorDB()
    return _db


def add_knowledge(content: str, source: str = "", metadata: Optional[dict] = None) -> dict:
    """Add text to the knowledge base for future retrieval."""
    try:
        db = _get_db()
        doc_id = db.add_text(content, source=source, metadata=metadata or {})
        return {"status": "added", "id": doc_id}
    except Exception as e:
        logger.exception("add_knowledge failed")
        return {"error": str(e)}


def search_knowledge(query: str, n_results: int = 5) -> dict:
    """Search the knowledge base for semantically similar content."""
    try:
        db = _get_db()
        results = db.search(query, n_results=n_results)
        return {
            "results": [
                {
                    "content": r["content"],
                    "source": r.get("source", ""),
                    "score": r.get("score", 0.0),
                    "id": r.get("id", ""),
                }
                for r in results
            ],
            "count": len(results),
        }
    except Exception as e:
        logger.exception("search_knowledge failed")
        return {"error": str(e)}


def list_knowledge(topics: bool = True) -> dict:
    """List all documents in the knowledge base."""
    try:
        db = _get_db()
        docs = db.list_documents()
        return {"documents": docs, "count": len(docs)}
    except Exception as e:
        logger.exception("list_knowledge failed")
        return {"error": str(e)}


def delete_knowledge(doc_id: str) -> dict:
    """Delete a document from the knowledge base by its ID."""
    try:
        db = _get_db()
        db.delete(doc_id)
        return {"status": "deleted", "id": doc_id}
    except Exception as e:
        logger.exception("delete_knowledge failed")
        return {"error": str(e)}


def register_tools():
    registry.register(
        name="add_knowledge",
        description="Add a text document to the knowledge base for future retrieval by semantic search",
        parameters={
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "The text content to store"},
                "source": {"type": "string", "description": "Optional source label (url, filename, etc)"},
                "metadata": {"type": "object", "description": "Optional metadata dict"},
            },
            "required": ["content"],
        },
        execute_fn=add_knowledge,
    )
    registry.register(
        name="search_knowledge",
        description="Search the knowledge base for semantically similar content to the query",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query text"},
                "n_results": {"type": "integer", "description": "Number of results to return (default 5)"},
            },
            "required": ["query"],
        },
        execute_fn=search_knowledge,
    )
    registry.register(
        name="list_knowledge",
        description="List all documents stored in the knowledge base",
        parameters={
            "type": "object",
            "properties": {
                "topics": {"type": "boolean", "description": "If True, group by topic (default True)"},
            },
            "required": [],
        },
        execute_fn=list_knowledge,
    )
    registry.register(
        name="delete_knowledge",
        description="Delete a document from the knowledge base by ID",
        parameters={
            "type": "object",
            "properties": {
                "doc_id": {"type": "string", "description": "Document ID to delete"},
            },
            "required": ["doc_id"],
        },
        execute_fn=delete_knowledge,
    )


def unregister_tools():
    for name in ["add_knowledge", "search_knowledge", "list_knowledge", "delete_knowledge"]:
        registry.unregister(name)
