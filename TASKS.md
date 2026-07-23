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

This is the first major milestone.

Tasks

- [ ] Upload PDF
- [ ] Validate file
- [ ] Save original PDF
- [ ] Extract page text
- [ ] Generate page images
- [ ] Store metadata

Output

Each uploaded manual should produce

- Original PDF
- Text
- Page Images
- Metadata

---

# Phase 3 — Chunking

Tasks

- [ ] Split pages into chunks
- [ ] Preserve page numbers
- [ ] Preserve document IDs
- [ ] Store chunk metadata

Output

Chunk

↓

Page Number

↓

Document

---

# Phase 4 — Embeddings

Tasks

- [ ] Load embedding model
- [ ] Generate embeddings
- [ ] Validate embedding quality
- [ ] Store embeddings

---

# Phase 5 — Vector Database

Tasks

- [ ] Setup ChromaDB
- [ ] Store embeddings
- [ ] Store metadata
- [ ] Implement similarity search

---

# Phase 6 — Retrieval Engine ⭐

This is the most important milestone.

Nothing else matters until this works.

Tasks

- [ ] Accept user query
- [ ] Generate query embedding
- [ ] Search vector database
- [ ] Return Top-K chunks
- [ ] Return page numbers
- [ ] Return similarity scores

Success Criteria

Searching

"How do I replace the cooling fan?"

should immediately return

- Relevant chunk
- Correct page number
- Relevant manual page

without using any AI model.

---

# Phase 7 — Backend APIs

Tasks

- [ ] Upload API
- [ ] Search API
- [ ] Documents API
- [ ] Page Image API

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
