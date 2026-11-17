审计完成。以下为 Stage 1+2 只读深查报告。审计纪律说明：全程未运行任何克隆仓库内脚本、未安装任何依赖；4 个小仓库以 `git clone --depth 1` 克隆后纯文本阅读（存于 `/tmp/re-audit/<name>`），crawl4ai 因体积 152MB 改用 `gh api` 与 raw.githubusercontent.com 读目录树与关键文件。所有结论均标注文件级证据；未验证处明确写「未验证」。

---

## cyanheads/openalex-mcp-server

- URL：https://github.com/cyanheads/openalex-mcp-server
- stars 18 / forks 8（建库于 2026 年 3 月 24 日）/ license Apache-2.0
- 最近提交（仓库 pushed_at）：2026 年 11 月 13 日
- releases：最新 v0.11.1（2026 年 11 月 11 日），此前 v0.11.0（10 月 29 日）、v0.10.1（10 月 26 日）
- open issues：5（含「hosted 端点是否支持传入用户自带 OpenAlex key」「resolve_name 的 filter 别名未翻译」等）
- 源码副本：`/tmp/re-audit/openalex-mcp-server`

**实际能力（源码佐证）**：5 个 MCP 工具 + 2 个 prompt + 1 个随包投放的 agent skill（`openalex-guide`）。工具注册名逐一核实于 `/tmp/re-audit/openalex-mcp-server/src/mcp-server/tools/definitions/`：

1. `openalex_search_entities`（search-entities.tool.ts:130）——跨 9 类实体（works、authors、sources、institutions、topics、keywords、publishers、funders、awards）检索、按 id 直取、复杂 filter 语法（AND、OR 用 `|`、AND 用 `+`、`!`、区间、比较）、语义检索、游标分页、随机采样、select 投影；
2. `openalex_analyze_trends`（analyze-trends.tool.ts:24）——group_by 聚合，趋势与分布分析；
3. `openalex_resolve_name`（resolve-name.tool.ts:141）——名称到 ID 消歧（autocomplete），支持 DOI、ORCID、ROR、PMID、PMCID、ISSN、arXiv ID 直接解析；
4. `openalex_get_citation_graph`（citation-graph.tool.ts:65）——引用图单跳：`cites`、`cited_by`、`related_to`；
5. `openalex_describe_fields`（describe-fields.tool.ts:21）——字段目录，无网络调用。

prompt：`openalex_literature_review`、`openalex_research_landscape`。另有一个公共托管端点 `https://openalex.caseyjhand.com/mcp`（README 声明）。

**OpenAlex API key 与 polite pool（重点核实）**：
1. 无需 key，默认匿名运行（README 与源码一致）；
2. `OPENALEX_API_KEY` 可选，是免费账号 key，以 `api_key=` 发送，提高速率与每日预算（openalex-service.ts:1782）；
3. `OPENALEX_MAILTO` 可选，以 `mailto=` 发送，但源码注释明确写着它「现在仅是礼貌标识，对预算/速率无影响」（openalex-service.ts:1779 至 1780）。也就是说 polite pool 的 mailto 在这个实现里没有实际提额作用。

**默认 rate limit 处理（重点核实）**：每呼叫计数并上报 OpenAlex 每日预算消耗与余额（`budget.costUsd`、`remainingUsd`）；429 被区分为两类——突发限流（可重试）与每日预算耗尽（不重试，提示次日 UTC 零点重置，openalex-service.ts:1494 至 1504）；付费计划才能用的 filter 走 429 时转为 Forbidden 不重试（openalex-service.ts:1887 至 1889）；重试参数：最多 3 次尝试、单次超时 10 秒、基础退避 1000ms 加抖动（MAX_ATTEMPTS=3、BASE_BACKOFF_MS=1000、REQUEST_TIMEOUT_MS=10_000，openalex-service.ts:1131 至 1133）；引用图工具种子查询与图页共享 50 秒截止。

**依赖与运行要求**：Node.js >= 24 或 Bun >= 1.4.4；仅 3 个直接依赖（`@cyanheads/mcp-ts-core`、`zod`、`pino-pretty`）；无需浏览器；无本地服务依赖。安装：`npx -y @cyanheads/openalex-mcp-server` 或 Docker（HTTP 传输）。

