"""Crossref provider: DOI metadata search (no key; polite mailto supported)."""

from __future__ import annotations

import re

from .base import Hit, HttpProvider, contact_email
from engine import util

_TAG_RE = re.compile(r"<[^>]+>")


def _strip_jats(text: str | None) -> str | None:
    if not text:
        return None
    plain = _TAG_RE.sub(" ", text)
    return " ".join(plain.split())


class CrossrefProvider(HttpProvider):
    name = "crossref"
    doc_types = ("paper", "dataset")
    base_url = "https://api.crossref.org"

    def search(self, query: str, limit: int = 10, timeout: float = 25.0,
               opts: dict | None = None) -> list[Hit]:
        params = {"query": query, "rows": min(max(limit, 1), 50)}
        mailto = contact_email()
        if mailto:
            params["mailto"] = mailto
        data = self._get_json(self.base_url + "/works", params, timeout)
        items = ((data.get("message") or {}).get("items")) or []
        hits: list[Hit] = []
        for item in items:
            doi = item.get("DOI")
            title = (item.get("title") or [None])[0]
            authors = []
            for a in (item.get("author") or [])[:12]:
                nm = " ".join(x for x in [a.get("given"), a.get("family")] if x)
                if nm:
                    authors.append(nm)
            issued = None
            for key in ("issued", "published", "published-print", "published-online"):
                dp = (item.get(key) or {}).get("date-parts")
                if dp and dp[0]:
                    issued = "-".join(str(x).rjust(2, "0") for x in dp[0][:3])
                    break
            venue = (item.get("container-title") or [None])[0]
            hits.append(Hit(
                title=title,
                url="https://doi.org/" + util.normalize_doi(doi) if doi else None,
                doi=util.normalize_doi(doi) if doi else None,
                platform=self.name,
                published_at=util.parse_date_loose(issued),
                authors=authors,
                doc_type="dataset" if item.get("type") == "dataset" else "paper",
                abstract=_strip_jats(item.get("abstract")),
                extra={"venue": venue, "type": item.get("type"),
                       "is_referenced_by_count": item.get("is-referenced-by-count")},
            ))
        return hits
