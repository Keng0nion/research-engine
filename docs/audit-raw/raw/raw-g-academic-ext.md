审计完成。以下为最终报告（全部结论基于 2026 年 11 月 17 日在 `/tmp/re-audit/` 下浅克隆的实际源码与 `gh api` 元数据；未克隆到的内容一律标注未验证）。

## smaniches/semantic-scholar-mcp

- URL：https://github.com/smaniches/semantic-scholar-mcp ｜ stars：26 ｜ license：MIT（`LICENSE` 文件，Copyright (c) 2025 TOPOLOGICA LLC；`pyproject.toml` 声明 `license = {text = "MIT"}`）
- 最近提交：2026 年 11 月 11 日（`28e9626`，合并 PR #205）；pushed_at 为 2026 年 11 月 12 日
- releases：由 release-please 自动化，最新 `semantic-scholar-mcp-v1.7.15`（2026 年 11 月 5 日），读到至少 10 个连续版本
- open issues：0 个 issue；3 个 open PR（#207 Dependabot 升级、#206 release PR 1.7.16、#203 CI 升级）

**实际能力（14 个 MCP 工具，逐一定位在 `src/semantic_scholar_mcp/server.py`）**：
1. `semantic_scholar_search_papers`（第 328 行，关键词搜索，year/field/publicationType/开放获取/最低引用数过滤，offset 分页）
2. `semantic_scholar_get_paper`（第 505 行，单篇详情，可选 `include_citations`/`include_references` 并行抓取，两个方向各有独立 offset 与 next 游标分页）
3. `semantic_scholar_search_authors`（第 620 行）
4. `semantic_scholar_get_author`（第 679 行，可选论文列表）
5. `semantic_scholar_recommendations`（第 731 行，单种子，recent/all-cs 池）
6. `semantic_scholar_bulk_papers`（第 778 行，POST paper/batch，上限 500 篇，位置对齐校验）
7. `semantic_scholar_bulk_search`（第 850 行，排序、布尔语法、token 游标分页）
8. `semantic_scholar_export_citation`（第 915 行，BibTeX）
9. `semantic_scholar_match_paper`（第 967 行，标题匹配，保留 matchScore）
10. `semantic_scholar_paper_authors`（第 1019 行，论文作者的完整档案）
11. `semantic_scholar_author_batch`（第 1057 行，上限 1000 个作者，逐位置身份校验）
12. `semantic_scholar_multi_recommend`（第 1135 行，正负样本多种子推荐）
13. `semantic_scholar_snippet_search`（第 1201 行，全文片段搜索）
14. `semantic_scholar_status`（第 1253 行，连通性与限流档位检查）

**依赖与运行**：Python >=3.10；`mcp>=1.30.0,<2`（官方 SDK 内置 FastMCP）、`httpx`、`pydantic>=2.1`、`starlette`；stdio 与 Streamable HTTP 双传输；PyPI 包名 `s2-mcp-server`，另有 ghcr.io Docker 镜像、SLSA 构建溯源与 CycloneDX SBOM。
**认证与成本**：`SEMANTIC_SCHOLAR_API_KEY` 可选（HTTP 传输时支持按请求绑定 key 的 middleware）。无 key 走共享池，客户端节流 1.0 秒/请求，有 key 默认 1.1 秒/请求（可配置）；429/502/503 自动重试，5 分钟 TTL 缓存。API key 免费（Semantic Scholar 官方）。

## akapet00/semantic-scholar-mcp

- URL：https://github.com/akapet00/semantic-scholar-mcp ｜ stars：39 ｜ license：MIT（`LICENSE`，Copyright (c) 2025 Ante Kapetanovic）
- 最近提交：2026 年 5 月 7 日（`51f97a5` "Remove typo"），此后约 6 个月无提交
- releases：无（`gh api .../releases` 返回空）；仅支持 `uvx --from git+...` 安装，无 PyPI 包
- open issues：1 个 issue + 1 个未合并修复 PR：#5「Server fails to start: fastmcp 2.x triggers fakeredis ImportError」（服务器无法启动），修复 PR #4 处于 open 状态未合并

