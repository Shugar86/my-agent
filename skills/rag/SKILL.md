# RAG (Retrieval-Augmented Generation)

Store and retrieve knowledge documents using vector search.

## Description
Enables the agent to maintain a persistent knowledge base. Documents are embedded and stored in ChromaDB for semantic search. When answering questions, the agent can search for relevant context to provide more accurate and informed responses.

## Capabilities
- **Add Knowledge**: Store text documents with metadata (source, tags)
- **Search Knowledge**: Find semantically similar content by query
- **List Knowledge**: Browse all stored documents
- **Delete Knowledge**: Remove outdated documents
- **Context Injection**: Automatically injects relevant knowledge when answering user queries

## Usage
```python
# Add knowledge
tools.add_knowledge(content="Text content", source="url_or_filename")

# Search
results = tools.search_knowledge(query="What is X?", n_results=5)

# List all
docs = tools.list_knowledge()
```

## Embedded Model
- ChromaDB default: all-MiniLM-L6-v2 (384-dim, ONNX runtime)
- Storage: `data/chroma/`
