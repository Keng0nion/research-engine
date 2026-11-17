"""stats: provider health and latency percentiles from the queries table (P0-4)."""

from __future__ import annotations

from .cache import SearchCache


def _pct(sorted_vals: list[float], p: float) -> float:
    if not sorted_vals:
        return 0.0
    k = max(0, min(len(sorted_vals) - 1, int(round(p / 100 * (len(sorted_vals) - 1)))))
    return sorted_vals[k]


def provider_stats(store, session_id: str | None = None) -> list[dict]:
    if session_id:
        rows = store.conn.execute("SELECT provider, status, latency_ms, error FROM queries WHERE session_id = ? ORDER BY id", (session_id,)).fetchall()
    else:
        rows = store.conn.execute("SELECT provider, status, latency_ms, error FROM queries ORDER BY id").fetchall()
    by_provider: dict[str, dict] = {}
    for r in rows:
        e = by_provider.setdefault(r["provider"], {"provider": r["provider"], "total": 0, "ok": 0,
                                                   "errors": {}, "latencies": []})
        e["total"] += 1
        if r["status"] == "ok":
            e["ok"] += 1
            if r["latency_ms"] is not None:
                e["latencies"].append(float(r["latency_ms"]))
        else:
            kind = (r["status"] or "error")
            e["errors"][kind] = e["errors"].get(kind, 0) + 1
    out = []
    for e in by_provider.values():
        lats = sorted(e.pop("latencies"))
        e["ok_rate"] = round(e["ok"] / e["total"], 3) if e["total"] else 0.0
        e["avg_latency_ms"] = int(sum(lats) / len(lats)) if lats else 0
        e["p50_latency_ms"] = int(_pct(lats, 50))
        e["p90_latency_ms"] = int(_pct(lats, 90))
        out.append(e)
    out.sort(key=lambda x: -x["total"])
    return out


def access_distribution(store, session_id: str | None = None) -> dict[str, int]:
    if session_id:
        docs = store.session_documents(session_id)
    else:
        docs = [dict(r) for r in store.conn.execute("SELECT access_status FROM documents").fetchall()]
    dist: dict[str, int] = {}
    for d in docs:
        dist[d["access_status"]] = dist.get(d["access_status"], 0) + 1
    return dist


def build_stats(store, root, session_id: str | None = None) -> dict:
    cache = SearchCache(root)
    return {
        "session": session_id,
        "providers": provider_stats(store, session_id),
        "access_distribution": access_distribution(store, session_id),
        "cache_bytes": cache.size_bytes(),
        "cache_entries": len(list(cache.dir.glob("*.json"))),
    }
