# Research Engine v2 —— Stage 1+2 仓库审计报告

审计方式：三个仓库均已 `git clone --depth 1` 到 `/tmp/re-audit/`（RivalSearchMCP 3.4MB、agent-search 1.1MB、searxng 30MB，均小于 100MB），全部结论来自实际读到的源码与文件内容；未运行任何仓库代码、未装依赖、未启动容器。元数据（stars/issues/releases）经 `gh api` 核实。

---

## damionrashford/RivalSearchMCP

**URL / stars / license / 最近提交 / releases / open issues**
- https://github.com/damionrashford/RivalSearchMCP
- stars 140，forks 24，open issues 9，MIT（LICENSE 文件确认）
- 最近提交 2026 年 11 月 12 日（`4d031f7`，docs 提交）
- releases：v1.2.0（2026 年 4 月 17 日，FastMCP 3 升级）、tag `v1.1.0-skills`（2026 年 3 月 18 日）；发布节奏明显落后于提交

**实际能力（精确清单，含佐证路径）**
由 `rival_search_mcp/server.py` 注册，共 9 个工具，名称逐一从装饰器核实：
1. `web_search`（`tools/search.py:20`，name="web_search"）——并发扇出 DuckDuckGo、Bing、Yahoo、Mojeek、Wikipedia 五引擎（`core/search/engines/` 下同名目录确认），keyless
2. `social_search`（`tools/social_media.py:53`）——platforms 枚举：reddit、hackernews、devto、producthunt、medium、stackoverflow、bluesky、lobsters、lemmy
3. `news_aggregation`（`tools/news.py:21`）——Google News、Bing News、Guardian、GDELT、DuckDuckGo News（`core/news/aggregator.py`）；time_range 枚举 anytime/day/week/month
4. `github_search`（`tools/github_tool.py:20`）——公开 API，无需 token，未认证 60 次/小时（server instructions 明示）
5. `scientific_research`（`tools/scientific.py:29`）——operation 枚举 academic_search/dataset_discovery；论文源 OpenAlex、CrossRef、arXiv、PubMed、Europe PMC；数据集源 Kaggle、HuggingFace、Zenodo、Harvard Dataverse（`core/scientific/{search,datasets}/providers/`）
6. `map_website`（`tools/traversal.py:23`）——模式 research/docs/map
7. `content_operations`（`tools/analysis.py:42`）——operation 枚举：retrieve、stream、analyze、extract、score、find_conflicts、validate、bibliography
8. `research_topic`（`tools/analysis.py:921`）——模式 topic/entity
9. `document_analysis`（`tools/pdf_tool.py:18`）——PDF/DOCX/文本/图片 OCR

**source scoring / conflict detection 是真实实现，不是 README 吹嘘**，且已接线到工具层：
- 评分：`rival_search_mcp/core/quality/score.py`（457 行）——四个信号合成 0 到 100 分与 tier（primary/reference/academic/news/community/vendor/aggregator/unknown）、freshness、跨域 corroboration、citations。挂载点已逐一验证：`tools/multi_search.py:222`（web_search 每条结果）、`tools/news.py:73`、`tools/social_media.py:141`、`tools/github_tool.py:67`、`tools/analysis.py:514` 与 `1083`（score 与 research_topic）
- 冲突检测：`rival_search_mcp/core/conflict/detect.py`（587 行）——numeric/date/polarity 三类，基于正则与启发式规则，经 `content_operations(operation="find_conflicts")` 可用（`tools/analysis.py:539-617`）。唯一名不副实处：代码注释里提到「可选的语义冲突检测走 ctx.sample()」，全库 grep 未发现任何 ctx.sample 调用，**LLM 语义冲突检测并未实现**，只有规则版

**依赖与运行要求**
- Python >=3.10；关键依赖：fastmcp>=3.2,<4、scrapling[fetchers]（TLS 指纹伪装，用于绕过 Bing/DDG/Yahoo 的 Cloudflare）、markdownify、pypdf、python-docx、pandas、pytrends、easyocr（OCR 可选，运行时才 import，首次用会下载模型，重）
- 安装：uv 体系（仓库含 uv.lock）。`uv tool install fastmcp` 后 `fastmcp install claude-desktop server.py`（stdio）或 `fastmcp run server.py --transport http --port 8000`。也可 `uv sync --extra dev`
- 资源消耗：未实测。运行时不跑 LLM；HTTP 部署配置（`fastmcp.json`）默认绑定 0.0.0.0:3000，本地用建议改为回环
- 代码规模：`rival_search_mcp/` 约 1.23 万行 Python；tests 20 个文件约 2.3 千行

