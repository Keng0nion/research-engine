"""arXiv provider: Atom API search (no key; be gentle with rate).

XML hardening: responses are untrusted; DTD/entity declarations are
rejected and response size is capped before parsing (no defusedxml
dependency needed for this narrow use).
"""

from __future__ import annotations

import re

from .base import Hit, HttpProvider, safe_parse_xml
from engine import util

NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}


class ArxivProvider(HttpProvider):
    name = "arxiv"
    doc_types = ("preprint", "paper")
    base_url = "https://export.arxiv.org/api/query"

    def search(self, query: str, limit: int = 10, timeout: float = 25.0,
               opts: dict | None = None) -> list[Hit]:
        params = {
            "search_query": "all:" + query,
            "start": 0,
            "max_results": min(max(limit, 1), 50),
            "sortBy": "relevance",
        }
        xml_text = self._get_text(self.base_url, params, timeout)
        root = safe_parse_xml(xml_text)
        hits: list[Hit] = []
        for entry in root.findall("atom:entry", NS):
            title = (entry.findtext("atom:title", "", NS) or "").strip()
            summary = (entry.findtext("atom:summary", "", NS) or "").strip()
            raw_id = entry.findtext("atom:id", "", NS) or ""
            m = re.search(r"abs/([^v]+)(v\d+)?$", raw_id)
            arxiv_id = util.normalize_arxiv_id(m.group(1)) if m else None
            url = "https://arxiv.org/abs/" + arxiv_id if arxiv_id else raw_id
            authors = [a.findtext("atom:name", "", NS) for a in entry.findall("atom:author", NS)]
            published = entry.findtext("atom:published", "", NS)
            doi = entry.findtext("arxiv:doi", None, NS)
            hits.append(Hit(
                title=" ".join(title.split()),
                url=url,
                snippet=" ".join(summary.split())[:300],
                platform=self.name,
                published_at=util.parse_date_loose(published),
                authors=[a for a in authors if a],
                arxiv_id=arxiv_id,
                doi=util.normalize_doi(doi) if doi else None,
                doc_type="preprint",
                abstract=" ".join(summary.split()),
                extra={"pdf_url": "https://arxiv.org/pdf/" + arxiv_id if arxiv_id else None},
            ))
        return hits
