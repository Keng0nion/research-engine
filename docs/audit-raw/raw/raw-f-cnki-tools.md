# CNKI 通道候选仓库审计报告（Research Engine v2 扩展候选，只读深查）

**审计方式与边界**：2026 年 11 月 17 日，`git clone --depth 1` 四个仓库到 `/tmp/re-audit/`，通读全部关键源码文件，辅以 `gh api` 取元数据（stars、license、releases、issues、提交历史）。**未运行任何仓库代码、未执行 install、未访问 CNKI 站点**。下文所有结论均有文件出处；凡属运行时行为（能否真的登录成功、验证码出现频率、选择器是否仍有效）一律标注「未实测」。

---

## SepineTam/cnki-mcp

**基本信息**
- URL：https://github.com/SepineTam/cnki-mcp ；stars 69（审计时）
- License：GPL-3.0。文件：`/tmp/re-audit/SepineTam/cnki-mcp/LICENSE`（标准 GNU GPL v3 全文），SPDX 标识 GPL-3.0
- 最近提交：2026 年 10 月 28 日（`Update pyproject.toml`，v0.2.1）；近期合入 PR #3
- Releases：4 个（v0.1.0、v0.1.1、v0.2.0、v0.2.1，最新 2026 年 10 月 28 日）
- Open issues：0（历史 1 条已关闭：测试未隔离真实 `~/.cnki-mcp` 配置）

**实现机制（关键）**
- **Playwright 驱动浏览器 + DOM 解析**，非官方 API。底层为持久化 Chromium 上下文（`launch_persistent_context`，默认有头），见 `src/cnki_mcp/core/runtime.py`、`core/browser_worker.py`（单线程持有浏览器，避免 Playwright sync API 与 asyncio 冲突）。
- 双检索入口：`easy-search` 走一框式检索 `https://kns.cnki.net/kns8s/defaultresult/index?crossids=...&korder=SU&kw=...`（`tools/basic_search.py`）；`advanced-search` 与统一检索全部走专业检索页 `https://kns.cnki.net/kns8s/AdvSearch?type=expert`，通过 `page.evaluate` 注入 JS 填表达式、提交、应用文献类型与来源类别过滤（`tools/professional_search.py`）。
- 检索列表字段：仅 title、authors、journal、date、url（`server/tool_registry.py::_search_result_to_dict`），**不含摘要**；摘要、关键词、DOI、卷期页码等在详情工具（`get-info-from-url` / `get-info-by-detail`）返回（`core/parsers/detail_parser.py`，`Article` 模型含 abstract、keywords、institution、doi、volume、issue、pages、download_url 字段）。
- 另有内部题录导出接口：`https://kns.cnki.net/dm8/API/GetExport`（POST form，EndNote 格式回传），供 `metadata_lookup` 打分定权使用（`core/tools/export.py`、`metadata_lookup.py`），在用户自己的会话内调用。
- 期刊通道：`navi.cnki.net/knavi/journals/...`（`tools/journal.py`），按 ISSN 定位某一期目录。
- 搜索结果缓存 10 分钟（`server/search_cache.py`，TTL 600 秒）。
- **PDF 下载：无**。仓库内存在 `src/cnki_mcp/core/tools/no-download-now.py`，全文仅一行注释：「暂时不要下载的功能，这个违反了使用规范的。」；MCP server instructions 明确写 `Full-text downloading is not provided`（`server/cnki_mcp_server.py`）。

**访问控制与合规（关键）**
- **未登录不可用**：所有 client 方法先 `ensure_login`（`core/client.py`）；无 profile 直接抛 `LoginRequired`。登录方式为 `fsso.cnki.net`（高校联邦认证入口）打开可见浏览器，**由用户本人完成机构认证**（`core/auth.py`），登录态（cookies.json + storage_state.json）按 profile 存于 `~/.cnki-mcp/profiles/<name>/`。
- 遇知网「请完成安全验证」：检测标题/正文关键词后**抛错交还人工**（`professional_search.py::_raise_for_security_verification`），README 与 Skill 文档均声明「登录、机构认证和验证码由用户亲自完成，不读取凭据」。**无验证码破解、无打码服务、无代理池**（全库 grep `captcha|验证码|proxy|代理|2captcha|ddddocr|打码` 仅命中上述人工处理提示与免责声明文本）。
- 内置节流与配额：默认 1 请求/秒、每 profile 每日 1000 次配额（`core/config.py`、`core/ratelimit.py`），超限抛 `RateLimited`。
- README 含完整免责声明、商标非关联声明，并明确「不应用于非法手段，包括批量访问知网、非正规途径获取论文」。

