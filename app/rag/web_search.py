from __future__ import annotations

from typing import Any

_MAX_BODY = 900
_MAX_WEB_BLOCKS = 14


def search_web_snippets(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    if not (query or "").strip():
        return []
    try:
        from ddgs import DDGS
    except ImportError:
        return []
    out: list[dict[str, Any]] = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query.strip(), max_results=max_results):
                body = (r.get("body") or "")[:_MAX_BODY]
                out.append(
                    {
                        "title": r.get("title") or "",
                        "url": r.get("href") or "",
                        "body": body,
                    }
                )
    except OSError:
        return out
    except Exception:  # noqa: BLE001
        return out
    return out


def search_news_snippets(query: str, max_results: int = 3) -> list[dict[str, Any]]:
    if not (query or "").strip():
        return []
    try:
        from ddgs import DDGS
    except ImportError:
        return []
    out: list[dict[str, Any]] = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.news(query.strip(), max_results=max_results):
                body = (r.get("body") or "")[:_MAX_BODY]
                out.append(
                    {
                        "title": r.get("title") or "",
                        "url": r.get("href") or "",
                        "body": body,
                    }
                )
    except OSError:
        return out
    except Exception:  # noqa: BLE001
        return out
    return out


def merge_web_snippets_from_queries(
    queries: list[str],
    *,
    max_per_query: int,
    cap_total: int = _MAX_WEB_BLOCKS,
) -> list[dict[str, Any]]:
    seen: set[str] = set()
    merged: list[dict[str, Any]] = []
    for q in queries:
        q = (q or "").strip()
        if not q:
            continue
        for r in search_web_snippets(q, max_results=max_per_query):
            u = (r.get("url") or "").strip()
            if u:
                if u in seen:
                    continue
                seen.add(u)
            elif merged and (r.get("title"), r.get("body")) == (
                merged[-1].get("title"),
                merged[-1].get("body"),
            ):
                continue
            merged.append(r)
            if len(merged) >= cap_total:
                return merged
    return merged


def merge_news_after(
    base: list[dict[str, Any]],
    news_query: str,
    *,
    max_results: int,
    cap_total: int = _MAX_WEB_BLOCKS,
) -> list[dict[str, Any]]:
    seen = {(r.get("url") or "").strip() for r in base if (r.get("url") or "").strip()}
    out = list(base)
    for r in search_news_snippets(news_query, max_results=max_results):
        u = (r.get("url") or "").strip()
        if u and u in seen:
            continue
        if u:
            seen.add(u)
        out.append(r)
        if len(out) >= cap_total:
            break
    return out
