"""SearXNG provider: local self-hosted meta-search via JSON API (loopback only)."""

from __future__ import annotations

import socket

from .base import Hit, HttpProvider
from engine import util

DEFAULT_BASE = "http://127.0.0.1:8080"
_CATEGORIES = ("general", "news", "science", "it", "files")


class SearxngProvider(HttpProvider):
    name = "searxng"
    doc_types = ("webpage", "news")

    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url or DEFAULT_BASE).rstrip("/")

    def available(self) -> str | None:
        try:
            host, port = "127.0.0.1", 8080
            u = self.base_url.split("//", 1)[-1]
            if ":" in u:
                host, port_s = u.split(":", 1)
                port = int(port_s.split("/")[0])
            with socket.create_connection((host, port), timeout=2):
                return None
        except OSError:
            return "SearXNG not reachable at " + self.base_url + " (is the container running?)"

    def search(self, query: str, limit: int = 10, timeout: float = 25.0,
               opts: dict | None = None) -> list[Hit]:
        opts = opts or {}
        category = opts.get("category", "general")
        if category not in _CATEGORIES:
            category = "general"
        params = {
            "q": query,
            "format": "json",
            "categories": category,
            "pageno": int(opts.get("pageno", 1)),
        }
        if opts.get("language"):
            params["language"] = opts["language"]
        if opts.get("time_range") in ("day", "week", "month", "year"):
            params["time_range"] = opts["time_range"]
        data = self._get_json(self.base_url + "/search", params, timeout)
        hits: list[Hit] = []
        for r in (data.get("results") or [])[: limit if limit else None]:
            hits.append(Hit(
                title=r.get("title"),
                url=r.get("url"),
                snippet=r.get("content"),
                platform=self.name,
                published_at=util.parse_date_loose(r.get("publishedDate")),
                doc_type="news" if r.get("category") == "news" else "webpage",
                extra={"engine": r.get("engine"), "category": r.get("category"),
                       "searxng_score": r.get("score")},
            ))
        return hits
