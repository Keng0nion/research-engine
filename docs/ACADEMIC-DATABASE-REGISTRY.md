# ACADEMIC-DATABASE-REGISTRY

学术数据库覆盖登记表：每个数据库的通道、凭证、能力边界与实测状态。

## 已接入（Through the engine）

| 数据库 | 通道 | 覆盖 | 凭证 | 全文能力 | 状态 |
|---|---|---|---|---|---|
| OpenAlex | REST（引擎原生 + arxiv MCP 的引用图底层） | 2.5 亿+ 作品、作者、机构、主题、资助 | 免 key | 元数据 + OA 链接（best_oa_location） | 已验证 |
| arXiv | Atom API（引擎原生 + arxiv MCP 19 工具） | 预印本（物理/数学/CS/生物/经济） | 免 key | **PDF 全文下载 + LaTeX 逐节精读**（MCP 本地库） | 已验证（PDF 148K 字符全文获取实测） |
| Crossref | REST（引擎原生 + nature-citation 技能 + 引文核验） | DOI 注册库（1.5 亿+ 记录） | 免 key（mailto 礼貌） | 元数据；JATS 摘要 | 已验证 |
| PubMed | E-utilities esearch/esummary/**efetch**（引擎原生 + pubmed MCP） | MEDLINE 3700 万+ 生物医学文献 | 免 key（NCBI_API_KEY 可选提速） | 摘要（efetch）；落地页被 bot 挑战不可抓（引擎已特判） | 已验证 |
| Europe PMC | REST（引擎原生 + pubmed MCP） | 生物医学 + 预印本 + 专利；**OA 全文 XML** | 免 key | **fullTextXML（JATS）全文** | 已验证（71K 字符 JATS 全文实测） |
| Semantic Scholar | Graph API（引擎原生 + 引用图） | 2 亿+ 论文、引用图、TLDR | 免 key（共享池限速） | OA PDF 链接 | 已验证（25 条引用边实测；429 自动重试） |
| Unpaywall | REST（引擎解析器） | 全 DOI 开放获取解析 | **必须邮箱** | 指向合法 OA 副本 | 已配置待邮箱（RE_CONTACT_EMAIL） |

## 覆盖但未直连（经由其他通道）

| 数据库 | 通道 | 说明 |
|---|---|---|
| CNKI（知网） | 用户可选：SepineTam/cnki-mcp（未代装） | 检索与题录限定；不下载全文；用户本人机构登录；内置 1 req/s 与每日 1000 次上限；合规评级低（四候选中最优）。启用步骤见 INSTALLATION-AND-CONFIGURATION.md |
| 82 个科研数据库端点 | database-lookup 技能（纯提示词文档，按需加载） | 含 ChEMBL、ClinicalTrials、Ensembl、UniProt 等端点说明 |
| PMC | 经 Europe PMC / pubmed MCP 全文链 | 引擎侧走 Europe PMC fullTextXML |
| iCite（NIH 引用指标） | pubmed MCP 工具 | RCR、NIH 百分位、引用数 |
| Zenodo / Figshare / DOAJ / OpenCitations / PubTator3 / ROR | paper-lookup 技能（18 源） | Agent 侧直查 |

## 明确排除

| 数据库 | 原因 |
|---|---|
| Scopus（Elsevier） | API key 实质要求机构订阅；qwe4559999/scopus-mcp 有未修复 bug，未采纳 |
| Web of Science | 无合规免 key 通道；YuanyuanMa03 的 wos-search 依赖已登录浏览器 + 内部 API + 反检测，合规风险 |
| ScienceDirect 全文 | 同上（sd-search 浏览器爬取被排除）；摘要级元数据可经 OpenAlex/Crossref 覆盖 |
| Google Scholar | 无官方 API；gs-search 已被作者移除；经 SearXNG google cse 引擎间接覆盖 |
| Sci-Hub / LibGen | 明确排除（灰色渠道） |

## 引文情报能力（MODULE 6）与各库的关系

- 后向引用（references）：Semantic Scholar `references` 端点（实测 25 条）
- 前向引用（cited_by）：Semantic Scholar `citations` + OpenAlex `filter=cites:W...`
- 引文存在性核验：DOI → Crossref 优先，失败回退 OpenAlex（覆盖 arXiv DOI）；标题 → Crossref/OpenAlex/arXiv 三源比对（相似度 0.72/0.8 双阈值）
- 主张级验证（某文献是否真支持某主张）：需阅读判断，由 Agent 完成并记入证据卡 `citation_status`
