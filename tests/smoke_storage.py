"""Smoke test for engine.storage: full lifecycle on a temp database."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine.storage import Store

root = Path("/tmp/re_storage_smoke")
if root.exists():
    import shutil
    shutil.rmtree(root)

s = Store(root)
sid = s.create_session("Can deep learning predict bacterial survival?", "deep")
assert sid.startswith("2026"), sid
qid = s.add_query(sid, "openalex", "deep learning bacterial survival", "ok", result_count=12, latency_ms=800)

did, created = s.upsert_document(
    url="https://example.org/a?utm_source=x", title="T", platform="openalex",
    doi="10.1000/XYZ", authors=["A", "B"], published_at="2026-01-02",
    doc_type="paper", abstract="abs")
assert created is True and did == 1

# dedup by same URL with different tracking params
did2, created2 = s.upsert_document(url="https://example.org/a?utm_medium=y", title="T", platform="web")
assert created2 is False and did2 == did, (did2, created2)

# dedup by DOI from a different URL
did3, created3 = s.upsert_document(url="https://doi.org/10.1000/xyz", title="T", platform="crossref", doi="10.1000/xyz")
assert created3 is False and did3 == did, (did3, created3)

s.link_hit(did, qid, 1, "snippet here")
s.set_document_access(did, "ABSTRACT_ONLY")
s.log_fetch("https://example.org/a", "ok", http_status=200, byte_count=1234, document_id=did)

eid = s.add_evidence(sid, did, claim="c1", numbers={"accuracy": 0.9})
assert eid.endswith("001")
s.update_evidence(eid, methodology="m", relevance="high", citation_status="verified")
ev = s.list_evidence(sid)[0]
assert ev["claim"] == "c1" and ev["methodology"] == "m" and ev["relevance"] == "high"
assert ev["citation_status"] == "verified"

s.add_citation(sid, "cites", citing_document_id=did, cited_doi="https://doi.org/10.1/ABC", cited_title="X", cited_year=2020)
s.add_conflict(sid, "topic", "numbers", "desc", [eid])
s.start_round(sid, 1)
s.finish_round(sid, 1, "diminishing returns")
n = s.bump_round(sid)
assert n == 1

sess = s.get_session(sid)
assert sess["rounds_run"] == 1
found = s.find_session(sid[:12])
assert found is not None and found["id"] == sid
assert len(s.session_documents(sid)) == 1
assert len(s.list_queries(sid)) == 1
assert len(s.list_citations(sid)) == 1 and s.list_citations(sid)[0]["cited_doi"] == "10.1/abc"
assert len(s.list_conflicts(sid)) == 1

# unknown field rejection
try:
    s.update_session(sid, bogus_column="x")
    raise SystemExit("FAIL: unknown field was not rejected")
except ValueError:
    pass

s.close()
print("SMOKE-OK", sid, "docs=1 evidence=1 citations=1 conflicts=1 rounds=1")
