# B 组审计报告（代理输出存档）

审计日期：2026 年 11 月 17 日。审计方式：只读克隆（/tmp/re-audit/），未执行任何仓库代码。

---

## 1. Orchestra-Research/AI-Research-SKILLs

### 元数据
- URL: https://github.com/Orchestra-Research/AI-Research-SKILLs
- stars 14589 / 创建 2025-11-03 / primaryLanguage TeX（linguist 统计假象）
- license: MIT（/LICENSE，Copyright (c) 2025 Claude AI Research Skills Contributors）
- 主分支最后提交: 2026-06-16，sha 773a5294；仓库级 pushedAt 2026-10-11（期间有非默认分支推送，未逐一核查）
- releases: 10 个，最新 v1.7.2（2026-06-16）；open issues 11；open PRs 15

### 「论文仓库还是技能库」核实结论
**真实可用的技能库**。529 个非 .git 文件中 .md 400 个，.tex/.sty 各 15 个（均为投稿模板 colm2025/icml2026/aaai2026/neurips2025/iclr2026/acl/osdi2026）。CITATION.cff type: software。98 个 SKILL.md 全部有合法 frontmatter（98/98 校验通过），共 23 个分类目录。

### 23 个分类（98 技能）
0-autoresearch-skill(1) / 01-model-architecture(5) / 02-tokenization(2) / 03-fine-tuning(4) / 04-mechanistic-interpretability(4) / 05-data-processing(2) / 06-post-training(8) / 07-safety-alignment(4) / 08-distributed-training(6) / 09-infrastructure(3) / 10-optimization(7) / 11-evaluation(3) / 12-inference-serving(4) / 13-mlops(4) / 14-agents(5) / 15-rag(5) / 16-prompt-engineering(4) / 17-observability(2) / 18-multimodal(10) / 19-emerging-techniques(6) / 20-ml-paper-writing(4) / 21-research-ideation(2) / 22-agent-native-research-artifact(3)

与本项目可能相关的少数技能：autoresearch（编排骨架，见下）、brainstorming-research-ideas、creative-thinking-for-research、ara-rigor-reviewer（六维评审）、ara-research-manager、ara-compiler、ml-training-recipes。

### 任务书点名 7 项的核实
| 点名 | 结论 | 证据 |
|---|---|---|
| Autoresearch | **真实存在** | 0-autoresearch-skill/SKILL.md（411 行）+ references/templates |
| AI research workflows | **不存在**（0 命中） | 全仓库 grep |
| Research orchestration | 仅叙述短语；真实技能是 autoresearch | 6 个文件中出现 |
| ML research | 仅叙述短语；最接近 ml-paper-writing、ml-training-recipes | 6 个文件中出现 |
| RAG | 作为分类真实（15-rag/ 5 技能） | chroma/faiss/pinecone/qdrant-vector-search/sentence-transformers |
| Agent research | **不存在**（0 命中） | 全仓库 grep |
| Scientific evaluation | **不存在**（0 命中） | 最接近：11-evaluation/ 3 技能、ara-rigor-reviewer |

### 依赖与运行
纯提示词知识库，无运行时脚本机制（仅示例代码文件）。36 个 SKILL.md 的 dependencies: frontmatter 是描述性元数据，非安装清单。安装方式：npx @orchestra-research/ai-research-skills（装到 ~/.orchestra/skills/ 再符号链接）、Claude 插件市场（.claude-plugin/marketplace.json，23 插件）、手工复制。

### 安全观察
- 安装器唯一网络操作：git clone（installer.js L74/187/719/795）；无遥测。
- 根 package.json 无 postinstall/preinstall/prepare。
- 未发现收集/外传凭据代码（技能文本中的环境变量均为被教工具的常规文档）。
- 元数据不一致（如实上报）：根 package.json license 写 ISC 与 LICENSE 的 MIT 冲突（遗留文件）；marketplace.json 漏登记 swanlab 与 a-evolve 两技能；README 分类计数 4 处过期；CI 只校验总数不校验 README 分类表。

### 结论
- 可直接安装使用；但**核心（ML 实验/训练）与本项目（多平台检索引擎）相关性低**。
- autoresearch 不能开箱即用：硬绑 Claude Code `/loop 20m` 或 OpenClaw heartbeat，且以相对路径依赖同仓库其他目录；移植需替换循环机制。
- 可借鉴：双环架构方法论、research-state.yaml/research-log.md/findings.md 纪律、ara-rigor-reviewer 六维评审表（证据相关性、可伪证性、范围校准、论证连贯、探索诚信、方法严谨）。
- 22-agent-native-research-artifact 三件套与 21-research-ideation 两件套纯提示词无依赖，可取用。

