"""Shared helpers: time, slugs, URL/DOI normalization."""

from __future__ import annotations

import datetime
import re
import unicodedata
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

# tracking params stripped during URL canonicalization
_TRACKING_PREFIXES = ("utm_", "ref_", "mc_", "pk_", "piwik_")
_TRACKING_EXACT = {
    "fbclid", "gclid", "yclid", "igshid", "spm", "from", "ref", "source",
    "src", "share_source", "share_medium", "share_plat", "share_tag", "timestamp",
}


def now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def today_compact() -> str:
    return datetime.datetime.now().strftime("%Y%m%d")


def slugify(text: str, max_len: int = 48) -> str:
    """ASCII slug for session ids; Chinese text falls back to pinyin-free hashless strip."""
    text = unicodedata.normalize("NFKD", text)
    ascii_text = text.encode("ascii", "ignore").decode("ascii")
    ascii_text = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_text).strip("-").lower()
    if not ascii_text:
        # keep CJK characters when no ASCII is available
        ascii_text = re.sub(r"[^\w\u4e00-\u9fff]+", "-", text).strip("-")[:max_len]
    return ascii_text[:max_len] or "session"


def normalize_url(url: str) -> str:
    """Lowercase host, strip fragment and tracking params; keep path & meaningful query."""
    try:
        parts = urlsplit(url.strip())
    except ValueError:
        return url.strip()
    scheme = parts.scheme.lower() or "https"
    host = parts.hostname.lower() if parts.hostname else ""
    netloc = host
    if parts.port and parts.port not in (80, 443):
        netloc = f"{host}:{parts.port}"
    path = re.sub(r"/+", "/", parts.path)
    if len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/")
    query_pairs = [
        (k, v)
        for k, v in parse_qsl(parts.query, keep_blank_values=True)
        if k not in _TRACKING_EXACT and not k.lower().startswith(_TRACKING_PREFIXES)
    ]
    query = urlencode(query_pairs)
    return urlunsplit((scheme, netloc, path, query, ""))


def normalize_doi(doi: str) -> str:
    d = doi.strip().lower()
    d = re.sub(r"^(https?://)?(dx\.)?doi\.org/", "", d)
    d = re.sub(r"^doi:", "", d)
    return d.strip().rstrip(".")


_ARXIV_RE = re.compile(r"(\d{4}\.\d{4,5})(v\d+)?$")


def normalize_arxiv_id(arxiv_id: str) -> str:
    a = arxiv_id.strip().lower()
    a = re.sub(r"^(https?://)?arxiv\.org/(abs|pdf)/", "", a)
    a = re.sub(r"\.pdf$", "", a)
    a = re.sub(r"v\d+$", "", a)
    return a


def parse_date_loose(text: str | None) -> str | None:
    """Best-effort YYYY-MM-DD or YYYY extraction from heterogeneous date strings."""
    if not text:
        return None
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", text)
    if m:
        return m.group(0)
    m = re.search(r"(\d{4})", text)
    if m:
        return m.group(1)
    return None


def truncate(text: str | None, limit: int) -> str:
    if not text:
        return ""
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"
