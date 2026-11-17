"""MODULE 3: dynamic source router + MODULE 2: deterministic query variants.

Routing maps a domain (explicit or keyword-detected) to a provider set and
SearXNG category. Query expansion here only produces deterministic,
low-risk variants; the agent adds semantic variants on top.
"""

from __future__ import annotations

DOMAIN_PROVIDERS: dict[str, list[str]] = {
    "bio":      ["pubmed", "europepmc", "openalex", "semanticscholar", "arxiv"],
    "cs":       ["arxiv", "semanticscholar", "openalex", "searxng"],
    "math":     ["arxiv", "openalex", "crossref", "searxng"],
    "physics":  ["arxiv", "openalex", "crossref", "searxng"],
    "chem":     ["crossref", "openalex", "pubmed", "searxng"],
    "med":      ["pubmed", "europepmc", "openalex", "searxng"],
    "zh":       ["searxng", "anysearch", "openalex", "crossref"],
    "se":       ["searxng", "anysearch"],
    "news":     ["searxng", "anysearch"],
    "general":  ["searxng", "anysearch", "openalex", "crossref", "semanticscholar", "arxiv"],
}

_SEARXNG_CATEGORY = {"news": "news", "zh": "general"}

_KEYWORDS = (
    ("bio", ("protein", "gene", "genome", "cell", "bacteria", "enzyme", "rna", "dna",
             "蛋白质", "基因", "细胞", "酶", "分子生物")),
    ("med", ("patient", "clinical", "disease", "treatment", "trial", "covid", "cancer",
             "临床", "疾病", "治疗", "病例")),
    ("cs", ("machine learning", "neural", "deep learning", "algorithm", "transformer",
            "llm", "computer", "software", "深度学习", "神经网络", "算法", "机器学习")),
    ("math", ("theorem", "proof", "topology", "algebra", "geometry", "number theory",
              "定理", "证明", "代数", "几何")),
    ("physics", ("quantum", "particle", "relativity", "condensed matter", "photon",
                 "量子", "粒子", "相对论", "凝聚态")),
    ("chem", ("molecule", "chemical", "catalyst", "synthesis", "polymer",
              "化学", "分子", "催化", "合成")),
    ("news", ("news", "latest", "2026", "breaking", "today", "新闻", "最新", "今日", "刚刚")),
    ("se", ("github", "stackoverflow", "api reference", "sdk", "library", "npm", "pypi",
            "代码", "文档", "框架")),
)


def detect_domain(query: str) -> str:
    low = query.lower()
    for domain, words in _KEYWORDS:
        for w in words:
            if w in low:
                return domain
    return "general"


def route(query: str, domain: str = "auto", providers: list[str] | None = None) -> dict:
    dom = detect_domain(query) if domain in ("auto", "", None) else domain
    if dom not in DOMAIN_PROVIDERS:
        dom = "general"
    plist = providers if providers else list(DOMAIN_PROVIDERS[dom])
    opts = {}
    if dom in _SEARXNG_CATEGORY:
        opts["searxng"] = {"category": _SEARXNG_CATEGORY[dom]}
    return {"domain": dom, "providers": plist, "provider_opts": opts}


def expand_query(query: str, domain: str = "auto") -> list[str]:
    """Deterministic variants; duplicates removed, original kept first."""
    dom = detect_domain(query) if domain in ("auto", "", None) else domain
    variants = [query]
    if dom in ("cs", "math", "physics"):
        variants += ["site:arxiv.org " + query, query + " survey", query + " benchmark"]
    if dom == "bio":
        variants += ["site:pubmed.ncbi.nlm.nih.gov " + query, query + " review"]
    if dom == "se":
        variants += ["site:github.com " + query, "site:stackoverflow.com " + query,
                     query + " documentation"]
    if dom == "news":
        variants += [query + " 2026"]
    seen, out = set(), []
    for v in variants:
        key = v.strip()
        if key and key not in seen:
            seen.add(key)
            out.append(key)
    return out