**认证与成本**
- 核心功能全部 keyless，无需任何 API key。代码内未发现引擎级 key 环境变量
- 可选环境变量：PORT、ENVIRONMENT、LOG_LEVEL、REDIS_URL（`core/cache/cache_manager.py` 支持 Redis 缓存，默认 redis://localhost:6379，未见强制）、ALLOWED_ORIGINS、LOG_FILE
- Guardian 新闻源硬编码公共 "test" key（`core/news/aggregator.py:203`）；Reddit 走第三方归档 API `api.pullpush.io`（`core/social/reddit.py:28`）而非 Reddit 官方接口——第三方依赖，可用性无保证

**安全观察**
- 未发现任何遥测/analytics/Sentry/posthog 代码
- 外发请求面：所有引擎请求本身 + 一个关键点——官方插件与 `.mcp.json` 默认注册**托管端点 `https://RivalSearchMCP.fastmcp.app/mcp`**（README 第 62 至 76 行、`plugins/rival-search-mcp/.mcp.json`），走托管端点意味着所有查询穿过第三方服务器；本地安装可完全避开
- 代码执行面：服务端不跑 LLM；easyocr 仅本地推理；有 token bucket 限流（`core/security/security.py`）与 CORS、null-id 校验中间件
- 红旗：单人维护且迭代极快；2026 年 9 月 19 日 open issue 报「streamable HTTP 部署下 prompt 模板损坏」；托管端点作为默认路径对隐私不友好

**结论：备选（强）**。作为 keyless 的「研究扇出 + 可信度评估」MCP 工具集，实现质量高于同类一般水准（评分与冲突检测均为真代码且有测试），适合与主搜索基础设施并行使用做交叉验证。建议本地部署、不用托管端点。

---

## cedarsaam/agent-search

**URL / stars / license / 最近提交 / releases / open issues**
- https://github.com/cedarsaam/agent-search
- stars **5**（核实无误，forks 6），MIT，created 2026 年 6 月 26 日
- 最近提交 2026 年 7 月 7 日（本地时间，UTC 为 7 月 8 日 04:09，与「最后提交 2026 年 7 月 8 日」的说法吻合）
- releases：**无**（0 个 release、0 个 tag；pyproject 标 version 2.0.0 但从未发版）；open issues 1
- 距今已约 4 个月无提交

**核实结论：声称的功能全部是真实实现，不是空壳**
- SearXNG 集成：`SearXNGEngine`（`search.py:707`），`SEARXNG_URL` 默认 `http://localhost:8888`；`docker-compose.yml` 实拉 searxng/searxng:latest 并挂载自带 `searxng/settings.yml` 与自定义引擎 `searxng/engines/doubao.py`
- query expansion：`query_expansions()`（`search.py:350`，price/doc 意图追加 official pricing/documentation）+ `plan_queries()`（`search.py:469`，对比意图扇出多子查询），另有分层拼写纠错（`fuzzy_correct_query` 411、rapidfuzz 可选）
- RAG 带引用：LLM 客户端 `search.py:1886`（OpenAI 兼容 `/chat/completions`，默认 DeepSeek），`answer_from_sources`（`search.py:1932`）；**需要配置 LLM key 才能用**
- deep research：`DeepResearch.research`（`search.py:2280`）——LLM 规划大纲 → 子查询并发扇出 → 全局来源池 → 逐章综合（全局编号引用，vega-lite 图可选依赖 vl-convert-python）→ 缺口反思补搜轮次 → 代码拼装参考来源；report_type 支持 standard/detailed/comparison/outline；同样**依赖 LLM key**
- 其余：抽取链 trafilatura → Jina Reader → requests（`ContentExtractor` 1074，crawl4ai 可选）、站内地图（1326）、2 至 6 级深抓（`DeepCrawler` 1421，纯 Python BFS 兜底）、GitHub 类型化搜索（gh CLI，1605）、`github_compare` 借 deps.dev 出 OpenSSF Scorecard、`compare_solutions` 矩阵（每个单元格带 source_url/excerpt/confidence）、Tavily 兼容端点 `POST /tavily/search`（`server.py:217`）、SQLite TTL 缓存（604）
- MCP 工具：`mcp_server.py` 实际注册 **10 个**：`health_check`、`web_search`、`web_ask`、`web_research`、`web_map`、`web_crawl`、`github_search`、`github_compare`、`compare_solutions`、`web_extract`。README 对比表与架构图写「8 tools」，与实际注册数不符（health_check 与 web_research 是后加的）
- HTTP 端点（`server.py`）：/search、/ask、/research、/extract、/map、/crawl、/github、/github/compare、/compare、/tavily/search、/openai-tools；默认绑定 127.0.0.1

