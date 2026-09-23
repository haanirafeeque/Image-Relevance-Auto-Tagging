"""
Matching and Guard Engine — computes semantic similarity between blog posts and images,
enforces safety guardrails, ranks candidates, and persists suggestions.
"""

import json
import logging
from typing import Optional

import numpy as np
from app.config import settings
from app.database import run_query, run_query_one, run_execute, run_execute_returning
from app.embeddings import get_or_create_post_embedding, get_or_create_image_embedding

logger = logging.getLogger(__name__)

CATEGORY_KEYWORDS = {
    "fox": ["fox", "foxes", "vixen", "kit"],
    "wolf": ["wolf", "wolves", "pack"],
    "dog": ["dog", "dogs", "puppy", "puppies", "canine", "hound", "retriever"],
    "bear": ["bear", "bears", "cub", "polar bear", "grizzly"],
}


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Calculate the cosine similarity between two float vectors."""
    a = np.array(vec_a, dtype=np.float32)
    b = np.array(vec_b, dtype=np.float32)
    norm_a = float(np.linalg.norm(a))
    norm_b = float(np.linalg.norm(b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def evaluate_guard(post: dict, image: dict, similarity: float) -> tuple[str, str]:
    """
    Check if a candidate match passes safety guardrails.

    Rules:
    1. Similarity score must meet or exceed settings.similarity_threshold.
    2. Vision model confidence must meet or exceed settings.min_vision_confidence.
    3. Image subject/category must not conflict with the post topic.

    Returns:
        (guard_status, reason) where guard_status is "approved" or "rejected".
    """
    if similarity < settings.similarity_threshold:
        return (
            "rejected",
            f"Similarity score {similarity:.2f} is below threshold {settings.similarity_threshold:.2f}",
        )

    confidence = image.get("confidence")
    if confidence is None or confidence < settings.min_vision_confidence:
        conf_str = f"{confidence:.2f}" if confidence is not None else "None"
        return (
            "rejected",
            f"Vision confidence {conf_str} is below threshold {settings.min_vision_confidence:.2f}",
        )

    post_title = (post.get("title") or "").lower()
    post_content = (post.get("content") or "").lower()
    post_text = f"{post_title} {post_content}"

    img_category = (image.get("category") or "").lower().strip()
    img_subject = (image.get("subject") or "").lower().strip()

    title_categories = {
        cat for cat, kws in CATEGORY_KEYWORDS.items()
        if any(kw in post_title for kw in kws)
    }

    if title_categories:
        if img_category and img_category not in title_categories:
            has_subject_match = any(
                kw in img_subject
                for cat in title_categories
                for kw in CATEGORY_KEYWORDS[cat]
            )
            if not has_subject_match:
                cats_str = ", ".join(sorted(title_categories))
                return (
                    "rejected",
                    f"Subject mismatch: image shows '{img_subject or img_category}' but post is about '{cats_str}'",
                )

    body_categories = {
        cat for cat, kws in CATEGORY_KEYWORDS.items()
        if any(kw in post_text for kw in kws)
    }
    if body_categories and img_category and img_category not in body_categories:
        cats_str = ", ".join(sorted(body_categories))
        return (
            "rejected",
            f"Subject mismatch: image shows '{img_subject or img_category}' but post relates to '{cats_str}'",
        )

    return ("approved", "Passed similarity, vision confidence, and subject relevance checks")


def persist_suggestion(
    post_id: int, image_id: int, similarity: float, guard_status: str, reason: str
) -> int:
    """Save or update a suggestion record in the database."""
    existing = run_query_one(
        "SELECT id FROM suggestions WHERE post_id = %s AND image_id = %s",
        (post_id, image_id),
    )
    if existing:
        run_execute(
            """
            UPDATE suggestions
            SET similarity = %s, guard_status = %s, reason = %s
            WHERE id = %s
            """,
            (similarity, guard_status, reason, existing["id"]),
        )
        return existing["id"]
    else:
        row = run_execute_returning(
            """
            INSERT INTO suggestions (post_id, image_id, similarity, guard_status, reason, review_status)
            VALUES (%s, %s, %s, %s, %s, 'pending')
            RETURNING id
            """,
            (post_id, image_id, similarity, guard_status, reason),
        )
        return row["id"] if row else 0


def match_images_for_post(post_id: int, top_k: int = 5) -> dict:
    """
    Find, rank, and guard images for a given blog post.
    Persists top suggestions into the suggestions table and returns a MatchResult dict.
    """
    post = run_query_one("SELECT * FROM posts WHERE id = %s", (post_id,))
    if not post:
        raise ValueError(f"Post {post_id} not found")

    post_embedding = get_or_create_post_embedding(post_id)

    images = run_query(
        """
        SELECT id, filename, path, subject, category, attributes, caption, confidence, embedding, status, created_at
        FROM images
        WHERE status IN ('processed', 'low_confidence') AND (embedding IS NOT NULL OR caption IS NOT NULL)
        """
    )

    candidates = []
    for img in images:
        img_embedding = None
        if img.get("embedding"):
            img_embedding = json.loads(img["embedding"])
        else:
            img_embedding = get_or_create_image_embedding(img["id"])

        if not img_embedding:
            continue

        sim = cosine_similarity(post_embedding, img_embedding)
        guard_status, reason = evaluate_guard(post, img, sim)

        img_clean = {
            "id": img["id"],
            "filename": img["filename"],
            "path": img["path"],
            "subject": img.get("subject"),
            "category": img.get("category"),
            "attributes": img.get("attributes"),
            "caption": img.get("caption"),
            "confidence": img.get("confidence"),
            "status": img["status"],
            "created_at": img["created_at"],
        }

        candidates.append({
            "image": img_clean,
            "similarity": round(sim, 4),
            "guard_status": guard_status,
            "reason": reason,
        })

    candidates.sort(key=lambda c: c["similarity"], reverse=True)

    ranked_matches = []
    best_match = None

    for rank_idx, cand in enumerate(candidates[:top_k], start=1):
        ranked_cand = {
            "rank": rank_idx,
            "image": cand["image"],
            "similarity": cand["similarity"],
            "guard_status": cand["guard_status"],
            "reason": cand["reason"],
        }
        ranked_matches.append(ranked_cand)

        persist_suggestion(
            post_id=post_id,
            image_id=cand["image"]["id"],
            similarity=cand["similarity"],
            guard_status=cand["guard_status"],
            reason=cand["reason"],
        )

        if best_match is None and cand["guard_status"] == "approved":
            best_match = ranked_cand

    post_clean = {
        "id": post["id"],
        "title": post["title"],
        "content": post["content"],
        "created_at": post["created_at"],
    }

    status = "matched" if best_match is not None else "no_confident_match"

    return {
        "post": post_clean,
        "matches": ranked_matches,
        "best_match": best_match,
        "status": status,
    }
