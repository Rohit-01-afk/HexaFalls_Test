# ARCHITECTURE.md

# Blueprint Eye
## System Architecture Document

Version: 1.0 (MVP)

---

# 1. Purpose

Blueprint Eye is an enterprise-grade technical manual retrieval platform.

The primary objective is **accurate information retrieval** from technical PDF manuals.

Version 1 intentionally focuses on retrieval rather than AI-generated responses.

Future versions will integrate LLMs and multimodal reasoning without changing the core retrieval architecture.

---

# 2. High-Level Architecture

```
                    USER
                      │
                      ▼
              Next.js Frontend
                      │
              REST API (FastAPI)
                      │
      ┌───────────────┴────────────────┐
      │                                │
      ▼                                ▼
Document Processing             Query Processing
      │                                │
      ▼                                ▼
Storage Layer                 Retrieval Layer
      │                                │
      └───────────────┬────────────────┘
                      ▼
                 Response Builder
                      │
                      ▼
                Frontend Display
```

---

# 3. System Workflow

```
Upload PDF
    │
    ▼
Extract Text
    │
    ▼
Generate Page Images
    │
    ▼
Chunk Text
    │
    ▼
Generate Embeddings
    │
    ▼
Store Embeddings
    │
    ▼
User Question
    │
    ▼
Query Processor
    │
    ├─────────────┐
    │             │
    ▼             ▼
Text Search   Visual Search
    │             │
    └──────┬──────┘
           ▼
Display Results
```

---

# 4. Architectural Principles

## Separation of Concerns

Each layer has one responsibility.

Processing

↓

Storage

↓

Retrieval

↓

Presentation

No layer should depend on frontend implementation.

---

## Modular Design

Every module must be replaceable.

Example:

Embedding Model

Current:

Sentence Transformers

Future:

BGE
E5
OpenAI
Gemini Embeddings

No code outside the embedding module should change.

---

## Retrieval First

Retrieval is the core of the system.

The retrieval engine must work independently of any AI model.

LLMs should consume retrieval results—not replace retrieval.

---

# 5. Layers

## Layer 1 — Frontend

Responsibilities

- Upload manuals
- Ask questions
- Display retrieved chunks
- Display manual pages
- Show search progress

Technology

- Next.js
- React
- Tailwind CSS

---

## Layer 2 — API Layer

Responsibilities

- Receive requests
- Validate inputs
- Return responses

Technology

FastAPI

No business logic inside API routes.

---

## Layer 3 — Processing Layer

Modules

PDF Processor

Chunk Generator

Embedding Generator

Image Generator

Metadata Generator

Responsibilities

Convert uploaded manual into searchable assets.

---

## Layer 4 — Storage Layer

Stores

Original PDF

Page Images

Embeddings

Metadata

Current storage

Local Filesystem

ChromaDB

Future

S3

Azure Blob

GCS

---

## Layer 5 — Retrieval Layer

Responsibilities

Receive user query

↓

Retrieve relevant chunks

↓

Retrieve relevant pages

↓

Return structured results

This layer never generates answers.

---

# 6. Backend Modules

```
backend/

api/
    upload.py
    search.py

services/
    pdf_processor.py
    chunker.py
    embeddings.py
    retriever.py
    image_store.py
    intent_router.py

models/

schemas/

core/

utils/

storage/

main.py
```

---

# 7. Frontend Modules

```
frontend/

app/

components/

hooks/

services/

types/

styles/
```

---

# 8. Data Model

## Document

```
Document

document_id

filename

upload_time
```

---

## Page

```
Page

page_number

image_path

document_id
```

---

## Chunk

```
Chunk

chunk_id

document_id

page_number

text

embedding
```

---

# 9. Query Flow

```
User Query

↓

Embedding Generator

↓

Vector Search

↓

Top-K Chunks

↓

Frontend
```

---

# 10. Visual Flow

```
User Query

↓

Identify Page

↓

Load PNG

↓

Display Image
```

---

# 11. API Design

## POST /upload

Input

PDF

Returns

Document ID

Processing Status

---

## GET /documents

Returns

Uploaded Manuals

---

## POST /search

Input

Question

Returns

Relevant Chunks

Page Numbers

Similarity Scores

---

## GET /page/{document_id}/{page_number}

Returns

PNG Page Image

---

# 12. Storage Layout

```
storage/

manuals/

page_images/

embeddings/

metadata/
```

---

# 13. Retrieval Pipeline

```
Question
      │
      ▼
Embedding Generator
      │
      ▼
Vector Search
      │
      ▼
Top-K Chunks
      │
      ▼
Response Builder
```

---

# 14. Future AI Integration

Version 2

```
Retriever

↓

LLM

↓

Generated Answer
```

The retriever must expose a clean interface.

Example

```
retrieve(query)

↓

{
    chunks,
    pages,
    metadata
}
```

No retrieval code should change when an LLM is introduced.

---

# 15. Future Vision Integration

```
Question

↓

Image Retrieval

↓

Gemini Vision

↓

Diagram Explanation
```

Again,

Vision models consume retrieved images.

They never replace image retrieval.

---

# 16. Folder Philosophy

Every module owns one responsibility.

Avoid giant utility files.

Keep modules independent.

Prefer composition over inheritance.

Keep interfaces stable.

---

# 17. Scalability Roadmap

Current

Single PDF

↓

Multiple PDFs

↓

Multiple Projects

↓

Organization Workspace

↓

Role-based Access

↓

Cloud Storage

↓

LLM Integration

↓

Multimodal RAG

---

# 18. Non-Goals

Version 1 does NOT implement

❌ Chatbot

❌ GPT

❌ Gemini Flash

❌ Gemini Vision

❌ OCR

❌ Agent Frameworks

❌ LangChain Dependency

❌ LlamaIndex Dependency

❌ Multimodal RAG

---

# 19. Definition of Success

A successful Version 1 should:

✔ Upload manuals

✔ Process PDFs

✔ Generate page images

✔ Generate embeddings

✔ Perform semantic retrieval

✔ Return relevant pages

✔ Display retrieved manual content

without using any LLM.