**工具/命令清单（精确）**
- MCP 业务工具（6 个，HTTP/SSE/stdio 均注册）：`easy-search`、`advanced-search`、`get-info-from-url`、`get-info-by-detail`、`list-journal`、`search-issn`
- stdio 额外：`login`、`logout`、资源 `profile://list`
- CLI：`cnki-mcp init`、`serve [--transport stdio|sse|http --host --port]`、`login`、`logout`、`tool search [--advanced EXPR]`、`tool info`、`tool journal --issn --year --vol`、`tool issn --journal`
- 附带 Skills（`plugins/skills/cnki-search`、`explore-cnki-view`）与 SubAgents（`plugins/agents/`）

**依赖与运行**
- Python ≥ 3.11；依赖仅 `mcp[cli]>=1.28.1,<2.0` 与 `playwright>=1.40.0`（`pyproject.toml`）。**必须安装 Playwright Chromium**。推荐 HTTP 传输（`serve --transport http`，默认 127.0.0.1:7788）。

**维护质量**
- 源码 5844 行、测试 4563 行，**236 个测试函数**；CI（publish.yml）发布前跑 `ruff check` + 全量 `pytest` 再上 PyPI。四仓库中最活跃、工程质量最高。

**结论**：**四者中首选 CNKI 通道（推荐）**。理由：唯一明确自我约束「不提供全文下载」（且有代码注释佐证出于使用规范考虑）、强制用户本人机构登录、验证码只交人工、内置速率与每日配额；同时维护最活跃、测试最厚、提供 MCP/CLI/Python API/Skill 多形态接入，适合 Research Engine v2 以独立服务（HTTP）方式集成。**合规风险评级：低**。依据：无下载、无破解、无代理、无绕过；残余风险仅为「用 Playwright 自动化操作知网页面」这一通用灰区，以及 GPL-3.0 的传染性——若打算把其代码并入本项目需评估许可证，作为独立进程/服务调用则无此问题。未实测项：登录与检索在真实环境的行为、专业检索页选择器现状。

---

## wuruiqi/cnki-mcp

**基本信息**
- URL：https://github.com/wuruiqi/cnki-mcp ；stars 35
- License：MIT。文件：`/tmp/re-audit/wuruiqi/cnki-mcp/LICENSE`（MIT License，Copyright 2026 wuruiqi），`pyproject.toml` 亦声明 MIT
- 最近提交：2026 年 10 月 1 日（`fix(download): fetch CNKI PDFs via httpx instead of in-browser download`）
- Releases：2 个（v0.1.0、v0.2.0，均 2026 年 6 月 13 日）
- Open issues：0 条 issue；1 个**未合并 PR**（#2：适配 mcp 2.x SDK、修多实例 Chrome 崩溃、补类型标注）

**实现机制（关键）**
- **Playwright 驱动浏览器**（异步 API、持久化上下文、强制 `headless=False` 可见窗口）+ 表单提交检索：打开 `https://kns.cnki.net/kns8s/`，填 `#txt_search`，点 `.search-btn`，解析 `.result-table-list` 行（`cnki/search.py`，字段：title、year、journal、authors、citations、url，**不含摘要**）。
- 批量工作流 `cnki_batch`：按发表时间与被引量各取前 N（默认各 50）合并去重，可选与 Zotero 库查重。
- **PDF/CAJ 下载路径（有完整代码证据，`cnki/download.py`）**：详情页找 `a#pdfDown` / `a#cajDown` 点击 → 经 `bar.cnki.net` 落地页跳 `docdown.cnki.net` 签名下载地址；代码用 `ctx.route(re.compile(r"docdown\.cnki\.net"))` **拦截并 abort 浏览器的下载请求**（注释说明：签名 URL 一次性，浏览器真发出去令牌就被消耗，留给 httpx 就只剩 HTML 错误页）；随后快照 Cookie，用 `httpx.AsyncClient(trust_env=False, verify=False)` 独立抓字节落盘。批量下载两篇之间**随机等待 6 至 12 秒**，验证码后额外等 2 倍。
- Zotero 导入：优先本地 connector `http://127.0.0.1:23119`，失败降级云 API `https://api.zotero.org`（`cnki/zotero.py`）；PDF 元数据核对用 PyMuPDF（`cnki/pdf_meta.py`）。