**实际能力（14 个工具，注册于 `src/semantic_scholar_mcp/server.py` 第 88 至 101 行）**：
1. `search_papers`（`tools/papers.py` 第 27 行）
2. `get_paper_details`（第 112 行，含 TLDR 开关）
3. `get_paper_citations`（第 172 行，被引论文，limit 1 至 1000，year 过滤）
4. `get_paper_references`（第 254 行，参考文献）
5. `search_authors`（`tools/authors.py` 第 49 行）
6. `get_author_details`（第 109 行）
7. `get_author_top_papers`（第 473 行，高引论文）
8. `find_duplicate_authors`（第 187 行，作者重名检测）
9. `consolidate_authors`（第 331 行，作者记录合并预览/执行）
10. `get_recommendations`（`tools/recommendations.py` 第 20 行）
11. `get_related_papers`（第 108 行，多正负样本推荐）
12. `list_tracked_papers`（`tools/tracking.py` 第 23 行，会话内已取论文追踪）
13. `clear_tracked_papers`（第 62 行）
14. `export_bibtex`（第 80 行，会话论文导出 BibTeX 文件）

**依赖与运行**：Python **>=3.13**（较高门槛）；独立 `fastmcp>=2.0,<3` 包（非官方 SDK 内置版）、`httpx`、`pydantic`；stdio。工程件含 circuit breaker、rate limiter、缓存、约 97% 覆盖率的测试（README 声称）。
**认证与成本**：`SEMANTIC_SCHOLAR_API_KEY` 可选；其余全为 `SS_` 前缀的本地调优变量（缓存、重试、熔断）。README 给出速率表：无 key 共享池每 5 分钟 5000 次、有 key 每秒 1 次。

**仓库 1 与 2 对比**：
- 工具数：持平，14 对 14。
- 类型化程度：仓库 1 输入侧全面 Pydantic 化（`models.py` 398 行、15 个 Input 模型），输出为 Markdown/JSON 字符串（所有工具 `structured_output=False`）；仓库 2 输入侧为裸函数签名，输出侧返回 Pydantic 模型（`list[Paper]`、`PaperWithTldr` 等），由 FastMCP 生成结构化输出。类型化方向相反，仓库 2 输出结构更好，仓库 1 输入校验与错误信息更精细（如 `_friendly_validation_message`、身份绑定校验 `_require_paper_record_identity`）。
- 引用图能力：仓库 1 在 `get_paper` 内做双向单跳抓取并支持独立 offset/next 分页；仓库 2 用两个独立工具做单向单跳，limit 到 1000 但无 offset 游标，分页能力弱。两者均无多跳图遍历。
- 覆盖面：仓库 1 独占 snippet 全文搜索、bulk 批量（论文 500/作者 1000）、bulk 排序搜索、标题 match、status；仓库 2 独占会话内追踪、BibTeX 文件导出、作者去重与合并、作者高引论文。
- 实现完整度判定：**仓库 1 明显更完整**——活跃维护（1 个月内多次发版，迭代至 1.7.15）、8 条 CI 工作流、SLSA/SBOM 供应链、无 open issue；仓库 2 有服务器启动级 bug 未修、6 个月停更、Python 3.13+ 门槛偏高。

## qwe4559999/scopus-mcp

- URL：https://github.com/qwe4559999/scopus-mcp ｜ stars：55 ｜ license：MIT（`LICENSE`，Copyright (c) 2026 Scopus MCP Contributors）
- 最近提交：2026 年 5 月 17 日（`03211b6`，合并缓存路径修复 PR #5）；此后约 6 个月无提交
- releases：无 GitHub release（`pyproject.toml` 版本 0.1.8，存在 `publish.yml`）
- open issues：3 个全是 bug：#10「get_citing_papers 400s on every call; get_abstract_details returns no abstract or authors」、#9 缓存相对路径问题、#8 Claude Desktop 崩溃

