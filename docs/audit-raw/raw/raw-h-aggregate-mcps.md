审计完成。以下为 6 个仓库的逐项审计报告，全部结论来自实际克隆到 /tmp/re-audit/ 下并逐文件读过的源码；渠道只用了 `git clone --depth 1` 与 `gh api`，未运行任何仓库内脚本。

# 审计方法与共同说明

1. 克隆路径：/tmp/re-audit/mcpsurfr、/tmp/re-audit/kindly、/tmp/re-audit/metasearchmcp、/tmp/re-audit/daedra、/tmp/re-audit/tadmstr-searxng、/tmp/re-audit/tisddm-searxng，均小于 100MB，未用到 gh 读树。
2. 元数据（stars、license SPDX、最近提交、releases、开放 issue）来自 `gh api`，代码结论来自 Read 工具逐文件阅读。
3. 一处未完全验证：mcpsurfr 依赖的 ddgs 库（uv.lock 锁定 9.16.0）内部实现未读源码（未安装、未克隆 ddgs 本身），「这些引擎全免 key」基于 mcpsurfr 源码中零 key 引用加 ddgs 公开设计，ddgs 内部逐引擎实现属未完全验证；关注点已在各节注明。

## nkapila6/mcpsurfr

**URL / stars / license / 提交 / releases / issues**
1. URL：https://github.com/nkapila6/mcpsurfr
2. stars 151，forks 22，未归档
3. license：MIT。文件 /tmp/re-audit/mcpsurfr/LICENSE（SPDX 文本「MIT License, Copyright (c) 2025 Nikhil Kapila」）；pyproject.toml 中 `license = "MIT"` 一致
4. 最近提交：2026 年 10 月 29 日（ecad09c，Merge PR #136 registry adapters）；pushed_at 2026 年 11 月 16 日（晚于最后提交，应为 tag 推送，未逐 tag 核实）
5. releases：10 个，最新 v1.2.3（2026 年 10 月 29 日），版本节奏活跃
6. open issues：非 PR 共 18 条，绝大多数是维护者自建的路线图条目（如 deep_research 报告空词项、Wayback 回落、学术搜索工具等），不是用户故障报告

**实际机制（读源码确认）**
1. 搜索源：全部经 `ddgs` 库（pyproject 依赖 ddgs>=9.16.0，uv.lock 锁 9.16.0）。文本后端在 src/mcpsurfr/main.py 第 15 行声明：`auto, brave, duckduckgo, google, grokipedia, mojeek, startpage, wikipedia, yahoo`；新闻后端 `auto, bing, duckduckgo, yahoo`。`auto` 是 ddgs 的多引擎并发元搜索。日期过滤时 auto 自动收窄为 `brave,duckduckgo,google,startpage,yahoo`（第 18 行 DATED_AUTO）
2. 免 key：全部免 key。全仓 grep 无任何 api_key 引用（唯一命中是分词器里的 token 一词）。ddgs 各引擎的内部抓取实现未读（见方法说明）。google/startpage/yahoo 常被反爬封锁，这是它自己代码注释承认的（main.py 第 39 行：「Google often blocks scrapers」，非 auto 后端空结果会自动重试 auto 并给出 warning）
3. 重排：真实本地模型 + BM25 分层。src/mcpsurfr/utils/embedder.py 用 MobileBERT（26MB embedder.tflite，位于 src/mcpsurfr/embedder/）做向量相似度；src/mcpsurfr/utils/tflite.py 是作者手写的纯 numpy 最小 TFLite 解释器（348 行，仅支持该模型用到的算子），不依赖原生 runtime、不拖 torch；src/mcpsurfr/utils/passages.py 是真正的 BM25（k1=1.5, b=0.75，含多词短语加权）。筛选分三档：关键词命中少于上限直接用 BM25 结果（tier「keywords」）；命中过多则 BM25 前 48 条用嵌入模型破平（「keywords+semantic」）；完全无命中则纯语义（「semantic」，最多 4 条并附低置信提示）。语义分数被明确注释为不可作阈值（passages.py 第 116 行）
4. 抓取链：primp（浏览器指纹模拟）为主；对 StackExchange、Wikipedia、GitHub、Hacker News、PyPI、npm、crates.io 有专用免 key API 适配器（utils/adapters.py 头注释，Reddit 因封锁被明确放弃）；docs 站（mkdocs、docusaurus 等）尝试 .md 镜像（utils/docsmd.py）；PDF 用 pypdf；5 词 shingle 去近重复；全页共享字符预算（默认 4 万字符，页面截断标 truncated）

