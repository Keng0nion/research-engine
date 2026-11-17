"""Live smoke test: query every provider once and report real results/errors."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from providers import get_provider

QUERY = "deep learning protein structure prediction"
NAMES = ["openalex", "arxiv", "crossref", "pubmed", "europepmc", "semanticscholar",
         "searxng", "anysearch", "unpaywall"]

for name in NAMES:
    p = get_provider(name)
    avail = p.available()
    if avail:
        print(name + ": UNAVAILABLE - " + avail)
        print()
        continue
    t0 = time.time()
    try:
        hits = p.search(QUERY, limit=5)
        dt = time.time() - t0
        print(name + ": " + str(len(hits)) + " hits in " + format(dt, ".1f") + "s")
        for h in hits[:2]:
            ident = h.doi or h.arxiv_id or h.pmid or h.url or ""
            print("   - " + (h.title or "")[:70] + " | " + str(ident)[:60])
    except Exception as e:
        print(name + ": ERROR " + type(e).__name__ + ": " + str(e)[:120])
    print()
