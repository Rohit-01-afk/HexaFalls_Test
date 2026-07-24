# Blueprint Eye System Architecture Document

Version: v0.3.5 (Sprint 6.5 — Answer Generation Layer Stabilization)

---

# 1. Purpose

Blueprint Eye is an enterprise-grade technical manual retrieval platform.

The primary objective is **accurate document retrieval** and **grounded technical answer generation** with strict explainability, performance observability, and deterministic retrieval confidence.

---

# 2. High-Level System Architecture

```text
                                USER
                                 │
                                 ▼
                         REST API (FastAPI)
                                 │
                 ┌───────────────┴────────────────┐
                 │                                │
                 ▼                                ▼
       Ingestion & Processing              RAG Retrieval Pipeline
       (PDF Processor, Chunker,            (SearchService, RetrievalFilter,
        Embedding Generator)               PromptBuilder, OllamaService)
                 │                                │
                 ▼                                ▼
       ChromaDB Vector Store               AskResponse Payload
```

---

# 3. RAG Retrieval Pipeline Architecture (Sprint 6.5)

```text
POST /api/v1/ask
        │
        ▼
   AskRequest
        │
        ▼
   RAGService ────────► SearchService (ChromaDB Vector Retrieval)
   (Response  │
    Assembly) ├─────────────► RetrievalFilter (Deduplication, Score Thresholding, Score Sorting,
              │                                 Top-K Limiting, Context Chars Capping, Confidence)
              │
              ├─────────────► PromptBuilder (Context Preparation, Whitespace Normalization & Grounded System Prompt)
              │
              └─────────────► OllamaService (Local Gemma LLM Generation)
              │
              ▼
   AskResponse (Grounded Answer, Rich Source References, Confidence, Diagnostics, Performance Metrics)
```

---

# 4. Core Service Responsibilities

| Service | Primary Responsibility | Architectural Rule |
| :--- | :--- | :--- |
| `SearchService` | Query embedding & ChromaDB vector similarity search | Single source of truth for semantic vector retrieval |
| `RetrievalFilter` | Chunk deduplication, score thresholding, score sorting, Top-K capping, context character capping, and confidence evaluation | Contains ONLY retrieval decision logic. Independent of Ollama & API layer |
| `PromptBuilder` | Pure context formatting, whitespace normalization, header formatting, and grounded system prompt construction | Receives pre-filtered context. MUST NEVER make retrieval, ranking, or threshold decisions |
| `OllamaService` | HTTP communication with local Ollama LLM server | Model generation only. No retrieval logic leakage |
| `RAGService` | Pipeline orchestration, soft-threshold fallback logic, response assembly, and latency metrics collection | Orchestrator layer. Keeps response assembly inside RAGService without external formatters |

---

# 5. Retrieval & Soft-Threshold Decision Pipeline (`RetrievalFilter`)

```text
Raw Search Candidates
         │
         ▼
  Deduplication (Retain highest score per chunk_id)
         │
         ▼
  Score Thresholding (Filter out score < RAG_SIMILARITY_THRESHOLD or soft cutoff)
         │
         ▼
  Score Sorting (Sort descending by similarity score)
         │
         ▼
  Top-K Limiting (Cap to top RAG_TOP_K chunks)
         │
         ▼
  Max Context Chars Capping (Preserve chunk boundaries under RAG_MAX_CONTEXT_CHARS)
         │
         ▼
  Deterministic Confidence Evaluation ("High", "Medium", "Low", "None")
```

---

# 6. Performance Observability & Metrics

Every RAG request measures latency breakdown in milliseconds (`RetrievalMetrics`):
- `search_ms`: Vector search execution time
- `filter_ms`: Filtering, sorting, and confidence calculation time
- `prompt_ms`: Prompt construction & context formatting time
- `generation_ms`: Local LLM text generation time
- `total_ms`: End-to-end request processing time

---

# 7. Non-Goals & Future Compatibility

Sprint 6.5 preserves clear separation of concerns and focuses strictly on stabilizing the generation layer.

Future Sprints will build upon this foundation without changing the core retrieval pipeline:
- Future Agent Workflows will consume `RetrievalFilter` output via clean APIs.
- Future Vision Integration will attach page diagram images to `SourceReference` items.

