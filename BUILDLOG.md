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
