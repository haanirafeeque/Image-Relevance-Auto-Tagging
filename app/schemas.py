"""
Pydantic schemas — define the shape of data going in and out of the API.

These are NOT database models. They validate request/response data
so we never send or receive garbage.
"""

from pydantic import BaseModel, Field
from typing import Optional, Union
from datetime import datetime


# ---------- Vision output (from AI model) ----------

class VisionOutput(BaseModel):
    """What the vision model returns after analyzing an image."""
    subject: str = Field(..., description="Main subject, e.g. 'red fox'")
    category: str = Field(..., description="Category, e.g. 'fox'")
    attributes: list[str] = Field(..., description="Descriptive tags")
    caption: str = Field(..., description="One-sentence description")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model confidence")


# ---------- Image ----------

class ImageResponse(BaseModel):
    """Image data returned by the API."""
    id: int
    filename: str
    path: str
    subject: Optional[str] = None
    category: Optional[str] = None
    attributes: Optional[list[str]] = None
    caption: Optional[str] = None
    confidence: Optional[float] = None
    status: str
    created_at: Union[datetime, str]


# ---------- Post ----------

class PostResponse(BaseModel):
    """Blog post data returned by the API."""
    id: int
    title: str
    content: str
    created_at: Union[datetime, str]


# ---------- Suggestion ----------

class SuggestionResponse(BaseModel):
    """A suggested image-post match with guard results."""
    id: int
    post_id: int
    image_id: int
    similarity: float
    guard_status: str
    reason: Optional[str] = None
    review_status: str
    created_at: Union[datetime, str]


# ---------- Ranked image result ----------

class RankedImage(BaseModel):
    """A single ranked image candidate for a post."""
    rank: int
    image: ImageResponse
    similarity: float
    guard_status: str
    reason: Optional[str] = None


class MatchResult(BaseModel):
    """The full matching result for a post."""
    post: PostResponse
    matches: list[RankedImage]
    best_match: Optional[RankedImage] = None
    status: str  # "matched", "no_confident_match"


# ---------- Job ----------

class JobResponse(BaseModel):
    """Batch processing job status."""
    id: int
    status: str
    total: int
    processed: int
    failed: int
    created_at: Union[datetime, str]


# ---------- AI log ----------

class AILogResponse(BaseModel):
    """Record of a single AI model call."""
    id: int
    operation: str
    model: str
    duration_ms: Optional[int] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    estimated_cost: float
    created_at: Union[datetime, str]
