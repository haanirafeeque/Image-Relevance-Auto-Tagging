# Build Log

Record of decisions, tools used, and mistakes throughout the project.

## Phase 0 — Environment Setup

**Date:** 2026-09-22

### Tools & Resources Used
- Verified environment setup (Python, Git, PostgreSQL, Ollama versions)
- Used AI assistant to generate boilerplate: `.gitignore`, `.env.example`, and `requirements.txt`

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

### Tools & Resources Used
- Designed project architecture and documented it in `DESIGN.md`
- Created FastAPI application skeleton and module layout
- Used AI assistant to scaffold boilerplate files

### Decisions Made
- Simple function-based architecture (no unnecessary classes)
- Direct SQL with psycopg (no ORM)
- Embeddings stored as JSON text in PostgreSQL (no pgvector needed at this scale)
- Cosine similarity computed in Python with numpy
- Background processing uses FastAPI BackgroundTasks (no Celery/Redis)

## Phase 2 — Database & Seed Data

**Date:** 2026-09-23

### Tools & Resources Used
- Wrote SQL migrations (`001_create_tables.sql`) and database helper functions (`database.py`)
- Designed Pydantic schemas for request/response validation
- Wrote seed script to download 40 images from Pexels across 4 categories
- Added image and post listing endpoints to `main.py`

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

### Tools & Resources Used
- Implemented vision processing in `app/vision.py` using Ollama `gemma3:4b` with JSON output and retry logic
- Created background batch processing job service in `app/jobs.py`
- Added FastAPI endpoints for job management and AI call logging
- Wrote unit and integration tests in `tests/test_vision.py` and `tests/test_api.py`
- Used AI assistant to help debug Pydantic v2 compatibility issues

### Decisions Made
- **Batch processing with FastAPI BackgroundTasks** — sequential execution per job prevents VRAM/GPU contention on the local Ollama instance.
- **Prompt template externalized** — kept in `prompts/image-understanding-v1.md` rather than hardcoding in Python code.
- **Token and latency tracking** — `ai_call_logs` records prompt and eval token counts plus elapsed milliseconds for cost/performance monitoring.
- **Confidence thresholding** — images with confidence < 0.60 are marked as `low_confidence` rather than `processed`.

### Mistakes Found
- **Pydantic v2 `created_at: str` vs psycopg datetime** — Pydantic v2 rejected Python `datetime.datetime` objects returned by psycopg when typed as `str`. Resolved by updating schema types to `Union[datetime, str]`.
- **Pydantic Settings deprecation** — `class Config: env_file = ".env"` raised deprecation warnings in Pydantic v2. Migrated to `model_config = SettingsConfigDict(env_file=".env", extra="ignore")`.
- **Cold model load latency** — Initial Ollama vision call took ~52 seconds while weights were being paged into memory; subsequent calls dropped to ~6-16 seconds.

## Phase 4 — Text Embeddings, Matching Engine & Mismatch Guard

**Date:** 2026-09-23

### Tools & Resources Used
- Built text embedding generation with Ollama `all-minilm` in `app/embeddings.py`
- Created matching engine and multi-rule mismatch guard in `app/matching.py`
- Extended `app/jobs.py` to embed image captions automatically during batch ingestion
- Added suggestion management and human review endpoints to `app/main.py`
- Wrote comprehensive tests in `tests/test_matching.py` and updated `tests/test_api.py`

### Decisions Made
- **384-dimensional dense vectors** stored as JSON strings in PostgreSQL text columns without requiring pgvector extension.
- **Multi-rule mismatch guard** — Combines similarity score threshold, vision model confidence, and subject/category keyword validation.
- **No guessing policy** — When no candidate image meets all guardrail requirements, returns `status="no_confident_match"` and `best_match=null`.
- **Suggestion persistence** — Matching candidates are persisted in the `suggestions` table for human approval/rejection workflows.

### Mistakes Found
- **Test parameter index shift** — Updating `process_image_record` to include `embedding` shifted the SQL update parameter index for `status` from index 5 to index 6, causing test assertion failures until fixed.
- **Misleading seed images handled cleanly** — An image named `wolf_01.jpg` was actually a landscape photo of a sunset and waterfall from Pexels. The vision model correctly classified it as landscape/sunset (0.85 confidence), which the matching engine properly rejected with a low similarity score (0.0156) against wolf posts.

## Phase 5 — Full Batch Processing & Evaluation Suite

**Date:** 2026-09-23

### Tools & Resources Used
- Wrote `scripts/run_batch_all.py` to batch process all remaining images with live progress output
- Built `evals/eval_matching.py` to evaluate matching quality across all 12 posts and write `evals/results.json`
- Wrote `evals/analyze_threshold.py` to study similarity score distributions and calibrate the threshold
- Ran evaluation, analyzed results, and tuned the similarity threshold from 0.60 → 0.40

### Decisions Made
- **Threshold recalibrated from 0.60 → 0.40** — `all-minilm` produces lower absolute cosine similarities when comparing short image captions to longer blog post text. After evaluating all 12 posts, 0.40 yields 8/12 matches (66.7%) with 100% subject accuracy.
- **No confident match is a correct output** — 4 posts ("Training Your Puppy", "Wild Canids", "Wildlife Photography", "Polar Bears") have no image in the corpus that closely matches their content. The system correctly returns `no_confident_match` rather than forcing a bad match.
- **Evaluation writes `evals/results.json`** — full structured output for later analysis or threshold tuning.

### Mistakes Found
- **Similarity threshold too strict at 0.60** — Initial default was appropriate for same-scale text comparisons, but `all-minilm` produces lower similarities when crossing text scales (short captions vs. long blog posts). This is a model characteristic, not a bug. Corrected through empirical evaluation — threshold lowered to 0.40.
