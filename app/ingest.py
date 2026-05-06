from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.config import Settings, get_settings
from app.rag.embedding import encode_texts
from app.rag.qdrant_store import upsert_records
from scrapers.bbc_sport_rss import fetch_bbc_football_rss
from scrapers.cleaning import clean_records
from scrapers.pickswise_betting_rss import fetch_pickswise_betting_rss


def run_scrapers_to_jsonl(path: Path) -> int:
    raw: list = []
    raw.extend(fetch_bbc_football_rss())
    raw.extend(fetch_pickswise_betting_rss())
    cleaned = clean_records(raw)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in cleaned:
            f.write(r.to_json_line())
    return len(cleaned)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def ingest_jsonl_to_qdrant(
    path: Path | None = None, *, settings: Settings | None = None
) -> int:
    s = settings or get_settings()
    p = path or s.jsonl_path()
    rows = load_jsonl(p)
    if not rows:
        return 0
    texts = [str(r.get("text", "")) for r in rows]
    vecs = encode_texts(texts, show_progress=len(texts) > 16)
    return upsert_records(rows, vecs, settings=s)


def full_ingest(*, rescrape: bool, settings: Settings | None = None) -> tuple[int, str]:
    s = settings or get_settings()
    p = s.jsonl_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    n_scraped = 0
    if rescrape:
        n_scraped = run_scrapers_to_jsonl(p)
    n = ingest_jsonl_to_qdrant(p, settings=s)
    msg = f"scraped={n_scraped}, upserted={n}" if rescrape else f"upserted={n}"
    return n, str(p)