**规模与质量信号**
- 总代码约 4,870 行 Python：`search.py` 单文件 3,534 行（全部引擎塞一个文件），`server.py` 405，`mcp_server.py` 313，`test_search.py` 550，doubao 引擎 68
- 测试为真实的单元测试（排序、SSRF 防护、缓存、gh compare 等约 20 余个用例），但无 CI（无 .github 目录）
- 自评：`EVAL_REPORT.md` 记录 50 用例、4 轮优化，总分 76.74 → 90.58（round 3 交付态）。**自报数据，未经独立复核**
- 自带 searxng 配置是「中国网络环境调优版」：google/bing/duckduckgo 全部 `disabled: true`，注释写明「国内 IP → CAPTCHA/301/challenge」；启用 brave、startpage、doubao、wikipedia、github、stackoverflow、reddit、news；`search.formats` 已含 json；limiter false

**认证与成本**
- 核心搜索 keyless；`web_ask`/`web_research`/`compare_solutions` 的 LLM 模式需要 OpenAI 兼容端点 key（默认 DEEPSEEK_API_KEY，可换 Ollama），否则这些工具直接报错返回
- 可选：`WEB_SEARCH_API_KEY`（火山引擎豆包搜索，**付费第三方 API**，仅自定义 SearXNG 引擎用）；可选出站代理 env 与 `scripts/agent-search-711-proxy.sh`（私有代理基建，公开仓不含真实值，不设则完全不启用）

**安全观察**
- 正面：抽取与爬取路径有 SSRF 防护（`url_is_safe` `search.py:178`，DNS 解析检查 + 重定向后复查，有测试）；HTTP 默认 127.0.0.1；`run.sh` 仅在用户显式配置 env 时启动 sing-box 代理
- 留意：自带的 SearXNG 配置关闭了 limiter（单用户本地合理）；未发现遥测
- 红旗：单人维护、5 stars、无 release/无 CI、4 个月无提交；全部逻辑集中在一个 3.5k 行的文件里，可维护性一般

**结论：备选（可用但需自担维护）**。它的每一项声称都有真实代码支撑，诚实度高于预期；作为「SearXNG 之上的自托管搜索增强层」（抽取、RAG、深研、Tavily 兼容）有实际价值。但不足以称「基础设施级」：无版本发布、无社区、无 CI。若选它，应视作「可参考与自持 fork 的代码库」，而非被动使用的上游依赖。不适合当唯一的搜索基础设施，只适合叠加在 SearXNG 之上。

---

## searxng/searxng

**URL / stars / license / 最近提交 / releases / open issues**
- https://github.com/searxng/searxng
- stars 39,606，forks 3,618，open issues 210，**AGPL-3.0**（LICENSE 文件确认为 GNU Affero GPL v3）
- 最近提交 2026 年 11 月 15 日（两天前，极活跃）
- releases：**无 GitHub release 也无 tag**，滚动发布；代码内 `searx/version.py` VERSION_STRING 为 "1.0.0"（dev 态）；镜像用 `latest` 或日期 tag（`.env.example` 示例 `2026.3.25-541c6c3cb`）

**部署方式（docker-compose 文件在仓库内）**
- 官方模板 `container/docker-compose.yml`：两个服务——`core`（`docker.io/searxng/searxng:${SEARXNG_VERSION:-latest}`，端口 `${SEARXNG_PORT:-8080}:8080`，挂载 `./core-config/` 到 `/etc/searxng/`，`env_file ./.env`）与 `valkey`（`valkey/valkey:9-alpine`，为 limiter 与缓存提供共享库）
- 配置模板 `container/settings.template.yml`（use_default_settings: true + secret_key + image_proxy）；`container/.env.example`（SEARXNG_VERSION/HOST/PORT）；`container/entrypoint.sh` 处理属主与 secret 替换
- 非容器路径：`requirements.txt` 本地安装（Python >=3.10，支持至 3.13，见 setup.py python_requires），uwsgi/granian/nginx/apache 文档齐备
- 资源消耗：文档未给出具体 RAM/CPU 数值，**未验证**；定性判断是一个 Flask 单进程 + 可选 valkey 的轻量服务，实际占用需本机实测

