# PROJECT_STRUCTURE.md

# Blueprint Eye Project Structure

Version: 1.0

---

# Philosophy

Every folder owns one responsibility.

Never mix business logic, storage logic, and API routes.

---

# Root Structure

```
BlueprintEye/

backend/

frontend/

storage/

docs/

tests/

requirements.txt

README.md
```

---

# Backend

```
backend/

api/

core/

services/

schemas/

models/

storage/

utils/

main.py
```

---

# api/

Contains ONLY FastAPI routes.

Examples

upload.py

search.py

documents.py

health.py

Rules

- No business logic
- Call services only

---

# services/

Contains business logic.

Examples

pdf_processor.py

chunker.py

embedding_service.py

retriever.py

image_service.py

Responsibilities

- PDF processing
- Retrieval
- Embedding generation
- Image generation

---

# schemas/

Contains Pydantic models.

Examples

UploadRequest

SearchResponse

DocumentResponse

---

# models/

Internal domain models.

Examples

Document

Page

Chunk

SearchResult

---

# storage/

Handles

Saving PDFs

Saving Images

Reading Metadata

No retrieval logic here.

---

# core/

Global configuration.

Examples

settings.py

logging.py

constants.py

---

# utils/

Small helper functions only.

Never place business logic here.

---

# Frontend

```
frontend/

index.html

css/

js/

assets/
```

---

# css/

All styling.

---

# js/

API calls

UI updates

Search logic

Upload logic

---

# assets/

Icons

Images

Logos

---

# Storage

```
storage/

manuals/

page_images/

embeddings/

metadata/
```

---

# Tests

```
tests/

unit/

integration/

fixtures/
```

---

# Documentation

```
docs/

PRD.md

ARCHITECTURE.md

TECHSTACK.md

DATA_MODEL.md

API_SPEC.md
```

---

# Import Rules

Allowed

```
API

↓

Services

↓

Storage
```

Not Allowed

```
Storage

↓

API
```

No circular dependencies.

---

# Future Expansion

When React is introduced

```
frontend/

src/

components/

pages/

hooks/

services/

types/
```

Backend architecture should remain unchanged.

---

# Folder Responsibilities Summary

| Folder | Responsibility |
|----------|---------------|
| api | REST endpoints |
| services | Business logic |
| schemas | API models |
| models | Domain models |
| storage | File handling |
| core | Configuration |
| utils | Helper functions |
| tests | Testing |
| frontend | User Interface |

---

# Golden Rule

Every new file must have one clear responsibility.

If a file begins handling multiple unrelated concerns, split it into separate modules.

Maintain clean boundaries between API, business logic, storage, and presentation layers at all times.