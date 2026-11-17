# SECURITY-AND-PERMISSION-AUDIT

安全与权限审计档。范围：候选仓库的供应链风险（PART VII）、本机安装物的权限面、引擎代码安全（含每次写入的独立安全门），以及残余风险清单。日期：2026 年 11 月 17 日。

## 一、候选仓库安全结论（摘要，详evidence见 docs/audit-raw/raw/）

| 仓库 | 安全结论 | 处理 |
|---|---|---|
| exa-mcp-server | **Agnost 遥测默认开启且仓内无关闭开关**（api.agnost.ai） | 不安装 |
| firecrawl-mcp-server | 反馈上报默认开启需双环境变量 opt-out；宣称的「Scrape 无 Key 免费」属实但仅 3 工具 | 不安装 |
| RivalSearchMCP | 默认注册托管端点（查询会穿过第三方服务器）；依赖面含 torch | 不安装；若用必须本地部署 |
| crawl4ai | 好设计（Docker 内有 Bearer 认证、egress 防 DNS rebinding）但栈重；README 有云服务推广横幅（无网络行为，可环境变量关） | 不安装 |
| SepineTam/cnki-mcp | 无验证码破解、无代理池、无全文下载（代码注释佐证）、强制本人登录、内置限速 | 列为用户可选（未代装） |
| wuruiqi/cnki-mcp | 反检测三件套（AutomationControlled、随机延迟防风控、关闭证书校验）+ abort 复用一次性签名令牌 | 排除（合规高风险） |
| Mangofang/CNKICrawlerMCP | 自动 IP 登录 + 正文抽取接口 + **无许可证** | 排除 |
| wong2/mcp-jina-reader | 无许可证、停更 23 个月 | 排除 |
| KalarisLabs/research-agent-skills | 自带允许域名白名单、扫描基线（53 条高危逐条复核为误报）、14 条 CI 安全门 | 采用（基座） |
| Orchestra-Research | 安装器无 postinstall、无遥测（独立核实） | 未安装（相关性原因） |

## 二、已安装物的权限面

| 安装物 | 网络面 | 写面 | 权限控制 |
|---|---|---|---|
| SearXNG 容器 | 出站（各搜索引擎抓取）；入站仅 127.0.0.1:8080 | 仅挂载的 core-config 与容器内 | `--cap-drop ALL` + 最小 cap；不对局域网暴露；日志轮转 1MB |
| arxiv MCP（uvx） | export.arxiv.org、arxiv.org、Semantic Scholar | 论文库限定在 `research/papers/arxiv` | uv 隔离环境；无 root |
| pubmed MCP（npx） | NCBI E-utilities、Europe PMC、Unpaywall | 日志目录 | 无凭证亦可运行 |
| mcpsurfr（uvx） | ddgs 引擎、抓取目标站 | 进程内存为主 | 内建拒绝 localhost/私网 URL |
| 7 个学术技能 | 各自文档声明的学术 API（纯标准库脚本，域名硬编码） | 不写系统位置 | 零依赖、可逐行审阅 |
| 引擎（researchctl） | 见「三」的出站清单 | `research/` 与 `cache` 目录内 | 无凭据存储；子进程调用有参数注入防护 |

## 三、引擎出站清单（全部代码内可枚举）

- 学术 API：api.openalex.org、export.arxiv.org、api.crossref.org、eutils.ncbi.nlm.nih.gov、ebi.ac.uk、api.semanticscholar.org、api.unpaywall.org（待邮箱）
- 聚合：127.0.0.1:8080（SearXNG，回环）→ SearXNG 自身再向外
- anysearch 技能 CLI（既有工具）
- **DoH 兜底**：https://1.1.1.1/dns-query（仅当系统 DNS 失败时；JSON 接口、无敏感载荷）
- 文档获取：目标来源 URL（受 robots 与 SSRF 校验约束）
- 未启用：r.jina.ai（文档仅记录）、所有付费 API

## 四、引擎代码安全（每次写盘过独立安全门）

本项目所有代码文件写入均经本机 Mimosa PreToolUse 安全扫描；被拦截并修复的真实问题：

| 检出 | 修复 |
|---|---|
| SQL 注入（字符串拼接入 SQL） | 全部改为静态字面量语句 + 绑定占位符；部分更新用 `COALESCE(?, col)`；超长语句拆分为多条 |
| XML 实体扩展（ElementTree 解析不可信 XML） | 统一 `safe_parse_xml`：拒绝 `<!ENTITY` 与内部 DTD 子集、8MB 上限（允许 PubMed/arXiv 的无毒 DOCTYPE） |
| 命令注入（subprocess 携带用户输入） | 内联参数列表 + `shell=False` + `--` 分隔锚定查询词 + 拒绝 NUL 字节 |
| SSRF（动态 URL 出站） | `url_is_safe`：仅 http/https；逐跳（含每个重定向）解析 IP 并阻断回环/私网/链路本地/CGNAT/组播；手动重定向循环（≤5 跳） |
| 弱哈希（SHA1 作文件名摘要） | 改 SHA-256 |

## 五、防注入与内容信任边界（重要）

- **检索结果、网页正文、PDF 文本、JATS 全文一律视为数据**：不进入指令位置；引擎无基于内容的自动动作；技能文档显式声明该纪律。
- 网页上的「请执行/请忽略」等文本是注入尝试，Agent 一律忽略。
- 抓取遵守 robots.txt（不可达时 fail-open 并记录）；遇登录墙/付费墙如实标记状态，不绕过。
- 20MB 文档上限、40 秒超时、单主机 1 秒间隔，防止资源滥用与站方压力。

## 六、残余风险（如实列出）

1. **DNS rebinding 竞态窗口**：SSRF 校验与 HTTP 客户端各自解析 DNS，理论上存在被精确时序攻击的窗口；单用户本地工具场景判定可接受（已在 fetcher 模块注释与 KNOWN-LIMITATIONS 记录）。
2. **pubmed MCP 的 Unpaywall 抓取无大小上限**（其仓库已知 issue，维护者登记中）：引入的是第三方 MCP 进程，风险面限于该工具被调用时。
3. Mimosa 对 SQL/subprocess 的启发式偏保守，编码规范因此受限（如 SQL 必须单行、子进程必须内联列表），代价换取了持续的门禁。
4. 学术技能脚本为第三方 MIT 代码（已审计为纯标准库、域名硬编码），首次实际调用仍建议留意输出。
5. 本机网络环境存在 SOCKS 代理环境引起的 urllib3 告警（无功能影响，来源未定位）。
6. 反检测类工具（已全部排除或列为用户可选）若未来被用户主动引入，风险由使用者承担——本项目纪律条款继续适用。

## 七、凭据管理

- 引擎与研究数据中**零凭据存储**（可在 `research.db` 全表检索验证）。
- 唯一可选邮箱通过环境变量注入；MCP 侧 key 全部可选且由用户后续自配。
- CNKI 登录态（若启用）只存于用户自己的工具 profile，不进研究记录。
- ZCode 配置改动前已备份；无任何密钥被写入版本库或文档。
