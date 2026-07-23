# TASKS.md

# Blueprint Eye - Development Roadmap

Version: 1.0

---

# Project Goal

Build an enterprise-grade technical manual retrieval system.

The first version focuses entirely on **accurate retrieval**.

AI-generated answers are intentionally postponed until the retrieval engine is stable.

---

# Priority Order

This project must always follow this development order.

```
1. Retrieval Engine (Highest Priority)

↓

2. Backend Services

↓

3. Frontend

↓

4. AI Integration (Future)
```

The Retrieval Engine is the foundation of the project.

Do NOT start implementing LLMs until retrieval works correctly.

---

# Phase 1 — Project Setup

## Backend

- [x] Initialize FastAPI project
- [x] Configure project structure
- [x] Environment configuration
- [x] Logging
- [x] Error handling

---

## Frontend

Keep the frontend intentionally simple.

Version 1 uses:

- HTML
- CSS
- JavaScript

Reason:

The frontend is only required to demonstrate the backend capabilities.

Avoid unnecessary frontend complexity.

React / Next.js can be introduced later after the backend is stable.

Tasks

- [ ] Upload page
- [ ] Search page
- [ ] Manual viewer
- [ ] Results section

---

# Phase 2 — PDF Processing

- [x] Upload PDF
- [x] Validate file
- [x] Save original PDF
- [x] Extract page text
- [x] Generate page images
- [x] Store metadata

---

# Phase 3 — Chunking

- [x] Split pages into chunks
- [x] Preserve page numbers
- [x] Preserve document IDs
- [x] Store chunk metadata

---

# Phase 4 — Embeddings

- [x] Load embedding model
- [x] Generate embeddings
- [x] Validate embedding quality
- [x] Store embeddings

---

# Phase 5 — Vector Database

- [x] Setup ChromaDB
- [x] Store embeddings
- [x] Store metadata
- [x] Implement similarity search

---

# Phase 6 — Retrieval Engine ⭐

- [x] Accept user query
- [x] Generate query embedding
- [x] Search vector database
- [x] Return Top-K chunks
- [x] Return page numbers
- [x] Return similarity scores

---

# Phase 7 — Backend APIs

- [x] Upload API
- [x] Search API
- [x] Chunking & Embedding API
- [x] RAG Answer API (`POST /api/v1/ask`)

---

# Phase 8 — AI Integration (Sprint 5)

- [x] Implement PromptBuilder with immutable Prompt dataclass
- [x] Implement OllamaService (`gemma4:e4b`) with latency tracking
- [x] Implement RAGService orchestrator
- [x] Implement domain exception handling (504, 503, 500)
- [x] Expose `POST /api/v1/ask`


---

# Phase 8 — Frontend Integration

Only begin after retrieval works.

Tasks

- [ ] Connect upload page
- [ ] Connect search page
- [ ] Display chunks
- [ ] Display manual pages
- [ ] Show loading states
- [ ] Error handling

---

# Phase 9 — Testing

Tasks

- [ ] Unit tests
- [ ] API tests
- [ ] Retrieval accuracy tests
- [ ] Upload tests

---

# Future Milestones

## Version 2

- [ ] Local LLM Integration

Text Query

↓

Retriever

↓

LLM

↓

Answer

---

## Version 3

- [ ] Gemini Vision

Retrieve Images

↓

Gemini Vision

↓

Diagram Explanation

---

## Version 4

- [ ] Multimodal RAG

Retrieve

Text

Images

Tables

↓

Single AI Model

---

# Important Rules

Never sacrifice retrieval quality for UI.

Never add an LLM before retrieval is reliable.

Keep backend modular.

Frontend should remain lightweight until the backend is mature.

Build one stable module at a time.
