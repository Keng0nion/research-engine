# Research Engine v2 Stage 1+2 仓库审计报告

审计日期：2026 年 11 月 17 日。审计纪律：三个仓库均为 `git clone --depth 1` 浅克隆至 `/tmp/re-audit/` 后纯只读检查；未运行仓库内任何脚本、未安装任何依赖；仓库元数据（stars、issues、releases 等）来自当日 `gh api` 实时查询；Firecrawl 自托管依赖一项额外引用了 `firecrawl/firecrawl` 主仓的 `SELF_HOST.md`（只读文本拉取）。凡文件中未读到的内容，一律标注「未验证」。

三个克隆位置：
- `/tmp/re-audit/exa-mcp-server`
- `/tmp/re-audit/firecrawl-mcp-server`
- `/tmp/re-audit/mcp-jina-reader`

---

## exa-labs/exa-mcp-server

- **URL / 元数据**：https://github.com/exa-labs/exa-mcp-server ；5,238 stars、414 forks、open issues 10（gh api 当日）。
- **License**：MIT。文件 `/tmp/re-audit/exa-mcp-server/LICENSE`（首行 "MIT License, Copyright (c) 2025 Exa Labs"），`package.json` 亦声明 `"license": "MIT"`。
- **最近提交**：`93c0d5e1`，2026 年 11 月 3 日，提交信息 "Bump to 3.4.3 (#474)"；GitHub API `pushed_at` 为 2026 年 11 月 5 日。
- **Releases**：gh api 查询 releases 为 0 条、tags 为 0 条；版本仅通过 npm 包（`package.json` version 3.4.3）与提交推进。

**实际能力（MCP 工具精确清单，来源 `/tmp/re-audit/exa-mcp-server/src/toolRegistry.ts` 第 11 至 94 行，注册逻辑在 `/tmp/re-audit/exa-mcp-server/src/mcp-handler.ts` 第 51 至 148 行）**

注册表共 12 个工具条目，实际注册名与各工具源文件中的注册调用逐一核对如下：

1. 默认启用：`web_search_exa`（`src/tools/webSearch.ts` 第 181 行）、`web_fetch_exa`（`src/tools/webFetch.ts` 第 39 行，`toolName || "web_fetch_exa"`）、`agent_run`（`src/tools/agentRun.ts` 第 674 行；注册表 `enabled: true` 但标 `requiresUserProvidedApiKey: true`，所以必须配置用户自带 API key 才会注册，见 `mcp-handler.ts` 第 73 至 77 行）。
2. 默认禁用（注册表 `enabled: false`，须经 `ENABLED_TOOLS`/`TOOLS` 或 hosted 端 `?tools=` 显式启用）：`web_search_advanced_exa`（`src/tools/webSearchAdvanced.ts` 第 147 行）、`get_code_context_exa`（`src/tools/exaCode.ts`，已标 Deprecated）、`company_research_exa`（`src/tools/companyResearch.ts`，Deprecated）、`people_search_exa`（`src/tools/peopleSearch.ts`，Deprecated）、`linkedin_search_exa`（`src/tools/linkedInSearch.ts`，Deprecated）、`deep_researcher_start` 与 `deep_researcher_check`（`src/tools/deepResearchStart.ts`、`deepResearchCheck.ts`，Deprecated 且要求用户 key）、`deep_search_exa`（`src/tools/deepSearch.ts`，Deprecated 且要求用户 key）、`crawling_exa`（Deprecated 别名，`mcp-handler.ts` 第 104 至 107 行指向 webFetch）。
3. **关于「DISABLED_TOOLS」**：源码中不存在此类配置。它是反向白名单模型：环境变量 `ENABLED_TOOLS`（兼容旧名 `TOOLS`，`src/stdio.ts` 第 12、30 行）「设置后替换默认集合」，hosted 端用 URL 参数 `?tools=`（`api/mcp.ts` 第 497 至 499 行，README 注明会替换默认值）；默认集合由注册表 `enabled` 字段决定（`src/toolRegistry.ts` 第 124 至 126 行；`env.example` 注：默认 `web_search_exa,web_fetch_exa`，可选 `agent_run`、`web_search_advanced_exa`，别名 `agent_tools` 展开为 `agent_run`）。
4. 附加 MCP 面：prompts `web_search_help`、`agent_research_help`；resources `exa://tools/list`、`exa://agent/skill`、`exa://agent/schema-templates`（`mcp-handler.ts` 第 155 至 271 行）。仓库还内置 Claude 插件与 Agent Skills（`/tmp/re-audit/exa-mcp-server/plugins/exa/`、`skills/`）。

