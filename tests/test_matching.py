"""
Unit tests for text embeddings, cosine similarity, mismatch guard, and matching engine.
"""

from unittest.mock import patch, MagicMock
import pytest

from app.matching import cosine_similarity, evaluate_guard, match_images_for_post
from app.embeddings import generate_embedding


# ---------- Cosine Similarity Tests ----------

def test_cosine_similarity_identical():
    v1 = [1.0, 2.0, 3.0]
    assert pytest.approx(cosine_similarity(v1, v1), 0.0001) == 1.0


def test_cosine_similarity_orthogonal():
    v1 = [1.0, 0.0, 0.0]
    v2 = [0.0, 1.0, 0.0]
    assert pytest.approx(cosine_similarity(v1, v2), 0.0001) == 0.0


def test_cosine_similarity_opposite():
    v1 = [1.0, 0.0]
    v2 = [-1.0, 0.0]
    assert pytest.approx(cosine_similarity(v1, v2), 0.0001) == -1.0


def test_cosine_similarity_zero_vector():
    v1 = [0.0, 0.0, 0.0]
    v2 = [1.0, 2.0, 3.0]
    assert cosine_similarity(v1, v2) == 0.0


# ---------- Guardrail Evaluation Tests ----------

def test_evaluate_guard_low_similarity():
    post = {"title": "The Behavior of Red Foxes in the Wild", "content": "Foxes are cunning..."}
    image = {"subject": "red fox", "category": "fox", "confidence": 0.95}
    # 0.35 is below the calibrated threshold of 0.40
    status, reason = evaluate_guard(post, image, similarity=0.35)
    assert status == "rejected"
    assert "below threshold" in reason.lower()


def test_evaluate_guard_low_confidence():
    post = {"title": "The Behavior of Red Foxes in the Wild", "content": "Foxes are cunning..."}
    image = {"subject": "red fox", "category": "fox", "confidence": 0.40}
    status, reason = evaluate_guard(post, image, similarity=0.85)
    assert status == "rejected"
    assert "below threshold" in reason.lower()


def test_evaluate_guard_subject_mismatch():
    post = {"title": "The Behavior of Red Foxes in the Wild", "content": "Foxes live in woodlands..."}
    image = {"subject": "gray wolf", "category": "wolf", "confidence": 0.95}
    status, reason = evaluate_guard(post, image, similarity=0.75)
    assert status == "rejected"
    assert "subject mismatch" in reason.lower()
    assert "wolf" in reason.lower()
    assert "fox" in reason.lower()


def test_evaluate_guard_approved():
    post = {"title": "The Behavior of Red Foxes in the Wild", "content": "Foxes hunt rodents..."}
    image = {"subject": "red fox", "category": "fox", "confidence": 0.95}
    status, reason = evaluate_guard(post, image, similarity=0.82)
    assert status == "approved"
    assert "passed" in reason.lower()


def test_evaluate_guard_multi_category_post():
    post = {
        "title": "The Differences Between Wild Canids: Foxes, Wolves, and Dogs",
        "content": "Canids share many behavioral traits...",
    }
    # A wolf image should be approved for this multi-canid post
    image = {"subject": "gray wolf", "category": "wolf", "confidence": 0.92}
    status, reason = evaluate_guard(post, image, similarity=0.78)
    assert status == "approved"


# ---------- Embeddings Module Tests ----------

def test_generate_embedding_empty_text():
    with pytest.raises(ValueError):
        generate_embedding("   ")


@patch("app.embeddings.ollama.Client")
@patch("app.embeddings.log_ai_call")
def test_generate_embedding_success(mock_log, mock_client_cls):
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.embedding = [0.1] * 384
    mock_client.embeddings.return_value = mock_response
    mock_client_cls.return_value = mock_client

    emb = generate_embedding("A test caption")
    assert len(emb) == 384
    assert mock_log.called


# ---------- Matching Engine Unit Tests ----------

@patch("app.matching.run_query_one")
def test_match_images_post_not_found(mock_query_one):
    mock_query_one.return_value = None
    with pytest.raises(ValueError, match="Post 9999 not found"):
        match_images_for_post(9999)


@patch("app.matching.persist_suggestion")
@patch("app.matching.get_or_create_post_embedding")
@patch("app.matching.run_query")
@patch("app.matching.run_query_one")
def test_match_images_for_post_with_candidates(
    mock_query_one, mock_query, mock_post_emb, mock_persist
):
    mock_query_one.return_value = {
        "id": 1,
        "title": "The Behavior of Red Foxes in the Wild",
        "content": "Foxes are solitary...",
        "created_at": "2026-09-23T10:00:00",
    }
    mock_post_emb.return_value = [1.0, 0.0]

    # Two candidate images: one fox (matches), one wolf (mismatch)
    mock_query.return_value = [
        {
            "id": 101,
            "filename": "fox_01.jpg",
            "path": "data/images/fox_01.jpg",
            "subject": "red fox",
            "category": "fox",
            "attributes": ["alert"],
            "caption": "Red fox in field",
            "confidence": 0.95,
            "embedding": "[0.9, 0.1]",
            "status": "processed",
            "created_at": "2026-09-23T10:00:00",
        },
        {
            "id": 102,
            "filename": "wolf_01.jpg",
            "path": "data/images/wolf_01.jpg",
            "subject": "gray wolf",
            "category": "wolf",
            "attributes": ["howling"],
            "caption": "Gray wolf howling",
            "confidence": 0.92,
            "embedding": "[0.8, 0.2]",
            "status": "processed",
            "created_at": "2026-09-23T10:00:00",
        },
    ]

    result = match_images_for_post(1, top_k=2)

    assert result["status"] == "matched"
    assert result["best_match"] is not None
    assert result["best_match"]["image"]["id"] == 101
    assert result["best_match"]["guard_status"] == "approved"

    # Verify wolf was rejected by guard
    wolf_match = [m for m in result["matches"] if m["image"]["id"] == 102][0]
    assert wolf_match["guard_status"] == "rejected"
    assert "subject mismatch" in wolf_match["reason"].lower()
