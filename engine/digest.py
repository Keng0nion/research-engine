"""digest: compress a full-text document into an evidence-ready digest (P0-3),
plus suggested numbers for conflict detection (P2-10).

Default path is deterministic extractive summarization (no model calls).
When RE_LLM_* env vars are configured, engine.llm.maybe_summarize is used
instead for the narrative part; extraction still supplies suggested numbers.
"""

from __future__ import annotations

import re
from pathlib import Path

from . import llm

_SENT_SPLIT = re.compile(r"[。！？!?;]\s*|(?<!\d)\.(?!\d)\s*|\n{2,}")
_NUM = re.compile(r"-?\d+(?:\.\d+)?\s*(?:%|％| percent)?")
_METRIC_WORDS = (
    "accuracy", "precision", "recall", "f1", "auc", "rmse", "mse", "mae", "bleu", "rouge",
    "perplexity", "loss", "p值", "p-value", "显著", "提升", "下降", "准确率", "召回率",
    "有效率", "成功率", "率", "参数", "亿", "万", "美元", "元", "倍", "人",
)


def _sentences(text: str) -> list[str]:
    parts = [s.strip() for s in _SENT_SPLIT.split(text)]
    return [p for p in parts if len(p) >= 12]


def suggest_numbers(text: str, cap: int = 10) -> list[dict]:
    """Pull (metric, value) candidates: the metric word nearest to each number wins."""
    out: list[dict] = []
    for sent in _sentences(text):
        m = _NUM.search(sent)
        if not m:
            continue
        low = sent.lower()
        num_pos = m.start()
        present = [(low.find(mw), mw) for mw in _METRIC_WORDS if mw in low]
        if not present:
            continue
        before = [(pos, mw) for pos, mw in present if pos <= num_pos]
        if before:
            metric = max(before, key=lambda t: len(t[1]))[1]  # longest metric preceding the number
        else:
            metric = min(present, key=lambda t: abs(t[0] - num_pos))[1]
        raw = m.group(0)
        num = float(re.sub(r"[^\d.\-]", "", raw) or 0)
        out.append({"metric": metric, "value": num, "unit": ("%" if "%" in raw or "％" in raw else None),
                    "context": " ".join(sent.split())[:160]})
        if len(out) >= cap:
            break
    return out


def digest_text(text: str, title: str = "", max_chars: int = 4000) -> dict:
    """Deterministic extractive digest: title terms boosted, number-bearing and
    section-initial sentences boosted, greedy fill up to max_chars."""
    title_terms = set(re.findall(r"[a-z]{4,}|[\u4e00-\u9fff]{2,}", (title or "").lower()))
    sents = _sentences(text)
    if not sents:
        return {"text": text[:max_chars], "suggested_numbers": []}
    scored = []
    for i, s in enumerate(sents):
        low = s.lower()
        score = 0.0
        score += sum(1 for t in title_terms if t in low) * 1.5
        if _NUM.search(s):
            score += 2.0
        if i < 3:
            score += 1.0
        if any(m in low for m in _METRIC_WORDS):
            score += 1.0
        scored.append((score, i, s))
    scored.sort(key=lambda x: (-x[0], x[1]))
    chosen: list[tuple[int, str]] = []
    total = 0
    for score, i, s in scored:
        if total + len(s) > max_chars and chosen:
            continue
        chosen.append((i, s))
        total += len(s)
        if total >= max_chars:
            break
    chosen.sort(key=lambda x: x[0])
    body = "\n".join(s for _, s in chosen)
    return {"text": body, "suggested_numbers": suggest_numbers(text)}


def digest_document(store, doc_id: int, max_chars: int = 4000, use_llm: bool = True) -> dict:
    doc = store.get_document(doc_id)
    if not doc:
        return {"error": "document not found"}
    path = doc.get("fulltext_path")
    text = ""
    if path and Path(path).exists():
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    if not text:
        text = doc.get("abstract") or doc.get("title") or ""
    title = doc.get("title") or ""
    extract = digest_text(text, title=title, max_chars=max_chars)
    llm_digest = llm.maybe_summarize(text, max_chars) if use_llm else None
    final = llm_digest or extract["text"]
    digest_path = None
    if path:
        digest_path = str(Path(path).with_suffix(".digest.md"))
        header = "# digest of: " + title + "\n# source: " + str(path) + "\n# llm: " + str(bool(llm_digest)) + "\n\n"
        Path(digest_path).write_text(header + final + "\n", encoding="utf-8")
    return {
        "doc_id": doc_id,
        "title": title,
        "digest_path": digest_path,
        "digest_chars": len(final),
        "llm_used": bool(llm_digest),
        "digest_head": final[:600],
        "suggested_numbers": extract["suggested_numbers"],
    }