**MCP 工具名**
1. 正式：`search`（只回答案段落）、`rag_search_ddgs`（整页）、`read_url`（URL 或 PDF，带 query 时只回段落）、`deep_research`（多词项 × 多后端）
2. 遗留（需环境变量 MCPSURFR_LEGACY_TOOLS 打开）：`rag_search_google`、`deep_research_google`、`deep_research_ddgs`
3. 另含资源 skill://mcpsurfr-search/SKILL.md 与 prompt `research`

**依赖与运行**
1. Python >=3.10；依赖仅 ddgs、fastmcp、lxml、numpy、primp、pypdf；无 torch、无浏览器、无媒体推理栈
2. 资源：模型 26MB，加载约 50ms 且进程内缓存；嵌入批上限 32，纯 numpy 矩阵乘，内存有专门优化（tflite.py 注释记录规划前峰值 1.3GB、后按月释放张量）。整体属轻量 CPU 级

**认证与成本**：零 key、零费用。边界：反爬（google/startpage 常失败，auto 规避）、ddgs 限流 429、read_url 拒绝 localhost 与私网地址（utils/tools.py public_url）。

**维护质量**：源码 2601 行（src 内 12 个 py 文件）；注释密度与设计说明异常高（README、SKILL、issue 路线图均完整）；但仓库内没有 tests 目录（find 全仓匹配 test 为零）——这是主要质量缺口；单一维护者。

**结论**：**主力候选（并列第一）**。真正多引擎、真本地重排、有段落级输出与 token 预算管理，免 key 且依赖极轻。红旗：无任何自动化测试；引擎封锁时质量依赖 ddgs auto 的运气；ddgs 版本升级风险需自行管理（建议锁 9.16.0）。

## Shelpuk-AI-Technology-Consulting/kindly-web-search-mcp-server

**URL / stars / license / 提交 / releases / issues**
1. URL：https://github.com/Shelpuk-AI-Technology-Consulting/kindly-web-search-mcp-server
2. stars 405（本批最高），forks 37
3. license：MIT（/tmp/re-audit/kindly/LICENSE，版权 2026 Shelpuk AI Technology Consulting GmbH）
4. 最近提交：2026 年 10 月 10 日（72a3e05，dependabot 合并）；pushed_at 2026 年 10 月 19 日（晚于最后提交，原因未核实）
5. releases：无（gh 返回空数组）
6. open issues：非 PR 仅 2 条（一条 Webz.io 新 provider 建议、一条赞助咨询）

**实际机制（读源码确认）**
1. 搜索 provider 注册表在 src/kindly_web_search_mcp_server/search/__init__.py 的 `PROVIDERS`（也是选择顺序，「先配置者胜，无跨 provider 回退」，源码注释原文）：Serper（SERPER_API_KEY）、SerpBase（SERPBASE_API_KEY）、Tavily（TAVILY_API_KEY）、SearXNG（SEARXNG_BASE_URL，自托管，按 base URL 不算 key）、Sofya（SOFYA_API_KEY）、You.com（YDC_API_KEY）、Serply（SERPLY_API_KEY）、apifare（APIFARE_TOKEN）
2. 免 key 清单：**搜索层为零**。八个搜索 provider 要么付费 key、要么自托管 SearXNG；未配置任何一个时直接抛 WebSearchProviderError。内容层免 key：StackExchange API（STACKEXCHANGE_KEY 可选，10k/天 vs 300/天）、Wikipedia API、arXiv API + PDF 解析均免 key；GitHub Issue/Discussion 走 GraphQL **必须** GITHUB_TOKEN（content/github_issues.py 第 286 行显式 raise）；任意网页有 nodriver 无头 Chromium 通用兜底（免 key，但会启动浏览器）
3. 重排/过滤：**无重排、无本地模型**。结果保持 provider 原始顺序，只做并发内容富化（server.py 的 enrich_one）。查询逐字发给所选 provider，无本地语义处理
4. 内容抓取链（content/resolver.py 注释）：StackExchange → GitHub Issue → GitHub Discussion → Wikipedia → arXiv → 通用 HTML（nodriver 无头 Chromium + trafilatura，readability 备用）。抓取质量是本仓库真正强项

