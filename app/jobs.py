import json
import logging
from typing import Optional
from app.config import settings
from app.database import run_query, run_query_one, run_execute
from app.vision import analyze_image
from app.embeddings import generate_embedding

logger = logging.getLogger(__name__)


def process_image_record(image_id: int) -> bool:
    """
    Process a single image record through the vision and embedding pipeline,
    and update the database.

    Returns True on success (processed or low_confidence), False on failure.
    """
    row = run_query_one("SELECT * FROM images WHERE id = %s", (image_id,))
    if not row:
        logger.error("Image ID %d not found in database", image_id)
        return False

    try:
        vision_output = analyze_image(row["path"])

        # Determine status based on confidence threshold
        if vision_output.confidence >= settings.min_vision_confidence:
            status = "processed"
        else:
            status = "low_confidence"

        # Generate embedding for the caption
        embedding_json = None
        if vision_output.caption:
            try:
                emb = generate_embedding(vision_output.caption)
                embedding_json = json.dumps(emb)
            except Exception as emb_err:
                logger.warning("Failed to generate embedding for image %d: %s", image_id, emb_err)

        update_sql = """
            UPDATE images
            SET subject = %s,
                category = %s,
                attributes = %s,
                caption = %s,
                confidence = %s,
                embedding = %s,
                status = %s
            WHERE id = %s
        """
        run_execute(
            update_sql,
            (
                vision_output.subject,
                vision_output.category,
                vision_output.attributes,
                vision_output.caption,
                vision_output.confidence,
                embedding_json,
                status,
                image_id,
            ),
        )
        logger.info(
            "Processed image %d (%s): %s [%s] confidence=%.2f",
            image_id,
            row["filename"],
            vision_output.subject,
            status,
            vision_output.confidence,
        )
        return True

    except Exception as e:
        logger.exception("Failed to process image %d (%s): %s", image_id, row["filename"], e)
        run_execute("UPDATE images SET status = 'failed' WHERE id = %s", (image_id,))
        return False


def run_batch_processing(job_id: int, limit: Optional[int] = None) -> None:
    """
    Background worker function to process pending images sequentially.
    """
    try:
        run_execute("UPDATE jobs SET status = 'running' WHERE id = %s", (job_id,))

        if limit is not None and limit > 0:
            query = "SELECT id FROM images WHERE status = 'pending' ORDER BY id LIMIT %s"
            rows = run_query(query, (limit,))
        else:
            query = "SELECT id FROM images WHERE status = 'pending' ORDER BY id"
            rows = run_query(query)

        # Update total count for this job
        run_execute("UPDATE jobs SET total = %s WHERE id = %s", (len(rows), job_id))

        for row in rows:
            success = process_image_record(row["id"])
            if success:
                run_execute("UPDATE jobs SET processed = processed + 1 WHERE id = %s", (job_id,))
            else:
                run_execute("UPDATE jobs SET failed = failed + 1 WHERE id = %s", (job_id,))

        run_execute("UPDATE jobs SET status = 'completed' WHERE id = %s", (job_id,))
        logger.info("Batch job %d finished successfully", job_id)

    except Exception as e:
        logger.exception("Batch job %d encountered an error: %s", job_id, e)
        run_execute("UPDATE jobs SET status = 'failed' WHERE id = %s", (job_id,))
