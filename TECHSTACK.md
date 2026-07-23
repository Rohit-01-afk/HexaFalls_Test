# TECHSTACK.md

# Blueprint Eye Technology Stack

Version: 1.0

---

# Philosophy

Technology choices should prioritize

- Simplicity
- Maintainability
- Performance
- Enterprise readiness
- Future scalability

Every selected technology should have a clear purpose.

---

# Frontend (Version 1)

Technology

- HTML5
- CSS3
- Vanilla JavaScript

Reason

The frontend is only required to interact with the backend.

Avoid introducing React or Next.js until the retrieval engine is complete.

Future

React

↓

Next.js

↓

TypeScript

---

# Backend

Framework

FastAPI

Reason

- Fast
- Async
- Type-safe
- Automatic API documentation
- Easy integration with ML libraries

---

# Language

Python 3.12+

Reason

Best ecosystem for

- NLP
- AI
- PDF processing
- Machine Learning

---

# PDF Processing

Library

PyMuPDF (fitz)

Responsibilities

- Read PDFs
- Extract text
- Render page images
- Extract metadata

---

# Embedding Model

Sentence Transformers

Model

all-MiniLM-L6-v2

Reason

- Fast
- Lightweight
- Excellent semantic search
- Runs locally

Future Options

- BAAI/bge-large-en
- multilingual-e5
- Gemini Embeddings

---

# Vector Database

ChromaDB

Responsibilities

- Store embeddings
- Similarity search
- Metadata filtering

Reason

- Lightweight
- Easy setup
- Local storage
- Good for MVP

Future

Qdrant

Milvus

Pinecone

---

# Storage

Version 1

Local Filesystem

Store

- PDFs
- Images
- Metadata

Future

AWS S3

Azure Blob

Google Cloud Storage

---

# API

REST API

Framework

FastAPI

Endpoints

POST /upload

POST /search

GET /documents

GET /page

---

# Frontend Communication

Fetch API

JSON

Multipart File Upload

---

# Search

Semantic Search

Cosine Similarity

Top-K Retrieval

---

# Development Tools

VS Code / Cursor / Antigravity

Git

GitHub

Postman

Docker (optional for MVP)

---

# Package Management

Python

pip

Frontend

No build system required for Version 1

---

# Logging

Python logging

Structured logs

---

# Testing

pytest

Manual API testing

Postman

---

# Deployment (Development)

Backend

localhost:8000

Frontend

Static HTML

---

# Deployment (Future)

Frontend

React / Next.js

Backend

FastAPI

Docker

NGINX

Cloud VM

---

# Future AI Stack

## Text

Retriever

↓

Local LLM / Gemini Flash

↓

Answer Generation

---

## Vision

Image Retrieval

↓

Gemini Vision

↓

Diagram Understanding

---

# Future Database Options

Current

ChromaDB

Possible Upgrades

Qdrant

Milvus

Pinecone

---

# Future Frontend

HTML/CSS/JS

↓

React

↓

Next.js

↓

TypeScript

---

# Current MVP Stack Summary

Frontend

- HTML
- CSS
- JavaScript

Backend

- FastAPI
- Python

Document Processing

- PyMuPDF

Embeddings

- Sentence Transformers (all-MiniLM-L6-v2)

Vector Database

- ChromaDB

Storage

- Local Filesystem

API

- REST

Version 1 intentionally excludes

- LangChain
- LlamaIndex
- Gemini
- OpenAI
- Local LLM
- Vision Models
- Multimodal RAG

These will be added only after the retrieval engine is fully functional and validated.
S