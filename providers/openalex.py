"""OpenAlex provider: works search (no API key; polite pool via mailto)."""

from __future__ import annotations

from .base import Hit, HttpProvider, contact_email
from engine import util


def _abstract_from_inverted(inverted: dict | None) -> str | None:
    """Rebuild plain abstract text from OpenAlex abstract_inverted_index."""
    if not inverted:
        return None
    positions = []
    for word, idxs in inverted.items():
        for i in idxs:
            positions.append((i, word))
    if not positions:
        return None
    positions.sort()
    return " ".join(w for _, w in positions)


class OpenAlexProvider(HttpProvider):
    name = "openalex"
    doc_types = ("paper", "preprint", "dataset")
    base_url = "https://api.openalex.org"

    def search(self, query: str, limit: int = 10, timeout: float = 25.0,
               opts: dict | None = None) -> list[Hit]:
        params = {"search": query, "per-page": min(max(limit, 1), 50)}
        mailto = contact_email()
        if mailto:
            params["mailto"] = mailto
        data = self._get_json(self.base_url + "/works", params, timeout)
        hits: list[Hit] = []
        for item in data.get("results", []) or []:
            doi = item.get("doi")
            if doi:
                doi = util.normalize_doi(doi)
            authors = []
            for a in (item.get("authorships") or [])[:12]:
                nm = (a.get("author") or {}).get("display_name")
                if nm:
                    authors.append(nm)
            source = ((item.get("primary_location") or {}).get("source") or {})
            hits.append(Hit(
                title=item.get("display_name"),
                url=item.get("doi") or (item.get("primary_location") or {}).get("landing_page_url"),
                doi=doi,
                platform=self.name,
                published_at=item.get("publication_date"),
                authors=authors,
                doc_type="preprint" if (item.get("type") == "preprint") else "paper",
                abstract=_abstract_from_inverted(item.get("abstract_inverted_index")),
                extra={
                    "openalex_id": item.get("id"),
                    "cited_by_count": item.get("cited_by_count"),
                    "venue": source.get("display_name"),
                    "is_oa": (item.get("open_access") or {}).get("is_oa"),
                    "oa_url": (item.get("best_oa_location") or {}).get("pdf_url")
                    or (item.get("best_oa_location") or {}).get("landing_page_url"),
                },
            ))
        return hits

    def cited_by(self, openalex_id: str, limit: int = 25, timeout: float = 25.0) -> list[Hit]:
        """Forward citations for a work id like 'https://openalex.org/W123' or 'W123'."""
        wid = openalex_id.rstrip("/").split("/")[-1]
        params = {"filter": "cites:" + wid, "per-page": min(max(limit, 1), 50)}
        mailto = contact_email()
        if mailto:
            params["mailto"] = mailto
        data = self._get_json(self.base_url + "/works", params, timeout)
        return self._results_to_hits(data)

    def _results_to_hits(self, data: dict) -> list[Hit]:
        hits: list[Hit] = []
        for item in data.get("results", []) or []:
            doi = item.get("doi")
            if doi:
                doi = util.normalize_doi(doi)
            hits.append(Hit(
                title=item.get("display_name"),
                url=item.get("doi"),
                doi=doi,
                platform=self.name,
                published_at=item.get("publication_date"),
                doc_type="paper",
                extra={"openalex_id": item.get("id"), "cited_by_count": item.get("cited_by_count")},
            ))
        return hits
