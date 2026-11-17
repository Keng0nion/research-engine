# GITHUB-REPOSITORY-RESEARCH

Research Engine v2 的 GitHub 仓库研究与核实总档。
完成日期：2026 年 11 月 17 日。全部结论基于当日实测（`gh api` 元数据 + 8 组源码级审计代理的只读深查），原始审计报告存于 `docs/audit-raw/`（含 `raw/` 子目录下 8 份完整报告）。

**状态图例**：已审计 = 源码级核查完成；已安装 = 文件落到本机；已配置 = 接入 ZCode 配置或引擎；已验证 = 有实测运行记录（可复现）。
**任务书偏差修正**：凡任务书描述与仓库事实不符处，均在第四节逐条修正。不虚构仓库、不凭 README 自述下结论。

## 一、必查 15 仓库核实结果（Part I）

| # | 仓库 | stars | 许可 | 事实要点 | 状态 |
|---|---|---|---|---|---|
| 1 | YuanyuanMa03/academic-research-skills | 79 | MIT | 16 技能；点名项中 gs-search 已被作者移除（文档残留）；cnki/sd/wos 三技能依赖浏览器反检测，合规风险 | 已审计；nature-citation 已安装 |
| 2 | KalarisLabs/research-agent-skills | 153 | MIT（含上游归属） | 281 技能；安全治理最完备（允许域名白名单、CI 门禁）；点名 7 项全部存在；核心学术技能纯标准库 | 已审计；6 技能已安装 |
| 3 | Orchestra-Research/AI-Research-SKILLs | 14589 | MIT | 真实技能库（98 技能，非论文仓库）；核心是 ML 实验训练，检索相关性低；点名 7 项中 3 项零命中（见修正节） | 已审计；未安装 |
| 4 | parallel-web/parallel-agent-skills | 94 | MIT | 点名 6 项全部存在；CLI 路径全部计费（Task 最高每千次 2400 美元）；匿名 MCP 端点免费；评测契约优秀 | 已审计；未安装（契约已借鉴） |
| 5 | damionrashford/RivalSearchMCP | 140 | MIT | 9 工具；评分（457 行）与冲突检测（587 行）为真实实现；**但 easyocr 为硬依赖（会拉 torch 2GB+）** | 已审计；未安装（依赖原因） |
| 6 | cedarsaam/agent-search | 5 | MIT | 声称功能全部真实但无 release、无 CI、4 个月停更、单文件 3.5k 行 | 已审计；未安装 |
| 7 | searxng/searxng | 39602 | AGPL-3.0 | 252 个引擎实现；上游默认禁用 google/bing/yahoo 通用搜索；JSON API 需手动开启 | **已安装/已配置/已验证**（本机回环） |
| 8 | exa-labs/exa-mcp-server | 5238 | MIT | 12 工具（多为 Deprecated）；需付费 key；**Agnost 遥测默认开启且仓内无法关闭** | 已审计；未安装 |
| 9 | firecrawl/firecrawl-mcp-server | 7835 | MIT | 33 工具；keyless 模式仅 3 个可用；反馈上报默认开启需 opt-out；194 open issues | 已审计；未安装 |
| 10 | unclecode/crawl4ai | 87438 | Apache-2.0 | Docker 整栈重（Playwright+Redis+RabbitMQ+Postgres，4GB 内存门槛）；另有 attribution 附加声明 | 已审计；未安装（JS 页面走 Agent 浏览器） |
| 11 | wong2/mcp-jina-reader | 47 | 无许可证 | 停更 23 个月；45 行转发壳；无许可证 = 不可合法复用 | 已审计；未安装（能力以引擎直调覆盖） |
| 12 | cyanheads/openalex-mcp-server | 18 | Apache-2.0 | 5 工具；仓年轻、重度依赖同作者框架 | 已审计；未安装（引擎原生 provider 覆盖） |
| 13 | cyanheads/pubmed-mcp-server | 168 | Apache-2.0 | 12 工具；全文回退链 PMC→EuropePMC→Unpaywall；全免费数据源；Unpaywall 抓取无大小防护（已知 issue） | **已安装/已配置** |
| 14 | blazickjp/arxiv-mcp-server | 3282 | Apache-2.0 | 19 工具（含 LaTeX 逐节精读）；README 警告同名 npm 包供应链陷阱（仅用 PyPI） | **已安装/已配置/已验证** |
| 15 | kujenga/zotero-mcp | 162 | MIT | 3 只读工具，为本机已有 zotero 官方插件的严格子集 | 已审计；未安装（去重） |

## 二、扩展发现（Part II，超出必查清单）

按任务书 45 个关键词 + 补充 12 个关键词做了 GitHub 检索（`gh search repos`，星数与活跃度过滤），新核实仓库如下（均有精确 URL 与元数据核实）。

**已安装**
- https://github.com/nkapila6/mcpsurfr （151★，MIT，活跃）——真本地语义重排（MobileBERT TFLite 纯 numpy）+ 只回答案段落；依赖轻（无 torch）。**已安装/已配置/已验证**

