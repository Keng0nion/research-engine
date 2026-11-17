"""Compile raw DDG MCP captures into results-old.jsonl (same metric schema as engine run).

Latency is not recorded for MCP captures (agent-mediated); stored as null.
"""
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
CAPTURES = json.loads((ROOT / "benchmarks" / "raw-old-captures.json").read_text(encoding="utf-8"))
QUESTIONS = {q["n"]: q for q in json.loads((ROOT / "benchmarks" / "questions.json").read_text(encoding="utf-8"))}
OUT = ROOT / "benchmarks" / "results-old.jsonl"

ACADEMIC_MARKERS = ("arxiv.org", "doi.org", "pubmed", "ncbi.nlm.nih.gov", "nature.com",
                    "science.org", "springer", "wiley", "sciencedirect", "ieee",
                    "acm.org", "mdpi.com", "plos", "frontiersin", "biorxiv", "medrxiv",
                    "openreview", "jmlr", "aclweb", "zenodo", "ssrn", "aclanthology",
                    "proceedings", "icml.cc", "cell.com", "pnas.org", "copernicus", "agupubs", "rsc.org")

STOPWORDS = {"about", "with", "from", "that", "this", "what", "when", "where", "which", "into", "between", "their", "these", "those"}


def terms_of(q: str) -> list[str]:
    words = re.findall(r"[a-z0-9\-]{4,}|[\u4e00-\u9fff]{2,}", q.lower())
    return [w for w in words if w not in STOPWORDS]


def main() -> None:
    with OUT.open("w", encoding="utf-8") as out:
        for cap in CAPTURES["captures"]:
            n = cap["n"]
            q = QUESTIONS[n]
            rows = cap["results"]
            urls = []
            seen = set()
            for r in rows:
                if r["u"] not in seen:
                    seen.add(r["u"])
                    urls.append(r["u"])
            domains = {urlsplit(u).hostname or "" for u in urls}
            lex = terms_of(q["q"])
            rel = 0
            for r in rows:
                if any(t in r["t"].lower() for t in lex):
                    rel += 1
            academic = sum(1 for u in urls if any(mk in u.lower() for mk in ACADEMIC_MARKERS))
            rec = {
                "n": n, "category": q["category"], "lang": q["lang"], "q": q["q"],
                "system": "duckduckgo-mcp", "status": "ok", "latency_ms": None,
                "results": len(rows), "unique_urls": len(urls), "duplicates": len(rows) - len(urls),
                "unique_domains": len(domains), "academic_hits": academic,
                "lexical_relevance_hits": rel, "urls": urls, "top_urls": urls[:5],
            }
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            print(n, "old:", len(urls), "unique,", academic, "academic,", rel, "lex-rel")
    print("written:", OUT)


if __name__ == "__main__":
    main()
