"""AnySearch bridge: invoke the existing skill CLI and parse its text output.

The CLI is an existing, user-installed tool (anonymous tier works without a
key). Output is markdown-ish; the parser is tolerant and degrades to
title/url extraction when fields are missing.

Execution safety: subprocess runs with an inline argument-list literal and
shell=False; the query is passed after a ``--`` separator so it can never
be parsed as a CLI flag; NUL bytes are rejected.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess

from .base import Hit, Provider, ProviderError

DEFAULT_CLI = "/Users/luna/.claude/skills/anysearch-skill-2.1.0/scripts/anysearch_cli.py"

_URL_RE = re.compile(r"\*\*URL\*\*:\s*(https?://\S+)")
_SOURCE_RE = re.compile(r"^source:\s*(\S+)", re.M)
_TITLE_FIELD_RE = re.compile(r"^title:\s*(.+)$", re.M)
_SNIPPET_RE = re.compile(r"^snippet:\s*'(.+?)'$", re.M | re.S)
_BLOCK_SPLIT_RE = re.compile(r"^###\s+", re.M)


def _extract_block_fields(block: str) -> dict:
    out: dict = {}
    m = _URL_RE.search(block)
    if m:
        out["url"] = m.group(1)
    m = _SOURCE_RE.search(block)
    if m:
        out["source"] = m.group(1)
    m = _TITLE_FIELD_RE.search(block)
    if m:
        out["title"] = m.group(1).strip().strip("'")
    m = _SNIPPET_RE.search(block)
    if m:
        out["snippet"] = " ".join(m.group(1).split())
    return out


class AnySearchProvider(Provider):
    name = "anysearch"
    doc_types = ("webpage", "paper")

    def _cli_path(self) -> str | None:
        path = os.environ.get("RE_ANYSEARCH_CLI", DEFAULT_CLI)
        return path if os.path.exists(path) else None

    def available(self) -> str | None:
        if not self._cli_path():
            return "disabled: anysearch CLI not found"
        if not shutil.which("python3"):
            return "disabled: python3 not on PATH"
        return None

    def search(self, query: str, limit: int = 10, timeout: float = 40.0,
               opts: dict | None = None) -> list[Hit]:
        cli = self._cli_path()
        if not cli:
            raise ProviderError("unavailable", "anysearch CLI not found")
        if "\x00" in query:
            raise ProviderError("unavailable", "query contains NUL byte")
        n = min(max(limit, 1), 10)
        # inline argument-list literal + shell=False; "--" anchors the query as a positional value
        try:
            proc = subprocess.run(["python3", cli, "search", "--max_results", str(n), "--", query], shell=False, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            raise ProviderError("timeout", "anysearch CLI timed out") from exc
        if proc.returncode != 0:
            raise ProviderError("http_error", "anysearch CLI exited " + str(proc.returncode))
        return self._parse(proc.stdout)

    def _parse(self, text: str) -> list[Hit]:
        hits: list[Hit] = []
        blocks = _BLOCK_SPLIT_RE.split(text)
        for block in blocks[1:]:
            lines = block.splitlines()
            if not lines:
                continue
            head = lines[0].strip()
            head_title = re.sub(r"^\d+\.\s*", "", head).strip()
            fields = _extract_block_fields(block)
            url = fields.get("url")
            title = fields.get("title") or head_title or None
            if not url and not title:
                continue
            src = (fields.get("source") or "").lower()
            doc_type = "paper" if src in ("arxiv", "openalex", "pubmed", "doi", "crossref", "semanticscholar") else "webpage"
            hits.append(Hit(
                title=title,
                url=url,
                snippet=fields.get("snippet"),
                platform=self.name,
                doc_type=doc_type,
                extra={"anysearch_source": fields.get("source")},
            ))
        return hits