**认证与成本**：key 免费、可选。免费边界核实：匿名额度小于带 key；例外是 `created_date`、`updated_date` 及其 `from_/to_` 过滤字段仅面向 OpenAlex 付费计划，不带 key 时会以 `upstream_plan_required` 报错且不重试（README 与错误契约源码均证实）。其余功能全免费。

**安全观察**：src 目录 grep 无任何文件写入（无 writeFile/appendFile）；日志经框架写 `LOGS_DIR`（默认 `<project-root>/logs`）；错误信息中的 URL 被 url-redaction 白名单机制裁到 origin，防止 `api_key` 与 `mailto` 泄漏进错误文本（url-redaction.ts 与 openalex-service.ts:1780 附近注释）；OpenTelemetry 默认关闭（`OTEL_ENABLED=false`）。存在官方托管的公共 MCP 端点（第三方运营方 caseyjhand.com），传给它的是公开学术目录查询数据，敏感性低。

**结论**：建议作为本项目 OpenAlex 目录层的主力，直装。红旗：一、仓库年轻（2026 年 3 月建库）、star 数低（18）；二、重度依赖同作者框架 `@cyanheads/mcp-ts-core`，供应链集中；三、建议锁定版本（固定版本的 npx 或 Docker tag），避免浮动升级。

---

## cyanheads/pubmed-mcp-server

- URL：https://github.com/cyanheads/pubmed-mcp-server
- stars 168 / license Apache-2.0
- 最近提交（pushed_at）：2026 年 11 月 13 日
- releases：最新 v2.12.2（2026 年 11 月 13 日），此前 v2.12.1（11 月 11 日）、v2.12.0（11 月 3 日）
- open issues：7
- 源码副本：`/tmp/re-audit/pubmed-mcp-server`

**实际能力（源码佐证）**：12 个 MCP 工具 + 1 个 resource（`pubmed://database/info`）+ 1 个 prompt（`research_plan`），工具注册名逐一核实于 `src/mcp-server/tools/definitions/`：

1. `pubmed_search_articles`（search-articles.tool.ts:514）——PubMed 完整查询语法、结构化过滤、日期范围、结果摘要；
2. `pubmed_fetch_articles`（fetch-articles.tool.ts:498）——按 PMID 取元数据、摘要、MeSH、化合物、基金、试验注册号、撤稿与更正通告；
3. `pubmed_fetch_fulltext`（fetch-fulltext.tool.ts:2006）——按 PMID/PMCID/DOI 取全文，回退链 PMC → Europe PMC → Unpaywall；
4. `pubmed_europepmc_search`（pubmed-europepmc-search.tool.ts:72）——Europe PMC 检索（预印本、专利、Agricola）；
5. `pubmed_europepmc_fetch`（pubmed-europepmc-fetch.tool.ts:159）——Europe PMC 完整记录；
6. `pubmed_fetch_citation_metrics`（fetch-citation-metrics.tool.ts:156）——NIH iCite 指标（RCR、NIH 百分位、引用数）；
7. `pubmed_format_citations`（format-citations.tool.ts:64）——APA 7、MLA 9、BibTeX、RIS、Vancouver；
8. `pubmed_find_related`（find-related.tool.ts:377）——相似/引用/参考文献，NCBI 失败回退 Europe PMC 再回退 OpenAlex；
9. `pubmed_spell_check`（spell-check.tool.ts:17）——NCBI ESpell；
10. `pubmed_lookup_mesh`（lookup-mesh.tool.ts:193）——MeSH 各类记录；
11. `pubmed_lookup_citation`（lookup-citation.tool.ts:158）——ECitMatch 残片引文解析；
12. `pubmed_convert_ids`（convert-ids.tool.ts:81）——DOI/PMID/PMCID 互转（PMC ID Converter）。

**Europe PMC / Unpaywall / PMC 全文集成整合情况**：
1. Europe PMC：独立 2 工具，且是全文链第二级与 find_related 回退；由 `EUROPEPMC_ENABLED` 控制，设 false 时两个工具不注册（src/index.ts:41 已核实条件注册）、全文链跳过该级；
2. Unpaywall：全文链第三级，构造服务的前置条件是设置了 `UNPAYWALL_EMAIL`，缺省则整级禁用（unpaywall-service.ts:35，fetch-fulltext.tool.ts:2721 报 `detail: 'UNPAYWALL_EMAIL is not set'`）；
3. PMC 全文：经 NCBI E-utilities 取 JATS 结构化全文，解析出章节、表格、图表（fetch-fulltext.tool.ts:2061 工具描述）。

