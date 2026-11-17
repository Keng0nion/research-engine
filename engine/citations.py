"""MODULE 6: citation intelligence.

- build edges from Semantic Scholar / OpenAlex for a paper
- verify a citation against Crossref + OpenAlex + arXiv (existence checks)
- export clean metadata for the citations table

Claim-level verification (does a source actually support a claim) is a
reading task performed by the agent; this module only does the mechanical
existence/identity layer.
"""

from __future__ import annotations

import difflib
import re

from providers import ProviderError, get_provider


def _similar(a: str | None, b: str | None) -> float:
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _s2_id_for_document(doc: dict) -> str | None:
    meta = {}
    try:
        import json
        meta = json.loads(doc.get("metadata_json") or "{}")
    except Exception:
        meta = {}
    if meta.get("s2_id"):
        return meta["s2_id"]
    if doc.get("doi"):
        return "DOI:" + doc["doi"]
    if doc.get("arxiv_id"):
        return "ARXIV:" + doc["arxiv_id"]
    url = doc.get("canonical_url") or ""
    m = re.search(r"arxiv\.org/(?:abs|pdf)/([^/?#]+)", url)
    if m:
        return "ARXIV:" + m.group(1)
    return None


def build_citation_edges(store, session_id: str, doc_id: int, *, limit: int = 25) -> dict:
    """Fetch references (backward) and citations (forward) for one stored document."""
    doc = store.get_document(doc_id)
    if not doc:
        return {"error": "document not found"}
    s2 = get_provider("semanticscholar")
    pid = _s2_id_for_document(doc)
    out = {"references": 0, "citations": 0, "errors": []}

    if pid:
        for direction, relationship in (("references", "cites"), ("citations", "cited_by")):
            try:
                if direction == "references":
                    hits = s2.references(pid, limit=limit)
                else:
                    hits = s2.citations(pid, limit=limit)
            except ProviderError as exc:
                out["errors"].append(direction + ": " + exc.kind)
                continue
            except Exception as exc:
                out["errors"].append(direction + ": " + str(exc)[:120])
                continue
            for hit in hits:
                if hit.doi or hit.title:
                    store.add_citation(session_id, relationship,
                                       citing_document_id=doc_id,
                                       cited_doi=hit.doi, cited_title=hit.title,
                                       cited_year=int(hit.published_at[:4]) if (hit.published_at and hit.published_at[:4].isdigit()) else None,
                                       source_platform="semanticscholar", verified=True)
                    out[direction] += 1
    else:
        out["errors"].append("no s2/doi/arxiv id for document")

    # OpenAlex forward citations as a cross-check / supplement
    meta = {}
    try:
        import json
        meta = json.loads(doc.get("metadata_json") or "{}")
    except Exception:
        meta = {}
    oa_id = meta.get("openalex_id")
    if oa_id:
        try:
            oa = get_provider("openalex")
            hits = oa.cited_by(oa_id, limit=limit)
            for hit in hits:
                store.add_citation(session_id, "cited_by", citing_document_id=doc_id,
                                   cited_doi=hit.doi, cited_title=hit.title,
                                   source_platform="openalex", verified=True)
                out["citations"] += 1
        except Exception as exc:
            out["errors"].append("openalex cited_by: " + str(exc)[:120])
    return out


def verify_citation(store, session_id: str, *, doi: str | None = None, title: str | None = None,
                    year: int | None = None, authors: str | None = None) -> dict:
    """Check that a cited work exists; returns {status, matched_by, record}."""
    verdict = {"status": "unverified", "matched_by": None, "record": None, "notes": []}

    if doi:
        try:
            crossref = get_provider("crossref")
            data = crossref._get_json(crossref.base_url + "/works/" + doi, {}, 20.0)
            item = data.get("message") or {}
            cr_title = (item.get("title") or [None])[0]
            verdict["record"] = {"doi": doi, "title": cr_title,
                                 "year": ((item.get("issued") or {}).get("date-parts") or [[None]])[0][0]}
            if not title or _similar(title, cr_title) >= 0.72:
                verdict["status"] = "verified"
                verdict["matched_by"] = "crossref-doi"
            else:
                verdict["status"] = "suspect"
                verdict["matched_by"] = "crossref-doi"
                verdict["notes"].append("title mismatch vs metadata")
            return verdict
        except Exception as exc:
            verdict["notes"].append("crossref doi lookup failed: " + str(exc)[:120])
        # OpenAlex fallback: covers arXiv DOIs (10.48550/...) and others Crossref misses
        try:
            openalex = get_provider("openalex")
            data = openalex._get_json(openalex.base_url + "/works/doi:" + doi, {}, 20.0)
            oa_title = data.get("display_name")
            verdict["record"] = {"doi": doi, "title": oa_title,
                                 "year": (data.get("publication_date") or "")[:4] or None}
            if not title or _similar(title, oa_title) >= 0.72:
                verdict["status"] = "verified"
                verdict["matched_by"] = "openalex-doi"
            else:
                verdict["status"] = "suspect"
                verdict["matched_by"] = "openalex-doi"
                verdict["notes"].append("title mismatch vs OpenAlex metadata")
            return verdict
        except Exception as exc:
            verdict["notes"].append("openalex doi lookup failed: " + str(exc)[:120])

    if title:
        probes = [("crossref", "crossref"), ("openalex", "openalex"), ("arxiv", "arxiv")]
        for pname, matched in probes:
            try:
                provider = get_provider(pname)
                hits = provider.search(title, limit=5)
            except Exception as exc:
                verdict["notes"].append(pname + " search failed: " + str(exc)[:120])
                continue
            best = max(hits, key=lambda h: _similar(title, h.title), default=None)
            score = _similar(title, best.title) if best else 0.0
            if best and score >= 0.8 and (year is None or not best.published_at or best.published_at[:4] == str(year) or abs(int(best.published_at[:4]) - year) <= 1):
                verdict["status"] = "verified"
                verdict["matched_by"] = matched
                verdict["record"] = {"title": best.title, "doi": best.doi,
                                     "url": best.url, "year": best.published_at}
                return verdict
            if best and score >= 0.65:
                verdict["status"] = "suspect"
                verdict["matched_by"] = matched
                verdict["record"] = {"title": best.title, "doi": best.doi, "url": best.url}
                verdict["notes"].append("closest match similarity " + format(score, ".2f"))
                return verdict
    if not verdict["notes"]:
        verdict["notes"].append("no lookup route available")
    return verdict