**MCP 工具名**：仅 2 个，`web_search` 与 `get_content`（server.py 第 375、556 行）。

**依赖与运行**
1. Python >=3.13（版本要求偏高，注意运行时环境）；依赖 mcp>=1.25,<2、starlette、uvicorn、pydantic、httpx[socks]、beautifulsoup4、markdownify、trafilatura、nodriver、PyMuPDF
2. 资源：nodriver 需下载/启动 Chromium（KINDLY_NODRIVER_BROWSER_POOL_SIZE 默认 1），带浏览器进程池、重试与超时控制；对纯聚合场景偏重

**认证与成本**：搜索必须付费 key（Serper、Tavily 等官方申请）或自建 SearXNG；内容抓取免 key。不能作为免 key 主力。

**维护质量**：源码 9407 行；测试 33326 行（66 个测试文件、覆盖率与变异测试配置、依赖上限守卫测试）；工程纪律本批最强（依赖边界注释、错误消息脱敏防 key 泄漏等）。社区反馈少而集中，无故障堆积。

**结论**：**备选（内容抓取层）**。它的「多 provider」是抽象多选一而非聚合；免 key 边界在搜索层为零，与本项目「无 key 聚合」目标不匹配。若将来有 Serper/Tavily 预算或自建 SearXNG，其 get_content 可作为高质量抓取补充。红旗：Python 3.13 硬下限；无 release 只有 git 主分支（滚动安装，依赖再解析风险作者自己也在注释里承认）。

## gefsikatsinelou/MetaSearchMCP

**URL / stars / license / 提交 / releases / issues**
1. URL：https://github.com/gefsikatsinelou/MetaSearchMCP
2. stars 58，forks 4；仓库创建于 2026 年 4 月 14 日（年轻）
3. license：MIT，但 /tmp/re-audit/metasearchmcp/LICENSE 版权署名是「reurinkkeano」，该用户名在 GitHub 查无此人（gh api users/reurinkkeano 返回 404），且 LICENSE 自首个提交即存在；我对署名疑点未做进一步溯源。属轻度红旗（署名与仓库主对不上），未见代码有问题
4. 最近提交：2026 年 10 月 20 日（621da40，新增 /health/providers）；近 100 笔提交作者均为 gefsikatsinelou（gh api 统计）
5. releases：无
6. open issues：非 PR 仅 1 条（基准讨论）

**实际机制（读源码确认）**
1. 形态：FastAPI HTTP 网关 + MCP stdio 两吃（server.py + broker.py + api/routes.py）
2. 规模：metasearchmcp/providers/ 下 253 个文件，providers/registry.py 的 `_ALL_PROVIDER_CLASSES` 注册 **250 个 provider 类**（精确计数），从 Google、DDG 到 PokeAPI、YuGiOh 级别的长尾免 key API 全收
3. 通用 web 引擎逐个列名（读 providers/ 文件）：免 key 且默认可用：DuckDuckGo（https://html.duckduckgo.com/html/ 抓取）、Bing（https://www.bing.com/search 抓取）、Startpage、Mojeek、Seznam.cz、Mwmbl（api.mwmbl.org）、Marginalia（公共 API）；被 ALLOW_UNSTABLE_PROVIDERS 开关闸住：Google 直连抓取、Qwant、Ecosia、Naver、Yandex、Baidu、Yahoo；需 key：Brave（brave_api_key）、You.com（ydc_api_key）、google_serpbase（SERPBASE_API_KEY）、google_serper（SERPER_API_KEY）。另有 Google News RSS、Bing News RSS 免 key 新闻源
4. 环境变量 key 清单（config.py）：SERPBASE_API_KEY、SERPER_API_KEY、BRAVE_API_KEY、YDC_API_KEY、GITHUB_TOKEN、STACKEXCHANGE_API_KEY（可选）、REDDIT_CLIENT_ID/SECRET、NCBI_API_KEY（可选）、SEMANTIC_SCHOLAR_API_KEY（可选）、ALPHA_VANTAGE_API_KEY（可选，25 次/天免费）、FINNHUB_API_KEY（可选，60 次/分免费）、UNSPLASH_ACCESS_KEY（可选）
5. 聚合是真的：orchestrator.py 对选中 provider 集合 `asyncio.gather` 并发执行，单 provider 超时（aggregator_timeout 默认 15 秒）、可配重试、按规范化 URL 去重（merge.py canonicalize_url）、TTL 缓存 300 秒
6. 重排是启发式，不是模型：ranking.py 的分数 = 多家命中共识数 × 2.0 + 查询词逐字命中 × 1.0（_CONSENSUS_WEIGHT/_TERM_WEIGHT），且 `RANK_RESULTS` 默认关闭（config.py `rank_results: bool = False`），默认保 provider 优先级顺序
7. 一个需要重点注意的行为：broker.py 的 `_dispatch_search_web` 在 `providers` 与 `tags` 都为空时，`pick_providers_by_tags` 原样返回全目录——即**默认一次 search_web 会并发打向全部约 240 个可用 provider**。工具描述原文「empty = all enabled」。实际使用必须先给 tags/providers 或 ENABLED_PROVIDERS 收窄

