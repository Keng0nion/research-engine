"""MODULE 10: synthesis report scaffold.

Assembles a structured markdown report from session data. Narrative
sections are left as explicit placeholders: the agent writes findings,
interpretations, and gaps; the engine provides the auditable skeleton
(platforms searched, evidence table, citations, conflicts, references).
"""

from __future__ import annotations

import json
from pathlib import Path

from . import util


def _fmt_access(status: str | None) -> str:
    mapping = {
        "FULL_TEXT_RETRIEVED": "全文已获取",
        "ABSTRACT_ONLY": "仅摘要",
        "METADATA_ONLY": "仅元数据",
        "LOGIN_REQUIRED": "需登录",
        "ACCESS_RESTRICTED": "受限访问",
        "EXTRACTION_FAILED": "提取失败",
        "UNKNOWN": "未尝试",
    }
    return mapping.get(status or "UNKNOWN", status or "UNKNOWN")


def build_report(store, session_id: str) -> str:
    sess = store.get_session(session_id)
    if not sess:
        return "# ERROR: session not found: " + session_id
    queries = store.list_queries(session_id)
    docs = store.session_documents(session_id)
    evidence = store.list_evidence(session_id)
    citations = store.list_citations(session_id)
    conflicts = store.list_conflicts(session_id)

    platforms: dict[str, dict] = {}
    for q in queries:
        entry = platforms.setdefault(q["provider"], {"queries": 0, "ok": 0, "results": 0})
        entry["queries"] += 1
        if q["status"] == "ok":
            entry["ok"] += 1
            entry["results"] += q["result_count"] or 0

    access_counts: dict[str, int] = {}
    for d in docs:
        access_counts[d["access_status"]] = access_counts.get(d["access_status"], 0) + 1

    lines: list[str] = []
    lines.append("# 研究报告：" + (sess["question"] or "")[:120])
    lines.append("")
    lines.append("## 研究问题")
    lines.append("")
    lines.append(sess["question"] or "")
    lines.append("")
    lines.append("## 研究方法")
    lines.append("")
    lines.append("- 模式：" + sess["mode"] + "；研究轮数：" + str(sess["rounds_run"]))
    lines.append("- 创建时间：" + sess["created_at"] + "；更新时间：" + sess["updated_at"])
    lines.append("- 检索平台与规模：")
    for name in sorted(platforms):
        p = platforms[name]
        lines.append("  - " + name + "：执行 " + str(p["queries"]) + " 次查询（成功 " + str(p["ok"])
                     + "），返回 " + str(p["results"]) + " 条结果")
    lines.append("- 去重后文档数：" + str(len(docs)) + "；文档获取状态分布：")
    for status, count in sorted(access_counts.items()):
        lines.append("  - " + _fmt_access(status) + "：" + str(count))
    lines.append("")
    lines.append("## 重要发现")
    lines.append("")
    lines.append("（由 Agent 依据下方证据卡撰写；区分已证实事实、假设与解读）")
    lines.append("")
    lines.append("## 主要证据（证据卡）")
    lines.append("")
    if evidence:
        lines.append("| 证据 ID | 来源 | 年份 | 平台 | 访问状态 | 主张 | 引文核验 |")
        lines.append("|---|---|---|---|---|---|---|")
        doc_by_id = {d["id"]: d for d in docs}
        for ev in evidence:
            doc = doc_by_id.get(ev["document_id"]) or {}
            year = (doc.get("published_at") or "")[:4] or "—"
            lines.append("| " + ev["id"] + " | " + util.truncate(doc.get("title"), 60)
                         + " | " + year + " | " + (doc.get("platform") or "—")
                         + " | " + _fmt_access(doc.get("access_status"))
                         + " | " + util.truncate(ev.get("claim"), 80)
                         + " | " + (ev.get("citation_status") or "unverified") + " |")
    else:
        lines.append("（尚无证据卡；使用 `researchctl evidence add` 生成）")
    lines.append("")
    lines.append("## 学术发现")
    lines.append("")
    lines.append("（学术来源专项小节：关键论文、作者团队、发表趋势）")
    lines.append("")
    lines.append("## 冲突证据")
    lines.append("")
    if conflicts:
        for c in conflicts:
            lines.append("- [" + c["kind"] + "] " + c["topic"] + "：" + c["description"]
                         + "（证据：" + ", ".join(_json_list(c["evidence_ids_json"])) + "；状态：" + c["status"] + "）")
    else:
        lines.append("（未检测到已记录的冲突；运行 `researchctl conflicts detect --save` 生成候选）")
    lines.append("")
    lines.append("## 研究空白与局限")
    lines.append("")
    lines.append("（由 Agent 撰写：未覆盖的问题、平台缺口、语言与时间范围限制、获取失败的文献）")
    lines.append("")
    lines.append("## 参考文献")
    lines.append("")
    for i, d in enumerate(docs, start=1):
        authors = ", ".join(_json_list(d["authors_json"])[:4]) or "—"
        lines.append(str(i) + ". " + (d.get("title") or "(无题名)") + "。" + authors + "。"
                     + (d.get("published_at") or "日期未知") + "。"
                     + (d.get("canonical_url") or d.get("doi") or d.get("arxiv_id") or "")
                     + "（" + _fmt_access(d.get("access_status")) + "；检索时间 "
                     + (d.get("first_seen_at") or "") + "）")
    lines.append("")
    if citations:
        lines.append("## 引文关系（机检记录）")
        lines.append("")
        rel_names = {"cites": "引用", "cited_by": "被引", "related": "相关"}
        for c in citations[:80]:
            lines.append("- " + rel_names.get(c["relationship"], c["relationship"]) + "："
                         + (c.get("cited_title") or c.get("cited_doi") or "?")
                         + "（" + (c.get("cited_doi") or "") + "，来源 " + (c.get("source_platform") or "")
                         + "，verified=" + str(bool(c["verified"])) + "）")
        lines.append("")
    return "\n".join(lines)


def _json_list(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
        return [str(x) for x in data] if isinstance(data, list) else []
    except Exception:
        return []


def save_report(store, session_id: str, out_dir: Path) -> Path:
    text = build_report(store, session_id)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / (session_id + ".md")
    path.write_text(text, encoding="utf-8")
    return path
