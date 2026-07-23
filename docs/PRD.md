# Blueprint Eye - Product Requirements Document (PRD)

Version: 1.0
Status: MVP
Project Type: AI-Powered Technical Manual Retrieval System

---

# 1. Overview

Blueprint Eye is an enterprise-focused technical manual retrieval platform that enables users to quickly locate relevant information from complex PDF manuals using natural language queries.

Unlike traditional AI chatbots, Version 1 focuses on intelligent retrieval rather than AI-generated answers.

The system should retrieve:

- Relevant text passages
- Relevant page numbers
- Relevant manual page images

Future versions will introduce LLM-based reasoning and multimodal understanding.

---

# 2. Problem Statement

Technical manuals often contain hundreds of pages, making information retrieval slow and inefficient.

Existing methods rely on:

- Manual browsing
- CTRL + F
- Static PDF viewers

These approaches struggle with semantic search and technical terminology.

Blueprint Eye aims to reduce document search time from minutes to seconds.

---

# 3. Objectives

Primary Objective

Build an intelligent retrieval engine capable of:

- Uploading technical manuals
- Processing PDFs
- Performing semantic search
- Returning relevant manual pages

Version 1 DOES NOT generate AI answers.

---

# 4. Users

- Maintenance Engineers
- Field Technicians
- Factory Operators
- Mechanical Engineers
- Electrical Engineers
- Students
- Manufacturing Organizations

---

# 5. Functional Requirements

## Manual Upload

Users can upload PDF manuals.

System shall:

- Validate PDF
- Store original document
- Begin preprocessing automatically

---

## PDF Processing

For every uploaded PDF:

Extract:

- page text
- page number
- metadata

Generate:

- page images (PNG)

---

## Chunking

Split extracted text into semantic chunks.

Each chunk must contain:

- chunk id
- document id
- page number
- chunk text

---

## Embedding Generation

Generate embeddings for every chunk using:

Sentence Transformers

Model:

all-MiniLM-L6-v2

---

## Vector Storage

Store embeddings inside ChromaDB.

Metadata:

- page number
- document id
- chunk id

---

## Image Storage

Store page images locally.

Maintain mapping:

Page Number
↓

Image Path

---

## Query Processing

Accept natural language queries.

Example:

How do I replace the cooling fan?

---

## Query Routing

Determine whether query is:

- Text Query
- Visual Query

Initial implementation may use rule-based classification.

---

## Text Retrieval

Generate query embedding.

Perform similarity search.

Return:

- Top K chunks
- Similarity score
- Page number

---

## Visual Retrieval

Retrieve relevant page images.

No vision model required in Version 1.

---

## UI

Display:

Question

↓

Relevant Chunks

↓

Relevant Page Numbers

↓

Manual Page Preview

---

# 6. Non Functional Requirements

Backend:

FastAPI

Frontend:

Next.js

Database:

ChromaDB

PDF Processing:

PyMuPDF

Embeddings:

Sentence Transformers

---

# 7. Out of Scope

Version 1 must NOT include:

- Gemini Flash
- GPT
- Local LLM
- Gemini Vision
- OCR
- Agent workflows
- Multimodal RAG
- Chatbot conversations

---

# 8. Future Roadmap

Version 2

Text Query

↓

Retriever

↓

LLM

↓

Generated Answer

Version 3

Visual Query

↓

Image Retrieval

↓

Gemini Vision

↓

Diagram Explanation

Version 4

True Multimodal RAG

---

# 9. Success Metrics

Successful PDF upload

Correct text extraction

Correct page image generation

Correct chunk creation

Embedding generation

Semantic retrieval accuracy

Relevant page mapping

Sub-2 second retrieval time (small manuals)

---

# 10. Deliverables

Backend APIs

PDF Processing Pipeline

Embedding Pipeline

Vector Search

Image Retrieval

Frontend Search UI

Document Viewer

Project Documentation
