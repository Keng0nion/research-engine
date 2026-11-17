"""New-system benchmark runner: Research Engine v2.

Same 12 questions, equivalent budget (single query round, no expansion),
plus up to 2 full-text acquisition attempts per question on academic hits.
"""
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine import router, util
from engine.executor import search_many
from engine.fetcher import Fetcher, acquire_document
from engine.storage import Store

QUESTIONS = json.loads((ROOT / "benchmarks" / "questions.json").read_text(encoding="utf-8"))
OUT = ROOT / "benchmarks" / "results-new.jsonl"

ACADEMIC_PLATFORMS = {"openalex", "arxiv", "crossref", "pubmed", "europepmc", "semanticscholar"}

STOPWORDS = {"about", "with", "from", "that", "this", "what", "when", "where", "which", "into", "between", "their", "these", "those"}


def distinctive_terms(q: str) -> list[str]:
    words = re.findall(r"[a-z0-9\-]{4,}|[\u4e00-\u9fff]{2,}", q.lower())
    return [w for w in words if w not in STOPWORDS]


def main() -> None:
    store = Store(ROOT / "research")
    fetcher = Fetcher(ROOT)
    with OUT.open("w", encoding="utf-8") as out:
        for item in QUESTIONS:
            sid = store.create_session("BENCH " + str(item["n"]) + ": " + item["q"],
                                       "standard", session_id="bench-" + str(item["n"]).rjust(2, "0"))
            route = router.route(item["q"], domain="auto")
            tasks = [{"provider": p, "query": item["q"], "limit": 8,
                      "opts": dict(route["provider_opts"].get(p) or {})}
                     for p in route["providers"] if p not in ("anysearch",)]  # keep budget comparable
            t0 = time.monotonic()
            summary = search_many(store, sid, tasks, workers=6, timeout=25.0, round_no=1, store_results=True)
            docs = store.session_documents(sid)
            # full-text acquisition attempts on up to 2 academic docs
            attempted = retrieved = 0
            for d in docs:
                if attempted >= 2:
                    break
                if d["platform"] in ACADEMIC_PLATFORMS and (d["doi"] or d["arxiv_id"] or d["platform"] == "arxiv"):
                    if d["access_status"] in ("UNKNOWN", "EXTRACTION_FAILED"):
                        attempted += 1
                        res = acquire_document(store, fetcher, d["id"])
                        if res["status"] == "FULL_TEXT_RETRIEVED":
                            retrieved += 1
            wall_ms = int((time.monotonic() - t0) * 1000)
            docs = store.session_documents(sid)
            uniq_domains = {urlsplit(d["canonical_url"] or "").hostname or "" for d in docs}
            academic_docs = sum(1 for d in docs if d["platform"] in ACADEMIC_PLATFORMS or d["doi"] or d["arxiv_id"])
            lex_terms = distinctive_terms(item["q"])
            rel = 0
            for r in summary["results"]:
                hay = ((r.get("title") or "") + " " + (r.get("snippet") or "")).lower()
                if any(t in hay for t in lex_terms):
                    rel += 1
            access_dist: dict[str, int] = {}
            for d in docs:
                access_dist[d["access_status"]] = access_dist.get(d["access_status"], 0) + 1
            rec = {
                "n": item["n"], "category": item["category"], "lang": item["lang"], "q": item["q"],
                "system": "research-engine", "session": sid,
                "domain_route": route["domain"], "providers": route["providers"],
                "status": "ok",
                "latency_ms": wall_ms,
                "tasks": summary["totals"]["tasks"], "ok": summary["totals"]["ok"],
                "errors": summary["totals"]["errors"],
                "raw_hits": summary["totals"]["hits"],
                "unique_docs": len(docs),
                "new_documents": summary["totals"]["new_documents"],
                "duplicates": max(0, summary["totals"]["hits"] - len(docs)),
                "unique_domains": len(uniq_domains),
                "academic_docs": academic_docs,
                "lexical_relevance_hits": rel,
                "fulltext_attempted": attempted, "fulltext_retrieved": retrieved,
                "access_dist": access_dist,
                "top_urls": [d["canonical_url"] for d in docs[:5]],
            }
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            out.flush()
            print("[" + str(item["n"]) + "/12] ENGINE:", len(docs), "docs,", academic_docs, "academic,",
                  "ft " + str(retrieved) + "/" + str(attempted), wall_ms, "ms, errors", summary["totals"]["errors"], flush=True)
    store.close()


if __name__ == "__main__":
    main()