**MCP 工具名（14 个）**：`search_web`、`search_google`、`search_academic`、`search_github`、`compare_engines`、`search_finance`、`search_code`、`search_news`、`search_social`、`search_images`、`search_videos`、`search_bio`、`list_providers`、`provider_health`。

**依赖与运行**
1. Python >=3.11；fastapi、uvicorn、pydantic、httpx、beautifulsoup4、lxml、mcp。零重依赖
2. 资源：单进程 asyncio，默认一次全量 fan-out 是它真正的资源风险（几十到几百个并发外部请求）

**认证与成本**：免 key 能力很大（约 240 个默认可用 provider 中绝大多数是公共 API），但不是「干净」的免 key：无 key 时通用 web 搜索只剩 DDG、Bing、Startpage、Mojeek、Seznam、Mwmbl、Marginalia 七个可用（Bing/Startpage 抓取稳定性存疑）。key 均为可选增强。

**维护质量**：源码 52728 行；测试 247 个文件、52607 行（每 provider 一个测试文件），工程投入显著；但仓库无 release、无版本 tag 语义（版本仍 0.1.0）、单一维护者、LICENSE 署名疑点。

**结论**：**备选（实验性）**。是六个里 provider 面最广的真聚合器，测试体量最大；但太年轻、默认全量 fan-out 的用法危险、无发布版本，不宜直接进主线。若采用，必须配 ENABLED_PROVIDERS 白名单（建议先只放 DDG、Mojeek、Mwmbl、Marginalia、Wikipedia 等稳定的）。红旗：LICENSE 署名查无此人；`search_web` 默认行为。

## dirmacs/daedra

**URL / stars / license / 提交 / releases / issues**
1. URL：https://github.com/dirmacs/daedra
2. stars 18（本批最低），forks 4
3. license：MIT（/tmp/re-audit/daedra/LICENSE，DIRMACS Global Services）；Cargo.toml `license = "MIT"` 一致
4. 最近提交：2026 年 11 月 4 日（4b1b015，「release: 0.5.15」）；Cargo 版本 0.5.15
5. releases：34 个；gh 最新 release 为 v0.5.14（2026 年 11 月 1 日），0.5.15 已有版本提交（发布记录未同步，属小滞后）
6. open issues：非 PR 为 0（gh 返回空数组，12 个 open_issues_count 全是 PR）

**实际机制（读源码确认）**
1. 后端 14 个，全部免 key，注册于 src/tools/backend/provider.rs 的 `SearchProvider::auto()`（逐条列名，count Box::new 精确 = 14）：Mwmbl（公共 JSON）、Brave（HTML 抓取）、Marginalia（公共 API，MARGINALIA_API_KEY 可选换高限额端点）、Bing RSS、Bing HTML 抓取、Google News RSS、Hacker News Algolia、Google HTML 抓取、Wikipedia、StackExchange（文件头注释明文「free, no API key」）、GitHub（GITHUB_TOKEN 可选）、Wiby、DDG Instant Answers、DuckDuckGo HTML 抓取（注明 last resort）
2. 环境变量仅两个且都可不设：MARGINALIA_API_KEY、GITHUB_TOKEN。README 原文「This crate does not accept paid search keys」；无任何付费 key 通道
3. 聚合是真的：`FuturesUnordered` 并发打全部可用后端，soft deadline 1.5 秒、per-backend 5 秒、hard 30 秒（provider.rs 常量 37/57/66 行）；熔断器 3 次失败开 30 秒（init_circuit_breakers）；govemor 限流 + 每后端限额；结果 k 路归并（merge_ranked_results，注释明确「弱后端不能靠数量压过强后端」）
4. 重排是启发式：src/tools/backend/rank.rs 的 relevance_score = 标题/URL/描述中命中查询词数占比（词干半命中计 0.5、词序全中加 1.0 奖励），无任何模型
5. 另有结构化查询解析（query.rs 支持 site:、after:、filetype: 等指令并后置过滤）、抓取工具带 readability（dom_smoothie）、markdown 转换（htmd）、PDF（pdf-inspector）、可选 Office 文档（anydoc，documents feature 默认开）

