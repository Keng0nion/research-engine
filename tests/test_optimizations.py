"""Tests for the v2 optimization batch: cache, circuit breaker, digest, stats, bib export."""
import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine import executor, stats as stats_mod
from engine.cache import SearchCache, cache_key
from engine.digest import digest_text, suggest_numbers
from engine.export import doc_to_bibtex
from engine.storage import Store
from providers.base import Hit

# --- cache roundtrip ---
tmp = Path(tempfile.mkdtemp())
c = SearchCache(tmp, ttl_s=60)
k = cache_key("openalex", "q", 10, {"a": 1})
assert c.get(k) is None
c.put(k, [Hit(title="T", url="https://x.org", platform="openalex")])
got = c.get(k)
assert got and got[0].title == "T" and got[0].url == "https://x.org"
assert c.size_bytes() > 0
print("cache OK")

# --- circuit breaker ---
executor._breakers.clear()
for _ in range(3):
    executor._record_failure("openalex")
assert executor._breaker_open("openalex")
executor._record_success("openalex")
assert not executor._breaker_open("openalex")
print("breaker OK")

# --- digest + suggested numbers ---
text = "引言部分介绍研究背景。该方法准确率达到 92.5%，比基线提升 3.1 倍。实验共 256 人参与，p值小于 0.01，差异显著。最后讨论方法的局限性。"
d = digest_text(text, title="某方法研究", max_chars=200)
assert d["text"]
nums = suggest_numbers(text)
assert any(n["metric"] == "准确率" and abs(n["value"] - 92.5) < 0.01 for n in nums), nums
print("digest OK, suggested numbers:", len(nums))

# --- bibtex ---
bib = doc_to_bibtex({"title": "A Study of X", "authors_json": json.dumps(["Zhang San", "Li Si"]),
                      "published_at": "2024-05-01", "doi": "10.1/x",
                      "canonical_url": "https://doi.org/10.1/x", "access_status": "FULL_TEXT_RETRIEVED"}, 1)
assert bib.startswith("@article{") and "10.1/x" in bib and "Zhang San and Li Si" in bib
print("bib OK:", bib.splitlines()[0])

# --- stats on synthetic store ---
sroot = Path(tempfile.mkdtemp())
s = Store(sroot)
sid = s.create_session("t", "standard")
for i in range(5):
    s.add_query(sid, "openalex", "q" + str(i), "ok" if i < 4 else "rate_limited",
                result_count=3, latency_ms=100 * (i + 1))
st = stats_mod.build_stats(s, sroot, sid)
oa = [p for p in st["providers"] if p["provider"] == "openalex"][0]
assert oa["total"] == 5 and oa["ok"] == 4 and oa["p50_latency_ms"] == 300, oa
assert oa["errors"].get("rate_limited") == 1
s.close()
print("stats OK: ok_rate", oa["ok_rate"], "p50", oa["p50_latency_ms"])

shutil.rmtree(tmp)
shutil.rmtree(sroot)
print("ALL-OPT-TESTS-OK")
