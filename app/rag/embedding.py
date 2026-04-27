from __future__ import annotations

import threading
from typing import Any

from sentence_transformers import SentenceTransformer

import app.config as _cfg

_lock = threading.Lock()
_model: SentenceTransformer | None = None


def get_embedder() -> SentenceTransformer:
    global _model
    with _lock:
        if _model is None:
            s = _cfg.get_settings()
            _model = SentenceTransformer(s.embed_model, device="cpu")
        return _model


def encode_texts(
    texts: list[str], *, batch_size: int = 32, show_progress: bool = False
) -> list[list[float]]:
    m = get_embedder()
    vecs = m.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=show_progress,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    return [v.tolist() for v in vecs]
