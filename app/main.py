"""
FastAPI application — the main entry point.

Run with: uvicorn app.main:app --reload
"""

from fastapi import FastAPI, HTTPException
from app.database import run_query, run_query_one

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
