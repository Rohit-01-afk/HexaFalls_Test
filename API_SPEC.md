# API_SPEC.md

# Blueprint Eye API Specification

Version: 1.0

---

# Base URL

```
http://localhost:8000/api/v1
```

---

# Upload Manual

## POST /upload

Uploads a technical manual.

Request

multipart/form-data

```
pdf=<file>
```

Success Response

```json
{
    "document_id":"doc001",
    "status":"processing"
}
```

---

# List Documents

## GET /documents

Response

```json
[
  {
    "document_id":"doc001",
    "filename":"manual.pdf",
    "pages":240
  }
]
```

---

# Search

## POST /search

Request

```json
{
    "query":"replace cooling fan",
    "document_id":"doc001"
}
```

Response

```json
{
    "results":[
        {
            "page_number":18,
            "score":0.94,
            "text":"Disconnect cable J7...",
            "image_path":"storage/page18.png"
        }
    ]
}
```

---

# Get Page Image

## GET /page/{document_id}/{page_number}

Response

PNG Image

---

# Get Document Details

## GET /document/{document_id}

Response

```json
{
    "document_id":"doc001",
    "filename":"manual.pdf",
    "pages":240,
    "status":"completed"
}
```

---

# Health Check

## GET /health

Response

```json
{
    "status":"ok"
}
```

---

# Error Response

Every endpoint should return

```json
{
    "error":"Description",
    "status":400
}
```

---

# HTTP Status Codes

200 OK

201 Created

400 Bad Request

404 Not Found

413 File Too Large

422 Validation Error

500 Internal Server Error

---

# Future APIs

Reserved

```
POST /ask
POST /vision
POST /chat
```

These endpoints are NOT implemented in Version 1.
