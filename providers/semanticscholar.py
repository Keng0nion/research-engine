"""Semantic Scholar provider: paper search plus citation graph edges (no key required)."""

from __future__ import annotations

import os

from .base import Hit, HttpProvider
from engine import util

_FIELDS = "title,year,venue,externalIds,abstract,authors,openAccessPdf,publicationTypes,publicationDate,citationCount"


class SemanticScholarProvider(HttpProvider):
    name = "semanticscholar"
    doc_types = ("paper", "preprint")
    base_url = "https://api.semanticscholar.org/graph/v1"

    def _headers(self) -> dict:
        key = os.environ.get("S2_API_KEY")
        return {"x-api-key": key} if key else {}

    def _get_json_auth(self, path: str, params: dict, timeout: float) -> dict:
        import httpx
        from .base import ProviderError, http_request
        try:
            resp = http_request("GET", self.base_url + path, params=params,
                                headers=self._headers(), timeout=timeout)
        except httpx.TimeoutException as exc:
            raise ProviderError("timeout", str(exc)) from exc
        except ProviderError as exc:
            raise exc
        except httpx.HTTPError as exc:
            raise ProviderError("http_error", str(exc)) from exc
        if resp.status_code == 429:
            raise ProviderError("rate_limited", "429 from Semantic Scholar")
        if resp.status_code >= 400:
            raise ProviderError("http_error", "HTTP " + str(resp.status_code))
        try:
            return resp.json()
        except ValueError as exc:
            raise ProviderError("parse_error", "non-JSON response") from exc

    def _paper_to_hit(self, p: dict) -> Hit:
        ext = p.get("externalIds") or {}
        doi = util.normalize_doi(ext["DOI"]) if ext.get("DOI") else None
        arxiv_id = util.normalize_arxiv_id(ext["ArXiv"]) if ext.get("ArXiv") else None
        if doi:
            url = "https://doi.org/" + doi
        elif arxiv_id:
            url = "https://arxiv.org/abs/" + arxiv_id
        elif p.get("paperId"):
            url = "https://www.semanticscholar.org/paper/" + p["paperId"]
        else:
            url = None
        oa = p.get("openAccessPdf") or {}
        return Hit(
            title=p.get("title"),
            url=url,
            doi=doi,
            arxiv_id=arxiv_id,
            platform=self.name,
            published_at=p.get("publicationDate") or (str(p.get("year")) if p.get("year") else None),
            authors=[a.get("name") for a in (p.get("authors") or [])[:12] if a.get("name")],
            doc_type="paper",
            abstract=p.get("abstract"),
            extra={
                "s2_id": p.get("paperId"),
                "venue": p.get("venue"),
                "citation_count": p.get("citationCount"),
                "open_access_pdf": oa.get("url"),
            },
        )

    def search(self, query: str, limit: int = 10, timeout: float = 25.0,
               opts: dict | None = None) -> list[Hit]:
        params = {"query": query, "limit": min(max(limit, 1), 100), "fields": _FIELDS}
        data = self._get_json_auth("/paper/search", params, timeout)
        return [self._paper_to_hit(p) for p in (data.get("data") or [])]

    def references(self, paper_id: str, limit: int = 25, timeout: float = 25.0) -> list[Hit]:
        params = {"limit": min(limit, 100), "fields": _FIELDS}
        data = self._get_json_auth("/paper/" + paper_id + "/references", params, timeout)
        return [self._paper_to_hit(e.get("citedPaper") or {}) for e in (data.get("data") or [])]

    def citations(self, paper_id: str, limit: int = 25, timeout: float = 25.0) -> list[Hit]:
        params = {"limit": min(limit, 100), "fields": _FIELDS}
        data = self._get_json_auth("/paper/" + paper_id + "/citations", params, timeout)
        return [self._paper_to_hit(e.get("citingPaper") or {}) for e in (data.get("data") or [])]
