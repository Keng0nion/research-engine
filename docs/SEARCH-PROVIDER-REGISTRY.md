# SEARCH-PROVIDER-REGISTRY

引擎供应商的权威登记表。可执行版本在 `config/providers.yaml`；本档记录实测状态（2026 年 11 月 17 日测）。

## 引擎原生供应商（researchctl 直连）

| 供应商 | 端点 | 凭证 | 限速/预算 | 实测状态 |
|---|---|---|---|---|
| openalex | api.openalex.org | 免 key（可选 mailto） | 免费池；带 key 更高 | **已验证**（1.3 秒 5 命中；DoH 兜底生效） |
| arxiv | export.arxiv.org | 免 key | 约 3 秒/请求礼貌间隔 | **已验证**（2.3 秒 5 命中） |
| crossref | api.crossref.org | 免 key（可选 mailto） | 免费 | **已验证**（2.6 秒 5 命中；DoH 兜底生效） |
| pubmed | eutils.ncbi.nlm.nih.gov | 免 key（可选 NCBI_API_KEY 3→10 rps） | 无 key 3 rps | **已验证**（1.6 秒 5 命中 + efetch 摘要） |
| europepmc | ebi.ac.uk/europepmc REST | 免 key | 软配额 | **已验证**（2.3 秒 5 命中 + OA 全文 XML） |
| semanticscholar | api.semanticscholar.org | 免 key（S2_API_KEY 可选提速） | 共享池（实测偶发 429，引擎自动重试） | **已验证**（引用图 25 条成功；429 时降级） |
| unpaywall | api.unpaywall.org | **必须邮箱（RE_CONTACT_EMAIL）** | 免费 | 已配置未启用（用户未设邮箱，引擎自动禁用） |
| searxng | 127.0.0.1:8080（本机 Docker） | 无（回环） | 单用户无限制 | **已验证**（JSON API 51 条结果；引擎的工作马） |
| anysearch | 既有技能 CLI（本机） | 免 key（匿名层） | 匿名额度 | **已验证**（3.3 秒 5 命中，解析器正常） |

## SearXNG 内部引擎实测（2026 年 11 月 17 日，本机 IP）

| 引擎 | 状态 | 说明 |
|---|---|---|
| brave | 正常 | 结果质量好，英文主力 |
| bing | 正常 | 稳定 |
| google cse | 正常（意外可用） | 免 key 出结果，中文质量好 |
| duckduckgo | 时好时坏 | 偶发 CAPTCHA，重试可恢复 |
| google（直连抓取） | 持续 access denied | 已禁用（上游默认也是禁用） |
| mojeek / wikipedia / startpage 等 | 正常（默认启用集） | 补充覆盖 |

## Agent 侧 MCP 工具（不属引擎直连，登记路由）

| 服务器 | 关键工具 | 凭证 | 状态 |
|---|---|---|---|
| duckduckgo | search / fetch / research | 免 key | 既有，保留 |
| arxiv（新装） | search_papers / download_paper / get_paper_latex_section / citation_graph | 免 key | 下次会话生效 |
| pubmed（新装） | pubmed_search_articles / pubmed_fetch_fulltext / pubmed_lookup_mesh | 免 key（邮箱可选） | 下次会话生效 |
| mcpsurfr（新装） | search（答案段落）/ rag_search_ddgs / read_url / deep_research | 免 key | 下次会话生效 |
| zotero（既有插件） | search_library / read_fulltext / export_bib / cite | 本地 Zotero | 既有 |

## 路由（MODULE 3）当前的领域映射

| 领域 | 供应商集 |
|---|---|
| bio | pubmed、europepmc、openalex、semanticscholar、arxiv |
| med | pubmed、europepmc、openalex、searxng |
| cs | arxiv、semanticscholar、openalex、searxng |
| math / physics | arxiv、openalex、crossref、searxng |
| chem | crossref、openalex、pubmed、searxng |
| zh | searxng、anysearch、openalex、crossref（CNKI 通道为用户可选，未装） |
| se | searxng、anysearch |
| news | searxng（news 分类）、anysearch |
| general | searxng、anysearch、openalex、crossref、semanticscholar、arxiv |

领域自动检测用关键词启发式（`engine/router.py`）；`--domain` 可手动覆盖。新增供应商只需在 `providers/` 加一个类并在注册表登记，不改动路由以外代码。

## 网络环境适配（重要）

本机网络网关 DNS（172.16.22.1）对 api.openalex.org 与 api.crossref.org 间歇返回空应答。引擎内置 **DoH 兜底**：系统解析或连接失败时，经 1.1.1.1 的 DNS-over-HTTPS JSON 接口解析 IP，再以正确的 Host 头与 TLS SNI 直连该 IP（证书仍按真实域名校验）。已验证两域名经兜底各返回 200。

## 已审计未接入的供应商与服务

Exa、Firecrawl、Parallel（付费；Parallel 匿名 MCP 端点 `search.parallel.ai/mcp` 为零成本备选，HTTP 传输兼容性未验证）、Tavily、Serper、Brave API、Scopus（机构订阅）——全部留档于 `docs/decisions.md`，启用需用户提供凭证且另行确认。