**settings.yml 可启用引擎分类（默认值精确核实）**
- `searx/engines/` 共 252 个引擎实现文件；默认 `settings.yml` 列 353 个引擎条目（含同引擎多分类重复），**123 个默认启用**
- 默认启用的 general 类：wikipedia、wikidata、dogpile、findborg、startpage、yandex api、wolframalpha_api、mojeek、brave，加上默认类别的 duckduckgo。**注意：当前 master（2026 年 11 月 15 日）把 google、bing、yahoo 的通用搜索全部默认 disabled**（图片/新闻/视频类如 bing images、google news、brave.news 等仍启用）
- 默认禁用但常用：google（全部）、bing 通用、yahoo 通用、qwant（全 4 个）、baidu（全 3 个）、sogou（全 4 个）、360search、quark、seznam、naver、marginalia、mwmbl、luxxle、yep、swisscows、startpagina 等
- **默认启用且需要 key 的引擎**：astrophysics data system、core.ac.uk、jina、springer nature、braveapi、exaapi（settings.yml 条目标了 api_key）；另有 google cse（需 API key + CSE ID）；引擎模块层面声明 require_api_key 的还有 azure、cloudflareai、flickr_api、freesound、deepl、kagi、yandex_api、marginalia 等（部分默认启用、无 key 时运行时报错但不影响实例）
- 默认 keyless 的通用搜索主力：duckduckgo、startpage、mojeek、brave（brave 为抓取版；braveapi 才是需要 key 的版本）

**JSON API 开启方式**
- `settings.yml` 的 `search.formats` 默认只有 `[html]`；改为含 `json`（合法值 html/csv/json/rss，`docs/admin/settings/settings_search.rst:114` 起有说明）。请求未启用的 format 返回 403
- 端点 GET/POST `/` 与 `/search`；参数文档（`docs/dev/search_api.rst`）：q（必需）、categories、language、pageno、time_range（day/month/year）、format、safesearch、theme；响应含 `unresponsive_engines` 字段（`searx/webapp.py:790`）
- 示例：`curl 'http://localhost:8080/search?q=searxng&format=json'`

**limiter（内置限流）**
- 实现：`searx/limiter.py` + `searx/botdetection/`（ip_limit、ip_lists、link_token、http_user_agent、http_accept 系列、valkeydb 等），默认配置 `searx/limiter.toml`
- `settings.yml` 默认 `limiter: false`、`public_instance: false`；启用 limiter 需要 valkey 提供共享状态（官方 compose 因此带 valkey 服务）。本机单用户使用无需开启
- 其余默认值留意的两点：`search.autocomplete` 默认 "duckduckgo"（会把输入前缀发给 DDG，可置空关闭）；`server.secret_key` 默认占位 "ultrasecretkey"，容器经 SEARXNG_SECRET 注入，暴露前必须改

**AGPL-3.0 对自托管使用的含义**
- 内部自用（自己跑、给自己的 agent 调）不触发源码披露义务；AGPL 的 §13 只在「修改后通过网络向他人提供服务」时要求向这些用户提供对应源码
- 本项目形态（本机/内网实例、自己消费 JSON API）完全合规，无需任何额外动作；只有将来把修改过的 SearXNG 公开给外部用户用时才需要开源修改

**本机（macOS + Docker）最短路径**
1. `mkdir -p searxng/core-config && cd searxng`
2. `curl -fsSL -O https://raw.githubusercontent.com/searxng/searxng/master/container/docker-compose.yml -O https://raw.githubusercontent.com/searxng/searxng/master/container/.env.example`
3. `cp .env.example .env`（可改 SEARXNG_PORT 等；默认 8080）
4. 写 `core-config/settings.yml`：`use_default_settings: true` + `server.secret_key: <openssl rand -hex 32 生成>` + `search.formats: [html, json]`
5. `docker compose up -d`
6. 验证：`curl 'http://localhost:8080/search?q=test&format=json'`

