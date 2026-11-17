"""Unpaywall resolver: find legal open-access copies of a DOI (email required, free)."""

from __future__ import annotations

from .base import Hit, HttpProvider, ProviderError, contact_email
from engine import util


class UnpaywallProvider(HttpProvider):
    name = "unpaywall"
    doc_types = ()
    base_url = "https://api.unpaywall.org/v2"

    def available(self) -> str | None:
        if not contact_email():
            return "disabled: Unpaywall requires an email address (set RE_CONTACT_EMAIL)"
        return None

    def search(self, query: str, limit: int = 10, timeout: float = 25.0,
               opts: dict | None = None) -> list[Hit]:
        # Unpaywall is a DOI resolver, not a search engine; use resolve() instead.
        raise ProviderError("unavailable", "unpaywall is a DOI resolver; use resolve(doi)")

    def resolve(self, doi: str, timeout: float = 20.0) -> dict | None:
        """Return {is_oa, best_url, pdf_url, title, year, venue} for a DOI, or None."""
        email = contact_email()
        if not email:
            return None
        clean = util.normalize_doi(doi)
        url = self.base_url + "/" + clean
        try:
            data = self._get_json(url, {"email": email}, timeout)
        except ProviderError:
            return None
        best = data.get("best_oa_location") or {}
        return {
            "is_oa": bool(data.get("is_oa")),
            "best_url": best.get("url") or best.get("url_for_landing_page"),
            "pdf_url": best.get("url_for_pdf"),
            "title": data.get("title"),
            "year": data.get("year"),
            "venue": data.get("journal_name"),
            "license": best.get("license"),
        }
