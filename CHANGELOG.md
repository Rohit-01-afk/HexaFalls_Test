# CHANGELOG.md

# Changelog

All notable changes to the Blueprint Eye project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0] - 2026-07-23

### Sprint 0 — Project Foundation

#### Added
- Complete backend folder structure matching `PROJECT_STRUCTURE.md` (`api`, `core`, `services`, `schemas`, `models`, `storage`, `utils`).
- Complete frontend, storage, docs, and test directory hierarchy.
- FastAPI entry point (`backend/main.py`) with CORS middleware and structured lifespan startup/shutdown logging.
- Configuration module (`backend/core/config.py`) using Pydantic `BaseSettings` reading environment variables.
- Structured Python logging setup (`backend/core/logging.py`).
- Global exception handlers (`backend/core/exceptions.py`) enforcing standardized error response schema.
- API v1 router and health endpoint (`backend/api/v1/endpoints/health.py`).
- Root health endpoint (`GET /health`) returning `{"status": "ok"}`.
- Requirements definition (`requirements.txt`), environment template (`.env.example`), and `.gitignore`.
- Unit tests (`tests/unit/test_health.py`) for health check verification.
