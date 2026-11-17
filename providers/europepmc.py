"""Europe PMC provider: REST search with open-access and fulltext flags (no key)."""

from __future__ import annotations

from .base import Hit, HttpProvider
from engine import util


class EuropePmcProvider(HttpProvider):
    name = "europepmc"
    doc_types = ("paper", "preprint")
    base_url = "https://www.ebi.ac.uk/europepmc/webservices/rest"

    def search(self, query: str, limit: int = 10, timeout: float = 25.0,
               opts: dict | None = None) -> list[Hit]:
        params = {
            "query": query,
            "format": "json",
            "pageSize": min(max(limit, 1), 50),
            "resultType": "core",
        }
        data = self._get_json(self.base_url + "/search", params, timeout)
        hits: list[Hit] = []
        for item in ((data.get("resultList") or {}).get("result")) or []:
            src = (item.get("source") or "").upper()
            pmid = item.get("pmid")
            pmcid = item.get("pmcid")
            if item.get("doi"):
                url = "https://doi.org/" + util.normalize_doi(item["doi"])
            elif pmid:
                url = "https://pubmed.ncbi.nlm.nih.gov/" + str(pmid) + "/"
            elif pmcid:
                url = "https://europepmc.org/article/" + pmcid
            else:
                url = None
            oa = str(item.get("isOpenAccess") or "").upper() == "Y"
            fulltext_xml = None
            if oa and pmcid:
                fulltext_xml = self.base_url + "/" + str(pmcid) + "/fullTextXML"
            hits.append(Hit(
                title=item.get("title"),
                url=url,
                doi=util.normalize_doi(item.get("doi")) if item.get("doi") else None,
                pmid=str(pmid) if pmid else None,
                platform=self.name,
                published_at=util.parse_date_loose(item.get("firstPublicationDate") or str(item.get("pubYear") or "")),
                authors=[a.strip() for a in (item.get("authorString") or "").split(",") if a.strip()][:12],
                doc_type="preprint" if src == "PPR" else "paper",
                abstract=item.get("abstractText"),
                extra={
                    "journal": item.get("journalTitle"),
                    "is_open_access": item.get("isOpenAccess"),
                    "pmcid": str(pmcid) if pmcid else None,
                    "fulltext_xml_url": fulltext_xml,
                    "has_fulltext": bool((item.get("fullTextIdList") or {}).get("fullTextId")),
                    "cited_by_count": item.get("citedByCount"),
                },
            ))
        return hits
