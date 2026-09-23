"""
Vision processing module — analyzes images using local Ollama model (gemma3:4b),
extracts structured metadata, validates with Pydantic, and logs AI calls.
"""

import json
import logging
import re
import time
from pathlib import Path
from typing import Optional

import ollama
from app.config import settings
from app.database import run_execute_returning
from app.schemas import VisionOutput

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "image-understanding-v1.md"


def load_prompt() -> str:
    """Load the vision system prompt from file."""
    if not PROMPT_PATH.exists():
        raise FileNotFoundError(f"Prompt file not found at: {PROMPT_PATH}")
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def log_ai_call(
    operation: str,
    model: str,
    duration_ms: int,
    input_tokens: Optional[int] = None,
    output_tokens: Optional[int] = None,
    estimated_cost: float = 0.0,
) -> Optional[int]:
    """Record an AI call in the ai_call_logs table."""
    sql = """
        INSERT INTO ai_call_logs (operation, model, duration_ms, input_tokens, output_tokens, estimated_cost)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
    """
    row = run_execute_returning(
        sql, (operation, model, duration_ms, input_tokens, output_tokens, estimated_cost)
    )
    return row["id"] if row else None


def clean_json_text(text: str) -> str:
    """Clean markdown code fences and extraneous text from JSON response."""
    text = text.strip()
    # Strip markdown ```json ... ``` code fence if present
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        return match.group(1).strip()
    return text


def analyze_image(image_path: str, max_retries: Optional[int] = None) -> VisionOutput:
    """
    Send an image to Ollama gemma3:4b for vision understanding.

    Returns validated VisionOutput containing:
    subject, category, attributes, caption, and confidence.
    """
    path_obj = Path(image_path)
    if not path_obj.exists():
        raise FileNotFoundError(f"Image not found at {image_path}")

    prompt = load_prompt()
    retries = max_retries if max_retries is not None else settings.max_retries
    client = ollama.Client(host=settings.ollama_host)

    last_error: Optional[Exception] = None

    for attempt in range(1, retries + 1):
        t0 = time.time()
        try:
            logger.info("Analyzing image %s (attempt %d/%d)", image_path, attempt, retries)
            response = client.chat(
                model=settings.vision_model,
                messages=[{
                    "role": "user",
                    "content": prompt,
                    "images": [str(path_obj.resolve())],
                }],
                format="json",
            )
            duration_ms = int((time.time() - t0) * 1000)

            # Extract token counts
            input_tokens = getattr(response, "prompt_eval_count", None)
            output_tokens = getattr(response, "eval_count", None)
            if input_tokens is None and isinstance(response, dict):
                input_tokens = response.get("prompt_eval_count")
                output_tokens = response.get("eval_count")

            # Log the AI call
            log_ai_call(
                operation="vision",
                model=settings.vision_model,
                duration_ms=duration_ms,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                estimated_cost=0.0,
            )

            # Extract and parse content
            raw_content = ""
            if hasattr(response, "message") and hasattr(response.message, "content"):
                raw_content = response.message.content
            elif isinstance(response, dict) and "message" in response:
                raw_content = response["message"]["content"]
            else:
                raw_content = str(response)

            cleaned = clean_json_text(raw_content)
            data = json.loads(cleaned)

            # Validate against schema
            vision_output = VisionOutput(**data)
            return vision_output

        except Exception as e:
            duration_ms = int((time.time() - t0) * 1000)
            logger.warning(
                "Attempt %d/%d failed for %s: %s (took %d ms)",
                attempt,
                retries,
                image_path,
                e,
                duration_ms,
            )
            last_error = e
            if attempt < retries:
                time.sleep(2 ** (attempt - 1))

    raise RuntimeError(f"Vision processing failed for {image_path} after {retries} attempts: {last_error}")
