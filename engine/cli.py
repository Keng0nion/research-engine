"""researchctl: unified entry point for the Research Engine.

Designed for agent use: every subcommand supports --json for structured
output. All state lives under <root>/research/research.db plus document
files under research/{papers,websites,reports}.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from . import citations as citations_mod
from . import conflicts as conflicts_mod
from . import router
from . import util
from .executor import search_many
from .fetcher import Fetcher, acquire_document
from .report import build_report, save_report
from .storage import Store
from providers import REGISTRY, get_provider


def _root(args) -> Path:
    if getattr(args, "root", None):
        return Path(args.root)
    env = os.environ.get("RE_ROOT")
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[1]


def _emit(args, data, human_lines=None) -> None:
    if getattr(args, "json", False):
        print(json.dumps(data, ensure_ascii=False, indent=2, default=str))
    else:
        for line in (human_lines if human_lines is not None else [str(data)]):
            print(line)


def _fail(message: str, code: int = 1):
    print("ERROR: " + message, file=sys.stderr)
    sys.exit(code)


# ---------- providers ----------

def cmd_providers(args) -> None:
    rows = []
    for name in sorted(REGISTRY):
        provider = get_provider(name)
        reason = provider.available()
        rows.append({"provider": name, "available": reason is None,
                     "status": "ok" if reason is None else reason,
                     "doc_types": list(provider.doc_types)})
    _emit(args, {"providers": rows},
          [r["provider"].ljust(18) + ("OK" if r["available"] else r["status"]) for r in rows])


# ---------- search ----------

def cmd_search(args) -> None:
    root = _root(args)
    store = Store(root / "research")
    try:
        providers = [p.strip() for p in args.providers.split(",")] if args.providers else None
        route_info = router.route(args.query, domain=args.domain, providers=providers)
        queries = router.expand_query(args.query, domain=route_info["domain"]) if args.expand else [args.query]
        tasks = []
        for query_text in queries:
            for pname in route_info["providers"]:
                if pname not in REGISTRY:
                    continue
                opts = dict(route_info["provider_opts"].get(pname) or {})
                if args.category and pname == "searxng":
                    opts["category"] = args.category
                if args.language and pname == "searxng":
                    opts["language"] = args.language
                if args.time_range and pname == "searxng":
                    opts["time_range"] = args.time_range
                tasks.append({"provider": pname, "query": query_text,
                              "limit": args.limit, "opts": opts})
        if not tasks:
            _fail("no providers selected")
        session_id = args.session
        explicit_round = args.round
        if session_id:
            sess = store.find_session(session_id)
            if not sess:
                _fail("session not found: " + session_id)
            session_id = sess["id"]
        round_no = explicit_round if explicit_round is not None else ((sess["rounds_run"] or 0) + 1 if sess else 1)
        summary = search_many(store, session_id, tasks, workers=args.workers,
                              timeout=args.timeout, round_no=round_no,
                              store_results=True)
        # only an explicitly passed --round syncs the session counter
        if session_id and explicit_round is not None:
            sess_row = store.get_session(session_id)
            if sess_row and (sess_row["rounds_run"] or 0) < explicit_round:
                store.update_session(session_id, rounds_run=explicit_round)
        summary["domain"] = route_info["domain"]
        summary["queries"] = queries
        if args.json:
            _emit(args, summary)
        else:
            t = summary["totals"]
            print("domain: " + summary["domain"] + " | tasks: " + str(t["tasks"])
                  + " ok: " + str(t["ok"]) + " errors: " + str(t["errors"])
                  + " hits: " + str(t["hits"]) + " new docs: " + str(t["new_documents"]))
            if summary["errors"]:
                print("errors:")
                for e in summary["errors"]:
                    print("  - " + str(e["provider"]) + ": " + str(e["status"]) + " " + str(e["error"])[:100])
            print("top results:")
            for r in summary["results"][:15]:
                print("  [" + str(r["doc_id"]) + "] " + (r["title"] or "")[:70]
                      + " | " + str(r["doi"] or r["url"] or "")[:70]
                      + " (" + str(r["platform"]) + ")")
    finally:
        store.close()


# ---------- fetch ----------

def cmd_fetch(args) -> None:
    root = _root(args)
    store = Store(root / "research")
    try:
        fetcher = Fetcher(root)
        if args.docs:
            results = []
            for raw in args.docs.split(","):
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    doc_id = int(raw)
                except ValueError:
                    results.append({"input": raw, "status": "EXTRACTION_FAILED", "detail": "not a doc id"})
                    continue
                if not store.get_document(doc_id):
                    results.append({"doc_id": doc_id, "status": "EXTRACTION_FAILED", "detail": "document not found"})
                    continue
                result = acquire_document(store, fetcher, doc_id)
                result["doc_id"] = doc_id
                results.append(result)
            ok = sum(1 for r in results if r["status"] == "FULL_TEXT_RETRIEVED")
            _emit(args, {"results": results, "full_text_retrieved": ok, "attempted": len(results)},
                  [str(r.get("doc_id")) + "  " + str(r["status"]) + "  " + str(r.get("detail", ""))[:80]
                   for r in results])
        elif args.doc is not None:
            doc = store.get_document(args.doc)
            if not doc:
                _fail("document not found: " + str(args.doc))
            result = acquire_document(store, fetcher, args.doc)
            result["doc_id"] = args.doc
        elif args.url:
            doc_id, _created = store.upsert_document(
                url=args.url, title=None, platform="manual",
                doc_type="paper" if args.kind == "paper" else "webpage")
            result = fetcher.fetch(args.url, kind=args.kind, slug_hint=None)
            store.log_fetch(url=args.url, outcome=result.get("outcome", "error"),
                            http_status=result.get("http_status"), detail=result.get("detail"),
                            byte_count=result.get("bytes"), document_id=doc_id)
            if result.get("status"):
                store.set_document_access(doc_id, result["status"], fulltext_path=result.get("path"))
            result["doc_id"] = doc_id
        else:
            _fail("provide a URL or --doc ID")
            return
        _emit(args, result)
    finally:
        store.close()


# ---------- sessions ----------

def cmd_session(args) -> None:
    root = _root(args)
    store = Store(root / "research")
    try:
        if args.action == "new":
            sid = store.create_session(args.question, args.mode)
            _emit(args, {"session_id": sid, "mode": args.mode}, ["session created: " + sid])
        elif args.action == "list":
            rows = store.list_sessions(limit=args.limit)
            _emit(args, {"sessions": rows},
                  [r["id"] + "  [" + r["mode"] + "]  " + str(r["status"]) + "  " + (r["question"] or "")[:60]
                   for r in rows] or ["no sessions"])
        elif args.action == "update":
            sess = store.find_session(args.session_id or "")
            if not sess:
                _fail("session not found")
                return
            fields = {}
            if args.plan:
                try:
                    fields["plan_json"] = json.dumps(json.loads(args.plan), ensure_ascii=False)
                except ValueError:
                    _fail("--plan must be valid JSON")
            if args.notes is not None:
                fields["notes"] = args.notes
            if args.status:
                fields["status"] = args.status
            if fields:
                store.update_session(sess["id"], **fields)
            rounds = store.bump_round(sess["id"]) if args.bump_round else sess["rounds_run"]
            _emit(args, {"session_id": sess["id"], "rounds_run": rounds,
                         "updated": sorted(fields.keys())},
                  ["session updated: " + sess["id"] + " (rounds=" + str(rounds) + ")"])
        elif args.action == "show":
            sess = store.find_session(args.session_id or "")
            if not sess:
                _fail("session not found")
                return
            sid = sess["id"]
            docs = store.session_documents(sid)
            payload = {
                "session": sess,
                "queries": store.list_queries(sid),
                "documents": [{"id": d["id"], "title": d["title"], "platform": d["platform"],
                               "access_status": d["access_status"], "doi": d["doi"],
                               "arxiv_id": d["arxiv_id"], "url": d["canonical_url"]} for d in docs],
                "evidence": [{"id": e["id"], "status": e["status"], "citation_status": e["citation_status"]}
                             for e in store.list_evidence(sid)],
                "conflicts": store.list_conflicts(sid),
                "citation_count": len(store.list_citations(sid)),
            }
            if args.json:
                _emit(args, payload)
            else:
                print("session: " + sid)
                print("question: " + (sess["question"] or ""))
                print("mode: " + sess["mode"] + " | rounds: " + str(sess["rounds_run"])
                      + " | queries: " + str(len(payload["queries"]))
                      + " | docs: " + str(len(docs))
                      + " | evidence: " + str(len(payload["evidence"])))
                for d in payload["documents"][:30]:
                    print("  [" + str(d["id"]) + "] " + (d["title"] or "")[:60]
                          + " | " + str(d["access_status"]))
        else:
            _fail("unknown session action")
    finally:
        store.close()


# ---------- evidence ----------

def cmd_evidence(args) -> None:
    root = _root(args)
    store = Store(root / "research")
    try:
        if args.action == "add":
            sess = store.find_session(args.session)
            if not sess:
                _fail("session not found")
                return
            numbers = None
            if args.numbers:
                try:
                    numbers = json.loads(args.numbers)
                except ValueError:
                    _fail("--numbers must be valid JSON")
            eid = store.add_evidence(
                sess["id"], args.doc, claim=args.claim, excerpt=args.excerpt,
                methodology=args.methodology, dataset=args.dataset, conditions=args.conditions,
                numbers=numbers, limitations=args.limitations, authority=args.authority,
                relevance=args.relevance, method_quality=args.method_quality,
                recency=args.recency, status="draft",
                citation_status=args.citation_status or "unverified")
            _emit(args, {"evidence_id": eid}, ["evidence added: " + eid])
        elif args.action == "draft":
            sess = store.find_session(args.session)
            if not sess:
                _fail("session not found")
                return
            doc = store.get_document(args.doc)
            if not doc:
                _fail("document not found")
                return
            excerpt = util.truncate(doc.get("abstract"), 1200) or None
            eid = store.add_evidence(sess["id"], args.doc, claim=None, excerpt=excerpt,
                                     methodology=None, status="draft", citation_status="unverified")
            payload = {"evidence_id": eid, "document": {"id": doc["id"], "title": doc["title"],
                       "doi": doc["doi"], "published_at": doc["published_at"],
                       "platform": doc["platform"], "access_status": doc["access_status"]},
                       "abstract_excerpt": excerpt}
            _emit(args, payload, ["draft evidence card " + eid + " created for doc " + str(args.doc)])
        elif args.action == "list":
            sess = store.find_session(args.session)
            if not sess:
                _fail("session not found")
                return
            rows = store.list_evidence(sess["id"])
            _emit(args, {"evidence": rows},
                  [r["id"] + " [" + r["status"] + "/" + r["citation_status"] + "] "
                   + util.truncate(r.get("claim"), 70) for r in rows] or ["no evidence"])
        elif args.action == "update":
            eid = args.evidence_id or args.target
            if not eid:
                _fail("provide the evidence id (positional) or --evidence-id")
            fields = {k: v for k, v in {
                "claim": args.claim, "excerpt": args.excerpt, "methodology": args.methodology,
                "dataset": args.dataset, "conditions": args.conditions,
                "limitations": args.limitations, "authority": args.authority,
                "relevance": args.relevance, "method_quality": args.method_quality,
                "recency": args.recency, "status": args.status,
                "citation_status": args.citation_status,
            }.items() if v is not None}
            if args.numbers:
                try:
                    fields["numbers"] = json.loads(args.numbers)
                except ValueError:
                    _fail("--numbers must be valid JSON")
            if not fields:
                _fail("nothing to update")
            store.update_evidence(eid, **fields)
            _emit(args, {"updated": eid, "fields": sorted(fields.keys())},
                  ["updated " + eid])
        else:
            _fail("unknown evidence action")
    finally:
        store.close()


# ---------- citations ----------

def cmd_citations(args) -> None:
    root = _root(args)
    store = Store(root / "research")
    try:
        if args.action == "build":
            sess = store.find_session(args.session)
            if not sess:
                _fail("session not found")
                return
            result = citations_mod.build_citation_edges(store, sess["id"], args.doc, limit=args.limit)
            _emit(args, result)
        elif args.action == "verify":
            sess = store.find_session(args.session) if args.session else None
            result = citations_mod.verify_citation(store, sess["id"] if sess else "adhoc",
                                                   doi=args.doi, title=args.title,
                                                   year=args.year, authors=args.authors)
            _emit(args, result)
        elif args.action == "list":
            sess = store.find_session(args.session)
            if not sess:
                _fail("session not found")
                return
            rows = store.list_citations(sess["id"])
            _emit(args, {"citations": rows},
                  [r["relationship"] + "  " + str(r.get("cited_title") or r.get("cited_doi") or "?")[:70]
                   for r in rows] or ["no citations"])
        else:
            _fail("unknown citations action")
    finally:
        store.close()


# ---------- conflicts ----------

def cmd_conflicts(args) -> None:
    root = _root(args)
    store = Store(root / "research")
    try:
        if args.action == "detect":
            sess = store.find_session(args.session)
            if not sess:
                _fail("session not found")
                return
            candidates = conflicts_mod.detect_conflicts(store, sess["id"], save=args.save)
            _emit(args, {"candidates": candidates, "saved": bool(args.save)},
                  [c["kind"] + " | " + c["topic"] + " | " + c["description"][:100] for c in candidates]
                  or ["no conflict candidates"])
        elif args.action == "list":
            sess = store.find_session(args.session)
            if not sess:
                _fail("session not found")
                return
            rows = store.list_conflicts(sess["id"])
            _emit(args, {"conflicts": rows},
                  [r["kind"] + " | " + r["topic"] + " | " + r["status"] for r in rows] or ["no conflicts"])
        elif args.action == "add":
            sess = store.find_session(args.session)
            if not sess:
                _fail("session not found")
                return
            ids = [x.strip() for x in (args.evidence or "").split(",") if x.strip()]
            cid = store.add_conflict(sess["id"], args.topic, args.kind, args.description, ids)
            _emit(args, {"conflict_id": cid}, ["conflict recorded: " + str(cid)])
        elif args.action == "update":
            if args.conflict_id is None:
                _fail("--conflict-id required")
                return
            if args.status not in ("unresolved", "explained", "resolved"):
                _fail("--status must be unresolved|explained|resolved")
                return
            store.set_conflict_status(args.conflict_id, args.status)
            _emit(args, {"conflict_id": args.conflict_id, "status": args.status},
                  ["conflict " + str(args.conflict_id) + " -> " + args.status])
        else:
            _fail("unknown conflicts action")
    finally:
        store.close()


# ---------- expand ----------

def cmd_expand(args) -> None:
    route_info = router.route(args.query, domain=args.domain)
    variants = router.expand_query(args.query, domain=args.domain)
    _emit(args, {"domain": route_info["domain"], "variants": variants, "providers": route_info["providers"]},
          variants)


# ---------- report ----------

def cmd_report(args) -> None:
    root = _root(args)
    store = Store(root / "research")
    try:
        sess = store.find_session(args.session)
        if not sess:
            _fail("session not found")
            return
        if args.stdout:
            print(build_report(store, sess["id"]))
        else:
            out_dir = Path(args.out) if args.out else (root / "research" / "reports")
            path = save_report(store, sess["id"], out_dir)
            _emit(args, {"report_path": str(path)}, ["report written: " + str(path)])
    finally:
        store.close()


# ---------- main ----------

def main(argv=None) -> None:
    parser = argparse.ArgumentParser(prog="researchctl", description="Research Engine v2 unified entry point")
    parser.add_argument("--root", default=None, help="project root (default: engine directory or RE_ROOT)")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    sub = parser.add_subparsers(dest="command", required=True)

    # shared flags accepted both before and after the subcommand
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", default=None, help=argparse.SUPPRESS)
    common.add_argument("--json", action="store_true", help=argparse.SUPPRESS)

    def sub_parser(name: str, **kwargs):
        return sub.add_parser(name, parents=[common], **kwargs)

    p = sub_parser("providers", help="list providers and availability")
    p.set_defaults(func=cmd_providers)

    p = sub_parser("search", help="federated parallel search")
    p.add_argument("query")
    p.add_argument("--providers", default=None, help="comma-separated provider names")
    p.add_argument("--domain", default="auto", help="auto|bio|cs|math|physics|chem|med|zh|se|news|general")
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--category", default=None, help="searxng category (general/news/science)")
    p.add_argument("--language", default=None)
    p.add_argument("--time-range", dest="time_range", default=None, choices=[None, "day", "week", "month", "year"])
    p.add_argument("--workers", type=int, default=6)
    p.add_argument("--timeout", type=float, default=25.0)
    p.add_argument("--session", default=None)
    p.add_argument("--round", type=int, default=None)
    p.add_argument("--expand", action="store_true", help="add deterministic query variants")
    p.set_defaults(func=cmd_search)

    p = sub_parser("fetch", help="fetch full text for a URL, a stored document, or a doc batch")
    p.add_argument("url", nargs="?", default=None)
    p.add_argument("--doc", type=int, default=None)
    p.add_argument("--docs", default=None, help="comma-separated document ids for batch acquisition")
    p.add_argument("--kind", default="web", choices=["web", "paper"])
    p.set_defaults(func=cmd_fetch)

    p = sub_parser("session", help="session management")
    p.add_argument("action", choices=["new", "list", "show", "update"])
    p.add_argument("question", nargs="?", default=None)
    p.add_argument("--mode", default="standard", choices=["quick", "standard", "deep", "systematic"])
    p.add_argument("--session-id", dest="session_id", default=None)
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--plan", default=None, help="JSON plan object")
    p.add_argument("--notes", default=None)
    p.add_argument("--status", default=None, choices=[None, "active", "completed", "aborted"])
    p.add_argument("--bump-round", dest="bump_round", action="store_true")
    p.set_defaults(func=cmd_session)

    p = sub_parser("evidence", help="evidence cards")
    p.add_argument("action", choices=["add", "draft", "list", "update"])
    p.add_argument("target", nargs="?", default=None, help="evidence id (for update)")
    p.add_argument("--session", default=None, required=False)
    p.add_argument("--doc", type=int, default=None)
    p.add_argument("--evidence-id", dest="evidence_id", default=None)
    p.add_argument("--claim", default=None)
    p.add_argument("--excerpt", default=None)
    p.add_argument("--methodology", default=None)
    p.add_argument("--dataset", default=None)
    p.add_argument("--conditions", default=None)
    p.add_argument("--numbers", default=None, help="JSON list [{metric,value,unit}]")
    p.add_argument("--limitations", default=None)
    p.add_argument("--authority", default=None)
    p.add_argument("--relevance", default=None)
    p.add_argument("--method-quality", dest="method_quality", default=None)
    p.add_argument("--recency", default=None)
    p.add_argument("--status", default=None, choices=[None, "draft", "reviewed", "rejected"])
    p.add_argument("--citation-status", dest="citation_status", default=None,
                   choices=[None, "verified", "unverified", "suspect"])
    p.set_defaults(func=cmd_evidence)

    p = sub_parser("citations", help="citation intelligence")
    p.add_argument("action", choices=["build", "verify", "list"])
    p.add_argument("--session", default=None)
    p.add_argument("--doc", type=int, default=None)
    p.add_argument("--limit", type=int, default=25)
    p.add_argument("--doi", default=None)
    p.add_argument("--title", default=None)
    p.add_argument("--year", type=int, default=None)
    p.add_argument("--authors", default=None)
    p.set_defaults(func=cmd_citations)

    p = sub_parser("conflicts", help="conflict detection")
    p.add_argument("action", choices=["detect", "list", "add", "update"])
    p.add_argument("--session", default=None)
    p.add_argument("--save", action="store_true")
    p.add_argument("--topic", default=None)
    p.add_argument("--kind", default="numbers",
                   choices=["numbers", "conditions", "datasets", "methods", "definitions", "conclusions", "temporal"])
    p.add_argument("--description", default=None)
    p.add_argument("--evidence", default=None, help="comma-separated evidence ids")
    p.add_argument("--conflict-id", dest="conflict_id", type=int, default=None)
    p.add_argument("--status", default=None, help="for update: unresolved|explained|resolved")
    p.set_defaults(func=cmd_conflicts)

    p = sub_parser("expand", help="deterministic query variants")
    p.add_argument("query")
    p.add_argument("--domain", default="auto")
    p.set_defaults(func=cmd_expand)

    p = sub_parser("report", help="assemble synthesis report scaffold")
    p.add_argument("--session", required=True)
    p.add_argument("--out", default=None)
    p.add_argument("--stdout", action="store_true")
    p.set_defaults(func=cmd_report)

    argv = sys.argv[1:] if argv is None else list(argv)
    args = parser.parse_args(argv)
    # normalize --json regardless of position (subparser defaults can shadow it)
    args.json = bool(getattr(args, "json", False)) or ("--json" in argv)
    args.func(args)


if __name__ == "__main__":
    main()