**依赖与运行要求**：Node >= 20（`package.json` engines；stdio 包以 esbuild 打为 CJS，target node20）。运行依赖 `@modelcontextprotocol/sdk`、`exa-js`、`zod`、`agnost`、`jose`、`mcp-handler`。**不需要浏览器或 Playwright**。`Dockerfile` 基于 `node:22-bookworm-slim`、非 root 用户、监听 8000（供自部署 hosted 逻辑用）。

**认证与成本**：环境变量核心是 `EXA_API_KEY`（`env.example` 第 1 至 2 行）。其余可配置项：`ENABLED_TOOLS`、`TOOLS`、`DEBUG`、`DEFAULT_SEARCH_TYPE`、`DYNAMIC_HIGHLIGHTS`、`EXA_SOURCE`、`MCP_SESSION_ID`、`MCP_MAX_DURATION_SECONDS`、`AGENT_CALL_WINDOW_MS`、`EXA_API_BASE_URL`（注释标注为测试用）、`AGNOST_LOG_LEVEL`。hosted 服务认证三选一：匿名（有速率限制）、OAuth、API key（可经 URL `?exaApiKey=`、`Authorization: Bearer`、`x-api-key` 传入，README "Authentication" 节）。**免费额度与定价：README 未给数字** —— 原文只有「hosted 服务可匿名使用但有速率限制；更高限制与 Exa Agent 需要 OAuth 或 API key」这一级别描述；全仓（含 skills、plugins）检索不到任何美元价格或额度数字。

**安全观察**
1. 遥测：`src/mcp-handler.ts` 第 273 至 298 行无条件调用 Agnost 的 `trackMCP`，上报端点 `https://api.agnost.ai`，配置显式关闭了输入、输出与错误上报（`disableInput/disableOutput/disableError: true`），即上报内容据其配置推断为调用事件元数据；**仓库中未读到关闭该遥测的开关**（`AGNOST_LOG_LEVEL` 只是日志级别）。具体上报字段未验证。
2. 向 Exa API 的出站请求自带 `x-exa-integration`、`x-exa-mcp-session-id`、`x-exa-mcp-client` 三个头（`src/tools/config.ts` 第 13 至 36 行），客户端元数据经过截断与清洗（`src/utils/mcpClientMetadata.ts`）。
3. hosted 入口匿名限流为 fail open：限流后端（Upstash Redis）检查失败时放行匿名 `tools/call`，并打 `[RATE_LIMIT_FAIL_OPEN]` 告警（`api/mcp.ts` 第 354 至 361 行）。
4. 正向设计：hosted 每请求重建 handler 以避免 API key 跨用户泄漏（`api/mcp.ts` 第 389 至 394、561 至 566 行）；CORS 用 `Origin: *` 且有理由注释（认证按请求头而非 cookie）。
5. 官方支持把 key 放进 URL query（`?exaApiKey=`），凭据会进入 URL，属较弱的凭据放置方式。

**结论：建议主力（搜索层）**。维护活跃（一周内推送）、MIT、默认工具面仅 2 至 3 个（上下文开销小）、白名单控制精确、无浏览器依赖，hosted 匿名可零配置充当保底。红旗：Agnost 第三方遥测默认开启且仓库内未见关闭开关；免费额度无数字，长期成本需上线后到 dashboard 核实；工具清单里 Deprecated 项占多数，启用时须避开。

---

## firecrawl/firecrawl-mcp-server

- **URL / 元数据**：https://github.com/firecrawl/firecrawl-mcp-server ；7,836 stars、938 forks、open issues 194（gh api 当日）。
- **License**：MIT（`/tmp/re-audit/firecrawl-mcp-server/LICENSE` 与 `package.json` `"license": "MIT"`）。
- **最近提交**：`561e5812`，2026 年 11 月 16 日；GitHub API `pushed_at` 同日。
- **Releases**：共 19 个 tag；最新 release `v3.36.1`（2026 年 11 月 3 日发布），而 `package.json` 版本已是 3.40.0 —— main 明显领先于 release。

**实际能力（MCP 工具精确清单）**

宿主完整面（带凭据）共 33 个工具，证据为契约快照 `/tmp/re-audit/firecrawl-mcp-server/tests/contract-snapshots/hosted-full.json`（sessions.apiKey）与 `stdio-api-key.json`：