**MCP 工具名（4 个）**：`web_search`、`search_duckduckgo`、`visit_page`、`crawl_site`（server/handler.rs 第 65 行起）。传输支持 stdio 与 SSE（axum）。

**依赖与运行**
1. Rust 单二进制，无运行时安装负担；依赖 tokio、reqwest、scraper、moka、axum 等，无 ML、无浏览器
2. 注意：rust-version 1.99（rust-toolchain.toml 已在发布包排除，但本机编译需新工具链）

**认证与成本**：纯免 key 零成本；边界在 IP 信誉：Brave/Bing/Google 从机房 IP 可能 429 或验证码（README 明说），Mwmbl、Marginalia、wiki、HN、StackOverflow、GitHub、RSS 系「any IP」稳定。

**维护质量**：src 14434 行；测试属性 423 处（src 内 + tests/ 三个集成文件）；带 criterion 基准、详细 CHANGELOG（21461 字节）与 AGENTS.md/CLAUDE.md；34 个 release 说明迭代认真，但社区很小（18 stars）。

**结论**：**主力候选（并列第一）**。六个里唯一把「免 key 多引擎 + 自动降级」写进设计目标的：14 个免 key 后端、熔断、期限、k 路归并、单二进制零依赖安装，全部在源码里落实。红旗：社区最小（18 stars）、单组织维护、机房 IP 上头部引擎可用率受限（但设计上已用免封锁源兜底）。

## TadMSTR/searxng-mcp

**URL / stars / license / 提交 / releases / issues**
1. URL：https://github.com/TadMSTR/searxng-mcp
2. stars 29，forks 2
3. license：MIT（/tmp/re-audit/tadmstr-searxng/LICENSE）
4. 最近提交：2026 年 10 月 7 日（6c02dbe，CodeRabbit 配置清理）；pushed_at 2026 年 11 月 16 日（晚于最后提交，未核实来源）
5. releases：34 个，最新 v3.30.1（2026 年 10 月 6 日），迭代频率很高
6. open issues：非 PR 1 条（time_range 校验缺陷）

**实际机制（读源码确认）**
1. 底层搜索源：自托管 SearXNG（SEARXNG_URL，默认 http://localhost:8081，支持逗号分隔多副本与 basic auth）。SearXNG 自身是元搜索引擎，真正的多引擎聚合发生在 SearXNG 里；本 MCP 不含任何公共搜索 API 调用
2. 重排：**外部服务**，不在进程内。src/reranker.ts 向 RERANKER_URL（默认 http://localhost:8787）发 POST /v1/rerank，代码注释指明对方是 FlashRank 类交叉编码器（cross-encoder）reranker；失败或 RERANKER_URL 置空时回退 SearXNG 原始排序并打降级日志（min_score 会明确宣告失效）。不存在 torch 类依赖
3. 抓取链（四层，src/tiers/ 与 fetch.ts）：tier1 Firecrawl（FIRECRAWL_URL 默认 http://localhost:3002，FIRECRAWL_API_KEY 默认「placeholder-local」，即自托管；FIRECRAWL_ENABLED=false 可关）、tier2 Crawl4AI（CRAWL4AI_URL 可选）、tier3 进程内 raw fetch + JSDOM Readability（唯一永远在线的层）、tier4 Wayback（WAYBACK_ENABLED=true 才激活）；GitHub URL 走专用快路径（GITHUB_TOKEN 可选）
4. 周边：robots.txt 尊重、SSRF 防护、反爬挑战检测、按域能力数据库（domain-db.ts，Valkey 后端、90 天 TTL，记录各 tier 成功率用于跳层）；Ollama 或任意 LLM_BASE_URL 可选做查询扩展与摘要（OLLAMA_URL 默认空即关闭，默认模型 qwen3:4b/14b）；KiWix、Hister 可选离线源；NATS/OTel 可选观测

