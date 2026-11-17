"""Engine configuration loader (config/engine.yaml) with defaults."""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]

DEFAULTS = {
    "budgets": {
        "max_workers": 6,
        "per_provider_timeout_s": 25,
        "fetch_timeout_s": 40,
        "max_retries": 2,
        "max_doc_bytes": 20000000,
        "search_results_per_provider": 10,
        "max_rounds_default": 3,
        "max_docs_per_session": 400,
        "cache_ttl_s": 86400,
        "circuit_breaker_threshold": 3,
        "circuit_breaker_seconds": 60,
        "retry_base_s": 0.5,
        "per_provider_max_concurrency": {
            "default": 2,
            "pubmed": 1,
            "arxiv": 1,
            "semanticscholar": 1,
            "unpaywall": 1,
            "anysearch": 1,
            "europepmc": 2,
            "openalex": 2,
            "crossref": 2,
            "searxng": 3,
        },
    }
}

_cfg: dict | None = None


def load() -> dict:
    global _cfg
    if _cfg is None:
        path = ROOT / "config" / "engine.yaml"
        data = {}
        if path.exists():
            try:
                data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            except yaml.YAMLError:
                data = {}
        merged = {"budgets": dict(DEFAULTS["budgets"])}
        merged["budgets"].update((data.get("budgets") or {}))
        # deep-merge the concurrency map
        conc = dict(DEFAULTS["budgets"]["per_provider_max_concurrency"])
        conc.update((data.get("budgets") or {}).get("per_provider_max_concurrency") or {})
        merged["budgets"]["per_provider_max_concurrency"] = conc
        merged.update({k: v for k, v in data.items() if k != "budgets"})
        _cfg = merged
    return _cfg


def budgets() -> dict:
    return load()["budgets"]
