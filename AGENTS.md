# AGENTS.md

Project: Blueprint Eye

---

# Mission

Build an enterprise-grade technical manual retrieval system.

The project is NOT an AI chatbot.

The primary goal is accurate document retrieval.

Every architectural decision should prioritize modularity, maintainability, and future extensibility.

---

# Architecture Philosophy

Always separate:

- Processing
- Storage
- Retrieval
- Presentation

Never tightly couple modules.

The retrieval layer must remain independent from any LLM.

Future AI models should consume retrieval output rather than replacing retrieval logic.

---

# Project Workflow

PDF Upload

↓

PDF Processing

↓

Chunking

↓

Embeddings

↓

Vector Storage

↓

User Query

↓

Query Processing

↓

Retrieval

↓

Frontend Display

---

# Development Principles

- Keep modules independent.
- Follow Clean Architecture.
- Use dependency injection where appropriate.
- Avoid global state.
- Keep APIs RESTful.
- Keep business logic inside services.
- Keep routes thin.
- Never mix retrieval logic with UI logic.

---

# Backend Structure

backend/

api/

services/

models/

schemas/

utils/

core/

storage/

---

# Frontend Structure

frontend/

components/

pages/

hooks/

services/

types/

---

# Coding Standards

Python

- Type hints everywhere
- Pydantic models
- Black formatting
- Clear function names

TypeScript

- Strict mode
- Functional components
- Reusable hooks
- Tailwind only

---

# PDF Processing Rules

Every uploaded manual must produce:

Original PDF

Extracted text

Page images

Chunk metadata

Embeddings

Every chunk must preserve:

Document ID

Page Number

Chunk ID

---

# Retrieval & Generation Rules

Never retrieve entire documents.

Always retrieve Top-K chunks.

Preserve metadata.

Similarity scores should be returned.

PromptBuilder Responsibilities:
- Receive pre-filtered chunks.
- Clean, normalize, and organize context blocks.
- Build immutable Prompt objects.
- MUST NEVER perform retrieval, chunk ranking, similarity calculation, confidence evaluation, threshold filtering, or fallback decisions.

RAGService Response Assembly:
- Orchestrate retrieval, filtering, prompt generation, LLM generation, and response payload assembly.
- Keep response formatting and source reference assembly inside RAGService without creating external formatter components.

Soft-Threshold Behavior:
- Soft-threshold fallback may ONLY relax the similarity threshold cutoff parameter.
- Must NEVER bypass RetrievalFilter deduplication, score sorting, Top-K limits, or max context character caps.

---


# Image Rules

Images should be generated once.

Never regenerate images during search.

Always map:

Page Number

↓

Image File

---

# API Principles

REST only.

Consistent response models.

Proper HTTP status codes.

Meaningful error messages.

---

# Error Handling

Handle:

Invalid PDFs

Corrupted PDFs

Empty pages

Missing metadata

Embedding failures

Database failures

Image generation failures

---

# Logging

Log:

Uploads

Processing time

Embedding generation

Retrieval latency

Errors

Never log document contents.

---

# Security

Validate uploaded PDFs.

Limit upload size.

Prevent path traversal.

Sanitize filenames.

---

# Performance

Processing should happen asynchronously.

Retrieval should remain fast.

Avoid duplicate embedding generation.

Cache reusable resources when possible.

---

# Version 1 Restrictions

DO NOT implement:

Gemini

GPT

Local LLM

Vision models

OCR

Agent frameworks

LangChain dependency

LlamaIndex dependency

Multimodal RAG

---

# Future Compatibility

The retrieval layer must expose a clean interface.

Future LLMs should simply call:

retrieve(query)

and receive:

Relevant chunks

Relevant page numbers

Metadata

without changing the retrieval implementation.

---

# Milestones

Milestone 1

Project setup

Milestone 2

PDF processing

Milestone 3

Chunking

Milestone 4

Embeddings

Milestone 5

Vector Search

Milestone 6

Frontend

Milestone 7

LLM Integration (Future)

Milestone 8

Vision Integration (Future)

---

# Definition of Done

A feature is complete only if:

- Code compiles
- Unit tested
- Type safe
- Properly documented
- Modular
- No duplicated logic
- API documented

---

# Development Strategy

This project is implementation-first.

Do not scaffold every future feature.

Complete one milestone fully before moving to the next.

Avoid placeholder code.

Avoid TODO implementations.

Every completed milestone must be executable, testable, and independently functional before proceeding.

---

# Code Minimization & Execution Rules (Ponytail)

Before writing or modifying any code, evaluate solutions strictly top-to-bottom using this ladder:

1. **YAGNI (You Aren't Gonna Need It):** If a requested utility, helper, abstraction, or configuration isn't strictly necessary for the active milestone, do not write it.
2. **Reuse Existing Code:** Inspect the current module and existing services before creating new utilities.
3. **Use Language Standard Libraries:** Prioritize Python standard library modules (`pathlib`, `json`, `re`, `typing`) over external dependencies.
4. **Use Native SDK / Direct APIs:** Use native database drivers and SDK methods directly without intermediate ORM or abstraction layers unless explicitly required.
5. **Write Minimal Code:** Select the solution that produces the fewest lines of readable, safe code.

### Code Quality Guardrails
* **Never sacrifice safety:** Validation, type safety, error boundaries, and security measures (such as path traversal checks) must never be removed or simplified for brevity.
* **Avoid Over-Abstraction:** Do not build abstract base classes, dynamic plugin loaders, or factory patterns unless more than two implementations actively exist.
* **Inline Over Modularization:** Keep single-use code local to its calling scope instead of creating standalone helper files.

---

Evidence Selection Rules

• Never send unnecessary context to the LLM.

• Select only the minimum number of chunks
required to answer the question.

• Evidence selection must remain deterministic.

• PromptBuilder receives only selected evidence.

• The LLM is not responsible for searching.