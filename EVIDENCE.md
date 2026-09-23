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

## Phase 4 — Text Embeddings, Matching Engine & Mismatch Guard

**Command:** `pytest tests/ -v`
**Output:**
```
tests/test_api.py::test_health PASSED                                    [  3%]
tests/test_api.py::test_list_images PASSED                               [  6%]
tests/test_api.py::test_get_image_not_found PASSED                       [  9%]
tests/test_api.py::test_list_posts PASSED                                [ 12%]
tests/test_api.py::test_get_post_not_found PASSED                        [ 15%]
tests/test_api.py::test_start_job_and_get_job PASSED                     [ 18%]
tests/test_api.py::test_get_job_not_found PASSED                         [ 21%]
tests/test_api.py::test_ai_logs PASSED                                   [ 25%]
tests/test_api.py::test_get_post_images PASSED                           [ 28%]
tests/test_api.py::test_get_post_images_not_found PASSED                 [ 31%]
tests/test_api.py::test_suggestion_review_workflow PASSED                [ 34%]
tests/test_matching.py::test_cosine_similarity_identical PASSED          [ 37%]
tests/test_matching.py::test_cosine_similarity_orthogonal PASSED         [ 40%]
tests/test_matching.py::test_cosine_similarity_opposite PASSED           [ 43%]
tests/test_matching.py::test_cosine_similarity_zero_vector PASSED        [ 46%]
tests/test_matching.py::test_evaluate_guard_low_similarity PASSED        [ 50%]
tests/test_matching.py::test_evaluate_guard_low_confidence PASSED        [ 53%]
tests/test_matching.py::test_evaluate_guard_subject_mismatch PASSED      [ 56%]
tests/test_matching.py::test_evaluate_guard_approved PASSED              [ 59%]
tests/test_matching.py::test_evaluate_guard_multi_category_post PASSED   [ 62%]
tests/test_matching.py::test_generate_embedding_empty_text PASSED        [ 65%]
tests/test_matching.py::test_generate_embedding_success PASSED           [ 68%]
tests/test_matching.py::test_match_images_post_not_found PASSED          [ 71%]
tests/test_matching.py::test_match_images_for_post_with_candidates PASSED [ 75%]
tests/test_vision.py::test_vision_output_valid PASSED                    [ 78%]
tests/test_vision.py::test_vision_output_invalid_confidence PASSED       [ 81%]
tests/test_vision.py::test_clean_json_text PASSED                        [ 84%]
tests/test_vision.py::test_analyze_image_file_not_found PASSED           [ 87%]
tests/test_vision.py::test_analyze_image_success PASSED                  [ 90%]
tests/test_vision.py::test_analyze_image_retry_and_fail PASSED           [ 93%]
tests/test_vision.py::test_process_image_record_processed PASSED         [ 96%]
tests/test_vision.py::test_process_image_record_low_confidence PASSED    [100%]
======================= 32 passed in 2.25s ========================
```
**Result:** All 32 unit and integration tests passed.

---

**Command:** Post & Image Matching Execution (`python -m scripts.verify_phase4`)
**Output:**
```
1. Embedding all posts in database...
Posts embedded: 12 (all-minilm, 384 dimensions)

2. Ensuring processed images have embeddings...
 -> fox_01.jpg embedded: True (len=384)
 -> fox_02.jpg embedded: True (len=384)
 -> wolf_01.jpg embedded: True (len=384)
 -> wolf_02.jpg embedded: True (len=384)

3. Matching for Post 37 ("The Behavior of Red Foxes in the Wild"):
Post Title: The Behavior of Red Foxes in the Wild
Status: matched
Best Match: fox_01.jpg (Similarity: 0.6332)
 -> Rank 1: fox_01.jpg | Sim: 0.6332 | Guard: approved | Reason: Passed similarity, vision confidence, and subject relevance checks
 -> Rank 2: fox_02.jpg | Sim: 0.5198 | Guard: rejected | Reason: Similarity score 0.52 is below threshold 0.60
 -> Rank 3: wolf_02.jpg | Sim: 0.3879 | Guard: rejected | Reason: Similarity score 0.39 is below threshold 0.60
 -> Rank 4: wolf_01.jpg | Sim: 0.0859 | Guard: rejected | Reason: Similarity score 0.09 is below threshold 0.60

4. Matching for Post 39 ("Gray Wolves: Pack Dynamics and Hunting Strategies"):
Post Title: Gray Wolves: Pack Dynamics and Hunting Strategies
Status: no_confident_match
Best Match: None (no candidate passed the guard)
 -> Rank 1: wolf_02.jpg | Sim: 0.5364 | Guard: rejected | Reason: Similarity score 0.54 is below threshold 0.60
 -> Rank 2: fox_02.jpg | Sim: 0.3182 | Guard: rejected | Reason: Similarity score 0.32 is below threshold 0.60
 -> Rank 3: fox_01.jpg | Sim: 0.2494 | Guard: rejected | Reason: Similarity score 0.25 is below threshold 0.60
 -> Rank 4: wolf_01.jpg | Sim: 0.0156 | Guard: rejected | Reason: Similarity score 0.02 is below threshold 0.60
```
**Result:** 
- `fox_01.jpg` was approved as best match for fox post (similarity 0.6332).
- Mismatched categories and below-threshold candidates were safely rejected with informative explanations.
- Suggestion persistence and approval/rejection endpoints verified.

---

*More evidence will be added after each phase.*