**实际能力（5 个工具 + 2 个 prompt，`src/scopus_mcp/server.py`）**：
1. `search_scopus`（第 23 行，Scopus 语法查询，结果上限 25）
2. `get_abstract_details`（第 48 行，按 Scopus ID 取摘要）
3. `get_author_profile`（第 62 行，按 Author ID 取作者档案）
4. `get_citing_papers`（第 76 行，用 `REFEID()` 查询做前向引用）
5. `get_quota_status`（第 101 行，配额余量）
prompts：`research-summary`、`author-analysis`（第 185 至 249 行）。inputSchema 为手写 JSON，返回值为 `str(dict)`，无 Pydantic 类型化。

**Scopus 凭证（核心问题，已读源码与 README 双重确认）**：
- 认证方式：`X-ELS-APIKey` 请求头，key 来源为环境变量 `SCOPUS_API_KEY` 或 `config.json` 的 `api_key`（`src/scopus_mcp/config.py` 第 24 至 45 行；`client.py` 第 24 至 28 行）。源码中**没有 insttoken（机构令牌）处理**。
- API key 的获取门槛：README 第 11 行原文「requesting an Elsevier Scopus API key generally requires that your organization or institution has a subscription to Elsevier database services」，第 34 行建议用教育/机构邮箱，公共邮箱域可能被拒。即：**实质上要求机构对 Elsevier 数据库的订阅**，不只是免费注册。
- 免费额度：README 与源码均未见具体免费额度数字（未验证）；代码只解析 `X-RateLimit-*` 响应头与处理 429。
- 佐证：open issue #10 报告 `get_abstract_details` 无论文即代码中「返回空」的典型表现出现在无订阅环境下（该因果为间接推断，issue 原文未说明订阅状态）。

**依赖与运行**：Python >=3.10；`httpx`、`mcp>=0.1.0`、`python-dotenv`；stdio。

## Ayanami0730/deep_research_bench

- URL：https://github.com/Ayanami0730/deep_research_bench ｜ stars：851 ｜ license：Apache-2.0（`LICENSE` 文件确认为 Apache License 2.0；注意 README 徽章写「Code_License-MIT」与实际文件不符，属文档瑕疵）
- 最近 push：2026 年 9 月 29 日
- releases：无；open issues：25 个（多为 leaderboard 提交申请，另有 #53 FACT LaTeX JSON 解析缺陷、#30 人工标注子集代码索取、#28 judge 模型弃用答疑等）

**评测方法（读自 `deepresearch_bench_race.py`、`run_benchmark.sh`、`utils/`、`prompt/`、`data/`）**：
两套互补管线，各给一组指标。

RACE（报告生成质量，参考对照式）：
1. 数据集：100 个任务（`data/prompt_data/query.jsonl` 实测 50 中文 + 50 英文），覆盖 22 个领域（实测：Science & Technology 16、Finance & Business 14、Software Development 10、Education & Jobs 8、Health 8，其余 18 个领域各 2 至 4 个），任务与领域分布源自 96,147 条匿名真实用户查询的统计（README 说明）。
2. 每任务动态标准：`data/criteria_data/criteria.jsonl`（100 条）内含 `dimension_weight`（四个维度逐任务不同权重，如任务 1 为 insight 0.36、comprehensiveness 0.30、instruction_following 0.20、readability 0.14）与 `criterions`（每维度若干条，每条含 criterion、explanation、weight）。标准由 `utils/generate_criteria.py` 离线用 LLM 生成后固化（不在评测运行时生成；运行时脚本不含此步）。
3. 评分：LLM judge 将待测文章与官方参考报告（`data/test_data/cleaned_data/reference.jsonl`，约 6MB）逐条标准对比打 0 至 10 连续分（`prompt/score_prompt_en.py`，含中英双版）；`utils/score_calculator.py` 做维度内加权平均、维度间加权和得 Overall。实测输出样例（`results/race/claude-3-7-sonnet-latest/race_result.txt`）：Comprehensiveness 0.4110、Insight 0.4051、Instruction Following 0.4621、Readability 0.4172、Overall 0.4218（0 至 1 尺度）。
4. 评测维度清单（四个，直接可借鉴）：Comprehensiveness（信息覆盖广度、深度与细节、数据事实支撑、多视角平衡）、Insight（分析深度与原创性、逻辑推理与因果、问题洞察与解法、前瞻启发）、Instruction Following（对任务具体要求的遵从，按任务生成标准）、Readability（清晰度、组织、呈现质量）。
5. Evaluator 治理：官方 judge 由 Gemini-2.5-Pro 迁至 GPT-5.5，迁移依据是在 200 篇人工标注子集上与人类判断的对齐率（人类标注者一致性 baseline 68.78%）。

