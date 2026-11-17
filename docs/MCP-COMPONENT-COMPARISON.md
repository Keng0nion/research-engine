# MCP-COMPONENT-COMPARISON

候选 MCP 服务器的对比、裁决与安装后状态。全部结论来自源码级审计（原始报告见 `docs/audit-raw/raw/`）。

## 已安装（Installed）

| 服务器 | 来源 | 形态 | 关键能力（源码核实） | 状态 |
|---|---|---|---|---|
| duckduckgo（既有） | mcp-duckduckgo（npx） | 通用网页 | search / fetch / research / search_and_crawl | 配置原有，保留 |
| arxiv | blazickjp/arxiv-mcp-server（uvx，PyPI，[pdf] 扩展） | 预印本 | 19 工具：搜索、下载、LaTeX 逐节精读、引用图、语义检索；本地论文库指向 `research/papers/arxiv` | **已安装/已配置/已验证启动** |
| pubmed | cyanheads/pubmed-mcp-server（npx） | 生物医学 | 12 工具：PubMed/EuropePMC 检索、全文回退链（PMC→EuropePMC→Unpaywall）、MeSH、iCite 指标、APA/MLA/BibTeX/RIS 格式化 | **已安装/已配置/已验证启动** |
| mcpsurfr | nkapila6/mcpsurfr（uvx，PyPI） | 检索重排 | MobileBERT TFLite 纯 numpy 本地语义重排 + BM25；只回答案段落省 token；免 key；无 torch | **已安装/已配置/已验证启动** |

安装位置：`~/.zcode/cli/config.json` → `mcp.servers`（改动前已备份 `config.json.bak-20261117-researchengine`）。
新服务器在 ZCode 下一次会话启动时加载；本会话内已完成进程级启动存活验证（三个服务器均正常初始化 stdio 传输）。

## 已审计未安装（Audited, not installed）

| 服务器 | 决定 | 理由（审计证据） |
|---|---|---|
| exa-labs/exa-mcp-server | 不安装 | 需付费 key；**Agnost 遥测（api.agnost.ai）在 mcp-handler 中无条件上报且仓库内无关闭开关**；12 工具中 8 个已标 Deprecated |
| firecrawl/firecrawl-mcp-server | 不安装 | 关键能力需付费 key；keyless 仅 scrape/search/parse 三个可用；反馈上报默认开启需双开关 opt-out；194 open issues；自托管整栈过重 |
| unclecode/crawl4ai | 不安装 | 自托管需 Playwright+Redis+RabbitMQ+Postgres（4GB 内存门槛）；JS 页面改由 Agent 浏览器工具升级处理 |
| kujenga/zotero-mcp | 不安装 | 与已装官方 zotero 插件（20+ 工具，含注释、高亮、写入）功能重复且为严格子集 |
| cyanheads/openalex-mcp-server | 不安装 | 引擎原生 OpenAlex provider 已覆盖管线需求；该仓仅 18★、重度依赖同作者框架 |
| smaniches/semantic-scholar-mcp | 不安装 | 引擎原生 S2 provider 覆盖检索与引用图；其独有面（推荐/片段）属交互增强 |
| damionrashford/RivalSearchMCP | 不安装 | **easyocr 为硬依赖（拉入 torch 2GB+）**，本机磁盘余量 12GB；其评分/冲突检测能力已由引擎自建模块覆盖 |
| dirmacs/daedra | 不安装（备用） | 14 个免 key 后端，设计优秀；但引入第三方预编译二进制，SearXNG 已覆盖聚合职能。SearXNG 故障时的首选替代 |
| TadMSTR/searxng-mcp | 不安装 | 需要外部 FlashRank 重排服务与完整本地栈；聚合职能已由引擎直连 SearXNG 覆盖 |
| gefsikatsinelou/MetaSearchMCP | 不安装 | 太年轻（2026-04 建库）、无 release、LICENSE 署名与仓库主对不上、默认向约 240 个 provider 全量扇出危险 |
| Shelpuk kindly-web-search-mcp-server | 不安装 | 搜索层 8 个 provider 全部需要付费 key 或自建 SearXNG，零免 key 路径 |
| tisDDM/searxng-mcp | 不安装 | 作者已标 deprecated |
| wong2/mcp-jina-reader | 不安装 | 无许可证 + 停更 23 个月 + 45 行转发壳（r.jina.ai 能力可直调，无需此壳） |
| qwe4559999/scopus-mcp | 不安装 | Scopus key 实质要求机构 Elsevier 订阅；3 个未修复 bug；6 个月停更 |
| akapet00/semantic-scholar-mcp | 不安装 | 服务器启动级 bug（issue #5）未修；6 个月停更 |
| 4 个 CNKI 候选 | 均未代装 | 唯一合规候选 SepineTam/cnki-mcp 需用户本人机构登录与交互式验证（列为可选步骤）；其余三个有批量下载防风控、自动 IP 登录或无许可证问题 |

## 引擎自建替代（不依赖 MCP 的能力）

以下能力由 `researchctl` 引擎直接实现（HTTP 直连或子进程桥），避免为每个数据源安装一个 MCP：

- 学术六源检索：OpenAlex、arXiv、Crossref、PubMed、Europe PMC、Semantic Scholar（全免费 REST）
- 多引擎聚合：本机 SearXNG JSON API（brave/bing/google cse/duckduckgo 等多引擎）
- AnySearch：既有技能 CLI 桥接
- 全文获取：httpx + trafilatura + pdftotext + Europe PMC JATS（分级访问状态）
- 引文图与核验：S2 references/citations + OpenAlex cited_by + Crossref/OpenAlex DOI 核验
- 冲突检测：数值分歧 + 极性对立（含否定式矛盾）