**访问控制与合规（关键）**
- 登录：`cnki_open_login_page` 打开知网首页并等待用户手动完成机构（含 CARSI/FSSO 校外访问）登录，Cookie 仅存 CNKI 域（`cnki/browser.py`）。下载依赖用户自己的机构访问权限（README 写明「有效的 CNKI 机构访问权限」为前提）。
- **明确的规避性设计（读代码确认）**：启动参数含 `--disable-blink-features=AutomationControlled`（隐藏自动化特征，`browser.py:94`）；`ignore_https_errors=True` 与 `--ignore-certificate-errors`（**关闭 TLS 证书校验**，理由为容忍 CDN 证书错配）；批量下载随机间隔的注释原文「降低触发 CNKI 风控的概率」（`download.py:11`）。
- **验证码不破解**：检测阿里云盾滑块等 DOM 特征后，在控制台提示用户**在可见浏览器中手动完成**，轮询等待（默认 120 秒）后重试一次（`download.py:153-180`）。`verify=False` 仅为抓字节直连。
- README 自述知网 IP 级风控会把请求 302 到 `/verify/home`，处理方式是人工过验证或「更换网络出口」；**无内置代理池、无打码服务**。`docs/status.md` 记录 v0.2.1 实测**批量下载 36 篇中文知网 PDF（234.7 MB）**。
- 免责声明仅一行「仅供个人学习研究用途，请遵守 CNKI 服务条款与所在机构的使用规定」。

**工具/命令清单（精确，9 个 MCP 工具，source: server.py）**
`cnki_login_status`、`cnki_open_login_page`、`cnki_save_cookies`、`cnki_search`、`cnki_download_pdf`、`cnki_import_to_zotero`、`cnki_batch`、`cnki_preview_metadata_updates`、`cnki_apply_metadata_updates`。无 CLI（入口即 `python server.py` / 安装后的 `cnki-mcp` 命令，stdio 传输）。

**依赖与运行**
- Python ≥ 3.10；`mcp[cli]`、`playwright`、`httpx`、`pydantic`、`python-dotenv`、`pymupdf`（`requirements.txt`）。**必须装 Playwright**（优先系统 Chrome）；浏览器须保持可见（headless=False 硬编码）。

**维护质量**
- 生产代码约 2360 行（`server.py` 554 行 + `cnki/*.py` 约 1810 行）+ 离线单测 156 行（19 个用例，`tests/test_unit.py`）；CI 只跑离线用例；`tests/` 下大量 `inspect_*`、`probe_*` 现场诊断脚本（按纪律未运行）。issue 区无用户 issue 记录（风控现象写进了 README 而非 issue）。

**结论**：作为**检索 + 下载 + Zotero 一体化**通道能力最完整，但不建议本项目采用。若只取其检索功能，价值不如 SepineTam（无摘要、无专业检索式、无期刊目录）。**合规风险评级：高**（默认启用批量下载路径时）。依据：批量下载（默认 50+50 篇）与知网服务条款的系统性下载限制直接冲突；代码存在三类刻意规避设计（隐藏自动化特征、随机延迟防风控、关闭证书校验，另加 abort 浏览器请求以复用一次性签名令牌）；README 自述 IP 级风控与 302 拦截、实测批量下载 36 篇，说明行为量级已触发知网反爬。不含验证码破解与代理池，若仅用其单篇检索、且关闭一切下载参数，风险可降至中，但这不是它的默认形态。

