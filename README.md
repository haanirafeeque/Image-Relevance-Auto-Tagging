# AI Image Understanding & Content Matching Engine

An AI-powered system that matches blog post images using vision understanding
and semantic similarity, with safety guards to prevent bad matches.

## Status

✅ **Phase 5 complete** — All 40 images processed, evaluation suite run across all 12 posts.

| Metric | Result |
|---|---|
| Images processed | 40/40 (100%) |
| Posts matched (confident) | 8/12 (66.7%) |
| Subject accuracy | 8/8 (100%) |
| Guard rejection rate | 89.2% |
| Similarity threshold | 0.40 (calibrated from eval) |

## Quick Start

```bash
# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Linux/macOS

# Install dependencies
pip install -r requirements.txt

# Copy environment file and edit with your database credentials
copy .env.example .env          # Windows
cp .env.example .env            # Linux/macOS

# Run the API server
uvicorn app.main:app --reload
```

## API Endpoints

- `GET /health` — Health check
- `GET /images` — List all images and processing statuses
- `GET /images/{id}` — Get single image details
- `GET /posts` — List all blog posts
- `GET /posts/{id}` — Get single blog post
- `GET /posts/{post_id}/images` — Match and rank images for a blog post with safety guardrails
- `POST /jobs/process-images` — Start batch image understanding job (supports `?limit=N`)
- `GET /jobs/{job_id}` — Get batch processing job status
- `GET /jobs` — List all batch processing jobs
- `GET /suggestions` — List proposed image suggestions
- `GET /suggestions/{suggestion_id}` — Get a suggestion by ID
- `POST /suggestions/{suggestion_id}/approve` — Human reviewer approves suggestion
- `POST /suggestions/{suggestion_id}/reject` — Human reviewer rejects suggestion
- `GET /ai-logs` — View AI model invocation and token logs

## Tech Stack

- **Python 3.13** + FastAPI
- **PostgreSQL 17** — data storage
- **Ollama** — local AI inference
  - `gemma3:4b` — image understanding (vision)
  - `all-minilm` — text embeddings (384 dimensions)
- **Pydantic** — data validation
- **numpy** — cosine similarity calculation

## Running Batch Processing & Evaluation

```bash
# Process all pending images (vision + embeddings)
python -m scripts.run_batch_all

# Evaluate matching quality across all posts
python -m evals.eval_matching

# Analyse threshold impact on results.json
python evals/analyze_threshold.py

# Run all automated tests
python -m pytest tests/ -v
```
