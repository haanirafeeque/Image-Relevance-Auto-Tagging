from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:password@localhost:5432/image_matching"
    ollama_host: str = "http://localhost:11434"
    vision_model: str = "gemma3:4b"
    embedding_model: str = "all-minilm"
    similarity_threshold: float = 0.60
    min_vision_confidence: float = 0.60
    max_retries: int = 3

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
