# AI Image Understanding & Content Matching Engine

An AI-powered system that matches blog post images using vision understanding
and semantic similarity, with safety guards to prevent bad matches.

## Status

🚧 Under construction — Phase 3 complete (Image Understanding & Vision Processing).

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
- `POST /jobs/process-images` — Start batch image understanding job (supports `?limit=N`)
- `GET /jobs/{job_id}` — Get batch processing job status
- `GET /jobs` — List all batch processing jobs
- `GET /ai-logs` — View AI model invocation and token logs

## Tech Stack

- **Python 3.13** + FastAPI
- **PostgreSQL 17** — data storage
- **Ollama** — local AI inference
  - `gemma3:4b` — image understanding (vision)
  - `all-minilm` — text embeddings (384 dimensions)
- **Pydantic** — data validation
- **numpy** — cosine similarity calculation
