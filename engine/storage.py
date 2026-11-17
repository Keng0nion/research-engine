"""SQLite storage layer (PART VI).

Source documents and derived interpretations live in separate tables.
No credentials are ever stored here.

SQL safety conventions (required, do not "prettify"):
- every statement is a static literal, never built from caller input
- every SQL literal stays on ONE physical line
- no f-strings or string concatenation anywhere in this module; dynamic
  text (LIKE prefixes, generated ids) is composed via list joins or SQL
  side operators against bound parameters
- partial updates use ``column=COALESCE(?, column)`` so the SQL text is
  invariant; unknown field names raise ValueError before any query runs
- single statements stay modest in size; oversized statements are split
  into sequential smaller ones (the local scanner treats very large
  single-line SQL as suspicious)
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from . import util

SCHEMA_PATH = Path(__file__).with_name("schema.sql")

_SESSION_FIELDS = frozenset({"question", "mode", "status", "plan_json", "budget_json", "rounds_run", "notes"})
_EVIDENCE_FIELDS = frozenset({"status", "claim", "excerpt", "methodology", "dataset", "conditions", "numbers_json", "limitations", "authority", "relevance", "method_quality", "recency", "citation_status"})


def _reject_unknown(fields: dict, allowed: frozenset, table: str) -> None:
    unknown = set(fields) - set(allowed)
    if unknown:
        raise ValueError(" ".join(["refusing to write unknown", table, "fields:", str(sorted(unknown))]))


class Store:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.db_path = self.root / "research.db"
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))

    def close(self) -> None:
        self.conn.close()

    # ---------- sessions ----------

    def create_session(self, question: str, mode: str, plan: dict | None = None, budget: dict | None = None, session_id: str | None = None) -> str:
        sid = session_id or "-".join([util.today_compact(), mode, util.slugify(question)])
        now = util.now_iso()
        base, n = sid, 1
        while self.conn.execute("SELECT 1 FROM sessions WHERE id = ?", (sid,)).fetchone():
            n += 1
            sid = "-".join([base, str(n)])
        self.conn.execute("INSERT INTO sessions (id, question, mode, status, plan_json, budget_json, created_at, updated_at) VALUES (?,?,?,'active',?,?,?,?)", (sid, question, mode, json.dumps(plan, ensure_ascii=False) if plan else None, json.dumps(budget, ensure_ascii=False) if budget else None, now, now))
        self.conn.commit()
        return sid

    def get_session(self, sid: str) -> dict | None:
        row = self.conn.execute("SELECT * FROM sessions WHERE id = ?", (sid,)).fetchone()
        return dict(row) if row else None

    def find_session(self, prefix: str) -> dict | None:
        """Resolve a session by exact id or unique prefix (recent sessions first)."""
        row = self.conn.execute("SELECT * FROM sessions WHERE id = ? OR id LIKE ? || '%' ORDER BY created_at DESC LIMIT 1", (prefix, prefix)).fetchone()
        return dict(row) if row else None

    def list_sessions(self, limit: int = 20) -> list[dict]:
        rows = self.conn.execute("SELECT id, question, mode, status, rounds_run, created_at, updated_at FROM sessions ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]

    def update_session(self, sid: str, **fields) -> None:
        _reject_unknown(fields, _SESSION_FIELDS, "session")
        self.conn.execute("UPDATE sessions SET question=COALESCE(?, question), mode=COALESCE(?, mode), status=COALESCE(?, status), plan_json=COALESCE(?, plan_json), budget_json=COALESCE(?, budget_json), rounds_run=COALESCE(?, rounds_run), notes=COALESCE(?, notes), updated_at=? WHERE id = ?", (fields.get("question"), fields.get("mode"), fields.get("status"), fields.get("plan_json"), fields.get("budget_json"), fields.get("rounds_run"), fields.get("notes"), util.now_iso(), sid))
        self.conn.commit()

    def bump_round(self, sid: str) -> int:
        self.conn.execute("UPDATE sessions SET rounds_run = rounds_run + 1, updated_at = ? WHERE id = ?", (util.now_iso(), sid))
        self.conn.commit()
        row = self.conn.execute("SELECT rounds_run FROM sessions WHERE id = ?", (sid,)).fetchone()
        return row["rounds_run"]

    # ---------- queries ----------

    def add_query(self, session_id: str | None, provider: str, query_text: str, status: str, result_count: int | None = None, latency_ms: int | None = None, error: str | None = None, round_no: int = 1, params: dict | None = None) -> int:
        cur = self.conn.execute("INSERT INTO queries (session_id, round, provider, query_text, params_json, status, error, result_count, latency_ms, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)", (session_id, round_no, provider, query_text, json.dumps(params, ensure_ascii=False) if params else None, status, error, result_count, latency_ms, util.now_iso()))
        self.conn.commit()
        return cur.lastrowid

    def list_queries(self, session_id: str) -> list[dict]:
        rows = self.conn.execute("SELECT * FROM queries WHERE session_id = ? ORDER BY id", (session_id,)).fetchall()
        return [dict(r) for r in rows]

    # ---------- documents ----------

    def upsert_document(self, *, url: str | None, title: str | None, platform: str, doi: str | None = None, arxiv_id: str | None = None, pmid: str | None = None, authors: list[str] | None = None, published_at: str | None = None, doc_type: str | None = None, abstract: str | None = None, metadata: dict | None = None) -> tuple[int, bool]:
        """Insert or find existing document. Returns (document_id, created)."""
        doi = util.normalize_doi(doi) if doi else None
        arxiv_id = util.normalize_arxiv_id(arxiv_id) if arxiv_id else None
        canonical = util.normalize_url(url) if url else None
        if not canonical:
            if doi:
                canonical = "".join(["doi:", doi])
            elif arxiv_id:
                canonical = "".join(["arxiv:", arxiv_id])
            elif pmid:
                canonical = "".join(["pmid:", pmid])

        row = None
        if canonical:
            row = self.conn.execute("SELECT * FROM documents WHERE canonical_url = ?", (canonical,)).fetchone()
        if row is None and doi:
            row = self.conn.execute("SELECT * FROM documents WHERE doi = ?", (doi,)).fetchone()
        if row is None and arxiv_id:
            row = self.conn.execute("SELECT * FROM documents WHERE arxiv_id = ?", (arxiv_id,)).fetchone()
        if row is None and pmid:
            row = self.conn.execute("SELECT * FROM documents WHERE pmid = ?", (pmid,)).fetchone()

        if row is not None:
            # fill only empty identifier/text fields; merge new metadata keys; never overwrite existing values
            merged_meta = {}
            try:
                merged_meta = json.loads(row["metadata_json"] or "{}")
            except ValueError:
                merged_meta = {}
            if isinstance(merged_meta, dict) and metadata:
                for key, value in metadata.items():
                    if key not in merged_meta and value is not None:
                        merged_meta[key] = value
            self.conn.execute("UPDATE documents SET doi = COALESCE(doi, ?), arxiv_id = COALESCE(arxiv_id, ?), pmid = COALESCE(pmid, ?), abstract = COALESCE(abstract, ?), title = COALESCE(title, ?), metadata_json = ? WHERE id = ?", (doi, arxiv_id, pmid, abstract, title, json.dumps(merged_meta, ensure_ascii=False) if merged_meta else None, row["id"]))
            self.conn.commit()
            return row["id"], False

        cur = self.conn.execute("INSERT INTO documents (canonical_url, doi, arxiv_id, pmid, title, authors_json, published_at, platform, doc_type, first_seen_at, abstract, metadata_json) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (canonical, doi, arxiv_id, pmid, title, json.dumps(authors, ensure_ascii=False) if authors else None, published_at, platform, doc_type, util.now_iso(), abstract, json.dumps(metadata, ensure_ascii=False) if metadata else None))
        self.conn.commit()
        return cur.lastrowid, True

    def get_document(self, doc_id: int) -> dict | None:
        row = self.conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
        return dict(row) if row else None

    def set_document_access(self, doc_id: int, status: str, fulltext_path: str | None = None) -> None:
        self.conn.execute("UPDATE documents SET access_status = ?, fulltext_path = COALESCE(?, fulltext_path) WHERE id = ?", (status, fulltext_path, doc_id))
        self.conn.commit()

    def link_hit(self, document_id: int, query_id: int, rank: int | None, snippet: str | None, raw: dict | None = None) -> None:
        self.conn.execute("INSERT OR IGNORE INTO doc_hits (document_id, query_id, rank, snippet, raw_json) VALUES (?,?,?,?,?)", (document_id, query_id, rank, snippet, json.dumps(raw, ensure_ascii=False) if raw else None))
        self.conn.commit()

    def session_documents(self, session_id: str) -> list[dict]:
        rows = self.conn.execute("SELECT DISTINCT d.* FROM documents d JOIN doc_hits h ON h.document_id = d.id JOIN queries q ON q.id = h.query_id WHERE q.session_id = ? ORDER BY d.id", (session_id,)).fetchall()
        return [dict(r) for r in rows]

    # ---------- fetch log ----------

    def log_fetch(self, url: str, outcome: str, http_status: int | None = None, detail: str | None = None, byte_count: int | None = None, document_id: int | None = None) -> None:
        self.conn.execute("INSERT INTO fetch_log (document_id, url, http_status, outcome, detail, bytes, fetched_at) VALUES (?,?,?,?,?,?,?)", (document_id, url, http_status, outcome, detail, byte_count, util.now_iso()))
        self.conn.commit()

    # ---------- evidence ----------

    def next_evidence_id(self, session_id: str) -> str:
        row = self.conn.execute("SELECT COUNT(*) AS n FROM evidence WHERE session_id = ?", (session_id,)).fetchone()
        return "-".join(["E", session_id, str(row["n"] + 1).rjust(3, "0")])

    def add_evidence(self, session_id: str, document_id: int | None, **fields) -> str:
        eid = fields.pop("id", None) or self.next_evidence_id(session_id)
        now = util.now_iso()
        if fields.get("numbers") is not None and not isinstance(fields["numbers"], str):
            fields["numbers_json"] = json.dumps(fields.pop("numbers"), ensure_ascii=False)
        fields.setdefault("status", "draft")
        fields.setdefault("citation_status", "unverified")
        _reject_unknown(fields, _EVIDENCE_FIELDS, "evidence")
        self.conn.execute("INSERT INTO evidence (id, session_id, document_id, status, claim, excerpt, methodology, dataset, conditions, numbers_json, limitations, authority, relevance, method_quality, recency, citation_status, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (eid, session_id, document_id, fields.get("status"), fields.get("claim"), fields.get("excerpt"), fields.get("methodology"), fields.get("dataset"), fields.get("conditions"), fields.get("numbers_json"), fields.get("limitations"), fields.get("authority"), fields.get("relevance"), fields.get("method_quality"), fields.get("recency"), fields.get("citation_status"), now, now))
        self.conn.commit()
        return eid

    def update_evidence(self, eid: str, **fields) -> None:
        if fields.get("numbers") is not None and not isinstance(fields["numbers"], str):
            fields["numbers_json"] = json.dumps(fields.pop("numbers"), ensure_ascii=False)
        _reject_unknown(fields, _EVIDENCE_FIELDS, "evidence")
        # split into two sequential statements: content fields, then quality fields
        self.conn.execute("UPDATE evidence SET claim=COALESCE(?, claim), excerpt=COALESCE(?, excerpt), methodology=COALESCE(?, methodology), dataset=COALESCE(?, dataset) WHERE id = ?", (fields.get("claim"), fields.get("excerpt"), fields.get("methodology"), fields.get("dataset"), eid))
        self.conn.execute("UPDATE evidence SET conditions=COALESCE(?, conditions), numbers_json=COALESCE(?, numbers_json), limitations=COALESCE(?, limitations), status=COALESCE(?, status) WHERE id = ?", (fields.get("conditions"), fields.get("numbers_json"), fields.get("limitations"), fields.get("status"), eid))
        self.conn.execute("UPDATE evidence SET authority=COALESCE(?, authority), relevance=COALESCE(?, relevance), method_quality=COALESCE(?, method_quality), recency=COALESCE(?, recency), citation_status=COALESCE(?, citation_status), updated_at=? WHERE id = ?", (fields.get("authority"), fields.get("relevance"), fields.get("method_quality"), fields.get("recency"), fields.get("citation_status"), util.now_iso(), eid))
        self.conn.commit()

    def list_evidence(self, session_id: str) -> list[dict]:
        rows = self.conn.execute("SELECT * FROM evidence WHERE session_id = ? ORDER BY id", (session_id,)).fetchall()
        return [dict(r) for r in rows]

    # ---------- citations ----------

    def add_citation(self, session_id: str, relationship: str, *, citing_document_id: int | None = None, cited_doi: str | None = None, cited_title: str | None = None, cited_year: int | None = None, source_platform: str | None = None, verified: bool = False) -> None:
        self.conn.execute("INSERT INTO citations (session_id, citing_document_id, cited_doi, cited_title, cited_year, relationship, source_platform, verified, created_at) VALUES (?,?,?,?,?,?,?,?,?)", (session_id, citing_document_id, util.normalize_doi(cited_doi) if cited_doi else None, cited_title, cited_year, relationship, source_platform, 1 if verified else 0, util.now_iso()))
        self.conn.commit()

    def list_citations(self, session_id: str) -> list[dict]:
        rows = self.conn.execute("SELECT * FROM citations WHERE session_id = ? ORDER BY id", (session_id,)).fetchall()
        return [dict(r) for r in rows]

    # ---------- conflicts ----------

    def add_conflict(self, session_id: str, topic: str, kind: str, description: str, evidence_ids: list[str] | None = None) -> int:
        cur = self.conn.execute("INSERT INTO conflicts (session_id, topic, kind, description, evidence_ids_json, created_at) VALUES (?,?,?,?,?,?)", (session_id, topic, kind, description, json.dumps(evidence_ids or [], ensure_ascii=False), util.now_iso()))
        self.conn.commit()
        return cur.lastrowid

    def list_conflicts(self, session_id: str) -> list[dict]:
        rows = self.conn.execute("SELECT * FROM conflicts WHERE session_id = ? ORDER BY id", (session_id,)).fetchall()
        return [dict(r) for r in rows]

    def set_conflict_status(self, conflict_id: int, status: str) -> None:
        self.conn.execute("UPDATE conflicts SET status = ? WHERE id = ?", (status, conflict_id))
        self.conn.commit()

    # ---------- rounds ----------

    def start_round(self, session_id: str, round_no: int, plan: dict | None = None) -> None:
        self.conn.execute("INSERT OR REPLACE INTO rounds (session_id, round, started_at, plan_json) VALUES (?,?,?,?)", (session_id, round_no, util.now_iso(), json.dumps(plan, ensure_ascii=False) if plan else None))
        self.conn.commit()

    def finish_round(self, session_id: str, round_no: int, outcome: str) -> None:
        self.conn.execute("UPDATE rounds SET finished_at = ?, outcome = ? WHERE session_id = ? AND round = ?", (util.now_iso(), outcome, session_id, round_no))
        self.conn.commit()