**各自需要的 key**：NCBI 系（PubMed、PMC、iCite、ECitMatch、ESpell、EInfo）与 Europe PMC 均无需 key；`NCBI_API_KEY` 可选（免费），把速率从 3 次/秒提到 10 次/秒；`NCBI_ADMIN_EMAIL` 建议填写；`UNPAYWALL_EMAIL` 必填（免费，只需邮箱）才能启用 Unpaywall 级；`EUROPEPMC_EMAIL` 可选。

**MeSH 支持**：有。专用工具 `pubmed_lookup_mesh`（descriptor、supplementary concept、qualifier、pharmacological action 四类记录，返回 `meshId`、树号、scope note、entry term 与可搜索 MeSH 的 PubMed 子句），且 `pubmed_fetch_articles` 默认带出 `includeMesh` 的 MeSH 词与化合物。

**rate limit 处理（源码核实）**：共享 NCBI 请求队列——请求起点加间隔（无 key 400ms、有 key 120ms，server-config.ts:130）、并发上限 8、重试 6 次、单请求超时 30 秒、全会话截止 60 秒；任一呼叫遇到 NCBI 429 触发全队列冷却门（1 秒起步，连续 429 加倍，成功一次复位，request-queue.ts:17 至 18）；Europe PMC 独立节流（200ms 间隔、重试 3、超时 20 秒、截止 45 秒）。

**依赖与运行要求**：Node.js >= 24 或 Bun >= 1.4.4；关键依赖 `fast-xml-parser`、`unpdf`（PDF 文本）、`linkedom`、`sanitize-html`、`defuddle`（HTML 抽取，跑在工作线程，10 秒截止、每进程并发 2）；无需浏览器；无本地服务依赖。

**认证与成本**：全部数据源免费。核对无付费例外（iCite、ECitMatch 亦是 NIH 免费服务）。有托管公共端点 `https://pubmed.caseyjhand.com/mcp`（第三方运营）。

**安全观察**：fetch-redaction.ts 把 fetch 拒绝信息中的 URL 裁到 origin，避免 NCBI key、邮箱与查询词进入错误文本与日志；src 无文件写入；OTEL 默认关闭；日志到 `LOGS_DIR`。反面发现（代码级核实）：`pubmed_fetch_fulltext` 的 Unpaywall 内容抓取以 `redirect: 'follow'` 整读响应体（unpaywall-service.ts:210 至 240 的 fetchAs，`readBody(response.arrayBuffer())` 无字节上限），且未见私网目的地拒绝逻辑——与仓库 open issues 中「Unpaywall content is read with no size limit」与「refuse private-network destinations」两项待办吻合（issue 标题经 API 核实，代码现状经本次 grep 核实为尚未有防护）。

**结论**：建议作为 biomedical 文献层主力，直装；配置 `NCBI_API_KEY`、`NCBI_ADMIN_EMAIL`、`UNPAYWALL_EMAIL`。红旗：一、Unpaywall 级抓取无大小与私网防护（维护者已在 issue 登记）；二、公共托管端点不宜传入未公开的研究查询。

---

## blazickjp/arxiv-mcp-server

- URL：https://github.com/blazickjp/arxiv-mcp-server
- stars 3282 / license Apache-2.0
- 最近提交：2026 年 11 月 14 日（`git log` 于克隆副本核实）
- releases：最新 v0.8.2（2026 年 10 月 8 日），此前 v0.8.1（10 月 5 日）、v0.8.0（10 月 3 日）
- open issues：8
- 源码副本：`/tmp/re-audit/arxiv-mcp-server`

**实际能力（源码佐证）**：19 个 MCP 工具（README 声明 19，与 src/arxiv_mcp_server/server.py:85 的 list_tools 数组一致；工具名逐一取自 `src/arxiv_mcp_server/tools/*.py` 的 `types.Tool(name=...)`）：

1. `search_papers`（search.py:531）
2. `get_abstract`（get_abstract.py:25）
3. `download_paper`（download.py:702）
4. `list_papers`（list_papers.py:28）
5. `read_paper`（read_paper.py:25）
6. `get_paper_outline`（paper_outline.py:1177）
7. `read_paper_section`（paper_outline.py:1205）
8. `search_paper_text`（paper_outline.py:1228）
9. `get_paper_latex`（latex.py:274）
10. `list_paper_latex_sections`（latex.py:289）
11. `get_paper_latex_section`（latex.py:314）
12. `citation_graph`（citation_graph.py:56）
13. `export_citations`（export_citations.py:199）
14. `watch_topic`（alerts.py:28）
15. `list_watches`（alerts.py:111）
16. `check_alerts`（alerts.py:77）
17. `unwatch_topic`（alerts.py:127）
18. `semantic_search`（semantic_search.py:46，需 `[pro]` 附加依赖）
19. `reindex`（semantic_search.py:81，需 `[pro]`）

