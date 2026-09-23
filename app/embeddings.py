"""
Text embedding module — generates 384-dimensional dense vectors using Ollama (all-minilm)
and logs AI calls to the database.
"""

import json
import logging
import time
from typing import Optional

import ollama
from app.config import settings
from app.database import run_query, run_query_one, run_execute
from app.vision import log_ai_call

logger = logging.getLogger(__name__)


def generate_embedding(text: str) -> list[float]:
    """
    Generate a 384-dimensional dense vector for a given text prompt
    using Ollama's all-minilm embedding model.
    """
    if not text or not text.strip():
        raise ValueError("Cannot generate embedding for empty text")

    client = ollama.Client(host=settings.ollama_host)
    t0 = time.time()
    try:
        response = client.embeddings(model=settings.embedding_model, prompt=text.strip())
        duration_ms = int((time.time() - t0) * 1000)

        # Log AI call
        log_ai_call(
            operation="embedding",
            model=settings.embedding_model,
            duration_ms=duration_ms,
            input_tokens=None,
            output_tokens=None,
            estimated_cost=0.0,
        )

        if isinstance(response, dict):
            embedding = response["embedding"]
        else:
            embedding = response.embedding

        return list(embedding)
    except Exception as e:
        logger.exception("Failed to generate embedding for text '%s...': %s", text[:40], e)
        raise


def get_or_create_post_embedding(post_id: int) -> list[float]:
    """
    Retrieve existing embedding for a post, or generate and persist it if missing.
    """
    post = run_query_one("SELECT id, title, content, embedding FROM posts WHERE id = %s", (post_id,))
    if not post:
        raise ValueError(f"Post {post_id} not found")

    if post.get("embedding"):
        return json.loads(post["embedding"])

    text_to_embed = f"{post['title']} {post['content']}".strip()
    embedding = generate_embedding(text_to_embed)

    run_execute(
        "UPDATE posts SET embedding = %s WHERE id = %s",
        (json.dumps(embedding), post_id),
    )
    logger.info("Generated and saved embedding for post %d (%s)", post_id, post["title"])
    return embedding


def get_or_create_image_embedding(image_id: int) -> Optional[list[float]]:
    """
    Retrieve existing embedding for an image caption, or generate and persist it if missing.
    """
    image = run_query_one("SELECT id, caption, embedding FROM images WHERE id = %s", (image_id,))
    if not image:
        return None

    if image.get("embedding"):
        return json.loads(image["embedding"])

    caption = image.get("caption")
    if not caption:
        return None

    embedding = generate_embedding(caption)
    run_execute(
        "UPDATE images SET embedding = %s WHERE id = %s",
        (json.dumps(embedding), image_id),
    )
    logger.info("Generated and saved embedding for image %d", image_id)
    return embedding


def embed_all_posts() -> int:
    """
    Generate embeddings for all posts that do not yet have one.
    Returns the number of posts embedded.
    """
    posts = run_query("SELECT id FROM posts WHERE embedding IS NULL ORDER BY id")
    for post in posts:
        get_or_create_post_embedding(post["id"])
    return len(posts)
