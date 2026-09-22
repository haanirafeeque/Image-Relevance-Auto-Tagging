"""
Configuration — loads settings from .env file.

All config values come from environment variables so we never
hardcode secrets in source code.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://postgres:password@localhost:5432/image_matching"

    # Ollama
    ollama_host: str = "http://localhost:11434"
    vision_model: str = "gemma3:4b"
    embedding_model: str = "all-minilm"

    # Matching thresholds
    similarity_threshold: float = 0.60
    min_vision_confidence: float = 0.60

    # Retry settings
    max_retries: int = 3

    class Config:
        env_file = ".env"


# Single shared settings instance used across the app
settings = Settings()
