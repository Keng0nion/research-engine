# INSTALLATION-CHANGELOG

安装与改造的完整时间线（2026 年 11 月 17 日，单日完成）。所有条目均已执行并验证；「计划」类条目不在本档。

## 前置状态（改造前）

- 搜索通道：duckduckgo MCP（npx mcp-duckduckgo）+ anysearch 技能（CLI）+ opencli（70+ 站点）+ 浏览器工具，无统一编排、无学术数据库连接、无研究存储。
- ZCode MCP 服务器：node_repl、computer-use（禁用）、duckduckgo、blender。
- 磁盘余量约 12GB；Docker 运行中（1 个无关容器）；无 docker compose。

## 时间线

| 阶段 | 动作 | 结果 |
|---|---|---|
| 侦察 | 清点现有配置、技能目录、工具链、Python 库生态 | 确认修复基线；确定 venv 依赖策略（trafilatura/httpx/pypdf） |
| Discover | 15 个必查仓库元数据核实（gh api）；45 + 12 个关键词扩展检索 | 全部存在；新增 22 + 15 个候选并核实 |
| Audit | 8 个并行审计代理做源码级只读深查（克隆 /tmp/re-audit，未执行任何仓库代码） | 8 份报告（约 1650 行），已归档 docs/audit-raw/raw/ |
| 基线探针 | DDG MCP 与 anysearch CLI 实测 | 均可用；发现 anysearch 已含 arXiv/OpenAlex 来源 |
| 立项 | 项目骨架建于 `/Users/luna/Documents/Dev/research-engine`；`docs/decisions.md` 记录裁决 | 选型矩阵成形 |
| 配置备份 | `~/.zcode/cli/config.json` → `config.json.bak-20261117-researchengine` | 可一键回滚 |
| Stage 4a | SearXNG 容器部署（127.0.0.1:8080，JSON API 开启，google 直连禁用） | 实测 51 条结果；brave/bing/google cse 正常 |
| Stage 4b | 安装 arxiv/pubmed/mcpsurfr 三个 MCP 并写入配置 | 三个服务器启动存活验证通过；下次会话生效 |
| Stage 4c | 7 个学术技能复制到 ~/.agents/skills + 来源存证文件 | 全部就位 |
| Stage 5 | 引擎实现：storage、9 个 provider、fetcher、executor、citations、conflicts、router、report、cli；研究技能 + 双入口包装脚本 | 全部模块可运行；每次写盘过独立安全门并修复 5 类问题 |
| Stage 6 | 逐供应商实测 → 全链路 E2E（检索→获取→证据卡→引文→冲突→报告） | 7 源全绿；openalex/crossref 经 DoH 兜底恢复；PubMed 摘要经 efetch 回填；JATS/PDF/markdown 三路全文实测 |
| Stage 7 | 12 题基准（基线 vs 引擎）+ 引文核验抽样 + 延迟分布 | 数据与结论见 RESEARCH-ENGINE-BENCHMARK.md |
| Stage 8 | 12 份交付文档 | 本批 |

## 本日修复的真实缺陷（引擎开发中）

1. URL 去重漏 `tracking` 参数 → canonical_url 规范化修正；
2. `metadata_json` 在文档已存在时不补齐 → 增加键级合并（fulltext_xml_url 因此可回填）；
3. PubMed 落地页被 bot 挑战 → 特判为摘要级（不抓取失败即如实标注）；
4. arXiv DOI 无法经 Crossref 核验 → OpenAlex DOI 回退；
5. `--json` 在子命令前被 argparse 覆盖 → 位置无关归一化；
6. 证据卡更新 ID 需位置参数 → 修正为位置参数（与技能文档一致）；
7. 会话轮数计数器与 `--round` 不同步 → 搜索后自动对齐；
8. uv 可编辑安装 .pth 两次失效 → 弃用，改 PYTHONPATH 包装双入口。

## v2.1 优化批（2026 年 11 月 17 日，第二批）

- 查询级 TTL 缓存（`engine/cache.py`，成功响应才缓存，`--no-cache` 绕过）；
- 供应商熔断器 + 每供应商并发信号量 + 抖动退避（`engine/executor.py`，参数在 `config/engine.yaml`）；
- `digest` 命令：全文抽取式摘要 + 建议数字（`engine/digest.py`，可选 `RE_LLM_*` 钩子经 `fetcher.safe_post_json` 走 SSRF 校验）；
- `stats` 命令：供应商成功率与延迟分位（`engine/stats.py`）；
- `session export`：report.md + session.json + references.bib（`engine/export.py`）；
- 获取适配器注册表（`fetcher.FETCH_ADAPTERS`：arxiv/europepmc/pubmed 规则结构化 + Unpaywall OA 解析）；
- DoH 解析缓存持久化（`cache/doh.json`）；
- 学术域路由加 SearXNG `science` 分类；anysearch 移出默认扇出；
- 基准追加 `benchmarks/trend.jsonl`；
- 测试新增 `tests/test_optimizations.py`（缓存/熔断/digest/数字抽取/bib/stats 全绿；修复了分句与指标词配对两个真实 bug）。

## 明确未执行（用户决策项）

- 付费服务（Exa/Firecrawl/Parallel CLI/Tavily 等）未启用、未注册；
- CNKI 通道未代装（需用户机构权限与本人登录；步骤已文档化）；
- 用户 Zotero 库未做任何写操作；
- 未改动任何与本研究无关的系统配置（除 ZCode MCP 配置与 SearXNG 容器）。
