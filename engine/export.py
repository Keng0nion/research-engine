"""Session export: report.md + session.json + references.bib bundle (P1-7)."""

from __future__ import annotations

import json
import re
from pathlib import Path

from .report import build_report


def _bib_key(title: str, authors_json: str | None, year: str | None, idx: int) -> str:
    surname = "anon"
    if authors_json:
        try:
            first = json.loads(authors_json)[0]
            surname = re.sub(r"[^A-Za-z]", "", first.split()[-1]) or "anon"
        except (ValueError, IndexError):
            pass
    word = re.sub(r"[^A-Za-z0-9]", "", (title or "untitled").split()[0]) if title else "untitled"
    return (surname + (year or "")[:4] + word)[:40].lower() or ("ref" + str(idx))


def doc_to_bibtex(doc: dict, idx: int) -> str:
    year = (doc.get("published_at") or "")[:4] or "n.d."
    key = _bib_key(doc.get("title") or "", doc.get("authors_json"), year, idx)
    authors = []
    if doc.get("authors_json"):
        try:
            authors = json.loads(doc["authors_json"])
        except ValueError:
            authors = []
    entry_type = "article"
    fields = [
        ("title", doc.get("title") or "Untitled"),
        ("author", " and ".join(authors) if authors else None),
        ("year", year if year != "n.d." else None),
        ("doi", doc.get("doi")),
        ("url", doc.get("canonical_url")),
        ("note", "access: " + str(doc.get("access_status"))),
    ]
    venue = None
    if doc.get("metadata_json"):
        try:
            venue = json.loads(doc["metadata_json"]).get("venue")
        except ValueError:
            venue = None
    if venue:
        fields.append(("journal", venue))
    lines = ["@" + entry_type + "{" + key + ","]
    for name, value in fields:
        if value:
            lines.append("  " + name + " = {" + str(value).replace("{", "{").replace("}", "}") + "},")
    lines.append("}")
    return "\n".join(lines)


def export_session(store, root: Path, session_id: str, out_dir: Path | None = None) -> dict:
    sess = store.find_session(session_id)
    if not sess:
        return {"error": "session not found"}
    sid = sess["id"]
    out = Path(out_dir) if out_dir else (Path(root) / "research" / "reports" / (sid + "-export"))
    out.mkdir(parents=True, exist_ok=True)

    report_path = out / "report.md"
    report_path.write_text(build_report(store, sid), encoding="utf-8")

    docs = store.session_documents(sid)
    payload = {
        "session": sess,
        "queries": store.list_queries(sid),
        "documents": docs,
        "evidence": store.list_evidence(sid),
        "citations": store.list_citations(sid),
        "conflicts": store.list_conflicts(sid),
    }
    session_path = out / "session.json"
    session_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    bib_lines = [doc_to_bibtex(d, i) for i, d in enumerate(docs, start=1)]
    bib_path = out / "references.bib"
    bib_path.write_text("\n\n".join(bib_lines) + "\n", encoding="utf-8")

    return {"session_id": sid, "dir": str(out),
            "files": [str(report_path), str(session_path), str(bib_path)],
            "documents": len(docs), "bib_entries": len(bib_lines)}
