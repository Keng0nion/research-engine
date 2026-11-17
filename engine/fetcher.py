"""MODULE 5: full document acquisition.

Rules honored here:
- robots.txt respected when reachable (fail-open when unreachable, logged)
- per-host minimum interval between requests
- response size cap and overall timeout
- SSRF guard: only http/https, and every hop (including each redirect)
  must resolve to a public IP; loopback/private/link-local/CGNAT and
  multicast ranges are blocked
- access statuses are explicit; nothing is ever reported as fully read
  unless real full text was extracted

Residual risk (documented): DNS is resolved twice (once for validation,
once by the HTTP client) so a determined clock-race rebinding attacker is
not fully excluded; acceptable for a single-user local research tool.
"""

from __future__ import annotations

import hashlib
import html as html_mod
import ipaddress
import re
import socket
import subprocess
import threading
import time
import urllib.robotparser
from pathlib import Path
from urllib.parse import urljoin, urlsplit

import httpx

from . import util

MAX_BYTES = 20 * 1024 * 1024
FETCH_TIMEOUT = 40.0
MIN_HOST_INTERVAL = 1.0
MIN_FULLTEXT_CHARS = 600
_THIN_CHARS = 200
_MAX_REDIRECTS = 5

UA = "research-engine/0.1 (personal research tool)"

_LOGIN_MARKERS = ("sign in to continue", "log in to continue", "please log in", "登录后", "请先登录")
_PAYWALL_MARKERS = ("subscribe to read", "purchase this article", "access denied", "access restricted",
                    "institutional access", "buy this article", "订阅", "购买本文")

_BLOCKED_NETS = tuple(ipaddress.ip_network(n) for n in (
    "0.0.0.0/8", "10.0.0.0/8", "100.64.0.0/10", "127.0.0.0/8", "169.254.0.0/16",
    "172.16.0.0/12", "192.0.0.0/24", "192.0.2.0/24", "192.168.0.0/16",
    "198.18.0.0/15", "224.0.0.0/4", "240.0.0.0/4",
    "::1/128", "fc00::/7", "fe80::/10",
))

_host_locks: dict[str, threading.Lock] = {}
_host_last: dict[str, float] = {}
_robots_cache: dict[str, urllib.robotparser.RobotFileParser | None] = {}
_registry_lock = threading.Lock()


