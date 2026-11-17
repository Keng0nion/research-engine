"""Baseline benchmark runner: DuckDuckGo-only (the old system's channel).

Queries the DDG HTML endpoint directly (the same channel the duckduckgo MCP
wraps), parses up to 20 organic results, and records per-question metrics.
No full-text acquisition is possible in this baseline by design.
"""
import html as html_mod
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

import httpx

ROOT = Path(__file__).resolve().parents[1]
QUESTIONS = json.loads((ROOT / "benchmarks" / "questions.json").read_text(encoding="utf-8"))
OUT = ROOT / "benchmarks" / "results-old.jsonl"

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"

_RESULT_RE = re.compile(
    r'<a rel="nofollow" class="result__a" href="([^"]+)"[^>]*>(.*?)</a>.*?'
    r'class="result__snippet"[^>]*>(.*?)</a>',
    re.S,
)

ACADEMIC_MARKERS = ("arxiv.org", "doi.org", "pubmed", "ncbi.nlm.nih.gov", "nature.com",
                    "science.org", "springer", "wiley", "sciencedirect", "ieee",
                    "acm.org", "mdpi.com", "plos", "frontiersin", "biorxiv", "medrxiv",
                    "openreview", "jmlr", "aclweb", "zenodo", "ssrn")

STOPWORDS = {"about", "with", "from", "that", "this", "what", "when", "where", "which", "into", "between", "their", "these", "those"}


def distinctive_terms(q: str) -> list[str]:
    words = re.findall(r"[a-z0-9\-]{4,}|[\u4e00-\u9fff]{2,}", q.lower())
    return [w for w in words if w not in STOPWORDS]


def strip_tags(s: str) -> str:
    return html_mod.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def clean_url(href: str) -> str:
    if "uddg=" in href:
        qs = parse_qs(urlsplit(href).query)
        if qs.get("uddg"):
            return unquote(qs["uddg"][0])
    if href.startswith("//"):
        return "https:" + href
    return href


def main() -> None:
    terms = {q["n"]: distinctive_terms(q["q"]) for q in QUESTIONS}
    with OUT.open("w", encoding="utf-8") as out, httpx.Client(timeout=25.0, headers={"User-Agent": UA}) as client:
        for item in QUESTIONS:
            t0 = time.monotonic()
            try:
                resp = client.post("https://html.duckduckgo.com/html/", data={"q": item["q"]})
                latency = int((time.monotonic() - t0) * 1000)
                rows = []
                for m in _RESULT_RE.finditer(resp.text):
                    url = clean_url(html_mod.unescape(m.group(1)))
                    rows.append({"title": strip_tags(m.group(2)), "url": url,
                                 "snippet": strip_tags(m.group(3))[:300]})
                    if len(rows) >= 20:
                        break
                status = "ok"
            except Exception as exc:
                latency = int((time.monotonic() - t0) * 1000)
                rows = []
                status = "error: " + str(exc)[:150]
            seen, uniq = set(), []
            for r in rows:
                if r["url"] not in seen:
                    seen.add(r["url"])
                    uniq.append(r)
            domains = {urlsplit(r["url"]).hostname or "" for r in uniq}
            lex_terms = terms[item["n"]]
            rel = 0
            for r in uniq:
                hay = (r["title"] + " " + r["snippet"]).lower()
                if any(t in hay for t in lex_terms):
                    rel += 1
            academic = sum(1 for r in uniq if any(mk in r["url"].lower() for mk in ACADEMIC_MARKERS))
            rec = {
                "n": item["n"], "category": item["category"], "lang": item["lang"], "q": item["q"],
                "system": "duckduckgo-only", "status": status, "latency_ms": latency,
                "results": len(rows), "unique_urls": len(uniq), "duplicates": len(rows) - len(uniq),
                "unique_domains": len(domains), "academic_hits": academic,
                "lexical_relevance_hits": rel,
                "urls": [r["url"] for r in uniq],
                "top_urls": [r["url"] for r in uniq[:5]],
            }
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            out.flush()
            print("[" + str(item["n"]) + "/12] DDG:", len(uniq), "unique,", academic, "academic,", latency, "ms", flush=True)
            time.sleep(2.5)  # stay gentle with the DDG html endpoint


if __name__ == "__main__":
    main()
