# Blueprint Eye Data Model Specification

Version: v0.3.5 (Sprint 6.5 — Answer Generation Layer Stabilization)

---

# Core Entities

## Document
Represents an uploaded technical manual.
- `document_id`: UUID
- `filename`: String
- `total_pages`: Integer
- `file_size_bytes`: Integer
- `upload_timestamp`: String (ISO-8601)

## Chunk
Searchable text unit extracted from a manual page.
- `chunk_id`: UUID
- `document_id`: UUID
- `page_number`: Integer (1-indexed)
- `text`: String
- `score`: Float (Cosine similarity score)

---

# RAG & Observability Entities (Sprint 6.5)

## SourceReference
Reference metadata for a supporting source chunk.
- `page`: Integer (1-indexed page number containing the chunk)
- `chunk_id`: String (UUID of the source chunk)
- `score`: Float (Similarity score)
- `document_id`: Optional[String] (UUID of the parent document)
- `preview`: Optional[String] (Text snippet preview capped by `RAG_MAX_PREVIEW_CHARS`, default 250)

## RetrievalDiagnostics
Diagnostic statistics for the retrieval and filtering pipeline.
- `raw_count`: Integer (Number of candidate chunks from vector search)
- `deduplicated_count`: Integer (Count of unique chunks after deduplication)
- `filtered_count`: Integer (Count of chunks meeting score threshold)
- `returned_count`: Integer (Final count of chunks included in prompt context)
- `confidence`: String (`"High"`, `"Medium"`, `"Low"`, `"None"`)
- `filter_reason`: Optional[String] (`"empty_search_results"`, `"filtered_below_threshold"`, `"max_context_chars_reached"`, `null`)
- `similarity_threshold`: Float (Configured minimum score threshold or relaxed soft cutoff)
- `top_k`: Integer (Configured Top-K limit)
- `max_context_chars`: Integer (Configured character limit)

## RetrievalMetrics
Pipeline latency execution breakdown in milliseconds.
- `search_ms`: Float (Vector search duration)
- `filter_ms`: Float (Filtering & confidence calculation duration)
- `prompt_ms`: Float (Prompt construction & context formatting duration)
- `generation_ms`: Float (Ollama LLM generation duration)
- `total_ms`: Float (Total request processing duration)

## Answer Generation Configuration (Sprint 6.5)
Configuration parameters governing prompt construction and soft-threshold fallback.
- `RAG_ENABLE_SOFT_THRESHOLD`: Boolean (Enable/disable soft threshold fallback, default `True`)
- `RAG_SOFT_THRESHOLD_MARGIN`: Float (Similarity threshold relaxation margin, default `0.05`)
- `RAG_INCLUDE_PAGE_HEADERS`: Boolean (Include formatted delimiter headers with page and similarity, default `True`)
- `RAG_MAX_PREVIEW_CHARS`: Integer (Character limit for SourceReference previews, default `250`)

## SearchRequest
Request payload for semantic vector search.
- `query`: String (Search query)
- `top_k`: Optional[Integer] (Maximum results cap)
- `document_id`: Optional[String] (Optional document UUID to filter vector search results by manual)

## AskRequest
Request payload for RAG question answering.
- `question`: String (User question)
- `document_id`: Optional[String] (Optional document UUID to filter RAG query by manual)

## AskResponse
Top-level payload returned by `/api/v1/ask`.

- `question`: String (User question)
- `answer`: String (Grounded answer or fallback message)
- `sources`: List[SourceReference] (Source attribution references)
- `confidence`: Optional[String] (Retrieval confidence rating: `"High"`, `"Medium"`, `"Low"`, `"None"`)
- `diagnostics`: Optional[RetrievalDiagnostics] (Filtering diagnostic statistics)
- `metrics`: Optional[RetrievalMetrics] (Latency performance breakdown)