def url_is_safe(url: str) -> tuple[bool, str]:
    """Return (ok, reason). Public http/https hosts only."""
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https") or not parts.hostname:
        return False, "unsupported scheme or missing host"
    port = parts.port or (443 if parts.scheme == "https" else 80)
    try:
        infos = socket.getaddrinfo(parts.hostname, port, proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        return False, "dns resolution failed"
    if not infos:
        return False, "dns returned no addresses"
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
            ip = ip.ipv4_mapped
        if any(ip in net for net in _BLOCKED_NETS):
            return False, "resolves to non-public address (" + str(ip) + ")"
    return True, "ok"


def _is_private_host(host: str) -> bool:
    if host in ("localhost", "127.0.0.1", "::1"):
        return True
    try:
        return ipaddress.ip_address(host).is_private
    except ValueError:
        return False


def safe_post_json(url: str, payload: dict, headers: dict | None = None,
                   timeout: float = 60.0, allow_private: bool = False) -> httpx.Response:
    """POST JSON with the same SSRF policy as fetch(): public hosts only,
    unless allow_private=True and the host is loopback/private (opt-in for
    local LLM endpoints)."""
    ok, why = url_is_safe(url)
    if not ok and allow_private:
        host = urlsplit(url).hostname or ""
        ok = _is_private_host(host)
    if not ok:
        from providers.base import ProviderError
        raise ProviderError("http_error", "blocked unsafe url: " + why)
    with httpx.Client(timeout=timeout, follow_redirects=False,
                      headers=dict({"User-Agent": UA}, **(headers or {}))) as client:
        return client.post(url, json=payload)


class Fetcher:
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.websites_dir = self.project_root / "research" / "websites"
        self.papers_dir = self.project_root / "research" / "papers"
        self.websites_dir.mkdir(parents=True, exist_ok=True)
        self.papers_dir.mkdir(parents=True, exist_ok=True)

    # ---------- politeness ----------

    def _wait_for_host(self, host: str) -> None:
        with _registry_lock:
            lock = _host_locks.setdefault(host, threading.Lock())
        with lock:
            last = _host_last.get(host, 0.0)
            delta = time.monotonic() - last
            if delta < MIN_HOST_INTERVAL:
                time.sleep(MIN_HOST_INTERVAL - delta)
            _host_last[host] = time.monotonic()

    def _robots_allow(self, url: str) -> tuple[bool, str]:
        host = urlsplit(url).hostname or ""
        if host in _robots_cache:
            rp = _robots_cache[host]
        else:
            rp = None
            robots_url = "https://" + host + "/robots.txt"
            safe, _why = url_is_safe(robots_url)
            if safe:
                try:
                    resp = httpx.get(robots_url, timeout=10.0,
                                     headers={"User-Agent": UA}, follow_redirects=True)
                    if resp.status_code == 200:
                        parser = urllib.robotparser.RobotFileParser(robots_url)
                        parser.parse(resp.text.splitlines())
                        rp = parser
                except httpx.HTTPError:
                    rp = None
            _robots_cache[host] = rp
        if rp is None:
            return True, "no robots policy reachable"
        try:
            allowed = rp.can_fetch(UA, url)
        except Exception:
            return True, "robots parse error (fail-open)"
        return (allowed, "allowed by robots.txt") if allowed else (False, "disallowed by robots.txt")

    # ---------- fetching ----------

    def _safe_get(self, client: httpx.Client, url: str) -> dict:
        """GET with per-hop SSRF validation and buffered size cap."""
        current = url
        for _hop in range(_MAX_REDIRECTS + 1):
            ok, why = url_is_safe(current)
            if not ok:
                return {"error": "unsafe_url", "detail": why}
            with client.stream("GET", current) as resp:
                location = resp.headers.get("location")
                if resp.status_code in (301, 302, 303, 307, 308) and location:
                    current = urljoin(current, location)
                    continue
                data = bytearray()
                for chunk in resp.iter_bytes():
                    data.extend(chunk)
                    if len(data) > MAX_BYTES:
                        return {"error": "too_large", "status_code": resp.status_code}
                return {"status_code": resp.status_code,
                        "ctype": (resp.headers.get("content-type") or "").lower(),
                        "body": bytes(data), "final_url": current}
        return {"error": "too_many_redirects"}

    def fetch(self, url: str, *, kind: str = "web", slug_hint: str | None = None) -> dict:
        """Fetch one URL. Returns {outcome, status, path, bytes, http_status, detail}."""
        ok, why = url_is_safe(url)
        if not ok:
            return {"outcome": "http_error", "status": "EXTRACTION_FAILED", "detail": why}
        host = urlsplit(url).hostname or ""
        allowed, robots_why = self._robots_allow(url)
        if not allowed:
            return {"outcome": "robots_blocked", "status": "ACCESS_RESTRICTED", "detail": robots_why}

        self._wait_for_host(host)
        try:
            with httpx.Client(timeout=FETCH_TIMEOUT, follow_redirects=False,
                              headers={"User-Agent": UA}) as client:
                got = self._safe_get(client, url)
        except httpx.TimeoutException:
            return {"outcome": "network_error", "status": "EXTRACTION_FAILED", "detail": "timeout"}
        except httpx.HTTPError as exc:
            return {"outcome": "network_error", "status": "EXTRACTION_FAILED", "detail": str(exc)[:200]}

        if "error" in got:
            outcome = "too_large" if got["error"] == "too_large" else "network_error"
            return {"outcome": outcome, "status": "EXTRACTION_FAILED",
                    "http_status": got.get("status_code"), "detail": got["error"] + ": " + str(got.get("detail", ""))}

        http_status = got["status_code"]
        ctype = got["ctype"]
        body = got["body"]
        final_url = got["final_url"]

        if http_status in (401, 403):
            status = "LOGIN_REQUIRED" if http_status == 401 else "ACCESS_RESTRICTED"
            return {"outcome": "login_required", "status": status,
                    "http_status": http_status, "detail": "HTTP " + str(http_status)}
        if http_status >= 400:
            return {"outcome": "http_error", "status": "EXTRACTION_FAILED",
                    "http_status": http_status, "detail": "HTTP " + str(http_status)}

        is_pdf = "application/pdf" in ctype or body[:5] == b"%PDF-"
        slug = self._slug(url, slug_hint)

        if is_pdf:
            return self._handle_pdf(body, slug, http_status, final_url)
        if "xml" in ctype and (b"<article" in body[:8000] or b"<article" in body[:8000].lower()):
            return self._handle_jats(body, slug, http_status)
        if "text/html" in ctype or ctype == "" or "xml" in ctype:
            return self._handle_html(body, slug, http_status, kind)
        if ctype.startswith("text/"):
            path = self._save_text(self._target_dir(kind), slug + ".txt", body.decode("utf-8", "replace"))
            return {"outcome": "ok", "status": "FULL_TEXT_RETRIEVED", "path": path,
                    "bytes": len(body), "http_status": http_status, "detail": "text/" + ctype}
        return {"outcome": "extract_failed", "status": "EXTRACTION_FAILED",
                "http_status": http_status, "detail": "unsupported content-type: " + ctype}

    # ---------- handlers ----------

    def _handle_html(self, body: bytes, slug: str, http_status: int, kind: str) -> dict:
        html = body.decode("utf-8", "replace")
        text = ""
        try:
            import trafilatura
            text = trafilatura.extract(html, output_format="markdown", include_links=False,
                                       include_comments=False) or ""
        except Exception:
            text = ""
        if len(text) < _THIN_CHARS:
            lowered = html.lower()
            if any(m in lowered for m in _LOGIN_MARKERS):
                return {"outcome": "login_required", "status": "LOGIN_REQUIRED",
                        "http_status": http_status, "detail": "login wall detected"}
            if any(m in lowered for m in _PAYWALL_MARKERS):
                return {"outcome": "login_required", "status": "ACCESS_RESTRICTED",
                        "http_status": http_status, "detail": "paywall marker detected"}
            return {"outcome": "extract_failed", "status": "EXTRACTION_FAILED",
                    "http_status": http_status, "detail": "content extraction produced no text"}
        path = self._save_text(self._target_dir(kind), slug + ".md", text)
        status = "FULL_TEXT_RETRIEVED" if len(text) >= MIN_FULLTEXT_CHARS else "METADATA_ONLY"
        return {"outcome": "ok", "status": status, "path": path,
                "bytes": len(body), "http_status": http_status,
                "detail": "markdown chars=" + str(len(text))}

    def _handle_jats(self, body: bytes, slug: str, http_status: int) -> dict:
        """Europe PMC fullTextXML (JATS): strip tags into readable plain text."""
        text = body.decode("utf-8", "replace")
        text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", text, flags=re.S | re.I)
        text = re.sub(r"<[^>]+>", " ", text)
        text = html_mod.unescape(text)
        text = " ".join(text.split())
        if len(text) < _THIN_CHARS:
            return {"outcome": "extract_failed", "status": "EXTRACTION_FAILED",
                    "http_status": http_status, "detail": "jats stripped text too thin"}
        path = self._target_dir("paper") / (slug + ".md")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# source: europepmc fullTextXML\n\n" + text, encoding="utf-8")
        return {"outcome": "ok", "status": "FULL_TEXT_RETRIEVED", "path": str(path),
                "bytes": len(body), "http_status": http_status,
                "detail": "jats chars=" + str(len(text))}

    def _handle_pdf(self, body: bytes, slug: str, http_status: int, final_url: str) -> dict:
        pdf_path = self._target_dir("paper") / (slug + ".pdf")
        pdf_path.write_bytes(body)
        text = self._pdf_to_text(pdf_path)
        if not text or len(text) < _THIN_CHARS:
            return {"outcome": "extract_failed", "status": "EXTRACTION_FAILED", "path": str(pdf_path),
                    "http_status": http_status, "detail": "pdf text extraction failed"}
        md_path = self._target_dir("paper") / (slug + ".md")
        md_path.write_text(text, encoding="utf-8")
        return {"outcome": "pdf_ok", "status": "FULL_TEXT_RETRIEVED", "path": str(md_path),
                "bytes": len(body), "http_status": http_status,
                "detail": "pdf chars=" + str(len(text))}

    def _pdf_to_text(self, pdf_path: Path) -> str:
        try:
            proc = subprocess.run(["pdftotext", "-layout", str(pdf_path), "-"], shell=False, capture_output=True, timeout=120)
            if proc.returncode == 0 and proc.stdout:
                return proc.stdout.decode("utf-8", "replace")
        except (OSError, subprocess.TimeoutExpired):
            pass
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(pdf_path))
            chunks = []
            for page in reader.pages[:120]:
                chunks.append(page.extract_text() or "")
            return "\n\n".join(chunks)
        except Exception:
            return ""

    # ---------- helpers ----------

    def _target_dir(self, kind: str) -> Path:
        return self.papers_dir if kind == "paper" else self.websites_dir

    def _slug(self, url: str, hint: str | None) -> str:
        if hint:
            base = util.slugify(hint, max_len=60)
        else:
            parts = urlsplit(url)
            base = util.slugify((parts.hostname or "") + "-" + parts.path, max_len=60)
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:8]
        return base + "-" + digest

    def _save_text(self, target_dir: Path, name: str, text: str) -> str:
        target_dir.mkdir(parents=True, exist_ok=True)
        path = target_dir / name
        header = "# source: auto-fetched document\n\n"
        path.write_text(header + text, encoding="utf-8")
        return str(path)


