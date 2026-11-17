"""Extra benchmark metrics: latency distribution and citation-verification sample."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.citations import verify_citation
from engine.storage import Store

recs = [json.loads(l) for l in (ROOT / "benchmarks" / "results-new.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
lats = sorted(r["latency_ms"] for r in recs)
n = len(lats)
print("engine latency: p50=" + str(lats[n // 2]) + "ms p90=" + str(lats[int(n * 0.9)]) + "ms max=" + str(lats[-1]) + "ms")
errs = sum(r["errors"] for r in recs)
tasks = sum(r["tasks"] for r in recs)
print("provider tasks: " + str(tasks) + ", provider errors: " + str(errs) + " (" + format(errs / tasks * 100, ".1f") + "%)")
print("fulltext total: " + str(sum(r["fulltext_retrieved"] for r in recs)) + "/" + str(sum(r["fulltext_attempted"] for r in recs)))

store = Store(ROOT / "research")
samples = []
for r in recs:
    sess = store.find_session(r["session"])
    if not sess:
        continue
    for doc in store.session_documents(sess["id"]):
        if doc["doi"]:
            samples.append({"q": r["n"], "doi": doc["doi"], "title": doc["title"]})
            break
    if len(samples) >= 6:
        break

print()
print("citation existence verification (sample of " + str(len(samples)) + "):")
verified = 0
for s in samples[:6]:
    verdict = verify_citation(store, "bench-sample", doi=s["doi"])
    ok = verdict.get("status") == "verified"
    verified += 1 if ok else 0
    print("  q" + str(s["q"]), s["doi"], "->", verdict.get("status"), "|", (s["title"] or "")[:50])
print("verified rate: " + str(verified) + "/" + str(min(6, len(samples))))
store.close()