---

## xxxxchaos/cnki-mcp-server

**基本信息**
- URL：https://github.com/xxxxchaos/cnki-mcp-server ；stars 29
- License：MIT。文件：`/tmp/re-audit/xxxxchaos/cnki-mcp-server/LICENSE`（MIT License，Copyright 2025 CNKI MCP Contributors）
- 最近提交：2026 年 6 月 1 日（`fix: 修复 CNKI 搜索因验证码和选择器失效导致的问题`），**四个仓库中最旧（已停滞约 5 个半月）**
- Releases：1 个（v0.2.0，2026 年 5 月 25 日）
- Open issues：0（仓库无任何 issue 记录）

**实现机制（关键）**
- **Playwright 无头浏览器驱动 + DOM 解析**：浏览器池（`browser.py`，headless=True 硬编码、共享 BrowserContext、空闲 600 秒关闭）；检索走 `www.cnki.net` 一框式表单（`#txt_SearchText`），解析 `table.result-table-list` 行（title、url、authors、source、date、cited_count、download_count，**不含摘要**，`search.py`）；支持 15 种检索字段与 5 种排序、多页翻页。
- 详情页（`detail.py`）解析出 17 字段：中英文标题、作者、机构、**中英文摘要**（`#ChDivSummary` / `#EnChDivSummary`）、中英文关键词、来源、年卷期页、DOI、被引、下载、基金、分类号。访问详情前先访问首页建立会话（注释：避免直接访问摘要页触发验证码）。
- 期刊浏览走 `navi.cnki.net/knavi/`（学科分类、期刊搜索、最新文章）。
- **无全文链接、无 PDF 下载工具**；唯一涉及 Zotero 的是导出格式说明文本。

**访问控制与合规（关键）**
- **完全匿名设计**：全库无任何登录、Cookie 持久化、会话导入逻辑（grep 确认）；检索与详情均匿名访问公开页面。未登录状态可用性：**代码层面成立**，实际可达性未实测。
- 触发验证码（URL 含 verify）时**直接返回错误**「请稍后再试或手动完成验证」；但 headless 模式下面向 MCP 调用者，实际无法人工介入，等价于失败即止。**无破解、无打码**。
- **存在反检测代码**：`--disable-blink-features=AutomationControlled`（`browser.py:106`）、注入脚本把 `navigator.webdriver` 覆写为 undefined（`browser.py:143-147`）、随机 User-Agent 轮换（`config.py`，3 条 UA）。
- 代理：读取 `CNKI_PROXY` / `HTTPS_PROXY` / `ALL_PROXY` 等环境变量注入 Playwright（`browser.py:30-60`），属用户自备代理，非内置代理池；故障排查文档建议「更换代理 IP 或使用住宅 IP」应对 418 拦截。
- 首次调用若浏览器缺失会**自动执行 `playwright install chromium`**（`browser.py::_install_browser`，含 Ubuntu 26 的 fallback）。

**工具/命令清单（精确，6 个 MCP 工具，source: server.py）**
`search_cnki`、`get_paper_detail`、`find_best_match`、`format_citation`（离线）、`browse_journals`、`export_papers`（离线，CSV/JSON/BibTeX/RIS）；资源 4 个：`cnki://search-types`、`cnki://status`、`cnki://citation-styles`、`cnki://export-formats`。无 CLI 业务命令（`python -m cnki_mcp` 即启动 stdio 服务）。

**依赖与运行**
- Python ≥ 3.10；`fastmcp>=2.0.0`、`playwright>=1.40.0`、`httpx[socks]`（`pyproject.toml`）。**必须装 Playwright Chromium**。

**维护质量**
- 生产代码约 2090 行 + 离线测试约 350 行（citation/export/match/utils/config，约 40 个用例）；CI 跑 ruff + pytest（Python 3.10 至 3.13 矩阵）。风险点：**停滞最久**，且最后一次提交标题即「修复验证码和选择器失效」，`config.py` 注释的前端验证日期标为「2025-05-25」（与仓库 2026 年 5 月创建不符，疑似笔误），选择器漂移风险最高。

