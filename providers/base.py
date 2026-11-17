"""Provider interface and shared HTTP helpers.

Includes a DNS-over-HTTPS fallback: some home/campus resolvers return
empty answers for specific domains (observed here for api.openalex.org
and api.crossref.org). When normal resolution/connect fails, the request
is retried against a DoH-resolved IP with correct Host header and TLS
SNI, so certificate verification still applies to the real hostname.
"""

from __future__ import annotations

import os
import re
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from urllib.parse import urlsplit, urlunsplit

import httpx

_MAX_XML_BYTES = 8 * 1024 * 1024


def safe_parse_xml(xml_text: str) -> ET.Element:
    """Parse untrusted XML with entity-expansion guards.

    Policy: DOCTYPE headers without an internal subset are tolerated (NLM
    and arXiv publish them); anything with an internal DTD subset or any
    ENTITY declaration is rejected; size is capped.
    """
    if len(xml_text) > _MAX_XML_BYTES:
        raise ProviderError("parse_error", "XML response exceeds size cap")
    lowered = xml_text.lower()
    if "<!entity" in lowered:
        raise ProviderError("parse_error", "XML with entity declarations rejected")
    if re.search(r"<!doctype[^>]*\[", lowered):
        raise ProviderError("parse_error", "XML with internal DTD subset rejected")
    try:
        return ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise ProviderError("parse_error", "invalid XML: " + str(exc)) from exc

USER_AGENT = "research-engine/0.1 (personal research tool; contact via RE_CONTACT_EMAIL)"

_DOH_URL = "https://1.1.1.1/dns-query"
_doh_cache: dict[str, tuple[float, list[str]]] = {}
_DOH_TTL = 300.0


def contact_email() -> str | None:
    return os.environ.get("RE_CONTACT_EMAIL") or None


def _doh_resolve(host: str) -> list[str]:
    now = time.monotonic()
    cached = _doh_cache.get(host)
    if cached and now - cached[0] < _DOH_TTL:
        return cached[1]
    ips: list[str] = []
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(_DOH_URL, params={"name": host, "type": "A"},
                              headers={"accept": "application/dns-json"})
            if resp.status_code == 200:
                for answer in (resp.json().get("Answer") or []):
                    if answer.get("type") == 1 and answer.get("data"):
                        ips.append(str(answer["data"]))
    except (httpx.HTTPError, ValueError):
        ips = []
    _doh_cache[host] = (now, ips)
    return ips


def http_request(method: str, url: str, *, params: dict | None = None,
                 headers: dict | None = None, timeout: float = 25.0) -> httpx.Response:
    """GET/POST with a DoH fallback on DNS or connect failure."""
    merged = dict({"User-Agent": USER_AGENT}, **(headers or {}))
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True, headers=merged) as client:
            return client.request(method, url, params=params)
    except httpx.ConnectError:
        pass  # fall through to DoH resolution

    parts = urlsplit(url)
    host = parts.hostname or ""
    ips = _doh_resolve(host)
    if not ips:
        raise ProviderError("http_error", "dns resolution failed and DoH fallback found no addresses")
    netloc_host = host + (":" + str(parts.port) if parts.port else "")
    last_exc: Exception | None = None
    for ip in ips:
        ip_netloc = ip + (":" + str(parts.port) if parts.port else "")
        ip_url = urlunsplit((parts.scheme, ip_netloc, parts.path, parts.query, ""))
        try:
            req = httpx.Request(method, ip_url, params=params,
                                headers=dict(merged, Host=netloc_host),
                                extensions={"sni_hostname": host})
            with httpx.Client(timeout=timeout) as client:
                return client.send(req, follow_redirects=True)
        except httpx.HTTPError as exc:
            last_exc = exc
            continue
    raise ProviderError("http_error", "DoH fallback connect failed: " + str(last_exc)[:150])


@dataclass
class Hit:
    title: str | None = None
    url: str | None = None
    snippet: str | None = None
    platform: str = ""
    published_at: str | None = None
    authors: list[str] = field(default_factory=list)
    doi: str | None = None
    arxiv_id: str | None = None
    pmid: str | None = None
    doc_type: str | None = None
    abstract: str | None = None
    extra: dict = field(default_factory=dict)


class ProviderError(Exception):
    def __init__(self, kind: str, message: str):
        super().__init__(message)
        self.kind = kind  # timeout | rate_limited | http_error | parse_error | unavailable
        self.message = message


class Provider:
    """Base class. Subclasses set name/doc_types and implement search()."""

    name: str = ""
    doc_types: tuple = ("paper", "webpage")

    def available(self) -> str | None:
        """Return None when usable, otherwise a human-readable reason."""
        return None

    def search(self, query: str, limit: int = 10, timeout: float = 25.0,
               opts: dict | None = None) -> list[Hit]:
        raise NotImplementedError


class HttpProvider(Provider):
    """Shared JSON/text GET helpers with consistent error mapping."""

    base_url: str = ""

    def _get_json(self, url: str, params: dict, timeout: float) -> dict:
        resp = self._request(url, params, timeout)
        try:
            return resp.json()
        except ValueError as exc:
            raise ProviderError("parse_error", "non-JSON response from " + url) from exc

    def _get_text(self, url: str, params: dict, timeout: float) -> str:
        return self._request(url, params, timeout).text

    def _request(self, url: str, params: dict, timeout: float) -> httpx.Response:
        try:
            resp = http_request("GET", url, params=params, timeout=timeout)
        except httpx.TimeoutException as exc:
            raise ProviderError("timeout", str(exc)) from exc
        except ProviderError:
            raise
        except httpx.HTTPError as exc:
            raise ProviderError("http_error", str(exc)) from exc
        if resp.status_code == 429:
            raise ProviderError("rate_limited", "429 from " + url)
        if resp.status_code >= 400:
            raise ProviderError("http_error", "HTTP " + str(resp.status_code) + " from " + url)
        return resp
