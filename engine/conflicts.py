"""MODULE 8: source conflict detection.

Deterministic candidate generation (numerical disagreement between
evidence cards; polarity opposition in claims). Candidates are stored for
agent review; nothing is auto-resolved and majority opinion is never
silently chosen.
"""

from __future__ import annotations

import json
import re

_OPPOSITES = (
    ("increase", "decrease"), ("higher", "lower"), ("improve", "worsen"),
    ("positive", "negative"), ("effective", "ineffective"), ("significant", "insignificant"),
    ("增加", "减少"), ("上升", "下降"), ("有效", "无效"), ("显著", "不显著"), ("优于", "劣于"),
)
_NEGATIONS = ("not ", "n't ", "no ", "never ", "cannot ", "without ", "fail", "未", "不", "无", "没有", "并未")
_NUM_RE = re.compile(r"-?\d+(?:\.\d+)?")


def _negation_before(text: str, word: str) -> bool:
    idx = text.find(word)
    if idx <= 0:
        return False
    window = text[max(0, idx - 18):idx]
    return any(neg in window for neg in _NEGATIONS)


def _parse_numbers(numbers_json: str | None) -> list[dict]:
    if not numbers_json:
        return []
    try:
        data = json.loads(numbers_json)
    except Exception:
        return []
    out = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and item.get("metric") is not None:
                try:
                    value = float(item.get("value"))
                except (TypeError, ValueError):
                    m = _NUM_RE.search(str(item.get("value")))
                    if not m:
                        continue
                    value = float(m.group(0))
                out.append({"metric": str(item["metric"]).strip().lower(),
                            "value": value, "unit": item.get("unit")})
    return out


def detect_numeric_conflicts(evidence_rows: list[dict]) -> list[dict]:
    by_metric: dict[str, list[tuple[str, float, str | None]]] = {}
    for ev in evidence_rows:
        for num in _parse_numbers(ev.get("numbers_json")):
            by_metric.setdefault(num["metric"], []).append((ev["id"], num["value"], num.get("unit")))
    candidates = []
    for metric, entries in by_metric.items():
        if len(entries) < 2:
            continue
        values = [v for _, v, _ in entries]
        lo, hi = min(values), max(values)
        scale = max(abs(lo), abs(hi), 1e-9)
        if (hi - lo) / scale >= 0.10 and not (lo <= 0 <= hi):
            candidates.append({
                "kind": "numbers",
                "topic": metric,
                "description": "metric " + metric + " varies across sources: "
                               + ", ".join(e[0] + "=" + format(e[1], ".4g") + ((" " + e[2]) if e[2] else "") for e in entries),
                "evidence_ids": [e[0] for e in entries],
            })
    return candidates


def detect_polarity_conflicts(evidence_rows: list[dict]) -> list[dict]:
    candidates = []
    claims = [(ev["id"], (ev.get("claim") or "")) for ev in evidence_rows if ev.get("claim")]
    for i in range(len(claims)):
        for j in range(i + 1, len(claims)):
            id_a, a = claims[i]
            id_b, b = claims[j]
            la, lb = a.lower(), b.lower()
            shared = set(re.findall(r"[a-z]{4,}|[\u4e00-\u9fff]{2,}", la)) & set(re.findall(r"[a-z]{4,}|[\u4e00-\u9fff]{2,}", lb))
            shared -= {"that", "this", "with", "from", "which", "results", "study", "研究", "结果", "显示"}
            if len(shared) < 2:
                continue
            flagged = False
            for pos, neg in _OPPOSITES:
                if (pos in la and neg in lb) or (neg in la and pos in lb):
                    flagged = True
                    break
            if not flagged:
                # negation asymmetry: same content word, one claim negates it
                for word in sorted(shared):
                    if _negation_before(la, word) != _negation_before(lb, word):
                        flagged = True
                        break
            if flagged:
                candidates.append({
                    "kind": "conclusions",
                    "topic": " / ".join(sorted(shared))[:80],
                    "description": "opposing polarity on shared terms [" + ", ".join(sorted(shared)[:6]) + "]: "
                                   + id_a + " vs " + id_b,
                    "evidence_ids": [id_a, id_b],
                })
    return candidates


def detect_conflicts(store, session_id: str, *, save: bool = False) -> list[dict]:
    rows = store.list_evidence(session_id)
    candidates = detect_numeric_conflicts(rows) + detect_polarity_conflicts(rows)
    if save:
        for cand in candidates:
            store.add_conflict(session_id, cand["topic"], cand["kind"],
                               cand["description"], cand["evidence_ids"])
    return candidates
