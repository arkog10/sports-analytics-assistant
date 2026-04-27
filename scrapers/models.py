from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
import json


class Category(str, Enum):
    STATS = "stats"
    BETTING = "betting"


@dataclass
class ScrapeRecord:
    text: str
    source_url: str
    timestamp: str  # ISO 8601
    category: str  # "stats" | "betting"
    title: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "text": self.text,
            "source_url": self.source_url,
            "timestamp": self.timestamp,
            "category": self.category,
        }
        if self.title is not None:
            d["title"] = self.title
        if self.extra:
            d["extra"] = self.extra
        return d

    def to_json_line(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False) + "\n"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )
