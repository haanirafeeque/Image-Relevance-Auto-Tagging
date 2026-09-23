"""
Integration and API endpoint tests using FastAPI TestClient.
"""

from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_list_images():
    response = client.get("/images")
    assert response.status_code == 200
    data = response.json()
    assert "images" in data
    assert "count" in data


def test_get_image_not_found():
    response = client.get("/images/99999999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Image not found"


def test_list_posts():
    response = client.get("/posts")
    assert response.status_code == 200
    data = response.json()
    assert "posts" in data
    assert "count" in data


def test_get_post_not_found():
    response = client.get("/posts/99999999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Post not found"


@patch("app.main.run_batch_processing")
def test_start_job_and_get_job(mock_bg_task):
    # Test starting a batch job with limit
    response = client.post("/jobs/process-images?limit=2")
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["status"] in ("pending", "running")
    job_id = data["id"]

    # Test retrieving the job
    job_response = client.get(f"/jobs/{job_id}")
    assert job_response.status_code == 200
    job_data = job_response.json()
    assert job_data["id"] == job_id

    # Test listing jobs
    jobs_list = client.get("/jobs")
    assert jobs_list.status_code == 200
    assert "jobs" in jobs_list.json()


def test_get_job_not_found():
    response = client.get("/jobs/99999999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"


def test_ai_logs():
    response = client.get("/ai-logs")
    assert response.status_code == 200
    data = response.json()
    assert "logs" in data
    assert "count" in data
