"""File-based search-result cache (P0-1).

Key = sha256(provider | query | limit | canonicalized opts). Values are
serialized Hit lists with a fetch timestamp; entries expire after
budgets.cache_ttl_s. Stored under <root>/cache/search/.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict
from pathlib import Path

from providers.base import Hit


def cache_key(provider: str, query: str, limit: int, opts: dict | None) -> str:
    canon_opts = json.dumps(opts or {}, sort_keys=True, ensure_ascii=False, default=str)
    raw = "|".join([provider, query, str(limit), canon_opts])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class SearchCache:
    def __init__(self, root: Path, ttl_s: int = 86400):
        self.dir = Path(root) / "cache" / "search"
        self.dir.mkdir(parents=True, exist_ok=True)
        self.ttl_s = ttl_s

    def _path(self, key: str) -> Path:
        return self.dir / (key + ".json")

    def get(self, key: str) -> list[Hit] | None:
        path = self._path(key)
        if not path.exists():
            return None
        try:
            if time.time() - path.stat().st_mtime > self.ttl_s:
                return None
            data = json.loads(path.read_text(encoding="utf-8"))
            hits = [Hit(**h) for h in data.get("hits", [])]
            return hits
        except (ValueError, TypeError, KeyError):
            return None

    def put(self, key: str, hits: list[Hit]) -> None:
        path = self._path(key)
        payload = {"fetched_at": time.time(), "hits": [asdict(h) for h in hits]}
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, default=str), encoding="utf-8")
        tmp.replace(path)

    def size_bytes(self) -> int:
        return sum(p.stat().st_size for p in self.dir.glob("*.json"))

    def clear(self) -> int:
        n = 0
        for p in self.dir.glob("*.json"):
            p.unlink()
            n += 1
        return n
