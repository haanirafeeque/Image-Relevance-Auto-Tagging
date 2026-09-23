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

## Phase 3 — Vision Processing & Image Understanding

**Command:** `pytest tests/ -v`
**Output:**
```
tests/test_api.py::test_health PASSED                                    [  6%]
tests/test_api.py::test_list_images PASSED                               [ 12%]
tests/test_api.py::test_get_image_not_found PASSED                       [ 18%]
tests/test_api.py::test_list_posts PASSED                                [ 25%]
tests/test_api.py::test_get_post_not_found PASSED                        [ 31%]
tests/test_api.py::test_start_job_and_get_job PASSED                     [ 37%]
tests/test_api.py::test_get_job_not_found PASSED                         [ 43%]
tests/test_api.py::test_ai_logs PASSED                                   [ 50%]
tests/test_vision.py::test_vision_output_valid PASSED                    [ 56%]
tests/test_vision.py::test_vision_output_invalid_confidence PASSED       [ 62%]
tests/test_vision.py::test_clean_json_text PASSED                        [ 68%]
tests/test_vision.py::test_analyze_image_file_not_found PASSED           [ 75%]
tests/test_vision.py::test_analyze_image_success PASSED                  [ 81%]
tests/test_vision.py::test_analyze_image_retry_and_fail PASSED           [ 87%]
tests/test_vision.py::test_process_image_record_processed PASSED         [ 93%]
tests/test_vision.py::test_process_image_record_low_confidence PASSED    [100%]
======================= 16 passed in 2.49s ========================
```
**Result:** All 16 automated tests passed.

---

**Command:** Batch Image Understanding Run (Ollama `gemma3:4b`)
**Output:**
```
Started test job 2 for 2 images...
Job result: {'id': 2, 'status': 'completed', 'total': 2, 'processed': 2, 'failed': 0}
Processed images:
 -> fox_01.jpg: subject='red fox', category='fox', confidence=0.95, status='processed'
 -> fox_02.jpg: subject='red fox', category='fox', confidence=0.95, status='processed'

AI Call Logs:
 -> id=1, operation='vision', model='gemma3:4b', duration_ms=16884, input_tokens=575, output_tokens=72
 -> id=2, operation='vision', model='gemma3:4b', duration_ms=6252,  input_tokens=575, output_tokens=54
```
**Result:** Image vision extraction accurately identified subject, category, attributes, caption, confidence, logged tokens and duration, and updated job and image statuses.

---

*More evidence will be added after each phase.*

