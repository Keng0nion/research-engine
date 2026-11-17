"""Compare baseline vs new-system benchmark results; print markdown tables.

Usage: .venv/bin/python benchmarks/compare.py
Reads benchmarks/results-old.jsonl and results-new.jsonl; pulls the full URL
list for the new system from the engine database (bench-XX sessions).
"""
import json
import sys
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.storage import Store


def load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def host_of(url: str) -> str:
    return (urlsplit(url or "").hostname or "?").lower()


def main() -> None:
    old = {r["n"]: r for r in load(ROOT / "benchmarks" / "results-old.jsonl")}
    new = {r["n"]: r for r in load(ROOT / "benchmarks" / "results-new.jsonl")}
    store = Store(ROOT / "research")
    for n, rec in new.items():
        sid = rec.get("session") or ("bench-" + str(n).rjust(2, "0"))
        sess = store.find_session(sid)
        if sess:
            rec["urls"] = [d.get("canonical_url") or "" for d in store.session_documents(sess["id"])]

    lines: list[str] = []
    lines.append("## 逐题对照")
    lines.append("")
    lines.append("| # | 类别 | 基线唯一来源 | 引擎唯一文档 | 基线学术命中 | 引擎学术文档 | 引擎全文获取 | 新增来源（引擎独有） |")
    lines.append("|---|---|---|---|---|---|---|---|")
    tot = {"old_uniq": 0, "new_docs": 0, "old_acad": 0, "new_acad": 0, "ft_a": 0, "ft_r": 0, "new_only": 0, "new_total": 0}
    for n in sorted(set(old) | set(new)):
        o, w = old.get(n), new.get(n)
        old_urls = set(o.get("urls") or o.get("top_urls") or []) if o else set()
        new_urls = set(w.get("urls") or []) if w else set()
        only = {u for u in new_urls if u and u not in old_urls}
        tot["old_uniq"] += o["unique_urls"] if o else 0
        tot["new_docs"] += w["unique_docs"] if w else 0
        tot["old_acad"] += o.get("academic_hits", 0) if o else 0
        tot["new_acad"] += w.get("academic_docs", 0) if w else 0
        tot["ft_a"] += w.get("fulltext_attempted", 0) if w else 0
        tot["ft_r"] += w.get("fulltext_retrieved", 0) if w else 0
        tot["new_only"] += len(only)
        tot["new_total"] += len(new_urls)
        ft = (str(w.get("fulltext_retrieved")) + "/" + str(w.get("fulltext_attempted"))) if w else "—"
        lines.append("| " + str(n) + " | " + (o or w)["category"] + " | "
                     + (str(o["unique_urls"]) if o else "—") + " | "
                     + (str(w["unique_docs"]) if w else "—") + " | "
                     + (str(o.get("academic_hits", "—")) if o else "—") + " | "
                     + (str(w.get("academic_docs", "—")) if w else "—") + " | " + ft + " | "
                     + (str(len(only)) if w else "—") + " |")
    lines.append("")
    lines.append("## 汇总")
    lines.append("")
    qcount = len(set(old) | set(new))
    lines.append("| 指标 | 基线（DDG-only） | 新引擎 | 说明 |")
    lines.append("|---|---|---|---|")
    lines.append("| 平均唯一来源/题 | " + format(tot["old_uniq"] / qcount, ".1f") + " | " + format(tot["new_docs"] / qcount, ".1f") + " | 去除重复 URL 后的来源数 |")
    lines.append("| 学术来源命中（12 题合计） | " + str(tot["old_acad"]) + " | " + str(tot["new_acad"]) + " | 基线用 URL 启发式；引擎按来源平台判定，口径不同仅供参考 |")
    lines.append("| 全文获取 | 不具备该能力 | " + str(tot["ft_r"]) + "/" + str(tot["ft_a"]) + "（" + format((tot["ft_r"] / tot["ft_a"] * 100) if tot["ft_a"] else 0, ".0f") + "%） | 仅为引擎侧能力 |")
    lines.append("| 引擎独有来源占比 | — | " + format((tot["new_only"] / tot["new_total"] * 100) if tot["new_total"] else 0, ".0f") + "% | 引擎来源中不在基线结果里的比例 |")
    old_lat = [o["latency_ms"] for o in old.values() if o.get("status") == "ok" and o.get("latency_ms")]
    new_lat = [w["latency_ms"] for w in new.values() if w.get("status") == "ok" and w.get("latency_ms")]
    if old_lat:
        lines.append("| 平均延迟 | " + format(sum(old_lat) / len(old_lat) / 1000, ".1f") + " 秒 | " + format(sum(new_lat) / len(new_lat) / 1000, ".1f") + " 秒 | 引擎含多供应商并行与全文获取 |")
    lines.append("")
    old_err = [o["n"] for o in old.values() if o.get("status") != "ok"]
    new_err = sum(w.get("errors", 0) for w in new.values())
    lines.append("基线失败题号：" + (str(old_err) if old_err else "无") + "；引擎供应商级错误合计：" + str(new_err) + " 次（单供应商失败不影响整体）。")
    lines.append("")
    lines.append("_口径备注见 RESEARCH-ENGINE-BENCHMARK.md。_")
    print("\n".join(lines))
    store.close()


if __name__ == "__main__":
    main()
