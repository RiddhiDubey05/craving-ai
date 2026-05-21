"""
Application configuration loaded from environment variables.
Uses pydantic-settings for validation and type-coercion.
"""
from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── AWS ──────────────────────────────────────────────────────────────────
    aws_access_key_id: str = Field(default="", alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str = Field(default="", alias="AWS_SECRET_ACCESS_KEY")
    aws_region: str = Field(default="us-east-1", alias="AWS_REGION")
    s3_bucket_name: str = Field(default="restaurant-images", alias="S3_BUCKET_NAME")

    # ── Bedrock ───────────────────────────────────────────────────────────────
    bedrock_region: str = Field(default="us-east-1", alias="BEDROCK_REGION")
    bedrock_llm_model_id: str = Field(
        default="anthropic.claude-3-5-sonnet-20241022-v2:0",
        alias="BEDROCK_LLM_MODEL_ID",
    )
    bedrock_embedding_model_id: str = Field(
        default="amazon.titan-embed-image-v1",
        alias="BEDROCK_EMBEDDING_MODEL_ID",
    )

    # ── FAISS ─────────────────────────────────────────────────────────────────
    faiss_index_path: str = Field(default="./data/faiss_index", alias="FAISS_INDEX_PATH")
    faiss_top_k: int = Field(default=5, alias="FAISS_TOP_K")

    # ── App ───────────────────────────────────────────────────────────────────
    app_env: str = Field(default="development", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    cors_origins: str = Field(
        default="http://localhost:5173,http://localhost:3000",
        alias="CORS_ORIGINS",
    )
    
    # ── Email / SMTP ──────────────────────────────────────────────────────────
    smtp_email: str = Field(default="", alias="SMTP_EMAIL")
    smtp_password: str = Field(default="", alias="SMTP_PASSWORD")


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance — call this everywhere."""
    return Settings()
