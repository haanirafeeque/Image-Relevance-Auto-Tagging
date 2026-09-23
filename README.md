# Image Relevance & Auto-Tagging Engine

A backend system that automatically understands image content using local AI vision models, generates semantic embeddings, and matches images to blog posts — with safety guardrails to prevent irrelevant or mismatched results.

Built with **FastAPI**, **PostgreSQL**, and local **Ollama** models (no cloud API required).

---

## How It Works

1. **Vision Analysis** — Each image is sent to `gemma3:4b` (local LLM via Ollama) which returns a structured JSON description: subject, category, tags, caption, and confidence score.
2. **Semantic Embedding** — The image caption and blog post text are independently embedded into 384-dimensional vectors using `all-minilm`.
3. **Cosine Similarity Ranking** — All images are ranked against a post by cosine similarity score.
4. **Mismatch Guard** — A multi-rule guard filters candidates that fall below the similarity threshold, have low vision confidence, or whose subject conflicts with the post topic.
5. **Human Review** — Suggestions are persisted in the database and exposed through approve/reject API endpoints for editorial review.

---



## Project Structure

```
app/
  main.py          # FastAPI routes
  vision.py        # Image analysis with gemma3:4b
  embeddings.py    # Text embeddings with all-minilm
  matching.py      # Cosine similarity + mismatch guard
  jobs.py          # Batch processing jobs
  database.py      # SQL query helpers
  schemas.py       # Pydantic models
  config.py        # Settings from .env

evals/
  eval_matching.py     # Full evaluation suite across all posts
  analyze_threshold.py # Threshold calibration analysis
  results.json         # Latest evaluation output

scripts/
  seed_data.py       # Download images and seed database
  run_batch_all.py   # Process all pending images

migrations/
  001_create_tables.sql

tests/
  test_api.py
  test_vision.py
  test_matching.py

prompts/
  image-understanding-v1.md  # Vision model system prompt
```

---

## Quick Start

**Prerequisites:** Python 3.11+, PostgreSQL, [Ollama](https://ollama.com) with `gemma3:4b` and `all-minilm` pulled.

```bash
# 1. Create virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Linux/macOS

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
copy .env.example .env        # Windows
cp .env.example .env          # Linux/macOS
# Edit .env with your database credentials

# 4. Run database migrations and seed data
python scripts/seed_data.py

# 5. Start the API server
uvicorn app.main:app --reload
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `GET` | `/images` | List all images and statuses |
| `GET` | `/images/{id}` | Get single image detail |
| `GET` | `/posts` | List all blog posts |
| `GET` | `/posts/{id}` | Get single post |
| `GET` | `/posts/{post_id}/images` | Match & rank images for a post (with guardrails) |
| `POST` | `/jobs/process-images` | Start batch vision + embedding job (`?limit=N`) |
| `GET` | `/jobs/{job_id}` | Get job status |
| `GET` | `/jobs` | List all jobs |
| `GET` | `/suggestions` | List match suggestions |
| `POST` | `/suggestions/{id}/approve` | Approve a suggestion |
| `POST` | `/suggestions/{id}/reject` | Reject a suggestion |
| `GET` | `/ai-logs` | View model call logs (tokens, latency) |

---

## Running Batch Processing & Evaluation

```bash
# Process all pending images (vision analysis + embeddings)
python -m scripts.run_batch_all

# Evaluate matching quality across all posts
python -m evals.eval_matching

# Analyse threshold impact from results.json
python evals/analyze_threshold.py

# Run all automated tests
python -m pytest tests/ -v
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| API | Python 3.13 + FastAPI |
| Database | PostgreSQL 17 |
| Vision model | Ollama `gemma3:4b` |
| Embedding model | Ollama `all-minilm` (384d) |
| Similarity | numpy cosine similarity |
| Validation | Pydantic v2 |
| Testing | pytest |