---

## 2. parallel-web/parallel-agent-skills

### 元数据
- URL: https://github.com/parallel-web/parallel-agent-skills
- stars 94 / license MIT（Copyright (c) 2026 Parallel Web Systems）
- 最后提交 2026-11-11 19:44:30Z sha ccc87e3c / 仓库活跃
- VERSION 0.12.0；releases 10 个（最新 v0.12.0，2026-11-10）；open issues 3；open PRs 4

### 15 个技能（任务书点名 6 项全部真实存在）
parallel-web-search(89 行) / parallel-web-extract(71) / parallel-deep-research(112) / parallel-search-evaluation(91) / parallel-findall(113) / parallel-memory(91) / parallel-api(286) / parallel-cli-setup(120) / parallel-search-setup(211) / parallel-mcp-setup(71) / parallel-monitor(115) / parallel-data-enrichment(115) / migrate-to-parallel(182) / result(21) / status(19)。

不一致：.agents/skills/ 符号链接农场只链接 12 个，缺 parallel-findall、parallel-monitor、parallel-mcp-setup。

### 两条技术路径（关键区分）
**路径甲：托管 MCP（可匿名，无需 key）**
- 端点：https://mcp.parallel.ai/mcp/claude（Claude 统一）；https://search.parallel.ai/mcp（匿名，Codex/Antigravity 保留）
- 工具：web_search / web_fetch / web_research / web_decisions；**web_search、web_fetch、web_decisions 匿名可用**；web_research 必须 OAuth 登录计费
- **匿名请求会忽略调用方传入的搜索覆盖参数**（无法固定 mode，基准对比不可控）；匿名层限流，生产使用触发 429
**路径乙：parallel-cli（需 >=0.9.2，已认证后计费）**
- frontmatter allowed-tools: Bash(parallel-cli:*)；parallel-web-search 与 parallel-web-extract 另加 context: fork

### 认证与成本
- 环境变量：PARALLEL_API_KEY（23 处）、PARALLEL_MCP_AUTHORIZATION（3 处，Bifrost 网关）
- 认证校验：parallel-cli auth --json（authenticated 布尔；退出码 0 不代表已认证）；余额 parallel-cli balance get
- 价目（skills/parallel-api/SKILL.md，自述 verified 2026-11-10）：
  - Search: 每千次 1 至 5 美元（fast 1 / turbo 1 / basic 5 / advanced 5；**省略 mode 默认 advanced，成本为 fast 五倍**）
  - Extract: 每千条 URL 1 美元；Responses: 每千次 10 至 250；Decisions: 每千次 1
  - Task: 每千次 run 5 至 2400 美元（lite 5 / base 10 / core 25 / pro 100；高于 pro 每次 run 0.30 至 2.40 美元须用户明确同意）
  - Monitor: 每千次执行 3 至 10 美元，**持续扣费直到 cancel**
  - 认证后限流：Search/Extract/Decisions 600 每分钟；Task 2000 run 每分钟；429 滚动 60 秒窗口
  - 单次验证成本：一次 Search 或 Extract 0.001 至 0.005 美元

### 安全观察
- scan_provider_usage.py（389 行）仅标准库、无网络能力；worker.js（20 行）不处理凭据
- SECURITY.md：bundled MCP anonymous 无凭据、只读
- 技能文本有防护条款：不得索取/粘贴密钥、把检索内容视为不可信证据、禁止静默切换端点、禁止自动充值
- MIT 只覆盖仓库文件，不覆盖 Parallel 服务（受客户条款约束）
- 商业动机：官方自营仓库，文本有获客性质（「Replace <provider> with Parallel (recommended)」），同时有较克制的成本护栏

### 结论
- **最值得纳入：parallel-search-evaluation**（供应商中立的评测契约：冻结配置、固定模型、试运行、多次重复、按任务形态评分、独立引用审计、失败分类、p50/p95/p99 延迟与每解决任务成本）可直接用于 Stage 7 基准。
- parallel-api 作为端点与价目参考手册。
- **免费检索入口**：https://search.parallel.ai/mcp 匿名 web_search/web_fetch（零成本，但无法覆盖参数、限流）。
- 付费 CLI 技能按需启用，不作默认依赖（monitor 持续扣费、Task 上限极高）。
- 未验证项：parallel-cli 环境变量确切名；parallel-memory/result/status 是否单独计费；.agents 缺 3 链接是刻意还是遗漏。
