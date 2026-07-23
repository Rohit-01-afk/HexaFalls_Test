# DATA_MODEL.md

# Blueprint Eye
## Data Model Specification

Version: 1.0

---

# Purpose

This document defines every data entity used throughout the system.

All modules must use these models consistently.

No module should invent additional fields unless this document is updated.

---

# Entity Relationship Diagram

```
                Document
               /        \
              /          \
          Page           Chunk
             \            /
              \          /
              Search Result
```

A Document owns many Pages.

A Document owns many Chunks.

Every Chunk belongs to exactly one Page.

Every Page belongs to exactly one Document.

---

# Document

Represents an uploaded technical manual.

Fields

| Field | Type | Description |
|--------|------|-------------|
| document_id | UUID | Unique document identifier |
| filename | String | Original filename |
| file_size | Integer | Size in bytes |
| total_pages | Integer | Number of pages |
| upload_time | DateTime | Upload timestamp |
| processing_status | Enum | uploaded / processing / completed / failed |

Example

```json
{
  "document_id": "doc_001",
  "filename": "service_manual.pdf",
  "total_pages": 348,
  "processing_status": "completed"
}
```

---

# Page

Represents one PDF page.

Fields

| Field | Type |
|--------|------|
| page_id | UUID |
| document_id | UUID |
| page_number | Integer |
| image_path | String |

Example

```json
{
    "page_number":18,
    "image_path":"storage/page_images/doc001/page18.png"
}
```

---

# Chunk

Small searchable text unit.

Fields

| Field | Type |
|--------|------|
| chunk_id | UUID |
| document_id | UUID |
| page_number | Integer |
| text | String |
| embedding | Vector |
| token_count | Integer |

Example

```json
{
    "chunk_id":"chunk_18_4",
    "page_number":18,
    "text":"Disconnect cable J7 before removing the fan."
}
```

---

# Query

Represents a user search.

Fields

| Field | Type |
|--------|------|
| query | String |
| embedding | Vector |

---

# Search Result

Returned by semantic retrieval.

Fields

| Field | Type |
|--------|------|
| chunk | Chunk |
| similarity_score | Float |
| page_number | Integer |
| image_path | String |

Example

```json
{
  "page_number":18,
  "similarity_score":0.94
}
```

---

# Processing Pipeline Objects

## Extracted Page

```
Document
↓

Page

↓

Text
```

---

## Embedded Chunk

```
Chunk

↓

Embedding

↓

Vector Database
```

---

# Metadata Rules

Every Chunk MUST know

- document_id
- page_number

Every Page MUST know

- document_id

No orphan records are allowed.

---

# Future Compatibility

Future versions may extend

Document

↓

Workspace

↓

Organization

↓

User Permissions

without changing current models.