另有 7 个内置 prompt（research-discovery、deep-paper-analysis、summarize_paper、compare_papers、literature_review、literature-synthesis、research-question）。

**PDF 下载与本地存储方式（重点核实）**：
1. `download_paper` 优先抓 arXiv HTML 页转 Markdown（download.py:897 构造 `https://arxiv.org/html/{paper_id}`），无可用 HTML 时回退 PDF 转换（需 `pdf` 附加依赖 `pymupdf4llm`、`pymupdf-layout`，pyproject.toml 已核实）；
2. 存储目录：默认 `~/.arxiv-mcp-server/papers`，可用命令行参数 `--storage-path` 指定（config.py:204 至 253 的 `STORAGE_PATH` 与 `_get_storage_path_from_args`）；经核实存储路径只走命令行参数，**未见对应环境变量**；
3. 落盘形态：Markdown 与 sidecar 文件（download.py:559 至 564，`storage_path / f"{filesystem_arxiv_stem(paper_id)}{suffix}"`）；LaTeX 源码档案与引用图、topic watch（告警）也全部缓存在该目录；内容返回默认截断到 12000 字符。

**是否依赖外部 API（核实）**：依赖。arXiv 官方 API（`https://export.arxiv.org/api/query`，download.py:1199）与 arxiv.org 的 HTML/PDF/LaTeX 源档案；`citation_graph` 走 Semantic Scholar Graph API（citation_graph.py:29，`https://api.semanticscholar.org/graph/v1`，每篇论文一次调用、结果磁盘缓存）。Semantic Scholar 可选免费 key `SEMANTIC_SCHOLAR_API_KEY`（无 key 在配额耗尽前可用）；arXiv 侧无 key，服务端自带约 3 秒/请求的进程级节流（config.py:51 `delay_seconds=3.0` 与 README 描述），重试参数 `ARXIV_MAX_RETRIES=2`、初始退避 2 秒、上限 30 秒，406（IP 级限流）单独走最小重试。

**依赖与运行要求**：Python >= 3.11；安装走 `uvx arxiv-mcp-server`（PyPI 包名 `arxiv-mcp-server`）；基础依赖含 `arxiv`、`httpx`、`aiohttp`、`mcp`；`[pdf]` 附加包用于 PDF 转换，`[pro]` 加 `sentence-transformers` 与 `numpy`（嵌入模型目前硬编码 all-MiniLM-L6-v2，见 open issue）；无需本地服务依赖。

**认证与成本**：全免费，无例外。唯一付费提示项是 Semantic Scholar 配额，免费 key 即可解决。

**安全观察**：无遥测迹象（克隆副本内未发现外发统计）；写入仅限 storage path；README 与 SECURITY.md 主动声明「论文正文是不可信外部内容，可能包含提示注入」，并给出缓解建议——这是该仓库的加分项。README 特别警告存在同名 npm 包，禁止用 npm/npx 安装本服务（供应链陷阱提示）。stdout 纪律：内容走 MCP 协议，无关消息不污染 stdout。

**结论**：建议作为预印本层与本地论文阅读工作台（LaTeX 逐节读取是本项目文献精读的差异化能力）。红旗：一、论文内容 prompt injection 天生存在（官方已披露并建议客户端审批控制）；二、citation_graph 无 key 时受 S2 配额制约；三、安装必须只认 PyPI，勿碰同名 npm 包。

---

## kujenga/zotero-mcp

- URL：https://github.com/kujenga/zotero-mcp
- stars 162 / license MIT
- 最近提交：2026 年 8 月 6 日（pushed_at 8 月 7 日）；近三个月无提交
- releases：最新 0.3.1（2026 年 8 月 7 日）
- open issues：4
- 源码副本：`/tmp/re-audit/zotero-mcp`（全仓库合计仅 953 行 Python，已全量读过关键文件）

