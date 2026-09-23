# Evidence

Actual command outputs and test results demonstrating that each feature works.

## Phase 0 — Environment

**Command:** `python --version`
**Output:** `Python 3.13.0`

**Command:** `ollama list`
**Output:**
```
NAME                 ID              SIZE
gemma3:4b            a2af6cc3eb7f    3.3 GB
all-minilm:latest    1b226e2802db    45 MB
```

**Command:** Python psycopg connection test
**Output:** `PostgreSQL connection from Python works!`

**Result:** Environment fully operational.

---

## Phase 2 — Database & Seed Data

**Command:** `psql -U postgres -d image_matching -f migrations/001_create_tables.sql`
**Output:**
```
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
```
**Result:** All 5 tables created (images, posts, suggestions, jobs, ai_call_logs).

---

**Command:** `python -m scripts.seed_data`
**Output:**
```
Downloaded: 40, Failed: 0

Database contents:
  Images: 40
  Posts:  12

  By category:
    bear: 10
    dog: 10
    fox: 10
    wolf: 10

[OK] Seed verified: 40 images, 12 posts
```
**Result:** 40 images (10 per category) and 12 blog posts seeded.

---

**Command:** API endpoint tests
**Output:**
```
GET /health          -> 200
GET /images          -> 200  count=40
GET /images/{id}     -> 200  filename=fox_01.jpg
GET /posts           -> 200  count=12
GET /posts/{id}      -> 200  title=The Behavior of Red Foxes...
GET /images/9999     -> 404  (expected 404)
```
**Result:** All API endpoints functional.

---

*More evidence will be added after each phase.*
