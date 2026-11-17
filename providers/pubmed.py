"""PubMed provider: NCBI E-utilities esearch+esummary+efetch (no key).

Abstracts come from one batched efetch XML call (guarded parse); PubMed
landing pages are bot-challenged and are never fetched as documents.
"""

from __future__ import annotations

from .base import Hit, HttpProvider, contact_email, safe_parse_xml
from engine import util


def _abstracts_from_efetch(xml_text: str) -> dict[str, str]:
    """Map PMID -> abstract text from a PubmedArticleSet document."""
    out: dict[str, str] = {}
    root = safe_parse_xml(xml_text)
    for article in root.iter("PubmedArticle"):
        pmid_el = article.find(".//MedlineCitation/PMID")
        if pmid_el is None or not pmid_el.text:
            continue
        parts = []
        for abs_text in article.findall(".//Abstract/AbstractText"):
            label = abs_text.get("Label")
            text = " ".join(("".join(abs_text.itertext())).split())
            if not text:
                continue
            parts.append((label + ": " + text) if label else text)
        if parts:
            out[pmid_el.text.strip()] = " ".join(parts)
    return out


class PubMedProvider(HttpProvider):
    name = "pubmed"
    doc_types = ("paper",)
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    def _common(self) -> dict:
        common: dict = {"tool": "research-engine"}
        mailto = contact_email()
        if mailto:
            common["email"] = mailto
        return common

    def search(self, query: str, limit: int = 10, timeout: float = 25.0,
               opts: dict | None = None) -> list[Hit]:
        common = self._common()
        n = min(max(limit, 1), 50)

        es = dict(common, db="pubmed", term=query, retmax=n, retmode="json", sort="relevance")
        search_data = self._get_json(self.base_url + "/esearch.fcgi", es, timeout)
        ids = ((search_data.get("esearchresult") or {}).get("idlist")) or []
        if not ids:
            return []

        sm = dict(common, db="pubmed", id=",".join(ids), retmode="json")
        summary_data = self._get_json(self.base_url + "/esummary.fcgi", sm, timeout)
        result = summary_data.get("result") or {}

        abstracts: dict[str, str] = {}
        try:
            ef = dict(common, db="pubmed", id=",".join(ids), retmode="xml", rettype="abstract")
            abstracts = _abstracts_from_efetch(self._get_text(self.base_url + "/efetch.fcgi", ef, timeout))
        except Exception:
            abstracts = {}  # abstracts are an enrichment; search still succeeds

        hits: list[Hit] = []
        for pmid in ids:
            item = result.get(pmid)
            if not item:
                continue
            doi = None
            for aid in item.get("articleids") or []:
                if aid.get("idtype") == "doi":
                    doi = aid.get("value")
                    break
            authors = [a.get("name") for a in (item.get("authors") or [])[:12] if a.get("name")]
            hits.append(Hit(
                title=item.get("title"),
                url="https://pubmed.ncbi.nlm.nih.gov/" + pmid + "/",
                pmid=pmid,
                doi=util.normalize_doi(doi) if doi else None,
                platform=self.name,
                published_at=util.parse_date_loose(item.get("pubdate")),
                authors=authors,
                doc_type="paper",
                abstract=abstracts.get(pmid),
                extra={"journal": item.get("source"), "elocationid": item.get("elocationid")},
            ))
        return hits