**实际能力（源码佐证）**：仅 3 个 MCP 工具，全部只读，注册于 `src/zotero_mcp/__init__.py` 的 `@mcp.tool` 装饰器（行 345、365、557）：

1. `zotero_item_metadata`——单条完整元数据（按 API 返回字段动态渲染，未知字段进 Other Fields）；
2. `zotero_item_fulltext`——全文（走 Zotero 的索引全文接口 `zot.fulltext_item(attachment.key)`）；附件选择逻辑：先取子附件，PDF 优先、HTML 次之、其他再次，同类按大小代理排序（client.py:44 至 110）；
3. `zotero_search_items`——文本检索，查询模式 `titleCreatorYear`（题录）与 `everything`（含摘要、Extra、笔记与附件全文）；搜索结果会附上子附件命中的关联处理。

**连接方式（重点核实）**：二选一，证据在 client.py:16 至 36：
1. 本地 API：`ZOTERO_LOCAL=true`，此时 `ZOTERO_LIBRARY_ID` 缺省为 `"0"`（即当前用户），不需要 key；前提是本机 Zotero 桌面端正在运行且已开启「允许此计算机上的其他应用程序与 Zotero 通信」（README 第 31 至 34 行）。**本地 API 端口号未在本仓库源码中出现（由 pyzotero 客户端封装），具体端口值本次未验证**；
2. Web API：需要 `ZOTERO_API_KEY` + `ZOTERO_LIBRARY_ID`（+ 可选 `ZOTERO_LIBRARY_TYPE`，user 或 group），用法向 api.zotero.org，无需桌面端运行。

**哪些功能需要本地 Zotero 桌面端运行**：本地模式（`ZOTERO_LOCAL=true`）下 3 个工具全部需要桌面端在跑；Web API 模式下全部 3 个工具都不需要桌面端，但全文工具的可用性取决于该文献是否已同步附件、且 Zotero 服务端能给出索引全文。另有一个差异点已核实（README 附录）：本地 API 的快搜索引包含 citation key，Web API 不含。

**依赖与运行要求**：Python >= 3.11；依赖 `mcp[cli]` 2.x、`pyzotero>=1.6.8`、`pydantic`、`python-dotenv`；`uvx zotero-mcp@latest` 或 Docker；无浏览器需求。

**认证与成本**：全免费（Zotero Web API 本身免费）；本地模式零凭据。

**安全观察**：仓库极小，无遥测、无多余外发请求；错误以文本返回而非抛出。Web API 模式凭据只经环境变量；本地模式完全不出本机。

**与「已有 Zotero 集成」的去重复核（本机 zotero 插件 0.2.1，路径 `/Users/luna/.zcode/cli/plugins/cache/zcode-plugins-official/zotero/0.2.1`）**：
1. 已有插件（`plugin_zotero`）工具面覆盖 `list_collections`、`search_library`、`get_item`、`search_annotations`、`read_fulltext`、`find_in_pdf`、`cite`、`export_bib`、`add_item`、`attach_pdf`、`update_item`、`add_note`、`create_collection`、`highlight`、`save_highlights`、`show_items`、`open_item`、`authorize_writes` 等 20 余项，且带侧栏面板、PDF 阅读器、读全文按页定位、用户注释检索、引用导出、写入（经 Zotero 自身授权对话框，key 以 0600 权限存储）；
2. kujenga 的 3 个只读工具是它的严格子集（且无页码定位、无注释/高亮、无导出、无写入）；连接上相反：kujenga 多出 Web API 模式（桌面端未运行时也能读），而已有插件仅走本地 API（默认 `127.0.0.1:23119`，端口可配置）。

**结论**：**不建议安装，属明确去重对象**（功能面被已有 ZCode zotero 插件全面覆盖且更弱）。保留例外：若未来确有「Zotero 桌面端不运行也要读库」的场景，kujenga 的 Web API 模式是已有插件没有的能力，可届时单点评估。红旗：一、仓库近三个月无提交、体量极小（953 行），长期维护性一般；二、无注释、高亮、写入能力，agent 侧的深度 Zotero 工作流做不了。

---

## unclecode/crawl4ai

