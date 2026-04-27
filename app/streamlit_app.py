"""Streamlit UI for Sports Analytics Assistant; calls POST /ask on the API."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import requests
import streamlit as st
from pydantic import ValidationError

from app.schemas import AskRequest

DEFAULT_API = "http://127.0.0.1:8000"
api_base = os.environ.get("API_BASE_URL", DEFAULT_API).rstrip("/")
ASK_URL = urljoin(api_base + "/", "ask")
INGEST_URL = urljoin(api_base + "/", "ingest")
HEALTH_URL = urljoin(api_base + "/", "health")
_ASK_TIMEOUT = float(os.environ.get("STREAMLIT_ASK_TIMEOUT", "300"))

st.set_page_config(page_title="Sports Analytics Assistant", layout="wide", page_icon="🏟️")

st.markdown(
    """
    <style>
    div[data-testid="stSidebarUserContent"] .stMarkdown p { font-size: 0.95rem; line-height: 1.45; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Sports Analytics Assistant")
st.caption(
    "Ask about sports using saved articles and optional live web search."
)

with st.sidebar:
    st.toggle(
        "Include web search",
        value=True,
        key="streamlit_include_web",
        help="When on, Sports Analytics Assistant uses live web search plus saved articles. Off = saved articles only.",
    )
    st.divider()
    if st.button("Refresh data", use_container_width=True, type="primary"):
        with st.spinner("Updating saved articles…"):
            try:
                r = requests.post(
                    INGEST_URL,
                    json={"rescrape": True},
                    timeout=600,
                )
                r.raise_for_status()
                d = r.json()
                n = d.get("points_upserted", 0)
                st.success(f"Updated {n} article(s) in the index.")
            except OSError as e:
                st.error(f"Could not connect: {e}")
            except requests.HTTPError as e:
                t = e.response.text[:2000] if e.response is not None else str(e)
                st.error(f"Something went wrong ({e.response.status_code if e.response else ''}): {t}")


def _ask_request_payload(query: str) -> dict[str, Any]:
    text = (query or "").strip()
    return AskRequest(
        query=text,
        use_web=bool(st.session_state.get("streamlit_include_web", True)),
    ).model_dump(mode="json", exclude_none=True)


def _post_ask_json(body: dict[str, Any]) -> requests.Response:
    return requests.post(
        ASK_URL,
        json=body,
        timeout=_ASK_TIMEOUT,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )


def _format_http_err(e: BaseException) -> str:
    r = getattr(e, "response", None)
    if r is not None:
        try:
            d = r.json()
        except Exception:  # noqa: BLE001
            d = None
        if isinstance(d, dict) and d.get("detail") is not None:
            return f"**HTTP {r.status_code}** — {d['detail']}"
        return f"**HTTP {r.status_code}** — {r.text[:4000]}"
    return f"**Error:** {e!s}"


def _citation_block_md(cites: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for c in cites:
        u = c.get("source_url", "#")
        title = c.get("title") or u
        src = c.get("source", "knowledge_base")
        label = "Saved article" if src == "knowledge_base" else "Web"
        cat = c.get("category", "")
        exc = (c.get("text_excerpt") or "").replace("\n", " ")
        if len(exc) > 220:
            exc = exc[:219] + "…"
        lines.append(
            f"- [{c.get('id', '')}] {label} — [{title}]({u}){f' — {cat}' if cat else ''}  \n  {exc}"
        )
    return "\n\n".join(lines)


def _render_ask_response_body(data: dict[str, Any]) -> None:
    st.markdown(data.get("answer", "") or "")
    cites = data.get("citations") or []
    if isinstance(cites, list) and len(cites) > 0:
        with st.expander(f"Sources · {len(cites)} link(s)", expanded=False):
            st.caption("Saved articles and web results used for this answer.")
            st.markdown(_citation_block_md(cites))


def _render_assistant_turn(m: dict[str, Any]) -> None:
    if m.get("error"):
        st.error(m.get("content", "") or "")
        return
    if "ask_response" in m:
        _render_ask_response_body(m["ask_response"])
        return
    st.markdown(m.get("content", "") or "")
    cites = m.get("citations")
    if isinstance(cites, list) and len(cites) > 0:
        with st.expander(f"Sources · {len(cites)} link(s)", expanded=False):
            st.markdown(_citation_block_md(cites))


if "messages" not in st.session_state:
    st.session_state.messages: list[dict[str, Any]] = []


def _check_health() -> bool:
    try:
        r = requests.get(HEALTH_URL, timeout=8)
        return r.status_code == 200
    except OSError:
        return False


st.divider()
if not _check_health():
    st.warning(
        f"Can’t reach the assistant service at {api_base}. "
        "Start the API from the project folder: `uvicorn app.main:app --reload`"
    )
else:
    st.success("Sports Analytics Assistant — API connected", icon="✅")

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        if m["role"] == "user":
            st.markdown(m.get("content", ""))
        else:
            _render_assistant_turn(m)

q = st.chat_input("Ask anything about sports or betting…", key="user_question")
if q:
    try:
        payload = _ask_request_payload(q)
    except ValidationError as e:
        st.error(f"**Invalid question:** {e!s}")
        st.stop()
    with st.chat_message("user"):
        st.markdown(payload["query"])
    with st.chat_message("assistant"):
        with st.spinner("Looking up sources and writing an answer…"):
            try:
                r = _post_ask_json(payload)
                r.raise_for_status()
                data: dict[str, Any] = r.json()
                _render_ask_response_body(data)
                st.session_state.messages.append(
                    {"role": "user", "content": payload["query"]}
                )
                st.session_state.messages.append(
                    {"role": "assistant", "ask_response": data}
                )
            except requests.HTTPError as e:
                tail = _format_http_err(e)
                st.error(tail)
                st.session_state.messages.append(
                    {"role": "user", "content": payload["query"]}
                )
                st.session_state.messages.append(
                    {"role": "assistant", "content": tail, "error": True}
                )
            except OSError as e:
                tail = f"**Connection issue:** {e!s}"
                st.error(tail)
                st.session_state.messages.append(
                    {"role": "user", "content": payload["query"]}
                )
                st.session_state.messages.append(
                    {"role": "assistant", "content": tail, "error": True}
                )
            except Exception as e:  # noqa: BLE001
                tail = (
                    _format_http_err(e)
                    if getattr(e, "response", None)
                    else f"**Error:** {e!s}"
                )
                st.error(tail)
                st.session_state.messages.append(
                    {"role": "user", "content": payload["query"]}
                )
                st.session_state.messages.append(
                    {"role": "assistant", "content": tail, "error": True}
                )
