from __future__ import annotations

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)
    top_k: int | None = Field(
        default=None, ge=1, le=32, description="Override default number of saved chunks to retrieve"
    )
    use_web: bool = Field(
        default=True,
        description="If true, run web search and merge with indexed context",
    )


class CitationItem(BaseModel):
    id: int
    source: str = Field(
        default="knowledge_base",
        description='"knowledge_base" (Qdrant) or "web" (search snippet)',
    )
    source_url: str
    title: str | None = None
    category: str
    text_excerpt: str = Field(
        default="",
        description="Short slice of retrieved chunk for the UI / transparency",
    )


class AskResponse(BaseModel):
    answer: str
    citations: list[CitationItem]
    model: str


class IngestRequest(BaseModel):
    rescrape: bool = Field(
        default=True, description="If true, run RSS scrapers before loading JSONL"
    )


class IngestResponse(BaseModel):
    points_upserted: int
    scraped_path: str
    message: str = ""