`firecrawl_scrape`、`firecrawl_map`、`firecrawl_search`、`alexandria_library_search`、`alexandria_library_read`、`firecrawl_save_skill`、`firecrawl_search_feedback`、`firecrawl_feedback`、`firecrawl_crawl`、`firecrawl_check_crawl_status`、`firecrawl_agent`、`firecrawl_agent_status`、`firecrawl_interact`、`firecrawl_interact_stop`、`firecrawl_parse`、`firecrawl_monitor_create`、`firecrawl_monitor_list`、`firecrawl_monitor_get`、`firecrawl_monitor_update`、`firecrawl_monitor_delete`、`firecrawl_monitor_run`、`firecrawl_monitor_checks`、`firecrawl_monitor_check`、`firecrawl_research_search_papers`、`firecrawl_research_inspect_paper`、`firecrawl_research_related_papers`、`firecrawl_research_read_paper`、`firecrawl_developer_search`、`firecrawl_gov_search`、`people_company_search`、`people_company_enrich`、`jobs_search`、`firecrawl_credit_usage`。

各分面差异（均来自 `tests/contract-snapshots/` 快照，README 第 43 行与之吻合）：
1. hosted 无凭据 keyless：仅 3 个（`firecrawl_scrape`、`firecrawl_search`、`firecrawl_parse`）。
2. 本机 stdio 无 key 且无 URL（keyless 模式）：列出 27 个（`stdio-keyless.json`），但 `firecrawl_map` 等调用返回 "Unauthorized: API key is required when not using a self-hosted instance"（`src/server.ts` 第 1047 至 1051 行同文）。
3. 自托管（设 `FIRECRAWL_API_URL`）：30 个（`stdio-self-hosted.json`、`http-self-hosted.json`），不含 `people_company_search`、`people_company_enrich`、`jobs_search`（这三者需云端账号与 Alexandria 权限）。
4. 搜索专用端点 `/v2/mcp-search`：固定 12 个（`hosted-search-primary.json`：四个 research、`firecrawl_developer_search`、`firecrawl_gov_search`、两个 enrich 加 jobs、`firecrawl_search`、`firecrawl_find_tools`、`firecrawl_scrape`）。

**self-hosted 与云 API 两种模式的差别（源码与文档佐证）**
1. 云模式：默认打 `https://api.firecrawl.dev`（`src/server.ts` 第 2448 至 2455 行常量 `DEFAULT_CLOUD_API_URL`），凭据 `FIRECRAWL_API_KEY`（形如 `fc-…`）。
2. 自托管模式：设 `FIRECRAWL_API_URL` 后全部调用转向该实例；API key 变为可选（README 第 291 至 297 行；`src/server.ts` 第 1012 行注释 "required for cloud, optional for self-hosted"）；本机 stdio 直接解析本地文件（`firecrawl_parse` 的 `filePath`）必须设 `FIRECRAWL_API_URL`（`src/server.ts` 第 3650 至 3653 行明确报错文案）；Alexandria 工具会把请求发到该 endpoint 由本地账号作答（README 第 297 行）。
3. 无 key 也无 URL：本机 stdio 进入 keyless，`scrape` 与 `search` 免费直打云（按 IP 限速），其余工具 Unauthorized（`src/index.ts` 第 113 至 126 行原文注释与提示）。
4. 凭据解析顺序：`FIRECRAWL_OAUTH_TOKEN` 优先于 `FIRECRAWL_API_KEY`（`src/service/profiles.ts` 第 104 至 109 行）；OAuth 访问令牌前缀 `fco_`；HTTP 传输还接受 `Authorization: Bearer`、`x-firecrawl-api-key`、`x-api-key`。
5. 相关环境变量另有：`FIRECRAWL_INTEGRATION`、`FIRECRAWL_MCP_LIBRARY_SKILLS`、`FIRECRAWL_MCP_ALLOWED_HOSTS`、`HTTP_STREAMABLE_SERVER`、`SSE_LOCAL`、`CLOUD_SERVICE`、`FASTMCP_ENDPOINT`、`FIRECRAWL_MCP_SEARCH_ENABLED`、`PORT`、`HOST`，以及反馈工具的关闭项（见安全观察）。

**云 API 免费额度与价格**：README **未给美元数字**。能读到的量化信息均为 credit 计量：keyless 免费层限速（`scrape`、`search`、`parse` 可用，其余需 key）；一次 search 计 2 credits、使用后提交 `firecrawl_search_feedback` 返还 1 credit，每日返还上限 100 credits/团队；`firecrawl_agent` 单次 `maxCredits` 默认 2,500（免费请求上限同为 2,500）。具体套餐价格不在本仓库文档内。

