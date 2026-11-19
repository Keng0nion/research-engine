# RESEARCH-ENGINE-ARCHITECTURE

Research Engine v2 的统一架构。状态：**已实现**（除明确标注「计划」者）。所有模块均有源码与实测记录。

## 总体分层

```
┌────────────────────────────────────────────────────────────┐
│  Agent 侧（研究会话的脑）                                     │
│  研究技能（SKILL.md 工作流）+ MCP 工具套件 + 浏览器工具         │
├────────────────────────────────────────────────────────────┤
│  统一入口 researchctl（CLI，全部子命令支持 --json）            │
├────────────────────────────────────────────────────────────┤
│  编排层                                                      │
│  router（MODULE 3 动态源路由）  executor（MODULE 4 并行执行）   │
├────────────────────────────────────────────────────────────┤
│  供应商层 providers/（9 个原生 + 注册表扩展点）                │
├────────────────────────────────────────────────────────────┤
│  获取层 fetcher/（MODULE 5 全文获取：分级状态 + SSRF 防护）     │
├────────────────────────────────────────────────────────────┤
│  情报层 citations（MODULE 6）conflicts（MODULE 8）             │
├────────────────────────────────────────────────────────────┤
│  存储层 storage（PART VI：SQLite + 文档文件）                  │
│  research/research.db + research/{papers,websites,reports}     │
└────────────────────────────────────────────────────────────┘
```

## 模块对照（PART IV 任务书 → 实现位置）

| 任务书模块 | 实现 | 状态 |
|---|---|---|
| MODULE 1 研究规划器 | Agent 主导（技能提供 plan JSON 结构与 `session update --plan` 落库）；引擎不做 LLM 调用 | 已实现（人机分工明确） |
| MODULE 2 查询扩展 | `engine/router.py::expand_query` 确定性变体（site: 限定、survey/benchmark 等）；语义变体由 Agent 生成 | 已实现 |
| MODULE 3 动态源路由 | `engine/router.py` 领域启发式 + 显式覆盖；供应商集可扩展 | 已实现 |
| MODULE 4 并行执行器 | `engine/executor.py`：有界线程池（默认 6）、按错误类别的重试策略、去重入库、逐任务审计日志 | 已实现 |
| MODULE 5 全文获取 | `engine/fetcher.py`：robots 遵守、主机限速、20MB 上限、逐跳 SSRF 校验、trafilatura/PDF/JATS 三路提取、六态访问状态 | 已实现 |
| MODULE 6 引文情报 | `engine/citations.py`：DOI 规范化、前后向引用、DOI 存在性核验（Crossref→OpenAlex 回退）、标题三源比对 | 已实现 |
| MODULE 7 证据情报 | 证据卡数据模型（18 字段）+ `evidence draft/update`；权威性/相关性/方法质量/时效四维分离，不合成伪概率 | 已实现 |
| MODULE 8 冲突检测 | `engine/conflicts.py`：数值分歧（阈值 10%）+ 极性对立（含否定词检测）；候选交 Agent 复核，不自动取多数 | 已实现 |
| MODULE 9 迭代控制器 | 轮次记账（`session update --bump-round`、`search --round N`）+ 停止规则写入技能（默认最多 3 轮、边际递减即停） | 已实现 |
| MODULE 10 综合报告 | `engine/report.py`：可审计骨架（平台统计、访问状态分布、证据表、冲突、参考文献全列表），叙述段由 Agent 填 | 已实现 |

## 为什么引擎不做 LLM 调用（关键设计决策）

任务书中的规划、扩展、综合属判断类任务。本机环境下（引擎为本地 CLI）不内置模型调用，理由：
1. Agent 本身就是最强的判断器，且已经在会话内；
2. 避免引擎引入模型凭证与费用面（付费零启用原则）；
3. 引擎输出的结构化数据（JSON、证据卡骨架、报告骨架）让 Agent 的判断有据可依、可审计。

即「**肌肉在引擎，大脑在 Agent**」，技能文档（[research-engine-skill](https://github.com/Keng0nion/research-engine-skill) 仓库的 `research-engine/SKILL.md`）负责两者的接缝。

## 数据模型（SQLite，`engine/schema.sql`）

源文档与衍生解读分表：`documents`（去重键：canonical_url / doi / arxiv_id / pmid）、`doc_hits`（哪次查询命中哪篇）、`queries`（逐次检索审计）、`fetch_log`（获取结果与失败原因）、`evidence`（证据卡）、`citations`（引文边）、`conflicts`、`sessions` / `rounds`（轮次）。

## Agent 侧工具面

- MCP：arxiv（预印本精读）、pubmed（生物医学）、mcpsurfr（本地重排）、duckduckgo（兜底）、zotero（研究库）
- 技能：paper-lookup、citation-verification、systematic-review-prisma、bibtex-hygiene、reference-manager-interop、database-lookup、nature-citation
- 浏览器：agent-browser / playwright-cli（JS 页面与登录态场景升级路径）

## 防注入原则（贯穿架构）

所有检索结果、网页正文、PDF 文本、XML 全文一律作为**数据**进入系统：不进入任何指令位置；引擎不做基于检索内容的自动动作（无自动执行、无自动外发）；技能文档显式声明该纪律。XML 解析有实体扩展防护；子进程调用有参数注入防护；网络获取有 SSRF 防护。

## 已知架构边界

- 单一 Agent 会话内的并行度受引擎线程池限制（6），跨会话并行由 Agent 层调度；
- 冲突检测为规则级（可复现、可解释），语义级矛盾需 Agent 判断；
- 全文获取对 JS 渲染页面无内置渲染器（升级路径为浏览器工具，设计取舍见 KNOWN-LIMITATIONS）。
