# Changelog

## v0.1.0 - Semantic Retrieval Backend

### Added
- PDF upload API
- PDF processing pipeline
- Chunk generation
- SentenceTransformer embeddings
- ChromaDB vector storage
- Semantic search API
- Search schemas
- Search service
- 32 unit tests

### Improved
- UUID validation
- Specific exception handling
- Configuration-driven search limits

## v0.2.0 - Retrieval-Augmented Generation (RAG) Engine

### Added
- RAG question answering API (`POST /api/v1/ask`)
- Grounded prompt builder (`PromptBuilder`) with immutable `Prompt` model
- Ollama service integration (`OllamaService`) for `gemma4:e4b` model communication & latency tracking
- Pure RAG orchestrator (`RAGService`) linking retrieval, prompt construction, and generation
- Grounded system prompt enforcing strict context adherence and fallback text
- Domain exception handling (`OllamaTimeoutError`, `OllamaConnectionError`, `OllamaResponseError`)
- RAG schemas (`AskRequest`, `SourceReference`, `AskResponse`)
- 11 new RAG unit tests (43 total unit tests across full suite)

### Status
- Stable