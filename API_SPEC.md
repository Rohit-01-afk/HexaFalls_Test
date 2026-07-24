# Blueprint Eye API Specification

Version: v0.3.5 (Sprint 6.5 — Answer Generation Layer Stabilization)

---

# Base URL

```text
http://localhost:8000/api/v1
```

---

# RAG Question Answering

## POST /ask

Executes complete RAG pipeline: vector search, retrieval filtering, soft-threshold evaluation, prompt construction, and Ollama generation.
Maintains 100% backward compatibility with all Sprint 6 API clients.

### Request

```json
{
  "question": "How do I replace the cooling fan assembly?",
  "document_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479"
}
```
*(Note: `document_id` is optional. When omitted, search is performed across all manuals).*


### Success Response (200 OK)

```json
{
  "question": "How do I replace the cooling fan assembly?",
  "answer": "Disconnect cable J7 before removing the cooling fan module from the rear chassis.",
  "sources": [
    {
      "page": 18,
      "chunk_id": "c1234567-58cc-4372-a567-0e02b2c3d479",
      "score": 0.94,
      "document_id": "doc-98765",
      "preview": "Disconnect cable J7 before removing the cooling fan module..."
    }
  ],
  "confidence": "High",
  "diagnostics": {
    "raw_count": 5,
    "deduplicated_count": 4,
    "filtered_count": 2,
    "returned_count": 1,
    "confidence": "High",
    "filter_reason": null,
    "similarity_threshold": 0.75,
    "top_k": 5,
    "max_context_chars": 12000
  },
  "metrics": {
    "search_ms": 12.5,
    "filter_ms": 0.4,
    "prompt_ms": 0.1,
    "generation_ms": 350.2,
    "total_ms": 363.2
  }
}
```

### Soft-Threshold Generation Fallback Response (200 OK - Confidence "Low")

When candidate chunks score below `RAG_SIMILARITY_THRESHOLD` but within `RAG_SOFT_THRESHOLD_MARGIN`, RAGService executes generation with relaxed threshold chunks and marks confidence `"Low"`:

```json
{
  "question": "Marginal procedure question",
  "answer": "Grounded answer derived from candidate chunks retrieved under relaxed threshold margin.",
  "sources": [
    {
      "page": 42,
      "chunk_id": "c9876543-12ab-34cd-56ef-7890abcdef12",
      "score": 0.72,
      "document_id": "doc-101",
      "preview": "Marginal procedure instructions context snippet..."
    }
  ],
  "confidence": "Low",
  "diagnostics": {
    "raw_count": 3,
    "deduplicated_count": 3,
    "filtered_count": 1,
    "returned_count": 1,
    "confidence": "Low",
    "filter_reason": null,
    "similarity_threshold": 0.70,
    "top_k": 5,
    "max_context_chars": 12000
  },
  "metrics": {
    "search_ms": 11.2,
    "filter_ms": 0.3,
    "prompt_ms": 0.2,
    "generation_ms": 280.5,
    "total_ms": 292.2
  }
}
```

### Fallback Response (Below Soft Threshold / No Chunks)

```json
{
  "question": "Unrelated question",
  "answer": "I could not find sufficiently relevant information in the manual.",
  "sources": [],
  "confidence": "None",
  "diagnostics": {
    "raw_count": 2,
    "deduplicated_count": 2,
    "filtered_count": 0,
    "returned_count": 0,
    "confidence": "None",
    "filter_reason": "filtered_below_threshold",
    "similarity_threshold": 0.75,
    "top_k": 5,
    "max_context_chars": 12000
  },
  "metrics": {
    "search_ms": 10.1,
    "filter_ms": 0.3,
    "prompt_ms": 0.0,
    "generation_ms": 0.0,
    "total_ms": 10.4
  }
}
```


---

# Semantic Search

## POST /search

Executes vector similarity search against embedded manual chunks.

### Request

```json
{
  "query": "replace cooling fan",
  "top_k": 5,
  "document_id": "doc001"
}
```
*(Note: `document_id` is optional. When omitted, search is performed across all manuals).*


### Response

```json
{
  "query": "replace cooling fan",
  "count": 1,
  "results": [
    {
      "document_id": "doc001",
      "chunk_id": "c1234567-58cc-4372-a567-0e02b2c3d479",
      "page_number": 18,
      "score": 0.94,
      "text": "Disconnect cable J7 before removing cooling fan module."
    }
  ]
}
```

---

# Upload Manual

## POST /upload

Uploads a technical manual PDF for processing.

### Request

`multipart/form-data` with `file=@manual.pdf`.

---

# Health Check

## GET /health

Response: `{"status": "healthy"}`

---

# Error Response Format

```json
{
  "error": "Error description message",
  "status": 400
}
```

HTTP Status Codes:
- `200 OK`
- `400 Bad Request`
- `422 Validation Error`
- `503 Service Unavailable (Ollama)`
- `504 Gateway Timeout (Ollama)`
