"""Provider registry."""

from __future__ import annotations

from .base import Hit, Provider, ProviderError
from .anysearch import AnySearchProvider
from .arxiv import ArxivProvider
from .crossref import CrossrefProvider
from .europepmc import EuropePmcProvider
from .openalex import OpenAlexProvider
from .pubmed import PubMedProvider
from .searxng import SearxngProvider
from .semanticscholar import SemanticScholarProvider
from .unpaywall import UnpaywallProvider

REGISTRY: dict[str, type[Provider]] = {
    cls.name: cls
    for cls in (
        OpenAlexProvider,
        ArxivProvider,
        CrossrefProvider,
        PubMedProvider,
        EuropePmcProvider,
        SemanticScholarProvider,
        UnpaywallProvider,
        SearxngProvider,
        AnySearchProvider,
    )
}

SEARCHABLE = tuple(
    name for name, cls in REGISTRY.items() if "search" in cls.__dict__ or cls.search is not Provider.search
)

__all__ = ["Hit", "Provider", "ProviderError", "REGISTRY", "SEARCHABLE", "get_provider"]


def get_provider(name: str) -> Provider:
    cls = REGISTRY.get(name)
    if cls is None:
        raise KeyError("unknown provider: " + name)
    return cls()
