from __future__ import annotations

from scrapers.models import Category, ScrapeRecord
from scrapers.rss_utils import BBC_FOOTBALL_RSS, fetch_rss_url


def fetch_bbc_football_rss(
    max_items: int = 30, delay_s: float = 0.3
) -> list[ScrapeRecord]:
    return fetch_rss_url(
        BBC_FOOTBALL_RSS,
        category=Category.STATS.value,
        source_label="bbc_sport_football",
        max_items=max_items,
        delay_s=delay_s,
    )