**self-hosted 部署依赖与本机资源要求**
1. 本仓库（MCP 服务器本身）：Node >= 22（`package.json` engines），依赖 `@modelcontextprotocol/server` 2.3.1、`firecrawl` 4.51.0、`hono`、`xsschema`、`zod` 4；**无 Playwright、无本地浏览器依赖**；Dockerfile 基于 `node:22.23.5-alpine3.23`，默认 stdio，HTTP 模式 `PORT` 默认 3000；官方镜像 `ghcr.io/firecrawl/firecrawl-mcp-server`。
2. 自托管 Firecrawl API 本体（另仓 `firecrawl/firecrawl`）：据我今日只读拉取的 `https://raw.githubusercontent.com/firecrawl/firecrawl/main/SELF_HOST.md`（109 行，main 分支文档）——Docker Compose 会起「Firecrawl API 与 workers、Playwright、Redis、RabbitMQ、NuQ PostgreSQL，以及可选的 FoundationDB 队列后端」；默认只把 API 暴露到 3002 端口；默认无认证（`USE_DB_AUTHENTICATION=false`）且默认无持久卷。**具体 RAM/CPU 数字未读到**（官方 self host 指南页面为 JS 渲染，抓取未获得数字），标注「未验证」。
3. 对本机（macOS）而言：跑 `npx firecrawl-mcp` 只是一个小 Node 进程加对云的出站请求；只有真正自托管整栈才需要 Docker 与上述多服务，浏览器负载不在本机。

**安全观察**
1. 出站指纹：每个 API 请求携带 `X-Origin` 头与 `origin` 字段，按优先级取 MCP 客户端名、User-Agent、OAuth 客户端名、Referer 主机等（`/tmp/re-audit/firecrawl-mcp-server/src/origin.ts` 第 1 至 18、250 至 306 行），Firecrawl 服务端可见你的客户端身份。
2. 本机 HTTP 模式有明确的防 DNS rebinding 与跨域设计：默认只答 localhost 系主机的 Host/Origin，其余 403，CORS 回显（README 第 176 至 192 行；`src/index.ts` 第 83 至 97 行）。
3. 反馈上报默认开启：`firecrawl_search_feedback` 与 `firecrawl_feedback` 默认注册，向厂商回传结构化使用反馈；关闭需显式设 `FIRECRAWL_NO_SEARCH_FEEDBACK=1`（或 `FIRECRAWL_DISABLE_SEARCH_FEEDBACK`）与 `FIRECRAWL_NO_ENDPOINT_FEEDBACK=1`（或 `FIRECRAWL_DISABLE_ENDPOINT_FEEDBACK`），见 `src/index.ts` 第 36 至 54 行。
4. README 明确警告不要把 key 放进 URL 或 agent 对话（第 77 行）；`src/index.ts` 第 15 行会 `process.loadEnvFile()` 读取当前目录 `.env`（小注意点）。
5. 依赖表中未见独立第三方分析/遥测 SDK；出站目标为 Firecrawl 云或你自托管地址。

**结论：建议主力候选（抓取与结构化数据层），上线前需做成本与反馈策略决定**。能力面远超 Exa（爬站、地图、监控、论文、政府索引、浏览器交互）；不足是开箱默认把使用反馈工具挂出来（有隐私与合规动作要求，须 opt out），以及 194 个 open issues、release 落后 main 的维护节奏。红旗：Alexandria 系工具（enrich、jobs、library）需要特定账号权限，团队计划里不要把它们当既定能力；云 API 有 credit 计费，免费层数字须另行向官方文档核实（本次未读到）。

---

## wong2/mcp-jina-reader

- **URL / 元数据**：https://github.com/wong2/mcp-jina-reader ；47 stars、8 forks、open issues 0；`archived` 与 `disabled` 均为 false（gh api 当日）。
- **License**：**无许可证文件**。仓库文件仅 6 个（`.gitignore`、`README.md`、`package.json`、`pnpm-lock.yaml`、`src/server.ts`、`tsconfig.json`），`ls` 无 LICENSE 或 COPYING；GitHub API 的 `license` 字段为 `null`。
- **最近提交**：`1301242884`，2024 年 12 月 11 日，提交信息 "Use litemcp"；`pushed_at` 同为 2024 年 12 月 11 日。**停更属实**：截至今日约 23 个月无提交。
- **Releases**：0 个 tag、0 个 release。
- **代码量**：`src/server.ts` 45 行；全仓文本合计 85 行（README 3 行、`package.json` 19 行、`tsconfig.json` 15 行、`.gitignore` 3 行、加源码 45 行）。
- **实现方式**：**不调自研，也不本地抽取**。核心就 4 至 14 行：`fetch("https://r.jina.ai/" + url)`，有 `JINA_API_KEY` 环境变量时加 `Authorization: Bearer`，否则匿名调用；无缓存、无重试、无超时，错误只透出 `response.statusText`。暴露 1 个 MCP 工具 `fetch_url_content`（第 18 至 27 行）与一个同名 prompt（第 29 至 43 行）。框架为 `litemcp ^0.7.0` 加 `zod ^3.23.8`。`package.json` 标 `"private": true`、`scripts` 为空，**未发布 npm**，只能克隆源码自行运行；README 只有一句话，未写安装与配置说明。

