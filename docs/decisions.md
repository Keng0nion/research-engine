# Research Engine v2 选型裁决记录

日期：2026 年 11 月 17 日。依据：8 组源码级审计（原始报告见 docs/audit-raw/raw/），全部结论可回溯。
三条前置约束（用户未答问时的保守默认，可逆）：项目位于 ~/Documents/Dev/research-engine；自托管 SearXNG 走回环；付费服务一律不启用，仅文档留档。

## 安装（Install）

| 组件 | 形态 | 理由（审计证据支撑） |
|---|---|---|
| SearXNG（本机 Docker，回环 8080） | 搜索基础设施 | 唯一当得起「基础设施」的候选（39.6k★、滚动发布）；开启 JSON API 后为引擎提供免 key 多引擎聚合；AGPL 自用无义务 |
| arxiv-mcp-server（uvx，PyPI） | Agent 侧 MCP | 19 工具：搜索、下载、LaTeX 逐节精读、引用图、告警；本地论文库（storage-path 指向项目）；仅认 PyPI（README 警告同名 npm 包陷阱） |
| pubmed-mcp-server（npx） | Agent 侧 MCP | 12 工具：PubMed/EuropePMC 检索、全文回退链（PMC→EuropePMC→Unpaywall）、MeSH、iCite 指标、引文格式化；全免费数据源 |
| mcpsurfr（uvx，PyPI） | Agent 侧 MCP | 唯一「真本地语义重排」（MobileBERT TFLite 纯 numpy）+ 只回答案段落；免 key、依赖轻、无 torch |
| 技能 7 个（KalarisLabs 6 + YuanyuanMa03 1） | Agent Skills | 见下表 |

### 技能清单
来自 KalarisLabs/research-agent-skills（整仓 MIT + 上游归属透明；安全治理最完备）：
1. paper-lookup（18 个免费 API、纯 stdlib）
2. citation-verification（纯 stdlib，直击引文幻觉）
3. systematic-review-prisma（stdlib 去重 + PRISMA 图）
4. bibtex-hygiene（零依赖 BibTeX 清洁）
5. reference-manager-interop（BibTeX/RIS/CSL-JSON 互转，桥接 Zotero）
6. database-lookup（82 个数据库端点文档，按需加载）

来自 YuanyuanMa03/academic-research-skills（MIT）：
7. nature-citation（纯 stdlib；GB/T 7714 中文引文与 Nature 系补引）

## 不安装（Skip，含原因，均可日后重审）

| 候选 | 否决理由 |
|---|---|
| RivalSearchMCP | **easyocr 为硬依赖（会拉入 torch，2GB+）**；本机磁盘仅余 12GB。评分/冲突检测能力由引擎自建模块覆盖 |
| firecrawl-mcp-server | 关键能力需付费 key；keyless 模式仅 3/27 工具可用且反馈上报需 opt-out；抓取能力由引擎 fetcher + 浏览器工具覆盖 |
| crawl4ai | 自托管整栈重（Playwright+Redis+RabbitMQ+Postgres，4GB 内存门槛）；JS 页面由 Agent 浏览器工具升级处理 |
| kujenga/zotero-mcp | 与已装官方 zotero 插件功能重复且为其严格子集（插件还有注释、高亮、写入） |
| cyanheads/openalex-mcp-server | 引擎原生 OpenAlex provider 覆盖管线需求；该仓仅 18★、重度依赖同作者框架，锁版本维护成本高 |
| smaniches/semantic-scholar-mcp | 引擎原生 S2 provider 覆盖检索与引用图；其独有面（推荐、片段搜索）属交互增强非管线能力 |
| exa-mcp-server | 需付费 key；且 Agnost 遥测默认开启且仓库内无法关闭（红旗） |
| parallel-agent-skills | 全部 6 点名技能真实存在，但 CLI 路径全部计费（Task 最高每千次 2400 美元）；匿名 MCP 端点（search.parallel.ai/mcp）可作为零成本备选，未接入 ZCode（HTTP 传输兼容性未验证）；其评测契约已被借用于 Stage 7 |
| wong2/mcp-jina-reader | 无许可证 + 停更 23 个月 + 45 行转发壳；r.jina.ai 能力以引擎 fetcher 可选层直接调用 |
| agent-search（cedarsaam） | 实现真实但 5★、无 release、无 CI、4 个月停更；单文件 3.5k 行不可维护 |
| daedra / MetaSearchMCP / TadMSTR searxng-mcp / kindly / tisDDM | 分别为：Rust 预编译二进制引入风险（且 SearXNG 已覆盖聚合）、太年轻+LICENSE 署名疑点、需自部署外部重排服务、搜索层零免 key、作者已弃用 |
| scopus-mcp | API key 实质要求机构 Elsevier 订阅；3 个未修复 bug、6 个月停更 |
| akapet00/semantic-scholar-mcp | 服务器启动级 bug 未修（issue #5）、6 个月停更、Python 3.13+ 门槛 |
| CNKI 4 候选（全组） | 合规红线：仅 SepineTam/cnki-mcp 可接受（检索限定、用户本人登录、不下载、限流），但其运行需用户机构 CNKI 权限与交互式登录——**列为用户可选步骤，本次不代装不代登录**；wuruiqi（批量下载防风控）、Mangofang（自动 IP 登录+无许可证）评级高；xxxxchaos 停滞最久 |
| Orchestra AI-Research-SKILLs | 真实技能库（98 技能）但其核心为 ML 实验训练引导，与检索基础设施错位；任务书点名的 7 项中 3 项在该仓零命中（叙述失真，已在文档修正）；仅借鉴 ara-rigor-reviewer 六维评审概念 |
| archora-skills / tisDDM / 其余 | 详见各审计原始报告 |

## 引擎自建（替代第三方组件的模块）
- 搜索引擎：OpenAlex、arXiv、Crossref、PubMed、Europe PMC、Semantic Scholar（全是免费 REST）
- 文档获取：httpx + trafilatura + pdftotext（poppler）+ 状态分级
- 引用图：S2 references/citations + OpenAlex cited_by + Crossref（反向链接）
- 冲突检测：规则版（数值比对、极性检测），Agent 复核
- 基准方法论：借用 deep_research_bench 的 RACE 四维 + FACT 三态引用验证管线

## 资源预算（PART VII）
max_workers 6；单供应商超时 25s；抓取超时 40s；文档上限 20MB；默认最大 3 轮；SearXNG 仅回环；所有付费 API 未启用。
