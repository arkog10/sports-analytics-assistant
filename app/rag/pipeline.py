from __future__ import annotations

from app.config import get_settings
from app.rag.embedding import encode_texts
from app.rag.llm import groq_chat
from app.rag.qdrant_store import search_similar
from app.rag.live_sports_web import (
    extra_web_queries_for_factual_sports,
    looks_like_live_sports_numbers_question,
    news_query_for_factual_sports,
)
from app.rag.web_search import merge_news_after, merge_web_snippets_from_queries
from app.schemas import AskResponse, CitationItem

_SYSTEM = (
    "Sports assistant. The user message includes numbered passages: your **saved article index** "
    "and/or **web search snippets**, labeled [1], [2], … When you cite them, say **the sources above**, "
    "**source [n]**, or **the indexed/web sources** — never use vague phrases like "
    "\"the information provided\" or \"the given text.\" "
    "For questions about who leads, standings, tables, point gaps, scores, or current-season stats: "
    "**Start with a direct, plain answer in the first sentence** (names, numbers, and units). "
    "Do not only point the user to sources or articles; synthesize the facts. "
    "If the context blocks do not include the specific numbers, say that clearly, then give the best "
    "supported summary; do not invent scores or tables. "
    "Cite [n] for any claim drawn from a block. If the index misses the topic, use web + careful "
    "general knowledge. Be concise. End with: Sources used: [n,…] or general knowledge."
)

_EXCERPT = 300
_KB_BODY_MAX = 500
_WEB_BODY_MAX = 450
_MAX_USER_CHARS = 8000


def _trim(s: str, limit: int) -> str:
    t = (s or "").strip()
    if len(t) <= limit:
        return t
    return t[: limit - 1] + "…"


def _excerpt(s: str) -> str:
    s = s.strip()
    if len(s) <= _EXCERPT:
        return s
    return s[: _EXCERPT - 1] + "…"


def run_rag(
    query: str,
    *,
    top_k: int | None = None,
    use_web: bool = True,
) -> AskResponse:
    settings = get_settings()
    if not (settings.groq_api_key or "").strip():
        raise ValueError("GROQ_API_KEY is not set")
    k = top_k or settings.assistant_top_k

    hits: list[tuple[float, dict]] = []
    try:
        (qv,) = encode_texts([query], batch_size=1, show_progress=False)
        hits = search_similar(qv, k, settings=settings)
    except Exception:  # noqa: BLE001
        hits = []

    web_snippets: list[dict] = []
    if use_web and settings.web_search_enabled:
        wq = [query]
        for ex in extra_web_queries_for_factual_sports(query):
            if ex.lower() not in {x.lower() for x in wq}:
                wq.append(ex)
        nq = len(wq)
        if nq == 1:
            per = max(1, settings.web_search_max_results)
        else:
            per = max(2, min(4, max(8 // nq, 2)))
        web_snippets = merge_web_snippets_from_queries(
            wq, max_per_query=per, cap_total=12
        )
        n_news = 2 if looks_like_live_sports_numbers_question(query) else 0
        if n_news and (nq1 := news_query_for_factual_sports(query)):
            web_snippets = merge_news_after(
                web_snippets, nq1, max_results=n_news, cap_total=12
            )

    blocks: list[str] = []
    citations: list[CitationItem] = []
    n = 1

    for _score, p in hits:
        raw_title = p.get("title")
        title_str = (
            raw_title
            if isinstance(raw_title, str) and raw_title.strip()
            else None
        )
        display = title_str or ((p.get("text") or "")[:80] or "Source")
        url = str(p.get("source_url", ""))
        body = _trim(str(p.get("text") or ""), _KB_BODY_MAX)
        cat = str(p.get("category", ""))
        blocks.append(
            f"[{n}] (knowledge base) title: {display!s}\n"
            f"source_url: {url}\ncategory: {cat}\ncontent:\n{body}\n"
        )
        citations.append(
            CitationItem(
                id=n,
                source="knowledge_base",
                source_url=url,
                title=title_str,
                category=cat,
                text_excerpt=_excerpt(body),
            )
        )
        n += 1

    for w in web_snippets:
        title = (w.get("title") or "Web result").strip()
        url = str(w.get("url") or "")
        body = _trim(str(w.get("body") or ""), _WEB_BODY_MAX)
        blocks.append(
            f"[{n}] (web search) title: {title!s}\n"
            f"source_url: {url}\ncontent:\n{body}\n"
        )
        citations.append(
            CitationItem(
                id=n,
                source="web",
                source_url=url or "https://duckduckgo.com/",
                title=title or None,
                category="web",
                text_excerpt=_excerpt(body),
            )
        )
        n += 1

    preamble = ""
    if not hits and not web_snippets:
        preamble = (
            "No indexed documents and no web snippets were retrieved. "
            "Answer using accurate general sports knowledge and state that your answer is not sourced to the knowledge base or live search.\n\n"
        )
    elif not hits:
        preamble = (
            "The knowledge base had no close matches; rely on the web snippets below and general knowledge as needed.\n\n"
        )

    ctx_core = (
        preamble
        + "Context blocks (same [n] numbers for citations):\n\n"
        + ("\n\n".join(blocks) if blocks else "(No context blocks.)")
    )
    suffix = f"\n\nUser question: {query}"
    if len(ctx_core) + len(suffix) > _MAX_USER_CHARS:
        keep = _MAX_USER_CHARS - len(suffix) - 120
        ctx_core = (
            ctx_core[:keep]
            + "\n\n[Context truncated to stay within model limits.]\n"
        )
    user_content = ctx_core + suffix
    answer = groq_chat(
        system=_SYSTEM,
        user=user_content,
        model=settings.groq_model,
        api_key=settings.groq_api_key.strip(),
        max_tokens=settings.groq_max_output_tokens,
    )
    if not (answer and answer.strip()):
        answer = "The model returned an empty response; try again or check the Groq model id."
    return AskResponse(
        answer=answer.strip(), citations=citations, model=settings.groq_model
    )