# ---------- fetch adapters (per-platform best full-text routes) ----------

FETCH_ADAPTERS: dict[str, object] = {}


def register_fetch_adapter(platform: str):
    """Register a platform adapter: fn(doc_row, meta) -> list[(url, kind)]."""
    def deco(fn):
        FETCH_ADAPTERS[platform] = fn
        return fn
    return deco


@register_fetch_adapter("arxiv")
def _arxiv_adapter(doc, meta):
    return [(meta["pdf_url"], "paper")] if meta.get("pdf_url") else []


@register_fetch_adapter("europepmc")
def _europepmc_adapter(doc, meta):
    return [(meta["fulltext_xml_url"], "paper")] if meta.get("fulltext_xml_url") else []


@register_fetch_adapter("pubmed")
def _pubmed_adapter(doc, meta):
    # PubMed landing pages are bot-challenged (HTTP 203); abstracts arrive via
    # efetch at search time, so the adapter intentionally returns no URLs and
    # the canonical landing page is skipped below.
    return []


def acquire_document(store, fetcher: Fetcher, doc_id: int, *, allow_fetch: bool = True) -> dict:
    """Try to obtain the best available text for a stored document and record status.

    Order: platform fetch adapter -> OA pdf/oa_url -> Unpaywall (if email set)
    -> canonical URL (unless platform adapter marks it skippable).
    Never bypasses access controls; robots and statuses apply.
    """
    doc = store.get_document(doc_id)
    if not doc:
        return {"status": "EXTRACTION_FAILED", "detail": "document not found"}
    if not allow_fetch:
        return {"status": doc.get("access_status") or "UNKNOWN", "detail": "fetch disabled"}

    meta = {}
    try:
        import json as _json
        meta = _json.loads(doc.get("metadata_json") or "{}")
    except Exception:
        meta = {}

    candidates: list[tuple[str, str]] = []
    adapter = FETCH_ADAPTERS.get(doc.get("platform") or "")
    if adapter:
        try:
            candidates.extend(adapter(doc, meta))
        except Exception:
            pass
    if meta.get("open_access_pdf"):
        candidates.append((meta["open_access_pdf"], "paper"))
    if meta.get("oa_url"):
        candidates.append((meta["oa_url"], "paper"))
    if doc.get("doi"):
        # legal open-access resolution via Unpaywall (needs RE_CONTACT_EMAIL)
        try:
            from providers import get_provider
            uw = get_provider("unpaywall")
            if uw.available() is None:
                info = uw.resolve(doc["doi"])
                if info and info.get("is_oa"):
                    if info.get("pdf_url"):
                        candidates.append((info["pdf_url"], "paper"))
                    if info.get("best_url"):
                        candidates.append((info["best_url"], "paper"))
        except Exception:
            pass
    if doc.get("canonical_url") and not doc["canonical_url"].startswith(("doi:", "arxiv:", "pmid:")):
        is_pubmed_landing = doc.get("platform") == "pubmed" and "pubmed.ncbi.nlm.nih.gov" in doc["canonical_url"]
        if not is_pubmed_landing:
            kind = "paper" if doc.get("doc_type") in ("paper", "preprint") else "web"
            candidates.append((doc["canonical_url"], kind))
    # dedupe preserving order
    seen_urls = set()
    deduped: list[tuple[str, str]] = []
    for url, kind in candidates:
        if url not in seen_urls:
            seen_urls.add(url)
            deduped.append((url, kind))
    candidates = deduped

    if not candidates:
        if doc.get("abstract"):
            store.set_document_access(doc_id, "ABSTRACT_ONLY")
            return {"status": "ABSTRACT_ONLY", "detail": "no fetchable URL; abstract retained"}
        store.set_document_access(doc_id, "METADATA_ONLY")
        return {"status": "METADATA_ONLY", "detail": "no fetchable URL"}

    last = None
    for url, kind in candidates:
        slug_hint = doc.get("title") or url
        result = fetcher.fetch(url, kind=kind, slug_hint=slug_hint)
        store.log_fetch(url=url, outcome=result.get("outcome", "error"),
                        http_status=result.get("http_status"), detail=result.get("detail"),
                        byte_count=result.get("bytes"), document_id=doc_id)
        last = result
        if result["status"] == "FULL_TEXT_RETRIEVED":
            # pubmed.ncbi.nlm.nih.gov landing pages carry abstracts, never full text
            if doc.get("platform") == "pubmed" and "pubmed.ncbi.nlm.nih.gov" in url:
                store.set_document_access(doc_id, "ABSTRACT_ONLY")
                result = dict(result, status="ABSTRACT_ONLY",
                              detail="pubmed landing page holds abstract only")
                return result
            store.set_document_access(doc_id, "FULL_TEXT_RETRIEVED", fulltext_path=result.get("path"))
            return result
    status = last["status"] if last else "EXTRACTION_FAILED"
    if status in ("LOGIN_REQUIRED", "ACCESS_RESTRICTED"):
        store.set_document_access(doc_id, status)
        return last
    if doc.get("abstract"):
        store.set_document_access(doc_id, "ABSTRACT_ONLY")
        return {"status": "ABSTRACT_ONLY", "detail": "full text unavailable; abstract retained"}
    store.set_document_access(doc_id, status)
    return last or {"status": "EXTRACTION_FAILED", "detail": "no candidates"}
