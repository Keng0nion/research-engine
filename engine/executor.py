"""MODULE 4: parallel federated search executor.

Bounded worker pool; per-task retry policy; every execution is logged to
the queries table; hits are deduplicated through the documents table.
"""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from providers import ProviderError, get_provider

DEFAULT_WORKERS = 6


def _run_task(task: dict, timeout: float, retries: int) -> dict:
    name = task["provider"]
    query = task["query"]
    limit = int(task.get("limit", 10))
    opts = task.get("opts") or {}
    started = time.monotonic()
    attempts = 0
    last_error = None
    while attempts <= retries:
        attempts += 1
        try:
            provider = get_provider(name)
            hits = provider.search(query, limit=limit, timeout=timeout, opts=opts)
            return {
                "provider": name, "query": query, "status": "ok",
                "hits": hits, "latency_ms": int((time.monotonic() - started) * 1000),
                "attempts": attempts, "error": None,
            }
        except ProviderError as exc:
            last_error = exc
            if exc.kind == "rate_limited" and attempts <= retries:
                time.sleep(3.0 * attempts)
                continue
            if exc.kind in ("timeout", "http_error") and attempts <= retries:
                time.sleep(1.0 * attempts)
                continue
            kind = exc.kind
            break
        except Exception as exc:  # provider bugs must not kill the pool
            last_error = exc
            kind = "provider_error"
            break
    status = "error"
    if isinstance(last_error, ProviderError) and last_error.kind in ("timeout", "rate_limited"):
        status = last_error.kind
    return {
        "provider": name, "query": query, "status": status, "hits": [],
        "latency_ms": int((time.monotonic() - started) * 1000), "attempts": attempts,
        "error": (str(last_error)[:300] if last_error else "unknown error"),
    }


def search_many(store, session_id: str | None, tasks: list[dict], *, workers: int = DEFAULT_WORKERS,
                timeout: float = 25.0, retries: int = 2, round_no: int = 1,
                store_results: bool = True) -> dict:
    """Execute search tasks concurrently and (optionally) persist hits.

    tasks: [{"provider": str, "query": str, "limit": int, "opts": dict}, ...]
    Returns a structured summary; never raises on individual provider failure.
    """
    results: list[dict] = []
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        futures = {pool.submit(_run_task, t, timeout, retries): t for t in tasks}
        for fut in as_completed(futures):
            try:
                results.append(fut.result())
            except Exception as exc:  # defensive: futures should not raise
                task = futures[fut]
                results.append({"provider": task.get("provider"), "query": task.get("query"),
                                "status": "error", "hits": [], "latency_ms": 0, "attempts": 0,
                                "error": str(exc)[:300]})

    summary = {"per_provider": {}, "totals": {"tasks": len(tasks), "ok": 0, "errors": 0,
               "hits": 0, "new_documents": 0}, "errors": [], "results": []}
    for res in results:
        provider = res["provider"]
        entry = summary["per_provider"].setdefault(provider, {"ok": 0, "errors": 0, "hits": 0, "new_documents": 0, "latency_ms": []})
        entry["latency_ms"].append(res["latency_ms"])
        query_id = None
        if store_results and store is not None:
            query_id = store.add_query(session_id, provider, res["query"], res["status"],
                                       result_count=len(res["hits"]), latency_ms=res["latency_ms"],
                                       error=res["error"], round_no=round_no)
        if res["status"] != "ok":
            entry["errors"] += 1
            summary["totals"]["errors"] += 1
            summary["errors"].append({"provider": provider, "query": res["query"],
                                      "status": res["status"], "error": res["error"]})
            continue
        entry["ok"] += 1
        summary["totals"]["ok"] += 1
        for rank, hit in enumerate(res["hits"], start=1):
            entry["hits"] += 1
            summary["totals"]["hits"] += 1
            if store_results and store is not None:
                doc_id, created = store.upsert_document(
                    url=hit.url, title=hit.title, platform=hit.platform, doi=hit.doi,
                    arxiv_id=hit.arxiv_id, pmid=hit.pmid, authors=hit.authors,
                    published_at=hit.published_at, doc_type=hit.doc_type,
                    abstract=hit.abstract, metadata=hit.extra or None)
                store.link_hit(doc_id, query_id, rank, hit.snippet, raw=hit.extra or None)
                if created:
                    entry["new_documents"] += 1
                    summary["totals"]["new_documents"] += 1
                summary["results"].append({
                    "doc_id": doc_id, "provider": provider, "rank": rank, "title": hit.title,
                    "url": hit.url, "doi": hit.doi, "arxiv_id": hit.arxiv_id, "pmid": hit.pmid,
                    "platform": hit.platform, "published_at": hit.published_at,
                    "snippet": (hit.snippet or "")[:300], "new": created,
                })
    for entry in summary["per_provider"].values():
        lats = entry.pop("latency_ms", [])
        entry["avg_latency_ms"] = int(sum(lats) / len(lats)) if lats else 0
    return summary
