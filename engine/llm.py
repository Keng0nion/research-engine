"""Optional LLM summarization hook (P2-12).

Disabled by default (the engine never calls a model unless explicitly
configured). Enable with three env vars:
  RE_LLM_BASE_URL   e.g. https://api.example.com/v1
  RE_LLM_MODEL      e.g. some-model
  RE_LLM_API_KEY    bearer key
For a local model (Ollama etc.) additionally set RE_LLM_ALLOW_PRIVATE=1
(private/loopback endpoints are otherwise rejected by the SSRF guard in
fetcher.safe_post_json).

Used only by `digest` to compress very long full texts. Never used for
routing, retries, or any control flow. The HTTP call lives in
fetcher.safe_post_json so the SSRF check stays in one audited place.
"""

from __future__ import annotations

import os

import httpx

from .fetcher import safe_post_json


def configured() -> bool:
    return bool(os.environ.get("RE_LLM_BASE_URL") and os.environ.get("RE_LLM_MODEL")
                and os.environ.get("RE_LLM_API_KEY"))


def maybe_summarize(text: str, max_chars: int = 4000) -> str | None:
    """Return an LLM digest of text, or None when not configured / disallowed / on failure."""
    if not configured() or not text:
        return None
    base = os.environ["RE_LLM_BASE_URL"].rstrip("/")
    url = base + "/chat/completions"
    model = os.environ["RE_LLM_MODEL"]
    key = os.environ["RE_LLM_API_KEY"]
    allow_private = os.environ.get("RE_LLM_ALLOW_PRIVATE") == "1"
    system = ("You compress research documents into a dense digest for an agent: "
              "bullet points of key claims, methods, numbers, limitations; keep exact "
              "figures; reply in the document's language; stay under " + str(max_chars) + " characters.")
    payload = {
        "model": model,
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": text[:120000]}],
        "temperature": 0.2,
        "max_tokens": 2048,
    }
    try:
        resp = safe_post_json(url, payload,
                              headers={"Authorization": "Bearer " + key},
                              timeout=90.0, allow_private=allow_private)
        if resp.status_code == 200:
            content = (((resp.json().get("choices") or [{}])[0].get("message") or {}).get("content"))
            if content:
                return content[: max_chars * 2]
    except (httpx.HTTPError, ValueError, KeyError):
        pass
    return None
