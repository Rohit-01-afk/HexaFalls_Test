# Blueprint Eye (v0.3.5)

Enterprise-grade technical manual retrieval system.

## Overview

Blueprint Eye is a high-precision document retrieval and RAG engine designed to rapidly query and locate relevant technical manual passages, page numbers, and grounded answers with complete explainability, performance metrics, deterministic retrieval confidence ratings, and advanced prompt engineering.

## Key Features (v0.3.5)

- **Vector Search & Semantic Retrieval:** ChromaDB vector storage with `sentence-transformers/all-MiniLM-L6-v2` embeddings.
- **Retrieval Decision Filter (`RetrievalFilter`):** Chunk deduplication, similarity score thresholding, score sorting, Top-K capping, and context character capping (`RAG_MAX_CONTEXT_CHARS`).
- **Prompt Engineering & Context Preparation (`PromptBuilder`):** Pure context formatting, whitespace normalization, header delimiters, deduplication, and strict grounding instructions preventing hallucinations.
- **Configurable Soft-Threshold Fallback:** Relaxed similarity margin retrieval fallback marking response confidence `"Low"` while enforcing full pipeline controls.
- **Latency Performance Observability:** Microsecond timing breakdown across `search_ms`, `filter_ms`, `prompt_ms`, `generation_ms`, and `total_ms`.

## Architecture

```text
POST /api/v1/ask
       │
       ▼
   AskRequest
       │
       ▼
   RAGService ────────► SearchService (ChromaDB & SentenceTransformers)
   (Response  │
    Assembly) ├─────────────► RetrievalFilter (Deduplication, Thresholding, Top-K, Max Chars, Confidence)
              │
              ├─────────────► PromptBuilder (Context Preparation, Whitespace Normalization & Grounded System Prompt)
              │
              └─────────────► OllamaService (Local Gemma LLM Generation)
              │
              ▼
   AskResponse (Grounded Answer, Rich Sources, Confidence, Diagnostics, Latency Metrics)
```


## Quickstart

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Copy environment configuration:
   ```bash
   cp .env.example .env
   ```

3. Run the development server:
   ```bash
   uvicorn backend.main:app --reload
   ```

4. API Endpoints & Documentation:
   - RAG Question Answering: POST `http://localhost:8000/api/v1/ask`
   - Semantic Vector Search: POST `http://localhost:8000/api/v1/search`
   - PDF Manual Upload: POST `http://localhost:8000/api/v1/upload`
   - Health Check: GET `http://localhost:8000/api/v1/health`
   - Interactive OpenAPI docs: `http://localhost:8000/docs`

5. Run Automated Tests:
   ```bash
   pytest
   ```