- URL：https://github.com/unclecode/crawl4ai
- stars 87438 / forks 可观 / license Apache-2.0（LICENSE 为 9998 字节标准 Apache 2.0 文本）
- 最近提交：默认分支最新 2026 年 11 月 4 日（pushed_at 2026 年 11 月 13 日）
- releases：最新 v0.9.5（2026 年 10 月 14 日），此前 v0.9.4（9 月 23 日）、v0.9.3（8 月 31 日）
- open issues：347
- 读取方式：未克隆（152MB 超限），经 gh api 读顶层与 `deploy/` 目录树，经 raw 拉取 README.md、pyproject.toml、requirements.txt、Dockerfile、deploy/docker/README.md、mcp_bridge.py、server.py、cloud_notice.py、egress_policy.py（均存 /tmp/re-audit/crawl4ai-*）

**核心能力（README 关键节 + 顶层结构）**：
1. JS 渲染：Playwright（Chromium、Firefox、WebKit），支持持久化 profile、CDP 远程浏览器、会话、代理、stealth；模块证据：`crawl4ai/browser_manager.py`、`crawl4ai/async_crawler_strategy.py`；
2. Markdown 提取：DefaultMarkdownGenerator 加内容过滤（PruningContentFilterLXML、BM25ContentFilter、LLMContentFilter），带 citation 引用表；模块证据：`crawl4ai/markdown_generation_strategy.py`、`content_filter_strategy.py`、`content_filter_strategy_lxml.py`；
3. Deep crawl：BFS、DFS、best-first，带 `resume_state` 崩溃恢复；另有 AdaptiveCrawler 与 AsyncUrlSeeder、DomainMapper；模块证据：`crawl4ai/deep_crawling/` 目录、`adaptive_crawler.py`、`async_url_seeder.py`、`domain_mapper.py`；
4. 结构化提取：JsonCssExtractionStrategy、JsonXPathExtractionStrategy、RegexExtractionStrategy、LLMExtractionStrategy（经其 fork 的 litellm 支持任意供应商）、CosineStrategy 与 chunking；模块证据：`crawl4ai/extraction_strategy.py`；
5. 工具/API 入口：Python 库 `AsyncWebCrawler.arun / arun_many`（`async_webcrawler.py`）、CLI `crwl`（`cli.py`，含 `--deep-crawl bfs --max-pages`）、Docker REST 服务器（`deploy/docker/server.py` 暴露 `/md`、`/html`、`/crawl`、`/crawl/stream`、`/screenshot`、`/pdf`、`/execute_js`）；
6. MCP 集成（自托管）：Docker 服务器内置 MCP 桥（`deploy/docker/mcp_bridge.py`），工具经 FastAPI 路由装饰自动注册（server.py 内 `@mcp_tool`），共 7 个：`md`、`html`、`screenshot`、`pdf`、`execute_js`、`crawl`、`ask`；传输为 SSE 与 WebSocket（`/mcp/sse`、`/mcp/ws`，deploy/docker/README.md）。另有官方托管的付费云 MCP（`https://api.crawl4ai.com/mcp`）。

**安装方式与浏览器依赖（核实）**：
1. `pip install -U crawl4ai` 后运行 `crawl4ai-setup`（一次性安装浏览器）；失败时手工 `python -m playwright install --with-deps chromium`；Python >= 3.10；
2. Docker：`unclecode/crawl4ai:latest`，端口 11235，必须设置 `CRAWL4AI_API_TOKEN`（否则只在容器内可用）；基础镜像 python:3.12-slim-bookworm，容器内自带 redis-server 与 supervisor；
3. 库直接依赖含 playwright、patchright、playwright-stealth、lxml、numpy、pypdf 等；**注意 `unclecode-litellm==1.81.13` 是精确 pin 的 litellm fork**（供应链相关观察，见下）。

**资源要求**：Docker 部署文档写明容器至少 4GB 内存（重负载更高），`--shm-size=1g`；库本身无明文资源要求，但浏览器渲染默认吃内存（未定量验证）。

**许可证与归属（要点）**：Apache-2.0；但 README 新增「Attribution Requirements」一节，写明「使用 Crawl4AI 时必须采用以下任一归属方式」——README 徽章或文档中一行文字。严格说 Apache 2.0 并不要求展示徽章，这是仓库自己加的分发条款式声明，转售或集成发布时值得法务留意（本次只核实到 README 文字本身，未有额外许可文件佐证）。

