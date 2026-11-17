"""MODULE 4: parallel federated search executor (v2: cache + circuit breaker + per-provider limits).

Bounded worker pool; per-provider semaphore; per-provider circuit breaker
(failures >= threshold open the breaker for circuit_breaker_seconds);
jittered backoff on retries; optional TTL result cache; every execution is
logged to the queries table; hits deduplicated through documents table.
"""

from __future__ import annotations

import secrets
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from . import config as cfg
from .cache import SearchCache, cache_key
from providers import ProviderError, get_provider

_breakers: dict[str, dict] = {}
_semaphores: dict[str, threading.Semaphore] = {}
_registry_lock = threading.Lock()


def _budgets() -> dict:
    return cfg.budgets()


def _breaker(name: str) -> dict:
    with _registry_lock:
        return _breakers.setdefault(name, {"fails": 0, "open_until": 0.0})


def _semaphore(name: str) -> threading.Semaphore:
    with _registry_lock:
        if name not in _semaphores:
            conc = _budgets().get("per_provider_max_concurrency") or {}
            limit = int(conc.get(name, conc.get("default", 2)))
            _semaphores[name] = threading.Semaphore(max(1, limit))
        return _semaphores[name]


def _breaker_open(name: str) -> bool:
    b = _breaker(name)
    return b["open_until"] > time.monotonic()


def _record_failure(name: str) -> None:
    b = _breaker(name)
    b["fails"] += 1
    threshold = int(_budgets().get("circuit_breaker_threshold", 3))
    if b["fails"] >= threshold:
        b["open_until"] = time.monotonic() + float(_budgets().get("circuit_breaker_seconds", 60))
        b["fails"] = 0


def _record_success(name: str) -> None:
    b = _breaker(name)
    b["fails"] = 0
    b["open_until"] = 0.0


def breaker_state() -> dict:
    """Snapshot for stats/providers output: provider -> open bool."""
    return {name: {"open": _breaker_open(name)} for name in _breakers}


def _run_task(task: dict, timeout: float, retries: int,
              cache: SearchCache | None = None, use_cache: bool = True) -> dict:
    name = task["provider"]
    query = task["query"]
    limit = int(task.get("limit", 10))
    opts = task.get("opts") or {}
    started = time.monotonic()

    if _breaker_open(name):
        return {"provider": name, "query": query, "status": "skipped", "hits": [],
                "latency_ms": 0, "attempts": 0, "error": "circuit breaker open",
                "cached": False}

    key = cache_key(name, query, limit, opts) if cache is not None else None
    if cache is not None and use_cache and key is not None:
        cached = cache.get(key)
        if cached is not None:
            return {"provider": name, "query": query, "status": "ok", "hits": cached,
                    "latency_ms": int((time.monotonic() - started) * 1000), "attempts": 0,
                    "error": None, "cached": True}

    attempts = 0
    last_error: Exception | None = None
    base_sleep = float(_budgets().get("retry_base_s", 0.5))
    while attempts <= retries:
        attempts += 1
        try:
            provider = get_provider(name)
            with _semaphore(name):
                hits = provider.search(query, limit=limit, timeout=timeout, opts=opts)
            _record_success(name)
            if cache is not None and key is not None:
                cache.put(key, hits)
            return {"provider": name, "query": query, "status": "ok", "hits": hits,
                    "latency_ms": int((time.monotonic() - started) * 1000), "attempts": attempts,
                    "error": None, "cached": False}
        except ProviderError as exc:
            last_error = exc
            _record_failure(name)
            if exc.kind in ("rate_limited", "timeout", "http_error") and attempts <= retries:
                time.sleep(base_sleep * attempts + secrets.randbelow(500) / 1000.0)
                continue
            kind = exc.kind
            break
        except Exception as exc:  # provider bugs must not kill the pool
            last_error = exc
            _record_failure(name)
            kind = "provider_error"
            break
    status = "error"
    if isinstance(last_error, ProviderError) and last_error.kind in ("timeout", "rate_limited"):
        status = last_error.kind
    return {"provider": name, "query": query, "status": status, "hits": [],
            "latency_ms": int((time.monotonic() - started) * 1000), "attempts": attempts,
            "error": (str(last_error)[:300] if last_error else "unknown error"),
            "cached": False}


def search_many(store, session_id: str | None, tasks: list[dict], *, workers: int | None = None,
                timeout: float | None = None, retries: int | None = None, round_no: int = 1,
                store_results: bool = True, cache: SearchCache | None = None,
                use_cache: bool = True) -> dict:
    """Execute search tasks concurrently and (optionally) persist hits.

    tasks: [{"provider": str, "query": str, "limit": int, "opts": dict}, ...]
    """
    b = _budgets()
    workers = workers if workers is not None else int(b.get("max_workers", 6))
    timeout = timeout if timeout is not None else float(b.get("per_provider_timeout_s", 25))
    retries = retries if retries is not None else int(b.get("max_retries", 2))

    results: list[dict] = []
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        futures = {pool.submit(_run_task, t, timeout, retries, cache, use_cache): t for t in tasks}
        for fut in as_completed(futures):
            try:
                results.append(fut.result())
            except Exception as exc:  # defensive: futures should not raise
                task = futures[fut]
                results.append({"provider": task.get("provider"), "query": task.get("query"),
                                "status": "error", "hits": [], "latency_ms": 0, "attempts": 0,
                                "error": str(exc)[:300], "cached": False})

    summary = {"per_provider": {}, "totals": {"tasks": len(tasks), "ok": 0, "errors": 0,
               "hits": 0, "new_documents": 0, "cached": 0}, "errors": [], "results": []}
    for res in results:
        provider = res["provider"]
        entry = summary["per_provider"].setdefault(provider, {"ok": 0, "errors": 0, "hits": 0, "new_documents": 0, "latency_ms": [], "cached": 0})
        entry["latency_ms"].append(res["latency_ms"])
        if res.get("cached"):
            entry["cached"] += 1
            summary["totals"]["cached"] += 1
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
                    "snippet": (hit.snippet or "")[:300], "new": created, "cached": bool(res.get("cached")),
                })
    for entry in summary["per_provider"].values():
        lats = entry.pop("latency_ms", [])
        entry["avg_latency_ms"] = int(sum(lats) / len(lats)) if lats else 0
    return summary