**高价值已审计未安装**
- https://github.com/SepineTam/cnki-mcp （69★，GPL-3.0，活跃）——CNKI 检索限定通道：不提供全文下载（有代码注释佐证）、强制用户本人机构登录、验证码交人工、内置限流。四候选中最合规。列为用户可选步骤（需机构权限，未代装）
- https://github.com/dirmacs/daedra （18★，MIT，Rust）——14 个免 key 后端单二进制聚合；SearXNG 的备用替代
- https://github.com/smaniches/semantic-scholar-mcp （26★，MIT，活跃）——14 工具，工程化最扎实的 S2 MCP
- https://github.com/Ayanami0730/deep_research_bench （851★，Apache-2.0）——RACE 四维 + FACT 引用验证管线，**基准方法论已借鉴**
- https://github.com/CYC2002tommy/Deep-Research-Agent （372★，MIT）——DOI 严格核验的多代理学术管线，参考
- https://github.com/shaun0927/openchrome （237★，MIT）——浏览器自动化 MCP 备选
- https://github.com/gefsikatsinelou/MetaSearchMCP （58★，MIT）——250 provider；太年轻 + LICENSE 署名疑点
- https://github.com/TadMSTR/searxng-mcp （29★，MIT）——SearXNG→重排→四级抓取链；需外部重排服务
- https://github.com/nkapila6/mcpsurfr 之外的聚合候选：dirmacs/daedra（上）与 TadMSTR/searxng-mcp（上）为代表

**已审计排除（含原因）**
- https://github.com/wuruiqi/cnki-mcp （35★）——批量下载 + 反检测（AutomationControlled、随机延迟、关证书校验）→ 合规高风险
- https://github.com/Mangofang/CNKICrawlerMCP （18★）——自动 IP 登录 + 正文接口 + **无许可证** → 排除
- https://github.com/xxxxchaos/cnki-mcp-server （29★）——停滞最久 + 反检测代码 → 备选慎用
- https://github.com/qwe4559999/scopus-mcp （55★）——API key 实质要求机构 Elsevier 订阅；3 个未修 bug
- https://github.com/akapet00/semantic-scholar-mcp （39★）——启动级 bug 未修、6 个月停更
- https://github.com/richard-kim-79/archora-skills （50★）——**无 LICENSE 文件**（README 声称 MIT）+ 6 个月停更
- https://github.com/tisDDM/searxng-mcp （43★）——作者已标注 deprecated
- https://github.com/Shelpuk-AI-Technology-Consulting/kindly-web-search-mcp-server （405★）——搜索层零免 key
- https://github.com/gefsikatsinelou/MetaSearchMCP、https://github.com/trapoom555/claude-paperloom、https://github.com/sanonone/kektordb 等——与现有能力重复或范围外

**生态参考（不安装，仅记录）**
- Alibaba-NLP/DeepResearch（20k★）、SkyworkAI/DeepResearchAgent（3.6k★）、NVIDIA-AI-Blueprints/deep-researcher-agent（934★）——完整深研系统（重型框架），与本项目「Agent 侧工具+引擎」路线互补而非替代

## 三、口头点名项的核实修正（任务书事实性偏差）

1. **gs-search 不存在**：YuanyuanMa03 仓库 CHANGELOG 明确记录 4 个 gs-* 插件因测试超时于 v2.0.0 移除；README 仍留安装命令属文档残留。
2. **Orchestra-Research 点名 7 项中 3 项零命中**：「AI research workflows」「Agent research」「Scientific evaluation」全仓库 grep 无结果；「Research orchestration」「ML research」仅为叙述短语。真实存在的只有 `autoresearch` 与 RAG 分类。
3. **RivalSearchMCP 的「冲突检测」真实存在**（587 行规则实现），但注释里提到的 LLM 语义冲突全库无调用（仅规则版）。
4. **mcp-jina-reader 无许可证**（GitHub API license 为 null），非「MIT 或宽松许可」。
5. **deep_research_bench 的 LICENSE 是 Apache-2.0**（README 徽章写 MIT 属瑕疵）；其 RACE 实测样例 Overall 0.4218（0 至 1 尺度）。
6. **SearXNG 上游现状**：google/bing/yahoo 通用搜索默认禁用（反爬），与「多引擎开箱即用」的常见描述不符；本机实测 google 直连持续 access denied、google cse 正常。

## 四、审计方法备忘（可复现）

- 元数据：`gh api repos/<owner>/<repo>`（stars/license/pushed_at/issues/archived）
- 检索：`gh search repos "<keyword>" --limit 8`（45 + 12 个关键词，2.2 秒间隔）
- 源码审计：`git clone --depth 1` 到 `/tmp/re-audit/`，只读阅读；大仓库用 `gh api` 读树；全程未运行任何仓库代码
- 证据归档：`docs/audit-raw/raw/*.md`（8 份完整报告，合计约 1650 行）
