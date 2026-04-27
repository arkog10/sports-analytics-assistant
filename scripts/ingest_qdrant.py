from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from app.config import get_settings
from app.ingest import full_ingest


def main() -> None:
    p = argparse.ArgumentParser(
        description="Load JSONL, embed, upsert to Qdrant. Use --rescrape to run RSS scrapers first.",
    )
    p.add_argument(
        "--rescrape",
        action="store_true",
        help="Run BBC + Pickswise scrapers before writing JSONL and upserting",
    )
    args = p.parse_args()
    s = get_settings()
    n, path = full_ingest(rescrape=args.rescrape, settings=s)
    print(f"path={path} points_upserted={n}")


if __name__ == "__main__":
    main()
