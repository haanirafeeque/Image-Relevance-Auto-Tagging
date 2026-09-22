# Design Document — AI Image Understanding & Content Matching Engine

## 1. Problem

Blog platforms need relevant images for their posts. Manually finding and matching
images to blog content is slow and error-prone. A human might pick an image of a
wolf for a blog post about foxes because they look similar at a glance.

This system automates image-to-post matching using AI vision understanding and
semantic similarity, with a safety guard that rejects bad matches and explains why.

## 2. Architecture

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  Client /   │────▶│   FastAPI     │────▶│  PostgreSQL   │
│  API User   │◀────│   Server     │◀────│  Database     │
└─────────────┘     └──────┬───────┘     └──────────────┘
                           │
                    ┌──────┴───────┐
                    │   Ollama     │
                    │  (local AI)  │
                    ├──────────────┤
                    │ gemma3:4b    │  ← vision understanding
                    │ all-minilm   │  ← text embeddings
                    └──────────────┘
```

### Flow

1. **Upload/seed images** → stored in `data/images/` and database
2. **Vision processing** → Ollama gemma3:4b analyzes each image → structured JSON
3. **Validation** → Pydantic validates the AI output, flags low confidence
4. **Embedding** → image captions + blog posts → all-minilm → 384-dim vectors
5. **Matching** → cosine similarity ranks images for each post
6. **Guard** → checks subject/category match, confidence, similarity threshold
7. **Review** → human approves or rejects suggestions via API

## 3. Database Design

Five tables, all using simple SQL:

### images
| Column     | Type    | Purpose                              |
|------------|---------|--------------------------------------|
| id         | SERIAL  | Primary key                          |
| filename   | TEXT    | Original filename                    |
| path       | TEXT    | File path on disk                    |
| subject    | TEXT    | What the image shows (e.g. "red fox")|
| category   | TEXT    | Category (e.g. "fox", "wolf")        |
| attributes | TEXT[]  | Descriptive tags                     |
| caption    | TEXT    | AI-generated description             |
| confidence | FLOAT   | Vision model confidence (0.0–1.0)    |
| embedding  | TEXT    | JSON-encoded embedding vector        |
| status     | TEXT    | pending / processed / failed / low_confidence |
| created_at | TIMESTAMP | When the record was created        |

### posts
| Column     | Type    | Purpose                    |
|------------|---------|----------------------------|
| id         | SERIAL  | Primary key                |
| title      | TEXT    | Blog post title            |
| content    | TEXT    | Blog post body text        |
| embedding  | TEXT    | JSON-encoded embedding     |
| created_at | TIMESTAMP | When created             |

### suggestions
| Column        | Type    | Purpose                              |
|---------------|---------|--------------------------------------|
| id            | SERIAL  | Primary key                          |
| post_id       | INTEGER | FK → posts                           |
| image_id      | INTEGER | FK → images                          |
| similarity    | FLOAT   | Cosine similarity score              |
| guard_status  | TEXT    | approved / rejected / no_confident_match |
| reason        | TEXT    | Human-readable explanation           |
| review_status | TEXT    | pending / approved / rejected        |
| created_at    | TIMESTAMP | When created                       |

### jobs
| Column     | Type      | Purpose                     |
|------------|-----------|-----------------------------|
| id         | SERIAL    | Primary key                 |
| status     | TEXT      | pending / running / completed / failed |
| total      | INTEGER   | Total images to process     |
| processed  | INTEGER   | Successfully processed      |
| failed     | INTEGER   | Failed to process           |
| created_at | TIMESTAMP | When the job started        |

### ai_call_logs
| Column         | Type      | Purpose                          |
|----------------|-----------|----------------------------------|
| id             | SERIAL    | Primary key                      |
| operation      | TEXT      | vision / embedding               |
| model          | TEXT      | Model name used                  |
| duration_ms    | INTEGER   | How long the call took           |
| input_tokens   | INTEGER   | Tokens sent (if available)       |
| output_tokens  | INTEGER   | Tokens received (if available)   |
| estimated_cost | FLOAT     | Estimated cost (0 for local)     |
| created_at     | TIMESTAMP | When the call was made           |

## 4. API Endpoints

| Method | Path                              | Purpose                        |
|--------|-----------------------------------|--------------------------------|
| GET    | /health                           | Health check                   |
| GET    | /images                           | List all images                |
| GET    | /images/{id}                      | Get single image               |
| GET    | /posts                            | List all posts                 |
| GET    | /posts/{id}                       | Get single post                |
| GET    | /posts/{post_id}/images           | Get ranked image suggestions   |
| POST   | /jobs/process-images              | Start batch image processing   |
| GET    | /jobs/{job_id}                    | Check job status               |
| GET    | /suggestions/{suggestion_id}      | Get suggestion details         |
| POST   | /suggestions/{suggestion_id}/approve | Approve a suggestion        |
| POST   | /suggestions/{suggestion_id}/reject  | Reject a suggestion         |
| GET    | /ai-logs                          | View AI call logs              |

## 5. Matching Strategy

### Step 1: Generate embeddings
- Image captions → all-minilm → 384-dimensional vectors
- Blog post (title + content) → all-minilm → 384-dimensional vectors

### Step 2: Cosine similarity
```
similarity = dot(a, b) / (magnitude(a) * magnitude(b))
```

### Step 3: Rank
- Sort all image candidates by similarity score (highest first)

### Step 4: Apply guard
- Check similarity ≥ SIMILARITY_THRESHOLD (default 0.60)
- Check vision confidence ≥ MIN_VISION_CONFIDENCE (default 0.60)
- Check subject/category relevance
- Reject mismatches with explanation

## 6. Mismatch Guard

The guard is the core safety feature. It prevents bad matches by checking:

1. **Similarity threshold** — is the cosine similarity high enough?
2. **Vision confidence** — was the AI confident about what's in the image?
3. **Subject relevance** — does the image subject match the post topic?

### Example rejection:
- Post: "The behavior of red foxes"
- Image: classified as "gray wolf"
- Result: **REJECTED**
- Reason: "Subject mismatch: image shows 'gray wolf' but post is about 'foxes'"

### No confident match:
If no candidate passes all checks, the system returns:
```json
{
  "match": null,
  "status": "no_confident_match",
  "reason": "No image passed the matching and safety checks."
}
```

The system never guesses. If it's not confident, it says so.

## 7. Non-Goal

**Real-time image processing** is explicitly NOT a goal. The vision model takes
several seconds per image, so processing is done as a batch background job, not
inline during API requests. Users check job status via polling.