**MCP 工具名（7 个）**：`search`、`search_and_fetch`、`fetch_url`、`search_and_summarize`、`crawl_site`、`clear_cache`、`domain_stats`。

**依赖与运行**
1. Node >=20；@modelcontextprotocol/sdk、jsdom、undici、iovalkey（Valkey/Redis 客户端）、@nats-io、OpenTelemetry、robots-parser、zod。无私有原生依赖，安装轻，但有效运行重量取决于你部署几个伴生服务
2. 资源：最小可用形态 = 只有 SearXNG + tier3（README 明确「SEARXNG_URL 是唯一必需」）；完整形态需 SearXNG + FlashRank + Crawl4AI/Firecrawl + Valkey，属「本地栈派」

**认证与成本**：设计上零云端 key（标题即 private web search），但代价是必须自部署 SearXNG（其抓取用你的 IP）；reranker/crawl4ai 全可选。对本项目「无 key」目标成立，对「零部署」目标不成立。task 描述里的「4 级抓取链」与源码一致（tier4 Wayback 是 flag 门控的第四层）。

**维护质量**：源码 11478 行；测试 96 个文件、20535 行；pre-commit、gitleaks、CodeRabbit 配置齐全；文档含架构、部署、安全、工具四份。工程质量高，但社区小、最后提交距 pushed_at 有一个月差。

**结论**：**备选（本地栈路线）**。若要「queries 不出本机」的私密聚合 + ML 重排 + 全页抓取，这是六个里最完整的成品；但引入 SearXNG 部署与运维成本，且重排依赖外部 FlashRank 服务，不在进程内。红旗：默认配置会向不存在的本地服务（Firecrawl 等）发请求并被作者在 README 里点名（首次运行需显式关闭），操作细节多。

## tisDDM/searxng-mcp

**URL / stars / license / 提交 / releases / issues**
1. URL：https://github.com/tisDDM/searxng-mcp
2. stars 43，forks 8
3. license：MIT（/tmp/re-audit/tisddm-searxng/LICENSE）
4. 最近提交：2026 年 1 月 23 日，提交信息只有一词「deprecated」（浅克隆只有此一笔，历史未展开，属未验证）
5. releases：无
6. open issues：非 PR 1 条，停留在 2025 年 4 月

**实际机制（读源码确认）**
1. 单引擎包装：src/index.ts（全文 414 行）把查询转给 SearXNG 的 /search JSON 接口；SEARXNG_URL 未设时从 searxng/searx-instances 的 instances.yml（raw.githubusercontent.com/searxng/searx-instances）拉公共实例清单随机选一个（USE_RANDOM_INSTANCE=false 可关）；支持 basic auth（SEARXNG_USERNAME/PASSWORD）
2. 无重排、无抓取、无去重、无缓存。输出为 markdown 文本结果列表
3. README 顶部已明确「This project is deprecated. Its successor is searxNcrawl（DasDigitaleMomentum）」；作者自述后继版不再包含随机实例轮换

**MCP 工具名**：仅 1 个，`searxngsearch`。随机公共实例路径在 README 有原生告警「429」常见。

**依赖与运行**
1. Node >=16；@modelcontextprotocol/sdk **0.6.0**（极旧）、axios、dotenv、yaml
2. 零 key、零成本：走公共 SearXNG 实例时连自部署都不需要，但可用性不可靠（README 自认）

**认证与成本**：免 key 成立但以公共实例的限流与稳定性为代价；私有实例则回到自部署 SearXNG。

**维护质量**：414 行单文件；无 tests、无 .github、无 CI；SDK 停在 0.6.0；最后动作是打上 deprecated。本批维护质量最低。

**结论**：**不采用**。被作者自己弃用并指定后继仓库；单引擎包装（聚合能力来自 SearXNG 本身）、无发布、测试为零。仅记录其公共实例轮换思路（随机实例兜底）可作参考。

# 横向对比表

