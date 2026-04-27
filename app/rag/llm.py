from __future__ import annotations

from groq import Groq


def _groq_err_context(e: BaseException) -> str:
    parts = [f"{type(e).__name__}: {e!s}"]
    body = getattr(e, "body", None)
    if body is not None and str(body).strip():
        parts.append(f"body={str(body)[:2500]}")
    resp = getattr(e, "response", None)
    if resp is not None and hasattr(resp, "text"):
        t = getattr(resp, "text", None)
        if t:
            parts.append(f"http_text={str(t)[:2500]}")
    return " | ".join(parts)


def groq_chat(
    *,
    system: str,
    user: str,
    model: str,
    api_key: str,
    temperature: float = 0.2,
    max_tokens: int = 1024,
) -> str:
    client = Groq(api_key=api_key)
    try:
        r = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(
            f"Groq request failed. Check GROQ_API_KEY, GROQ_MODEL, and account limits. "
            f"({_groq_err_context(e)})"
        ) from e
    msg = r.choices[0].message
    if msg and msg.content:
        return msg.content
    return ""
