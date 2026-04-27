from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.ingest import full_ingest
from app.schemas import AskRequest, AskResponse, IngestRequest, IngestResponse

app = FastAPI(
    title="Sports Analytics Assistant",
    version="0.2.0",
    description="Sports Analytics Assistant API: Qdrant index, optional web search, Groq answers with citations.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str | bool]:
    s = get_settings()
    return {
        "status": "ok",
        "qdrant_target": s.qdrant_url,
        "collection": s.qdrant_collection,
        "groq_key_set": bool((s.groq_api_key or "").strip()),
        "groq_model": s.groq_model,
    }


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    from app.rag.pipeline import run_rag

    try:
        return run_rag(
            req.query, top_k=req.top_k, use_web=req.use_web
        )
    except ValueError as e:
        msg = str(e)
        if "GROQ" in msg.upper():
            raise HTTPException(status_code=503, detail=msg) from e
        raise HTTPException(status_code=400, detail=msg) from e
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e


@app.post("/ingest", response_model=IngestResponse)
def ingest(req: IngestRequest) -> IngestResponse:
    try:
        n, path = full_ingest(rescrape=req.rescrape)
        msg = "Ingestion complete."
        if n == 0:
            msg = "No points upserted. Run with rescrape=true or ensure the JSONL file has rows."
        return IngestResponse(
            points_upserted=n, scraped_path=path, message=msg
        )
    except Exception as e:  # noqa: BLE001
        raise HTTPException(
            status_code=500, detail=f"Ingestion failed: {e!s}"
        ) from e
