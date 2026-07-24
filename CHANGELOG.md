# v0.3.5 – Sprint 6.5

## Added

- Redesigned `SYSTEM_PROMPT` in `PromptBuilder` adhering strictly to Prompt Design Principles (deterministic structure, grounding, hallucination prevention, support distinction)
- Context preparation formatting pipeline in `PromptBuilder`: whitespace normalization, redundant header cleanup, chunk text deduplication, and structured delimiter blocks (`==========\nPage X\nSimilarity: Y\nContent:...`)
- Configurable answer generation settings in `Settings`: `RAG_ENABLE_SOFT_THRESHOLD`, `RAG_SOFT_THRESHOLD_MARGIN`, `RAG_INCLUDE_PAGE_HEADERS`, `RAG_MAX_PREVIEW_CHARS`
- Soft-threshold retrieval fallback mechanism in `RAGService` that relaxes similarity threshold margin while strictly enforcing `RetrievalFilter` deduplication, sorting, Top-K, and character caps
- Soft-threshold confidence rating (`"Low"`) with rich source attribution when retrieved under relaxed margin
- Configurable preview truncation (`settings.RAG_MAX_PREVIEW_CHARS`, default 250) in `SourceReference`
- Pure `PromptBuilder` architecture preserving formatting responsibilities without retrieval logic leakage
- Comprehensive unit test suite in `tests/unit/test_prompt_builder.py` and updated `tests/unit/test_rag.py` (61 passing tests)

## Architecture

Question
↓
SearchService
↓
RetrievalFilter
↓
PromptBuilder (Pure Context Preparation & Prompt Formatting)
↓
OllamaService
↓
RAGService (Response Assembly) -> AskResponse

## Validation

- Prompt engineering principles and grounding instructions unit tested
- Whitespace normalization, context deduplication, and header delimiter formatting verified
- Soft threshold retrieval fallback path and confidence rating (`"Low"`) verified
- 100% backward compatibility with Sprint 6 API schemas verified
- Full automated test suite passed (61 unit tests)

---

# v0.3.0 – Sprint 6


## Added

- `RetrievalFilter` service stage for retrieval decision logic between vector search and prompt construction
- Configurable retrieval parameters: `RAG_TOP_K`, `RAG_SIMILARITY_THRESHOLD`, `RAG_MAX_CONTEXT_CHARS`
- Chunk deduplication, cosine similarity score thresholding, score sorting, and whole-chunk context window capping
- Deterministic retrieval confidence rating (`High`, `Medium`, `Low`, `None`) based on top and average similarity scores
- Differentiated 3-case fallback handling (No search results, Below threshold filtering, Empty search collection)
- Rich source reference metadata (`document_id`, `preview`, `page`, `chunk_id`, `score`)
- Strongly typed Pydantic models `RetrievalDiagnostics` and `RetrievalMetrics` in `AskResponse`
- Standardized stage-by-stage latency performance metrics (`search_ms`, `filter_ms`, `prompt_ms`, `generation_ms`, `total_ms`)
- Comprehensive unit test suite in `tests/unit/test_retrieval_filter.py` and updated `tests/unit/test_rag.py`

## Architecture

Question
↓
SearchService
↓
RetrievalFilter
↓
PromptBuilder
↓
OllamaService
↓
AskResponse

## Validation

- Deduplication, thresholding, sorting, top-k, and max context chars capping unit tested
- Deterministic retrieval confidence ratings verified
- Latency breakdown metrics and diagnostics verified
- Differentiated fallback responses verified
- Full test suite passed (52 unit tests)

---

# v0.2.0 – Sprint 5

## Added

- Retrieval-Augmented Generation (RAG) engine
- PromptBuilder service
- OllamaService for local Gemma inference
- RAGService orchestration
- POST /api/v1/ask endpoint
- Grounded answer generation
- Source reference metadata
- Ollama configuration
- Domain-specific exception handling
- Comprehensive RAG unit tests

## Architecture

Question
↓
SearchService
↓
PromptBuilder
↓
OllamaService
↓
Grounded Answer

## Validation

- Semantic retrieval verified
- Grounded answer generation verified
- Source attribution verified
- Empty retrieval fallback verified
- Exception handling verified