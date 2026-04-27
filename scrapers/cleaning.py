from __future__ import annotations

import re

from bs4 import BeautifulSoup

from scrapers.models import ScrapeRecord


def strip_html(html: str) -> str:
    if not html or not str(html).strip():
        return ""
    s = str(html)
    if "<" not in s:
        return s
    soup = BeautifulSoup(s, "lxml")
    return soup.get_text(separator="\n")


def normalize_whitespace(s: str) -> str:
    t = s.replace("\r\n", "\n").replace("\r", "\n")
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n[ \t]+", "\n", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def clean_text_field(raw: str) -> str:
    return normalize_whitespace(strip_html(raw))


def clean_record(r: ScrapeRecord) -> ScrapeRecord:
    text = clean_text_field(r.text)
    title = (r.title or "").strip() or None
    return ScrapeRecord(
        text=text,
        source_url=r.source_url,
        timestamp=r.timestamp,
        category=r.category,
        title=title,
        extra={**r.extra, "cleaned": True},
    )


def clean_records(records: list[ScrapeRecord]) -> list[ScrapeRecord]:
    return [clean_record(r) for r in records]
