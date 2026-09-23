"""
Unit and integration tests for Phase 3: Vision Processing & Image Understanding.
"""

import json
from unittest.mock import patch, MagicMock
import pytest
from pydantic import ValidationError

from app.schemas import VisionOutput, JobResponse, AILogResponse
from app.vision import clean_json_text, analyze_image
from app.jobs import process_image_record


# ---------- Schema Validation Tests ----------

def test_vision_output_valid():
    data = {
        "subject": "red fox",
        "category": "fox",
        "attributes": ["orange fur", "alert", "forest"],
        "caption": "A red fox in the forest",
        "confidence": 0.95,
    }
    output = VisionOutput(**data)
    assert output.subject == "red fox"
    assert output.category == "fox"
    assert len(output.attributes) == 3
    assert output.confidence == 0.95


def test_vision_output_invalid_confidence():
    data = {
        "subject": "red fox",
        "category": "fox",
        "attributes": ["orange fur"],
        "caption": "A red fox",
        "confidence": 1.5,  # Invalid: > 1.0
    }
    with pytest.raises(ValidationError):
        VisionOutput(**data)


def test_clean_json_text():
    raw_markdown = '```json\n{"subject": "gray wolf", "category": "wolf", "attributes": ["wild"], "caption": "Wolf", "confidence": 0.9}\n```'
    cleaned = clean_json_text(raw_markdown)
    data = json.loads(cleaned)
    assert data["subject"] == "gray wolf"

    plain_json = '{"subject": "brown bear", "category": "bear", "attributes": ["large"], "caption": "Bear", "confidence": 0.88}'
    cleaned2 = clean_json_text(plain_json)
    data2 = json.loads(cleaned2)
    assert data2["subject"] == "brown bear"


# ---------- Vision Module Unit Tests ----------

def test_analyze_image_file_not_found():
    with pytest.raises(FileNotFoundError):
        analyze_image("non_existent_image_12345.jpg")


@patch("app.vision.ollama.Client")
@patch("app.vision.log_ai_call")
def test_analyze_image_success(mock_log, mock_client_cls, tmp_path):
    # Create dummy image file
    dummy_img = tmp_path / "test.jpg"
    dummy_img.write_text("dummy")

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.message.content = json.dumps({
        "subject": "golden retriever",
        "category": "dog",
        "attributes": ["golden coat", "playful"],
        "caption": "A cheerful golden retriever outdoors",
        "confidence": 0.92,
    })
    mock_response.prompt_eval_count = 100
    mock_response.eval_count = 45
    mock_client.chat.return_value = mock_response
    mock_client_cls.return_value = mock_client

    result = analyze_image(str(dummy_img), max_retries=1)

    assert result.subject == "golden retriever"
    assert result.category == "dog"
    assert result.confidence == 0.92
    assert mock_log.called


@patch("app.vision.ollama.Client")
def test_analyze_image_retry_and_fail(mock_client_cls, tmp_path):
    dummy_img = tmp_path / "test.jpg"
    dummy_img.write_text("dummy")

    mock_client = MagicMock()
    mock_client.chat.side_effect = Exception("Ollama connection timed out")
    mock_client_cls.return_value = mock_client

    with pytest.raises(RuntimeError):
        analyze_image(str(dummy_img), max_retries=2)


# ---------- Job Processor Unit Tests ----------

@patch("app.jobs.generate_embedding")
@patch("app.jobs.run_query_one")
@patch("app.jobs.run_execute")
@patch("app.jobs.analyze_image")
def test_process_image_record_processed(mock_analyze, mock_execute, mock_query, mock_emb):
    mock_emb.return_value = [0.1] * 384
    mock_query.return_value = {
        "id": 1,
        "filename": "fox_01.jpg",
        "path": "data/images/fox_01.jpg",
        "status": "pending",
    }
    mock_analyze.return_value = VisionOutput(
        subject="red fox",
        category="fox",
        attributes=["bushy tail", "orange"],
        caption="A red fox",
        confidence=0.85,
    )

    success = process_image_record(1)
    assert success is True
    # Verify UPDATE with status='processed' and embedding present
    calls = mock_execute.call_args_list
    assert len(calls) == 1
    args = calls[0][0][1]
    assert args[5] is not None  # embedding_json
    assert args[6] == "processed"  # status param


@patch("app.jobs.generate_embedding")
@patch("app.jobs.run_query_one")
@patch("app.jobs.run_execute")
@patch("app.jobs.analyze_image")
def test_process_image_record_low_confidence(mock_analyze, mock_execute, mock_query, mock_emb):
    mock_emb.return_value = [0.1] * 384
    mock_query.return_value = {
        "id": 2,
        "filename": "blurry_01.jpg",
        "path": "data/images/blurry_01.jpg",
        "status": "pending",
    }
    mock_analyze.return_value = VisionOutput(
        subject="unknown canine",
        category="dog",
        attributes=["blurry"],
        caption="Blurry animal",
        confidence=0.45,  # Below 0.60 threshold
    )

    success = process_image_record(2)
    assert success is True
    # Verify status is 'low_confidence'
    args = mock_execute.call_args[0][1]
    assert args[6] == "low_confidence"