**结论**：若只求「免登录拿公开元数据」，是四者中唯一的纯匿名方案，且**零下载、零付费墙绕过**，行为面最窄；但维护停滞、无头模式遇验证码即死、反检测代码并存。**合规风险评级：中**。依据：无下载、无破解、无登录盗用，匿名抓取的是公开检索页与摘要页；但存在明确的反检测规避代码（webdriver 覆写、AutomationControlled）与代理绕行建议，属反爬对抗性质，且批量翻页（最多 10 页/次）语义上仍属自动化采集。不建议作为主通道，可作为免责登录场景的备选并慎用。

---

## Mangofang/CNKICrawlerMCP

**基本信息**
- URL：https://github.com/Mangofang/CNKICrawlerMCP ；stars 18
- License：**无**。仓库内无 LICENSE 文件，`gh api` 返回 `license: null`（默认保留全部权利，**不可合法复用代码**）
- 最近提交：2026 年 10 月 16 日（`检索结果与详情页补充发表年份`）
- Releases：4 个（1.0.0 至 1.1.1，最新 2026 年 10 月 16 日，tag 形如 `2026/10/16`）
- Open issues：0（历史 1 条已关闭：**「下载论文2篇以后有验证码」**，正文称「成功下载两篇论文后就失败，好像是被 cnki 限制了，后续手动点击下载，都需要点击验证码」，无回复记录）

**实现机制（关键）**
- **Go 直连 KNS 内部 AJAX 接口**（colly + goquery，无浏览器）：检索 POST `https://kns.cnki.net/kns8s/brief/grid`，请求体 `QueryJson`（Resource=CROSSDB，主题字段 SU/Operator=TOPRANK），**翻页参数 `turnpage` 为硬编码令牌** `vLP2bNpghntZLRq9Q5Y7Qg!!`（`scanner.go:107`；`types/types.go` 注释：「翻页触发人机验证关键参数 第9页的 turnpage = ... 可查1~17页」）。单次检索上限如实限定 50 条（`maxTotalResults`，代码注释批评「对外宣称 100 却只给得出 50」）。
- 检索结果字段：标题、作者、来源、来源链接、年份、发表时间原文、网络首发标记、**复合/综合影响因子**（逐期刊从 `knavi.cnki.net` 抓取，24 小时进程内缓存；`scanner.go`、`throttle.go`）。
- 详情（`GetPaperInfo`）：解析详情页返回**摘要** + `#cajDown`、`#pdfDown`、`.btn-html` 三个链接（CAJ/PDF 下载链接与 HTML 在线阅读链接）——**工具本身不落地任何文件**，只回传链接。
- **正文提取（`GetPaperMainBody`）**：由 HTML 阅读链接的 302 跳转提取 `invoice/fileName/tableName/dbCode`，GET `https://kns.cnki.net/nzkhtml/knsread/litNotes/getPaperInfo?...` 拿章节 JSON，剥标签还原为纯文本正文（`scanner.go:359-383`、`ulti.go::RestoreArticleText`）。README 注明「仅订阅套餐中允许查看的」。
- 登录：**自动 IP 登录**——`IpLogin()` 直接 POST `https://login.cnki.net/TopLoginCore/api/loginapi/IpLoginFlushPo`（空 JSON）换取机构 IP 登录 Cookie 存全局变量（`ulti.go:205-244`）；校园网 IP 环境下自动获得机构会话，无需用户操作；非校园网环境需手动 `SetGlobalCookie` 粘贴自己的 Cookie。每个工具入口先 `CheckLogin`，Cookie 失效自动重登一次。