FACT（引用可信度，四步管线）：`utils/extract.py`（LLM 提取 fact、ref_idx、url 三元组）→ `utils/deduplicate.py`（去重）→ `utils/scrape.py`（经 Jina r.jina.ai 抓取网页正文）→ `utils/validate.py`（三态判定 supported/unsupported/unknown）→ `utils/stat.py` 汇总三项指标：total_citations（每任务平均引用数）、total_valid_citations（每任务平均被验证支持数）、valid_rate（= 有效/总数，即引用准确率）。实测样例：28.07、24.51、0.873。
- 「PAR / OPC / FAP / FAS」四个缩写仅出现在 README 新闻表格（evaluator 选型对照），**在全部代码与数据文件中找不到定义**（未验证，不猜测其含义）。

**借鉴到「Research Engine 自建基准」的参考清单**：一、任务导向的评测框架（任务 prompt 进、报告出）；二、逐任务动态标准与动态权重（避免一套固定 rubric 打天下）；三、参考报告对照打分（给 LLM judge 分数锚点）；四、四维质量框架可直接复用；五、引用可信度管线（提取、去重、抓取、三态验证）可独立复用为引用审计器；六、evaluator 本身要用人标子集校准；七、中英双语与真实需求分布采样。
**依赖与运行**：Python >=3.9；仅 `tqdm`、`pandas`、`numpy`、`requests`。
**认证与成本**：`LLM_BACKEND`（默认 openrouter，可切 openai）+ `OPENROUTER_API_KEY` 或 `OPENAI_API_KEY` + `JINA_API_KEY`（FACT 抓取）；模型默认 `RACE_MODEL=openai/gpt-5.5`、`CLEAN_MODEL=openai/gpt-5.6-luna`、`FACT_MODEL=openai/gpt-5.4-mini`。全部为按量付费 API，无免费额度（金额未验证）。

## richard-kim-79/archora-skills

- URL：https://github.com/richard-kim-79/archora-skills ｜ stars：50 ｜ license：**仓库无 LICENSE 文件**（GitHub license API 404；README 徽章与 `.claude-plugin/plugin.json` 声称 MIT，实际文件缺失，属不一致）
- 创建于 2026 年 5 月 15 日；最近 push 2026 年 5 月 20 日（约 6 个月未更新）
- releases：v1.0.0、v1.1.0（均 2026 年 5 月 15 日）；open issues：0

**真实存在的技能（9 个，均为纯 Markdown 指令、无脚本，合计 732 行）**：
1. `skills/hypothesis/SKILL.md`（72 行）——从笔记/文档生成可证伪的研究假设
2. `skills/validation/SKILL.md`（83 行）——为假设设计实验方案（自变量、因变量、对照、含功效分析的样本量）
3. `skills/draft/SKILL.md`（68 行）——按 IMRaD 结构写论文草稿
4. `skills/figure/SKILL.md`（98 行）——生成 matplotlib/seaborn 与 Mermaid 图表代码
5. `skills/stats/SKILL.md`（85 行）——检查统计错误与逻辑谬误（p-hacking、相关因果混淆等）
6. `skills/counterargument/SKILL.md`（71 行）——生成魔鬼代言人式批评
7. `skills/peer-review/SKILL.md`（99 行）——模拟期刊评审（EIC + 3 位评审人、1 至 10 分、Accept/Minor/Major/Reject 四档结论）
8. `skills/synthesis/SKILL.md`（60 行）——跨笔记提炼交叉主题
9. `skills/wiki-sync/SKILL.md`（96 行）——笔记整理为带 wikilink 的 wiki 知识库
README 并给出七步链条化用法（wiki 整理 → 假设 → 实验设计 → 统计校验 → 草稿 → 模拟评审 → 反驳），这是其设计卖点。