注意与 agent-search 的端口差异：agent-search 自带 compose 映射的是 8888。另外因上游默认关掉了 google/bing/yahoo 通用搜索，若要这两家需自行在 settings.yml 启用（可能遭遇验证码，属预期，属上游默认关闭的原因）。

**安全观察**
- 项目设计为不追踪用户；无遥测。请求面：所有引擎的外呼 + 默认 autocomplete 外呼
- JSON API 无内置认证（limiter 是防机器人不是鉴权），若绑定到 localhost 之外需自行加反向代理与鉴权
- `locate`/`find`/`command` 等本地执行类引擎在默认配置均为注释状态并有告警说明，勿在公开实例启用

**结论：主力（自托管搜索基础设施）**。二天前的提交、近 4 万 stars、成熟的容器交付与文档，是三者中唯一当得起「基础设施」的选项。API 层面只是个 keyless 的聚合 JSON 搜索端点，RAG/深研等要在其之上自建。

---

## 对比总结与取舍建议

三者定位不同，不构成完全互斥的替代关系：

| 维度 | RivalSearchMCP | agent-search | SearXNG |
|---|---|---|---|
| 定位 | MCP 工具集（研究扇出） | SearXNG 之上的增强层 | 元搜索引擎本体 |
| 成熟度 | 较高（140 stars，活跃） | 低（5 stars，无 release，4 个月未提交） | 最高（39.6k stars，滚动发布） |
| 部署形态 | uv/fastmcp，stdio 或 HTTP；默认有托管端点 | Docker（SearXNG）+ Python 进程 | 单容器 + valkey，官方 compose |
| 引擎依赖 | 自行直连 5 引擎与各 API（keyless） | 依赖 SearXNG 实例 | 自带 252 个引擎实现 |
| RAG / 深研 | 无（服务端不跑 LLM，返回结构化数据） | 有（需 LLM key） | 无 |
| 评分与冲突检测 | 有真实实现（quality 457 行 + conflict 587 行） | 有本地重排（官方源加权、内容农场降权）；无冲突检测 | 无（原样聚合） |
| 许可 | MIT | MIT | AGPL-3.0（自用无义务） |

**建议分工**：
1. **SearXNG 作为主力搜索基础设施**：本机 docker compose 起一个实例，`formats` 加 json，绑定 127.0.0.1。这是唯一建议无条件采用的组件；引擎启停按需在 settings.yml 调整（记住上游默认已关 google/bing/yahoo 通用搜索）。
2. **agent-search 列为「评估过的源码参考 + 可选增强」，不建议直接作为关键路径**：其 SearXNG 集成、query expansion、RAG、deep research、Tavily 兼容全部属实，但无版本发布、无 CI、单人维护、四个月停滞，自带配置还是按中国网络环境定制的（google/bing/ddg 全关）。合理用法：只取其中经过审读的模块思路（抽取链、重排、深研管线），或自行 fork 维护；不要把它当作会被持续维护的上游。
3. **RivalSearchMCP 作为并行的验证与深挖 MCP（备选主力）**：与 SearXNG 互补性强——它走的是「多源并发 + 每条结果带 quality 评分 + 规则化冲突检测」的路线，且 keyless、本地可跑（务必本地部署，别用默认的 fastmcp.app 托管端点）。适合承担「事实核验、学术与社交源补充、争议检测」，其评分与冲突检测是经过源码核实的真实功能。
4. **待确认事项（未验证项）**：RivalSearchMCP 与 SearXNG 的实际检索质量、引擎反爬稳定性均未实测；SearXNG 容器资源占用未实测；agent-search 的 EVAL_REPORT 为自报数据。这些建议在 Stage 3 上机试跑时补齐。

关键佐证文件路径（均在 /tmp/re-audit 下）：`RivalSearchMCP/rival_search_mcp/server.py`、`RivalSearchMCP/rival_search_mcp/core/quality/score.py`、`RivalSearchMCP/rival_search_mcp/core/conflict/detect.py`、`RivalSearchMCP/rival_search_mcp/tools/multi_search.py`、`agent-search/search.py`、`agent-search/mcp_server.py`、`agent-search/docker-compose.yml`、`agent-search/searxng/settings.yml`、`searxng/container/docker-compose.yml`、`searxng/searx/settings.yml`、`searxng/docs/dev/search_api.rst`、`searxng/docs/admin/settings/settings_search.rst`。