**访问控制与合规（关键）**
- 未登录不可用：无 Cookie 时自动尝试 IP 登录，失败即报「请确认处于校园网环境」（`RefreshLogin`）。
- 风控处理：检测「滑动验证/人机验证/安全验证/captcha」等字样后返回 `ErrBlocked` 错误，**不绕过、不破解**；登录页字样单独识别为 Cookie 失效（避免误报风控）。
- 节流：全局最小间隔 1.2 秒 + 0 至 0.9 秒随机抖动，指数退避重试（`ErrBlocked`/`ErrCookieExpired` 不重试）（`throttle.go`）。
- **风险点**：自动 IP 登录使工具可静默占用机构 IP 资源（机构与知网之间的接入协议约束此类自动化使用）；正文接口把在线阅读的章节内容整体拉成纯文本，超出「检索元数据」范畴；硬编码 turnpage 令牌被注释标注为「翻页触发人机验证关键参数」，带有工程上绕开翻页触发点的意味（该令牌是否仍有效未实测）；closed issue 显示真实用户下载 2 篇即遭验证码。
- README 免责声明：「仅为技术研究目的开发，使用本工具产生的任何法律问题与开发者无关」。

**工具/命令清单（精确，5 个 MCP 工具，source: main.go）**
`ScanPaper`（检索，参数 value/pageSize/pageNum/withFactors）、`GetPaperInfo`（详情+摘要+三个链接）、`GetPaperMainBody`（正文纯文本）、`SetGlobalCookie`、`GetGlobalCookie`。无 CLI。

**依赖与运行**
- Go ≥ 1.24.5 构建；`github.com/mark3labs/mcp-go`、`github.com/gocolly/colly/v2`、`github.com/PuerkitoBio/goquery`（`go.mod`）。**无需浏览器**（纯 HTTP 抓取）。

**维护质量**
- 1300 行 Go，**零测试、无 CI、无 LICENSE**；提交活跃至 2026 年 10 月，代码注释质量意外地好（如实记录接口限制与历史 bug 根因）。

**结论**：**不推荐**。**合规风险评级：高**。依据：三项独立高危证据——自动 IP 登录接口取机构会话（无需用户在场）、正文全文抽取接口（在线阅读数据的整体抓取）、硬编码翻页令牌；叠加**无许可证**（代码不可复用，仅可参考）与用户 issue 佐证 2 篇下载即触发验证码。检索元数据能力本身不错（含影响因子），但获取方式与扩展面均越过本项目应守的边界。

---

## 横向对比与推荐

| 维度 | SepineTam | wuruiqi | xxxxchaos | Mangofang |
|---|---|---|---|---|
| 语言/运行时 | Python ≥ 3.11 + Playwright Chromium | Python ≥ 3.10 + Playwright（需可见） | Python ≥ 3.10 + Playwright（无头） | Go ≥ 1.24.5（无浏览器） |
| 访问方式 | 驱动浏览器（专业检索页/一框式/详情/navi） | 驱动浏览器（一框式/详情） | 驱动浏览器（一框式/详情/navi，匿名） | 直连 KNS 内部 AJAX 接口 |
| 检索结果含摘要 | 否（详情工具另取，含关键词/DOI） | 否 | 否（详情 17 字段含中英文摘要） | 详情含摘要（另有正文接口） |
| PDF/全文下载 | **无，显式禁用** | 有，批量 + 随机延迟防风控 | 无 | 不落地文件，回传 PDF/CAJ/正文链接 |
| 需登录 | 必须，用户本人机构认证 | 需要（机构权限），用户手动登录 | 不需要（匿名） | 自动 IP 登录或手动 Cookie |
| 验证码处理 | 报错交人工 | 暂停等人工 | 报错（无头下即失败） | 报错即止 |
| 反检测/规避代码 | 无 | AutomationControlled、随机延迟、关证书校验、abort 保 token | AutomationControlled、webdriver 覆写、UA 轮换、代理注入 | 节流抖动（无隐藏特征） |
| 许可 | GPL-3.0 | MIT | MIT | **无** |
| 维护活跃度 | 最高（2026 年 10 月 28 日，4 releases，236 测试） | 中（2026 年 10 月 1 日，2 releases，19 测试） | 低（2026 年 6 月停滞，1 release） | 中（2026 年 10 月 16 日，无测试） |
| 合规评级 | **低** | 高 | 中 | 高 |

