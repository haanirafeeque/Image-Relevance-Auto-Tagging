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


@patch("app.main.match_images_for_post")
def test_get_post_images(mock_match):
    mock_match.return_value = {
        "post": {"id": 1, "title": "Fox Post", "content": "Text", "created_at": "2026-09-23T10:00:00"},
        "matches": [],
        "best_match": None,
        "status": "no_confident_match",
    }
    response = client.get("/posts/1/images")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "no_confident_match"
    assert "matches" in data


@patch("app.main.match_images_for_post")
def test_get_post_images_not_found(mock_match):
    mock_match.side_effect = ValueError("Post 9999 not found")
    response = client.get("/posts/9999/images")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


@patch("app.main.run_execute_returning")
@patch("app.main.run_query_one")
@patch("app.main.run_query")
def test_suggestion_review_workflow(mock_query, mock_query_one, mock_exec):
    mock_query.return_value = [
        {
            "id": 10,
            "post_id": 1,
            "image_id": 2,
            "similarity": 0.85,
            "guard_status": "approved",
            "reason": "OK",
            "review_status": "pending",
            "created_at": "2026-09-23T10:00:00",
        }
    ]
    mock_query_one.return_value = mock_query.return_value[0]
    mock_exec.return_value = {**mock_query.return_value[0], "review_status": "approved"}

    # List suggestions
    list_res = client.get("/suggestions")
    assert list_res.status_code == 200
    assert len(list_res.json()["suggestions"]) == 1

    # Get single suggestion
    get_res = client.get("/suggestions/10")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == 10

    # Approve suggestion
    appr_res = client.post("/suggestions/10/approve")
    assert appr_res.status_code == 200
    assert appr_res.json()["review_status"] == "approved"

    # Reject suggestion
    mock_exec.return_value = {**mock_query.return_value[0], "review_status": "rejected"}
    rej_res = client.post("/suggestions/10/reject")
    assert rej_res.status_code == 200
    assert rej_res.json()["review_status"] == "rejected"

