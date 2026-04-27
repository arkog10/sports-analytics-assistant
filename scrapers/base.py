from __future__ import annotations

import time
import requests

DEFAULT_UA = (
    "Sports-Analytics-Assistant/0.1 (educational project; +https://example.local) "
    "python-requests"
)


def get_session() -> requests.Session:
    s = requests.Session()
    s.headers.update(
        {
            "User-Agent": DEFAULT_UA,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
    )
    return s


def fetch_text(
    url: str,
    *,
    timeout: float = 30.0,
    delay_s: float = 0.0,
    session: requests.Session | None = None,
) -> str:
    if delay_s > 0:
        time.sleep(delay_s)
    sess = session or get_session()
    r = sess.get(url, timeout=timeout)
    r.raise_for_status()
    r.encoding = r.apparent_encoding or "utf-8"
    return r.text
