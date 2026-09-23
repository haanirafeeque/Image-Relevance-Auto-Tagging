"""
FastAPI application — the main entry point.

Run with: uvicorn app.main:app --reload
"""

from typing import Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from app.database import run_query, run_query_one, run_execute_returning
from app.jobs import run_batch_processing
from app.matching import match_images_for_post

app = FastAPI(
    title="AI Image Understanding & Content Matching Engine",
    description="Matches blog post images using AI vision and semantic similarity",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    """Simple health check to verify the API is running."""
    return {"status": "healthy", "version": "0.1.0"}


# --- Image endpoints ---

@app.get("/images")
def list_images():
    """List all images in the database."""
    rows = run_query("SELECT * FROM images ORDER BY id")
    return {"images": rows, "count": len(rows)}


@app.get("/images/{image_id}")
def get_image(image_id: int):
    """Get a single image by ID."""
    row = run_query_one("SELECT * FROM images WHERE id = %s", (image_id,))
    if not row:
        raise HTTPException(status_code=404, detail="Image not found")
    return row


# --- Post endpoints ---

@app.get("/posts")
def list_posts():
    """List all blog posts."""
    rows = run_query("SELECT * FROM posts ORDER BY id")
    return {"posts": rows, "count": len(rows)}


@app.get("/posts/{post_id}")
def get_post(post_id: int):
    """Get a single post by ID."""
    row = run_query_one("SELECT * FROM posts WHERE id = %s", (post_id,))
    if not row:
        raise HTTPException(status_code=404, detail="Post not found")
    return row


# --- Job endpoints ---


@app.post("/jobs/process-images")
def start_image_processing_job(background_tasks: BackgroundTasks, limit: Optional[int] = None):
    """Start batch processing of pending images in the background."""
    # Count pending images that will be processed
    if limit is not None and limit > 0:
        count_row = run_query_one(
            "SELECT COUNT(*) AS total FROM (SELECT id FROM images WHERE status = 'pending' LIMIT %s) sub",
            (limit,),
        )
    else:
        count_row = run_query_one("SELECT COUNT(*) AS total FROM images WHERE status = 'pending'")

    total_pending = count_row["total"] if count_row else 0

    insert_sql = """
        INSERT INTO jobs (status, total, processed, failed)
        VALUES ('pending', %s, 0, 0)
        RETURNING id, status, total, processed, failed, created_at
    """
    job = run_execute_returning(insert_sql, (total_pending,))

    # Add to background tasks
    background_tasks.add_task(run_batch_processing, job["id"], limit)

    return job


@app.get("/jobs")
def list_jobs():
    """List all batch processing jobs."""
    rows = run_query("SELECT * FROM jobs ORDER BY id DESC")
    return {"jobs": rows, "count": len(rows)}


@app.get("/jobs/{job_id}")
def get_job_status(job_id: int):
    """Get the status of a specific batch processing job."""
    row = run_query_one("SELECT * FROM jobs WHERE id = %s", (job_id,))
    if not row:
        raise HTTPException(status_code=404, detail="Job not found")
    return row


# --- AI Call Log endpoints ---

@app.get("/ai-logs")
def list_ai_logs(limit: int = 100):
    """List recent AI model calls and cost tracking."""
    rows = run_query("SELECT * FROM ai_call_logs ORDER BY id DESC LIMIT %s", (limit,))
    return {"logs": rows, "count": len(rows)}


# --- Matching & Suggestion endpoints ---


@app.get("/posts/{post_id}/images")
def get_post_images(post_id: int, top_k: int = 5):
    """Match and rank relevant images for a blog post with safety guards."""
    try:
        result = match_images_for_post(post_id, top_k=top_k)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/suggestions")
def list_suggestions(limit: int = 50):
    """List proposed image-post suggestions."""
    rows = run_query("SELECT * FROM suggestions ORDER BY id DESC LIMIT %s", (limit,))
    return {"suggestions": rows, "count": len(rows)}


@app.get("/suggestions/{suggestion_id}")
def get_suggestion(suggestion_id: int):
    """Get a suggestion by ID."""
    row = run_query_one("SELECT * FROM suggestions WHERE id = %s", (suggestion_id,))
    if not row:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    return row


@app.post("/suggestions/{suggestion_id}/approve")
def approve_suggestion(suggestion_id: int):
    """Reviewer approves an image suggestion."""
    row = run_execute_returning(
        "UPDATE suggestions SET review_status = 'approved' WHERE id = %s RETURNING *",
        (suggestion_id,),
    )
    if not row:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    return row


@app.post("/suggestions/{suggestion_id}/reject")
def reject_suggestion(suggestion_id: int):
    """Reviewer rejects an image suggestion."""
    row = run_execute_returning(
        "UPDATE suggestions SET review_status = 'rejected' WHERE id = %s RETURNING *",
        (suggestion_id,),
    )
    if not row:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    return row


