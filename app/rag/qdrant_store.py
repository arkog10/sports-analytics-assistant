from __future__ import annotations

import uuid
from hashlib import sha256
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from app.config import Settings, get_settings

_client: QdrantClient | None = None


def get_qdrant_client(settings: Settings | None = None) -> QdrantClient:
    global _client
    s = settings or get_settings()
    if _client is None:
        kwargs: dict[str, Any] = {"url": s.qdrant_url}
        if s.qdrant_api_key:
            kwargs["api_key"] = s.qdrant_api_key
        _client = QdrantClient(**kwargs)
    return _client


def _point_id_for_row(row: dict[str, Any]) -> str:
    key = f"{row.get('source_url', '')}\n{row.get('title', '')}\n{str(row.get('text', ''))[:2000]}"
    h = sha256(key.encode("utf-8")).hexdigest()
    return str(uuid.uuid5(uuid.NAMESPACE_URL, h))


def ensure_collection(
    client: QdrantClient, name: str, vector_size: int, *, settings: Settings | None = None
) -> None:
    s = settings or get_settings()
    if not client.collection_exists(name):
        client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(
                size=vector_size, distance=Distance.COSINE
            ),
        )


def upsert_records(
    rows: list[dict[str, Any]],
    vectors: list[list[float]],
    *,
    collection: str | None = None,
    settings: Settings | None = None,
) -> int:
    if len(rows) != len(vectors):
        raise ValueError("rows and vectors length mismatch")
    s = settings or get_settings()
    name = collection or s.qdrant_collection
    client = get_qdrant_client(s)
    ensure_collection(client, name, s.vector_size, settings=s)
    points: list[PointStruct] = []
    for row, vec in zip(rows, vectors, strict=True):
        pid = _point_id_for_row(row)
        payload: dict[str, Any] = {
            "text": (row.get("text") or "")[:16000],
            "source_url": row.get("source_url", ""),
            "timestamp": row.get("timestamp", ""),
            "category": row.get("category", ""),
        }
        if row.get("title") is not None:
            payload["title"] = row.get("title")
        if row.get("extra") is not None and isinstance(row.get("extra"), dict):
            payload["extra"] = row.get("extra")
        points.append(PointStruct(id=pid, vector=vec, payload=payload))
    if points:
        client.upsert(collection_name=name, points=points)
    return len(points)


def search_similar(
    query_vector: list[float],
    limit: int,
    *,
    category: str | None = None,
    collection: str | None = None,
    settings: Settings | None = None,
) -> list[tuple[float, dict[str, Any]]]:
    s = settings or get_settings()
    name = collection or s.qdrant_collection
    client = get_qdrant_client(s)
    fl: Filter | None = None
    if category:
        fl = Filter(
            must=[FieldCondition(key="category", match=MatchValue(value=category))]
        )
    resp = client.query_points(
        collection_name=name,
        query=query_vector,
        limit=limit,
        with_payload=True,
        query_filter=fl,
    )
    out: list[tuple[float, dict[str, Any]]] = []
    for p in resp.points:
        if p.payload is not None:
            out.append((float(p.score), dict(p.payload)))
    return out