**与两个参照库的差异化（两者均已本地核验 remote）**：
- YuanyuanMa03/academic-research-skills（16 插件、481 文件、2026 年 10 月 29 日更新）：定位是**检索渠道库**（cnki-search、sd-search、wos-search、pm-search 四个平台检索 + scansci-pdf 下载/引用/Zotero 推送 hub + 11 个 nature-* 写作技能）。archora 与之几乎无功能重叠（一个管检索入口，一个管写作链路），属互补。
- KalarisLabs/research-agent-skills（281 技能、3260 文件、2026 年 11 月 13 日更新）：定位是**巨型全科库**，覆盖科研全生命周期（含 peer-review、hypothesis-generation、scientific-writing、statistical-analysis 等），带质量门禁、benchmark 与安全扫描。archora 的 9 项能力在 KalarisLabs 中**基本都有同类对应**，属重复；archora 的补充价值仅在于把 9 个技能串成一条极简链条（单文件、低上下文成本），以及挂接其商业产品。
- 判定：**对两个成熟库而言是「重复为主、补充为辅」**。
**依赖与运行**：无运行时依赖（Markdown 即技能）；需 Agent Skills 兼容宿主（Claude Code 等），安装经 `npx skills add`。

## 总结：各仓库在本项目中的角色建议

1. **smaniches/semantic-scholar-mcp：建议采纳为首选 Semantic Scholar MCP 底座。** 活跃、工程化最扎实（供应链溯源、CI、无 open issue）、工具面最宽（14 个，含 snippet 与 bulk），认证零成本可选。红旗：无（仅提示输出为非结构化字符串，若项目需要结构化输出需自行加壳）。
2. **akapet00/semantic-scholar-mcp：不建议作为底座，可作为设计参考。** 它的输出类型化、会话内论文追踪与作者去重/合并是有价值的思路，可移植到仓库 1；但「服务器无法启动」bug 未修、6 个月停更、Python 3.13+ 门槛与无版本发布构成实质可用性风险。
3. **qwe4559999/scopus-mcp：不建议纳入，除非项目已有机构 Elsevier 订阅。** 该工具的 API key 申请一般要求机构订阅（README 原文），无订阅时摘要与前向引用功能不可用（对应其未修复的 open issue #10），且实现无类型化、3 个 open bug、6 个月停更。若未来需要 Scopus 覆盖，建议在具备机构凭证后重审或自建轻量客户端。
4. **Ayanami0730/deep_research_bench：强烈建议作为「Research Engine 自建基准」的方法论蓝本（建议借鉴而非直接 fork 其评测服务）。** 其四维 RACE 框架、逐任务动态 criteria 与权重、参考报告对照、引用三态验证管线、evaluator 人标校准机制都可直接迁移；注意它自身依赖付费 LLM 与 Jina key，且代码存在 FACT 长文处理缺陷（issue #53）与 judge 模型迁移成本。
5. **richard-kim-79/archora-skills：不建议纳入。** 9 个技能与 KalarisLabs 库高度重复、体量极小、6 个月停更、无 LICENSE 文件（法律状态存疑），且带商业产品引流属性。若要学术写作类技能，应优先评估已本地存在的 KalarisLabs/research-agent-skills（覆盖更全）与 YuanyuanMa03/academic-research-skills（中文检索渠道独有）。

**未验证项清单**（按纪律列出，未猜测）：一、deep_research_bench 的 PAR/OPC/FAP/FAS 具体定义（代码中无出处）；二、scopus-mcp 的免费额度具体数字（README 未提）；三、各付费服务的具体金额（未查定价页）；四、akapet00 服务器启动 bug 在当前 fastmcp 最新版本下的实际复现情况（按纪律未运行其代码）。