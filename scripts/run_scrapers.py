from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scrapers.bbc_sport_rss import fetch_bbc_football_rss
from scrapers.cleaning import clean_records
from scrapers.pickswise_betting_rss import fetch_pickswise_betting_rss


def main() -> None:
    p = argparse.ArgumentParser(
        description="Fetch BBC + Pickswise RSS, clean, write JSONL.",
    )
    p.add_argument(
        "--out",
        type=Path,
        default=_ROOT / "data" / "scraped.jsonl",
        help="Output JSONL path (default: data/scraped.jsonl)",
    )
    p.add_argument(
        "--max-per-feed",
        type=int,
        default=30,
        help="Max items per feed",
    )
    args = p.parse_args()
    args.out = args.out.resolve()
    args.out.parent.mkdir(parents=True, exist_ok=True)

    raw: list = []
    raw.extend(
        fetch_bbc_football_rss(max_items=args.max_per_feed, delay_s=0.3)
    )
    raw.extend(
        fetch_pickswise_betting_rss(max_items=args.max_per_feed, delay_s=0.3)
    )
    cleaned = clean_records(raw)
    with open(args.out, "w", encoding="utf-8") as f:
        for r in cleaned:
            f.write(r.to_json_line())
    print(f"Wrote {len(cleaned)} records to {args.out}")


if __name__ == "__main__":
    main()
