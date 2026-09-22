"""
FastAPI application — the main entry point.

Run with: uvicorn app.main:app --reload
"""

from fastapi import FastAPI

app = FastAPI(
    title="AI Image Understanding & Content Matching Engine",
    description="Matches blog post images using AI vision and semantic similarity",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    """Simple health check to verify the API is running."""
    return {"status": "healthy", "version": "0.1.0"}
