# Semantic Search & Retrieval Layer Specification

Version: v0.3.5 (Sprint 6.5 — Answer Generation Layer Stabilization)

---

# 1. Retrieval Architecture Preserved

Sprint 6.5 does **NOT** modify the underlying vector retrieval layer.

The vector search pipeline remains unchanged:
- Query embedding generation via `SentenceTransformers` (`all-MiniLM-L6-v2`).
- ChromaDB vector collection querying (`manual_chunks`).
- Optional metadata filtering (`where={"document_id": document_id}`) when `document_id` is supplied in `SearchRequest` or `AskRequest`. When omitted, search is performed across the entire collection.
- Cosine similarity score calculation.


---

# 2. Retrieval Decision Filtering (`RetrievalFilter`)

Candidate search results returned by `SearchService` pass through `RetrievalFilter`:
1. **Deduplication:** Retains highest scoring chunk per `chunk_id`.
2. **Score Thresholding:** Filters out chunks below `RAG_SIMILARITY_THRESHOLD` (or `soft_threshold` when soft-threshold fallback is active).
3. **Score Sorting:** Sorts candidates descending by similarity score.
4. **Top-K Limiting:** Caps candidate list to top `RAG_TOP_K` items.
5. **Context Window Capping:** Enforces cumulative text character cap `RAG_MAX_CONTEXT_CHARS` while preserving chunk boundaries.
6. **Deterministic Confidence Evaluation:** Rates retrieval confidence (`High`, `Medium`, `Low`, `None`).

---

# 3. How `PromptBuilder` Consumes Filtered Chunks

`PromptBuilder` acts purely as a consumer of pre-filtered chunk arrays returned by `RetrievalFilter`:

```text
SearchService (ChromaDB Search)
         │
         ▼
RetrievalFilter (Filter, Deduplicate, Sort, Top-K, Max Chars, Confidence)
         │
         ▼
Filtered Chunks (List[SearchResult])
         │
         ▼
PromptBuilder (Whitespace Normalization, Header Delimiters, Deduplication, System Prompt Assembly)
```

- `PromptBuilder` receives `filtered_chunks` directly from `RetrievalFilter`.
- `PromptBuilder` performs no retrieval queries or filtering logic.
- The formatted context string built by `PromptBuilder` is passed to `OllamaService` for generation.
