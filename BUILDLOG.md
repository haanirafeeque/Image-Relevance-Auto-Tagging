# Build Log

Honest record of AI assistance, decisions, and mistakes throughout the project.

## Phase 0 — Environment Setup

**Date:** 2026-09-22

### AI Assistance
- Used AI assistant to check environment (Python, Git, PostgreSQL, Ollama versions)
- AI generated `.gitignore`, `.env.example`, and `requirements.txt`
- AI suggested project structure based on capstone requirements

### Decisions Made
- **Python 3.13.0** — already installed, meets ≥3.11 requirement
- **PostgreSQL 17** — installed locally (not Docker) for simplicity
- **Ollama gemma3:4b** — chosen over gemma3:1b because 1b doesn't support image input
- **all-minilm** — small, fast embedding model (384 dimensions)
- **Branch renamed** from `master` to `main` for GitHub convention
- **requirements.txt** — listed only direct dependencies, not full transitive tree

### Mistakes Found
- Virtual environment was partially created (missing pip) — had to recreate it
- `psql` wasn't on PATH after PostgreSQL install — added manually

## Phase 1 — Design & Project Structure

**Date:** 2026-09-22

### AI Assistance
- AI generated DESIGN.md based on capstone requirements
- AI created the basic FastAPI application skeleton
- AI created capstone.yaml

### Decisions Made
- Simple function-based architecture (no unnecessary classes)
- Direct SQL with psycopg (no ORM)
- Embeddings stored as JSON text in PostgreSQL (no pgvector needed at this scale)
- Cosine similarity computed in Python with numpy
- Background processing uses FastAPI BackgroundTasks (no Celery/Redis)

## Phase 2 — Database & Seed Data

**Date:** 2026-09-23

### AI Assistance
- AI generated the SQL migration (001_create_tables.sql)
- AI created database.py helper functions
- AI created Pydantic schemas (schemas.py)
- AI generated the seed script with Pexels image URLs
- AI added image and post listing endpoints to main.py

### Decisions Made
- **5 tables** — images, posts, suggestions, jobs, ai_call_logs
- **Simple SQL** — no ORM, just psycopg with parameterized queries
- **run_query / run_execute pattern** — each function gets a fresh connection
- **Pexels images** — free license, 400px width for small download size
- **Idempotent seed** — checks for duplicates before inserting

### Mistakes Found
- **8 Pexels URLs were 404** — many Pexels photo IDs no longer exist. Had to test and replace URLs iteratively until all 40 images downloaded.
- **SQL GROUP BY alias error** — PostgreSQL doesn't allow `GROUP BY alias_name` like MySQL does. Had to repeat the full CASE expression in GROUP BY.
- **Unicode encoding error** — Windows cp1252 terminal can't print ✓ and ✗ characters. Replaced with ASCII `[OK]` and `[!!]`.
- **Serial IDs don't reset** — after DELETE + re-INSERT, PostgreSQL SERIAL doesn't restart from 1. API test script had to query actual IDs instead of hardcoding 1.

## Phase 3 — Vision Processing & Image Understanding

**Date:** 2026-09-23

### AI Assistance
- AI implemented vision processing in `app/vision.py` using Ollama `gemma3:4b` with JSON format and retry logic
- AI created background batch processing job service in `app/jobs.py`
- AI added FastAPI endpoints for `POST /jobs/process-images`, `GET /jobs/{job_id}`, `GET /jobs`, and `GET /ai-logs`
- AI created unit and integration test suite in `tests/test_vision.py` and `tests/test_api.py`

### Decisions Made
- **Batch processing with FastAPI BackgroundTasks** — sequential execution per job prevents VRAM/GPU contention on the local Ollama instance.
- **Prompt template externalized** — kept in `prompts/image-understanding-v1.md` rather than hardcoding in Python code.
- **Token and latency tracking** — `ai_call_logs` records prompt and eval token counts plus elapsed milliseconds for cost/performance monitoring.
- **Confidence thresholding** — images with confidence < 0.60 are marked as `low_confidence` rather than `processed`.

### Mistakes Found
- **Pydantic v2 `created_at: str` vs psycopg datetime** — Pydantic v2 rejected Python `datetime.datetime` objects returned by psycopg when typed as `str`. Resolved by updating schema types to `Union[datetime, str]`.
- **Pydantic Settings deprecation** — `class Config: env_file = ".env"` raised deprecation warnings in Pydantic v2. Migrated to `model_config = SettingsConfigDict(env_file=".env", extra="ignore")`.
- **Cold model load latency** — Initial Ollama vision call took ~52 seconds while weights were being paged into memory; subsequent calls dropped to ~6-16 seconds.

