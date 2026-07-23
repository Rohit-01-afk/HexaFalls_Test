# Blueprint Eye

Enterprise-grade technical manual retrieval system.

## Overview

Blueprint Eye is a high-precision document retrieval system designed to rapidly query and locate relevant technical manual passages, pages, and diagrams.

## Sprint 0 — Project Foundation

This repository provides the core RESTful backend service built with FastAPI.

### Quickstart

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Copy environment file:
   ```bash
   cp .env.example .env
   ```

3. Run the development server:
   ```bash
   uvicorn backend.main:app --reload
   ```

4. Health Check:
   - GET `http://localhost:8000/health`
   - GET `http://localhost:8000/api/v1/health`
   - Interactive OpenAPI docs: `http://localhost:8000/docs`