| 仓库 | 引擎架构 | 真多引擎？ | 免 key 开箱能力 | 重排机制（源码位置） | 语言/运行时 | 测试规模 | 活跃度（最后提交 / releases） | 许可 | 本项目角色 |
|---|---|---|---|---|---|---|---|---|---|
| nkapila6/mcpsurfr | ddgs 库 9 个文本后端 + 4 个新闻后端 | 是（引擎级，经 ddgs） | 完全免 key | 真本地模型：MobileBERT TFLite 纯 numpy 推理 + BM25（utils/embedder.py、tflite.py、passages.py） | Python >=3.10，无 torch | 无 tests 目录 | 2026 年 10 月 29 日 / 10 个（v1.2.3） | MIT | 主力候选（并列第一） |
| kindly-web-search-mcp-server | 8 个 provider 取先配置者，无回退 | 否（抽象多选一；配 SearXNG 才继承聚合） | 搜索层零免 key；内容层免 key | 无重排（仅并发富化） | Python >=3.13 + 无头 Chromium | 33326 行 | 2026 年 10 月 10 日 / 无 release | MIT | 备选（抓取层） |
| gefsikatsinelou/MetaSearchMCP | 250 个 provider 注册，并发 fan-out + 去重 | 是（provider 级，最广） | 约 240 个默认可用，含 7 个通用引擎（DDG/Bing/Startpage/Mojeek/Seznam/Mwmbl/Marginalia） | 启发式共识 + 词命中（ranking.py），默认关闭 | Python >=3.11 + FastAPI | 52607 行 / 247 文件 | 2026 年 10 月 20 日 / 无 release | MIT（署名疑点） | 备选（实验性，需白名单） |
| dirmacs/daedra | 14 个免 key 后端并发 + 熔断 + k 路归并 | 是（后端级，设计目标即此） | 完全免 key，单二进制 | 启发式词命中 + 词序奖励（backend/rank.rs） | Rust（rust-version 1.99） | 423 处测试 | 2026 年 11 月 4 日 / 34 个（v0.5.14 记录） | MIT | 主力候选（并列第一） |
| TadMSTR/searxng-mcp | 委托自托管 SearXNG（聚合在其内部） | 委托型（SearXNG 是多引擎） | 需要自部署 SearXNG；云 key 为零 | 外部 FlashRank 交叉编码器服务，可关可回退（reranker.ts） | Node >=20 + 可选本地栈 | 20535 行 / 96 文件 | 2026 年 10 月 7 日 / 34 个（v3.30.1） | MIT | 备选（私密本地栈路线） |
| tisDDM/searxng-mcp | 单 SearXNG 包装 | 否（且弃用） | 公共实例免部署但高 429 | 无 | Node >=16，SDK 0.6.0 | 无 | 2026 年 1 月 23 日「deprecated」/ 无 release | MIT | 不采用 |

# 最终结论：无 key 可用的多引擎聚合 MCP，选谁

1. **首选 dirmacs/daedra**：它是六个里唯一从设计到实现都为「免 key 多引擎聚合」服务的（README 第 8 行原文「14 unkeyed backends」、第 75 行「does not accept paid search keys」），14 个后端逐一在 provider.rs 验证存在且无 key 路径，带熔断、期限、限流、k 路归并与结构化查询过滤，Rust 单二进制部署零成本。主要保留项是社区小（18 stars）与机房 IP 下头部引擎被封锁（已由 Mwmbl/Marginalia/wiki/HN 等兜底）。
2. **并列推荐 nkapila6/mcpsurfr 作为互补**：若项目需要「重排后只回答案段落、控制 token」，它的纯 numpy MobileBERT 重排是全批唯一的真本地模型重排方案，且免 key、依赖极轻。与 daedra 搭配可形成两类工具覆盖（字节级聚合优先用 daedra，答案级段落优先用 mcpsurfr）。风险是零测试覆盖。
3. **MetaSearchMCP 暂作备选**：聚合面最大（250 provider）且免 key 面大，但太年轻、无发布版本、LICENSE 署名对不上、默认全量 fan-out 危险；仅在需要长尾数据源（学术、包注册表等）时以白名单方式接入。
4. **kindly 与 TadMSTR 均不作聚合主力**：kindly 搜索层零免 key（强在抓取）；TadMSTR 云 key 为零但要求自部署 SearXNG，属「换一种运维成本」。两者可作为后续「内容抓取质量」的补充候选（kindly 的 content 层、TadMSTR 的四级抓取链）。
5. **tisDDM 直接排除**：作者弃用、单引擎包装、无测试无发布。

待验证项（如实列出）：ddgs 库内部逐引擎实现未读；MetaSearchMCP 约 240 个默认可用 provider 只抽验了通用搜索引擎一批，未逐个验证；两处 pushed_at 晚于最后提交（mcpsurfr、TadMSTR）的来源未核实；tisDDM 提交历史因浅克隆未展开。