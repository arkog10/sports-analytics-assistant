from __future__ import annotations

from scrapers.models import Category, ScrapeRecord
from scrapers.rss_utils import PICKSWISE_RSS, fetch_rss_url


def fetch_pickswise_betting_rss(
    max_items: int = 30, delay_s: float = 0.3
) -> list[ScrapeRecord]:
    return fetch_rss_url(
        PICKSWISE_RSS,
        category=Category.BETTING.value,
        source_label="pickswise",
        max_items=max_items,
        delay_s=delay_s,
    )