**安全观察**：
1. 库内无网络遥测，但有推广横幅模块 `crawl4ai/cloud_notice.py`：在 setup、首次爬取、被反爬拦截时向 stderr 打印云服务广告（带 ref 参数链接），不发起任何网络请求，仅在 `~/.crawl4ai/` 写入 `.cloud-notice-shown`、`.cloud-notice-blocked` 两个标记文件；可用 `CRAWL4AI_NO_CLOUD_NOTICE=1` 全关（源码注释原文核实）；
2. Docker 服务器安全设计较好：端点强制 Bearer token 认证（AuthGateMiddleware）、内部回环调用用短时限 JWT 服务令牌、`egress_proxy.PinningProxy` 防 DNS rebinding（egress_policy.py 注释与 deploy/docker/egress_proxy.py 核实）；
3. 凭据场景：`CRAWL4AI_API_TOKEN`（自托管）、`CRAWL4AI_KEY`（云）；库对 LLM key 只在用户配置 LLM 提取时使用。

**认证与成本**：库与自托管全免费（Apache-2.0，自付基础设施）；官方云是付费服务（免费额度 1,000 credits/月，定价细节未核）；云是可选路径，非必须。

**结论**：若本项目需要「JS 渲染 + 深爬 + 结构化提取」的网页获取层，crawl4ai 是成熟度最高、生态最大的候选，建议以**自托管 Docker MCP 服务器**形态接入（7 个工具、token 认证、SSE/WS 传输），而非把它当 Python 库嵌进业务流程。红旗：一、README 的 attribution 附带声明；二、云推广横幅（可控、无网络行为）；三、Docker 栈较重（含 Redis 与 supervisor、4GB 内存门槛）；四、精确 pin 的第三方 fork 依赖（unclecode-litellm==1.81.13），版本升级需随仓库节奏；五、347 个 open issues，接口面大，接入时锁定 v0.9.5 对应的镜像 tag。

---

## 跨仓库汇总与选型建议

**元数据总表**（全部经 gh api 于本次审计时点核实）：

| 仓库 | stars | license | 最近提交 | 最新 release | open issues |
|---|---|---|---|---|---|
| cyanheads/openalex-mcp-server | 18 | Apache-2.0 | 2026 年 11 月 13 日 | v0.11.1（11 月 11 日） | 5 |
| cyanheads/pubmed-mcp-server | 168 | Apache-2.0 | 2026 年 11 月 13 日 | v2.12.2（11 月 13 日） | 7 |
| blazickjp/arxiv-mcp-server | 3282 | Apache-2.0 | 2026 年 11 月 14 日 | v0.8.2（10 月 8 日） | 8 |
| kujenga/zotero-mcp | 162 | MIT | 2026 年 8 月 6 日 | 0.3.1（8 月 7 日） | 4 |
| unclecode/crawl4ai | 87438 | Apache-2.0 | 2026 年 11 月 4 日（默认分支） | v0.9.5（10 月 14 日） | 347 |

**免费边界（已按「是否有例外」核实）**：五个对象的数据源基本全免费；已核实的例外只有三处——一、OpenAlex 的 `created_date`、`updated_date` 过滤字段属付费计划专属（不带 key 会 `upstream_plan_required`）；二、crawl4ai 官方云是付费服务（免费额度 1,000 credits/月，可选不用）；三、NCBI 无 key 时 3 次/秒、Europe PMC 与 Semantic Scholar 有软配额（免费 key 可放宽）。

**建议角色与去重结论**：
1. openalex-mcp-server：装（OpenAlex 目录层，5 工具精而深，锁版本）；
2. pubmed-mcp-server：装（biomedical 层，12 工具，配齐三个邮箱类配置）；
3. arxiv-mcp-server：装（预印本与 LaTeX 精读层，19 工具，`--storage-path` 指向项目约定目录）；
4. kujenga/zotero-mcp：**不装**（与已有 ZCode zotero 插件功能重复且为严格子集；唯一独有面是 Web API 模式，按需再评估）；
5. crawl4ai：按需装（暂定为网页获取层的自托管 Docker MCP 形态）。

**本次未验证事项（照实列明）**：一、kujenga/zotero-mcp 本地 API 的具体端口号（源码未出现，由 pyzotero 封装）；二、arxiv-mcp-server 存储目录内部子目录布局（只核实了根目录与文件命名方式，未逐目录展开）；三、openalex.caseyjhand.com 与 pubmed.caseyjhand.com 两个托管端点的运营方隐私政策；四、crawl4ai 云定价细节；五、pubmed 的 Unpaywall 私网防护问题仅有 issue 标题与代码现状 grep 佐证，未读该功能对应 PR 讨论。