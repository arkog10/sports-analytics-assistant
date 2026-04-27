from __future__ import annotations

import time
import feedparser
from email.utils import parsedate_to_datetime

from scrapers.base import fetch_text, get_session
from scrapers.models import ScrapeRecord, utc_now_iso

BBC_FOOTBALL_RSS = "https://feeds.bbci.co.uk/sport/football/rss.xml"
PICKSWISE_RSS = "https://www.pickswise.com/feed/"


def _entry_timestamp_iso(entry: feedparser.FeedParserDict) -> str:
    t = entry.get("published_parsed") or entry.get("updated_parsed")
    if t:
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", t)
    raw = entry.get("published") or entry.get("updated")
    if raw:
        try:
            dt = parsedate_to_datetime(raw)
            if dt.tzinfo is None:
                from datetime import timezone

                dt = dt.replace(tzinfo=timezone.utc)
            return dt.replace(microsecond=0).isoformat().replace("+00:00", "Z")
        except (TypeError, ValueError, OverflowError):
            pass
    return utc_now_iso()


def _entry_link(entry: feedparser.FeedParserDict) -> str:
    return (entry.get("link") or entry.get("id") or "").strip()


def _entry_title(entry: feedparser.FeedParserDict) -> str:
    t = entry.get("title", "")
    if isinstance(t, str):
        return t.strip()
    return str(t or "").strip()


def _entry_summary_text(entry: feedparser.FeedParserDict) -> str:
    s = entry.get("summary", "") or ""
    c = None
    if "content" in entry and entry.content:
        c = entry.content[0].get("value", "")
    body = c if c else s
    if isinstance(body, str):
        return body.strip()
    return str(body or "").strip()


def parse_feed(
    body: str,
    *,
    category: str,
    source_label: str,
    max_items: int = 30,
) -> list[ScrapeRecord]:
    feed = feedparser.parse(body)
    out: list[ScrapeRecord] = []
    for i, entry in enumerate(feed.entries):
        if i >= max_items:
            break
        title = _entry_title(entry)
        link = _entry_link(entry)
        if not link:
            continue
        body_html = _entry_summary_text(entry)
        if not body_html and not title:
            continue
        ts = _entry_timestamp_iso(entry)
        text_for_now = f"{title}\n\n{body_html}" if title else body_html
        out.append(
            ScrapeRecord(
                text=text_for_now,
                source_url=link,
                timestamp=ts,
                category=category,
                title=title or None,
                extra={"source": source_label, "kind": "rss"},
            )
        )
    return out


def fetch_rss_url(
    url: str,
    *,
    category: str,
    source_label: str,
    max_items: int = 30,
    delay_s: float = 0.3,
) -> list[ScrapeRecord]:
    xml = fetch_text(url, delay_s=delay_s, session=get_session())
    return parse_feed(
        xml, category=category, source_label=source_label, max_items=max_items
    )