**推荐**：**SepineTam/cnki-mcp** 作为 Research Engine v2 的 CNKI 通道。理由按权重排序：一、它是唯一把「不下载全文」写进代码与产品说明的方案（`no-download-now.py`、MCP instructions），与我们对 CNKI 通道「只做检索与元数据」的定位完全一致；二、访问控制模型最干净——强制用户本人机构登录、验证码只交人工、内置 1 请求/秒与每日 1000 次配额；三、维护最活跃、测试最厚（236 个测试函数、发布前全量 pytest），选择器漂移风险有持续修复机制；四、接入形态最全（HTTP MCP 服务可直接作为本项目的外部工具，也可 CLI/Python API 调用），便于与现有检索编排解耦。注意两点：GPL-3.0 代码不要直接并入本项目仓库，以独立服务进程调用；未实测其登录链路在当前知网环境下的可用性，建议接入前做一次人工冒烟（走一次 `init` + `easy-search`）。

---

## 最终总结：CNKI 通道在本项目「中文文献检索」中的可用性

1. **可用性结论**：CNKI 元数据检索（题名、作者、来源、年份、被引，进一步可取摘要、关键词、DOI、卷期页码）经上述任一仓库均可实现，但**推荐仅采用 SepineTam 通道，且限定在检索与题录元数据范围**。检索结果层面的差异：SepineTam 检索列表不含摘要但详情完整且支持专业检索式与期刊目录；xxxxchaos 可免登录但停滞最久；wuruiqi 检索面最窄（无摘要无检索式）而其价值集中在下载（本项目不需要）；Mangofang 的设计边界超出可接受范围。四者的运行时可用性（登录是否成功、选择器是否仍有效、风控触发频率）本次均**未实测**，报告只在代码与文档证据层面成立。

2. **合规红线提示**（建议写进项目规范）：
   1. **不使用任何 CNKI 全文/PDF 下载功能**，含 wuruiqi 的 `cnki_download_pdf` 与 `cnki_batch` 下载路径、Mangofang 的正文接口；本项目 CNKI 通道只取检索结果与题录元数据。
   2. **不使用自动 IP 登录**（Mangofang 的 `IpLogin` 模式）：机构 IP 资源的使用须由本人、按机构与知网约定进行，不得由工具静默占用。
   3. **不共享机构凭据**：登录态仅存本机 profile，凭据与 Cookie 不进版本库、不跨人分发。
   4. **不绕过风控**：验证码一律人工处理；不得引入打码服务、代理池、指纹伪装（webdriver 覆写、AutomationControlled 之类）来对抗知网的反爬判定。
   5. **严守频率上限**：以 SepineTam 默认值（1 请求/秒、每 profile 每日 1000 次）作为上限参考，不做批量并发采集。
   6. **许可证卫生**：SepineTam 为 GPL-3.0（隔离调用）；Mangofang 无许可证（代码禁止复用，仅可阅读参考）；wuruiqi 与 xxxxchaos 为 MIT。
   7. **元数据使用边界**：知网题录字段的使用与再分发（尤其进入对外产物）应遵守知网服务条款与著作权法对数据库/汇编内容的限制，检索结果仅用于内部调研与引证定位，署名数据以原文为准。
   8. **保留人工复核**：CNKI 页面结构频繁变更，通道输出（尤其年份、来源、作者切分）须经检索质量抽检，异常时回退人工检索。

**关键文件索引（供后续接入）**：`/tmp/re-audit/SepineTam/cnki-mcp/src/cnki_mcp/core/tools/professional_search.py`（专业检索实现）、`/tmp/re-audit/SepineTam/cnki-mcp/src/cnki_mcp/core/auth.py`（登录与 profile）、`/tmp/re-audit/SepineTam/cnki-mcp/src/cnki_mcp/core/ratelimit.py`（限流配额）、`/tmp/re-audit/SepineTam/cnki-mcp/src/cnki_mcp/server/cnki_mcp_server.py`（MCP 注册）；下载与风控对照证据在 `/tmp/re-audit/wuruiqi/cnki-mcp/cnki/download.py`、`/tmp/re-audit/wuruiqi/cnki-mcp/cnki/browser.py`、`/tmp/re-audit/xxxxchaos/cnki-mcp-server/cnki_mcp/browser.py`、`/tmp/re-audit/Mangofang/CNKICrawlerMCP/ulti.go` 与 `scanner.go`。