**停更加无许可证意味着什么（基于上述事实的合规与工程判断）**
1. 法律：无 LICENSE 即默认保留全部权利，严格意义上不可复制、修改、再分发（公开可见不等于授权）；把它作为依赖引入组织产品或并入 Research Engine 都有明确合规风险。
2. 安全：23 个月无维护、无 CI 可见痕迹；运行需要在安装时从 npm 拉取 `litemcp` 这一小生态包的旧版本树，供应链面不受控；任何上游破坏性变更或漏洞都不会被此仓库吸收。
3. 功能：能力等价于「URL 转 Markdown 的一次匿名转发」，无错误分级、无自托管选项；目标 URL 全量交给第三方 `r.jina.ai`，隐私边界完全外置。
4. 运营盲点：`JINA_API_KEY` 只在源码第 5 行出现，README 未文档化，使用方必须读代码才知道有该配置。

**结论：不采用（作为组件）**。它就是一个 45 行的转发壳，不值得承担「无许可证加停更」的代价。如仍需「URL 转 Markdown」这一能力，可以用自家几行代码直调 `r.jina.ai`（与它做的事完全相同），或改用 Exa 的 `web_fetch_exa`、Firecrawl 的 `firecrawl_scrape` 这类维护活跃的替代路径。本仓库序号、行数、提交日期与许可证缺失情况均已逐项核实（见上）。上游 `r.jina.ai` 服务当前质量未做实测，标注「未验证」。

---

## 对比与建议

**Exa 对比本机现有搜索能力**：本机现有路径是内置 WebSearch/WebFetch 加 DuckDuckGo MCP（据项目全局配置描述；本次为只读审计，未运行任何搜索做实测，故以下为能力结构对比而非实测结论）。Exa 的差异点（源码级证据）：`web_search_exa` 返回「干净正文」而非仅链接（默认 10 条结果、单条上限 3000 字符，`src/tools/config.ts` 第 96 至 97 行），并提供过滤器型高级搜索与多步研究的 `agent_run`；DDG MCP 路线是关键词检索加自行抓取。二者定位互补：Exa 走语义检索与正文直出，DDG 走关键词与零成本兜底。接纳成本极低（hosted 匿名可用，本地 `npx` 加一个 `EXA_API_KEY` 即可）。

**Firecrawl 对比 Crawl4AI**：`firecrawl-mcp-server` 的 README、`docs/` 与 CHANGELOG 中未出现 Crawl4AI 字样（全文检索无命中），按约定跳过该对比；本仓库内也没有可引用的官方对比数据。

**Jina Reader 是否还值得用**：就这个仓库而言不值得继续用（无许可证、停更 23 个月、45 行转发壳）。它证明的只是「`r.jina.ai` 端点本身可用」这一调用形式；若只是要这个端点能力，直接一到五行自研调用即可绕开该仓库的全部风险；若想零代码，Exa 与 Firecrawl 的抓取工具已覆盖同等能力且维护活跃。

**在本项目中的建议角色汇总**：
1. Exa MCP：主力搜索层（先用 hosted 匿名或免费 key 验证检索质量与中文覆盖，再决定是否常驻）。
2. Firecrawl MCP：抓取与结构化层主力候选；建议先以云 API 加 key 做小规模验证，同时决定两件事——是否 opt out 反馈工具、以及是否值得承担自托管整栈（Playwright、Redis、RabbitMQ、PostgreSQL）为替代。
3. Jina Reader：不采用；需求由前两者或自研直调覆盖。
4. 待办核实项（本次未验证或未读到）：Exa 与 Firecrawl 的免费额度、付费价格（两个 README 均无美元数字）；Firecrawl 自托管整栈的具体硬件要求（官方文档页未读到数字）；Exa 遥测的具体字段集（只验证了开关项的配置意图）。