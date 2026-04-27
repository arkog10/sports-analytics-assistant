from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    groq_api_key: str = Field(default="", description="Groq API key for chat")
    groq_model: str = "llama-3.1-8b-instant"
    groq_max_output_tokens: int = 512

    qdrant_url: str = "http://127.0.0.1:6333"
    qdrant_api_key: str | None = None
    qdrant_collection: str = "sports_analytics_assistant"
    embed_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    vector_size: int = 384

    assistant_top_k: int = Field(
        default=4,
        validation_alias=AliasChoices("ASSISTANT_TOP_K", "RAG_TOP_K"),
    )
    scraped_jsonl: str = "data/scraped.jsonl"

    web_search_enabled: bool = True
    web_search_max_results: int = 3

    def jsonl_path(self) -> Path:
        p = Path(self.scraped_jsonl)
        if p.is_absolute():
            return p
        return _PROJECT_ROOT / p


@lru_cache
def get_settings() -> Settings:
    return Settings()
